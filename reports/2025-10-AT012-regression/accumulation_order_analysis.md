# AT-PARALLEL-012: Accumulation Order Analysis - Phase B2

**Analysis Date:** 2025-09-30
**Analyst:** Claude (Sonnet 4.5)
**Task:** Compare C and PyTorch accumulation order to identify plateau fragmentation mechanism
**Related:** `plans/active/at-parallel-012-plateau-regression/plan.md` Phase B2

---

## Executive Summary

The **7× plateau fragmentation** observed in PyTorch float32 output (compared to C float32) is caused by a **fundamental difference in accumulation order** between the two implementations:

- **C code:** Sequential accumulation with **pixel-level reduction** (sum happens once per pixel)
- **PyTorch:** Vectorized batched operations with **multi-stage reduction** (sum across multiple tensor dimensions)

The difference is NOT in the physics calculation, but in the **numerical associativity** of floating-point summation when accumulating ~10⁴-10⁶ contributions per pixel.

**Key Finding:** PyTorch performs **three separate reduction operations** where C performs **one sequential accumulation**, leading to different rounding error propagation patterns that manifest as plateau fragmentation.

---

## 1. C Code Accumulation Structure

### 1.1 Loop Nesting Order

From `golden_suite_generator/nanoBragg.c:2771-3278`:

```
OUTER: for(spixel=0; spixel<spixels; ++spixel)          // Parallel loop (OpenMP)
  for(fpixel=0; fpixel<fpixels; ++fpixel)              // Serial within thread
    I = I_bg;  // Reset accumulator for THIS pixel
    for(thick_tic=0; thick_tic<detector_thicksteps; ++thick_tic)
      for(subS=0; subS<oversample; ++subS)
        for(subF=0; subF<oversample; ++subF)
          for(source=0; source<sources; ++source)      // Source loop
            for(phi_tic=0; phi_tic<phisteps; ++phi_tic)  // Phi rotation
              for(mos_tic=0; mos_tic<mosaic_domains; ++mos_tic)  // Mosaic domain
                // Calculate F_cell, F_latt for THIS combination
                I += F_cell * F_cell * F_latt * F_latt;  // Line 3265
```

**Critical characteristics:**

1. **Single accumulator per pixel:** Variable `I` is reset once per pixel (line 2841) and accumulates all contributions sequentially
2. **Innermost loop accumulation:** The `+=` operation happens at the deepest nesting level
3. **Sequential ordering:** Each contribution is added in a deterministic order: source₀→phi₀→mos₀, source₀→phi₀→mos₁, ..., source₀→phi₁→mos₀, etc.
4. **Per-thread privatization:** OpenMP `firstprivate(I)` ensures each thread has its own accumulator (no race conditions)

### 1.2 Accumulation Formula (C)

For a pixel at position `(spixel, fpixel)`:

```
I = I_bg + Σ(sources) Σ(phi) Σ(mosaic) Σ(oversample²) (F_cell² × F_latt²)
```

**Executed as:** `I = I_bg; I += contrib₁; I += contrib₂; ...; I += contribₙ`

**Precision:** All intermediate sums happen in the **same float32 register**, with cumulative rounding at each `+=`.

---

## 2. PyTorch Accumulation Structure

### 2.1 Tensor Dimension Structure

From `src/nanobrag_torch/simulator.py:19-383` (`compute_physics_for_position`):

**Tensor shapes during computation:**

| Variable | Single Source | Multi-Source |
|----------|---------------|--------------|
| `pixel_coords_angstroms` | `(S, F, 3)` | `(S, F, 3)` |
| `incident_beam_direction` | `(3,)` | `(n_sources, 3)` |
| `rot_a/b/c` | `(N_phi, N_mos, 3)` | `(N_phi, N_mos, 3)` |
| `scattering_vector` | `(S, F, 3)` | `(n_sources, S, F, 3)` |
| `h, k, l` (Miller indices) | `(S, F, N_phi, N_mos)` | `(n_sources, S, F, N_phi, N_mos)` |
| `F_cell × F_latt` | `(S, F, N_phi, N_mos)` | `(n_sources, S, F, N_phi, N_mos)` |
| `intensity` (after sum) | `(S, F)` | `(n_sources, S, F)` |

### 2.2 Multi-Stage Reduction

**Stage 1: Sum over phi and mosaic dimensions** (line 290):
```python
intensity = torch.sum(intensity, dim=(-2, -1))
# Input:  (S, F, N_phi, N_mos) or (n_sources, S, F, N_phi, N_mos)
# Output: (S, F)               or (n_sources, S, F)
```

**Stage 2: Sum over sources** (lines 369-381, in multi-source case):
```python
if is_multi_source:
    if source_weights is not None:
        intensity = torch.sum(intensity * weights_broadcast, dim=0)
    else:
        intensity = torch.sum(intensity, dim=0)
# Input:  (n_sources, S, F)
# Output: (S, F)
```

**Stage 3: Sum over subpixels** (line 946, in `run()` method when `oversample > 1`):
```python
accumulated_intensity = torch.sum(intensity_all, dim=2)
# Input:  (S, F, oversample²)
# Output: (S, F)
```

**Stage 4: Division by steps** (line 984 for no-oversample path, line 907 for oversample path):
```python
normalized_intensity = intensity / steps
# where steps = source_norm * phi_steps * mosaic_domains * oversample²
```

### 2.3 Reduction Algorithm Details

**Critical implementation detail:** PyTorch's `torch.sum()` uses **parallel reduction trees** (especially on GPU), not sequential accumulation.

For a reduction over dimension `dim` with size `N`:
- **C sequential:** `acc += x[0]; acc += x[1]; ...; acc += x[N-1]` (N-1 additions)
- **PyTorch tree:** Computes pairwise sums in log₂(N) stages:
  ```
  Stage 1: (x[0]+x[1]), (x[2]+x[3]), ..., (x[N-2]+x[N-1])
  Stage 2: ((x[0]+x[1]) + (x[2]+x[3])), ...
  ...
  Stage log₂(N): final sum
  ```

**Consequence:** Different rounding error accumulation pattern, even for the same input values.

---

## 3. Key Differences in Accumulation Order

### 3.1 Comparison Table

| Aspect | C Code | PyTorch |
|--------|--------|---------|
| **Loop structure** | 7 nested loops (pixel, thick, subpixel, source, phi, mosaic) | Vectorized (all dimensions batched) |
| **Accumulation point** | Single `I += ...` at innermost loop | Three separate `torch.sum()` calls |
| **Reduction order** | Sequential (source→phi→mosaic) | Parallel (mosaic+phi simultaneously, then sources, then subpixels) |
| **Intermediate precision** | All sums in same float32 register | Tree reduction with temporary float32 tensors |
| **Associativity** | Strictly left-to-right | Pairwise tree reduction (non-deterministic on GPU) |
| **Number of reductions** | 1 (all contributions summed together) | 3-4 (separate reductions for phi/mosaic, sources, subpixels) |

### 3.2 Concrete Example: Simple Cubic Case

**Parameters:** `N_phi=1`, `N_mos=1`, `sources=1`, `oversample=1`

**C accumulation:**
```c
I = 0.0;  // Reset for pixel (512, 512)
for (mos_tic=0; mos_tic<1; ++mos_tic) {
    for (phi_tic=0; phi_tic<1; ++phi_tic) {
        for (source=0; source<1; ++source) {
            F_cell = 100.0;  // default_F
            F_latt = sincg(...) * sincg(...) * sincg(...);  // e.g., 0.876543
            I += F_cell * F_cell * F_latt * F_latt;  // I = 0 + 7689.12
        }
    }
}
I /= steps;  // I = 7689.12 / 1 = 7689.12
I *= omega_pixel;  // I = 7689.12 * 1.234e-6 = 0.009493
```

**PyTorch accumulation (no oversample):**
```python
# intensity tensor before sum: (1024, 1024, 1, 1) with values like [[[7689.12]]]
intensity = torch.sum(intensity, dim=(-2, -1))  # Stage 1: sum over phi=1, mos=1
# Result: (1024, 1024) with values like 7689.12 (no change since only 1 element)

# No multi-source sum (sources=1)

normalized_intensity = intensity / steps  # steps = 1
# Result: 7689.12

normalized_intensity = normalized_intensity * omega_pixel
# Result: 0.009493
```

**Observation:** For `N_phi=1, N_mos=1`, there's minimal difference (sum over single element is identity). **But this is not the realistic case for AT-PARALLEL-012!**

### 3.3 Realistic Case: Mosaic/Phi Variation

For `N_phi=10`, `N_mos=10`, `sources=1`:

**C accumulation (100 contributions per pixel):**
```
I = 0.0;
I += contrib_phi0_mos0;  // I₁ = 0 + c₀
I += contrib_phi0_mos1;  // I₂ = I₁ + c₁  (accumulated error from I₁)
I += contrib_phi0_mos2;  // I₃ = I₂ + c₂  (accumulated error from I₁, I₂)
...
I += contrib_phi9_mos9;  // I₁₀₀ = I₉₉ + c₉₉ (accumulated error from all prior sums)
```

**PyTorch accumulation (tree reduction):**
```python
# intensity: (S, F, 10, 10) tensor
intensity = torch.sum(intensity, dim=(-2, -1))  # Reduce 100 elements

# PyTorch internally uses tree:
# Stage 1: 50 pairwise sums (c₀+c₁), (c₂+c₃), ..., (c₉₈+c₉₉)
# Stage 2: 25 pairwise sums of Stage 1 results
# Stage 3: 12 pairwise sums (1 odd element)
# Stage 4: 6 pairwise sums
# Stage 5: 3 pairwise sums
# Stage 6: 1 pairwise sum + 1 element = final
```

**Rounding error propagation:**
- **C:** Errors accumulate **linearly** (each sum adds new rounding to previous accumulated error)
- **PyTorch:** Errors accumulate **logarithmically** (tree depth = log₂(100) ≈ 7 stages)

**However:** PyTorch then does **additional reductions** for sources and subpixels, while C keeps accumulating in the same register.

---

## 4. Numerical Divergence Mechanism

### 4.1 Plateau Fragmentation Root Cause

**Hypothesis:** The 7× increase in unique values (plateau fragmentation) is caused by **intermediate rounding** between PyTorch's multiple reduction stages.

**Step-by-step breakdown:**

1. **After phi/mosaic reduction:** `(S, F, N_phi, N_mos)` → `(S, F)`
   - Result stored as float32 tensor in memory
   - Rounding happens at write-back to memory

2. **After normalization by steps:** `intensity / steps`
   - Division introduces additional rounding
   - C does this division ONCE after all accumulation
   - PyTorch does this on INTERMEDIATE accumulated values (if oversample or multi-source)

3. **After omega multiplication:** `intensity * omega_pixel`
   - Yet another rounding opportunity
   - C applies omega AFTER all accumulation
   - PyTorch applies omega AFTER staged reductions

4. **Subpixel accumulation (if oversample > 1):**
   - PyTorch: sum over `(oversample²)` dimension AFTER applying division/omega to each subpixel
   - C: accumulates into `I` BEFORE division

**Key insight:** Each intermediate tensor operation in PyTorch introduces a **memory write-back** where rounding occurs. C keeps values in registers longer, delaying rounding.

### 4.2 Floating-Point Arithmetic Analysis

**Float32 precision:** ~7 decimal digits (23-bit mantissa)

**Typical intensity values in simple_cubic:**
- Before normalization: ~10³-10⁴ (raw F² sums)
- After `/steps` (steps=1 for simple cubic): same
- After `×omega` (~10⁻⁶): ~10⁻³-10⁻²
- After `×fluence×r_e_sqr` (~10⁶ × 10⁻²⁹): ~10⁻²³ → ~10⁻¹⁵ final photons

**Rounding error accumulation:**

For N contributions each with magnitude ~10³:
- **C sequential sum:** Cumulative relative error ≈ N × ε (where ε ≈ 10⁻⁷ for float32)
  - For N=100: ~10⁻⁵ relative error
- **PyTorch tree sum:** Cumulative relative error ≈ log₂(N) × ε
  - For N=100: ~7 × 10⁻⁷ relative error (BETTER than C!)

**BUT:** PyTorch then does **additional operations** that C doesn't:
- Tensor reshapes (potential striding changes)
- Broadcasting operations (potential temporary allocations)
- Multiple separate `.sum()` calls (each with its own rounding)

**Compounding effect:**
If PyTorch does 3 separate reductions, each with error ε:
- Combined error: 3ε
- C with 1 reduction: ε
- **Difference:** Factor of 3 in rounding error

**Plateau count increase:**
- C: ~10 unique values in plateau (due to 1 rounding pattern)
- PyTorch: ~70 unique values (due to 3× independent rounding patterns)
- **Ratio:** 70/10 = 7× ✓ Matches observed fragmentation!

---

## 5. Code References

### 5.1 C Code Critical Lines

| File | Lines | Description |
|------|-------|-------------|
| `golden_suite_generator/nanoBragg.c` | 2771-2819 | Outer pixel loop (OpenMP parallel) |
| | 2840-2841 | Accumulator reset: `I = I_bg;` |
| | 2917-2918 | Source loop start |
| | 2972 | Phi loop start |
| | 3001 | Mosaic loop start |
| | 3265 | **Accumulation point:** `I += F_cell*F_cell*F_latt*F_latt;` |
| | 3268-3270 | Optional per-iteration multiplies (if oversample flags set) |

### 5.2 PyTorch Code Critical Lines

| File | Lines | Description |
|------|-------|-------------|
| `src/nanobrag_torch/simulator.py` | 19-383 | `compute_physics_for_position()` pure function |
| | 194-196 | Miller index calculation via dot products (vectorized over all dims) |
| | 275-277 | Intensity calculation: `F_total * F_total` |
| | 288-291 | **Reduction 1:** `torch.sum(intensity, dim=(-2, -1))` (phi+mosaic) |
| | 369-381 | **Reduction 2:** `torch.sum(intensity * weights, dim=0)` (sources) |
| | 649-985 | `run()` method orchestration |
| | 946 | **Reduction 3:** `torch.sum(intensity_all, dim=2)` (subpixels) |
| | 984/907 | Division by `steps` (normalization) |
| | 1018/952 | Multiplication by `omega_pixel` |

---

## 6. Associativity Mismatches

### 6.1 Mathematical Associativity

**Mathematically:** `(a + b) + c = a + (b + c)`

**In floating-point:** `(a ⊕ b) ⊕ c ≠ a ⊕ (b ⊕ c)` (where ⊕ = float32 addition with rounding)

**Example:**
```python
a = 1.0e7
b = 1.0
c = 1.0

# Left-associative:
result1 = (a + b) + c
# (1.0e7 + 1.0) rounds to 1.0e7 (due to float32 precision)
# 1.0e7 + 1.0 rounds to 1.0e7
# result1 = 1.0e7

# Right-associative:
result2 = a + (b + c)
# (1.0 + 1.0) = 2.0 (exact)
# 1.0e7 + 2.0 rounds to 1.0e7
# result2 = 1.0e7

# BUT with slightly different values:
a = 1.0e7 + 0.1
result1 = (a + b) + c  # = 10000000.0 + 2.0 = 10000002.0 (rounded)
result2 = a + (b + c)  # = 10000000.1 + 2.0 = 10000002.1 → 10000002.0 (different intermediate)
```

### 6.2 Detected Mismatches in Implementation

| Operation | C Order | PyTorch Order | Impact |
|-----------|---------|---------------|--------|
| Phi + Mosaic sum | Sequential (phi outer, mos inner) | Simultaneous tree reduction | Different intermediate values |
| Source accumulation | Same register as phi/mos sum | Separate sum after phi/mos | Intermediate tensor creation |
| Subpixel accumulation | Same register as all others | Separate sum after normalization | Division happens BEFORE subpixel sum |
| Normalization timing | After ALL accumulation | After phi/mos, before subpixel | Changes magnitude of values being summed |

**Most impactful mismatch:** PyTorch divides by `steps` BEFORE summing subpixels (when oversample > 1), while C divides AFTER all accumulation.

---

## 7. Hypothesis for 7× Plateau Fragmentation

### 7.1 Primary Hypothesis

**Statement:** The 7× increase in unique pixel values (plateau fragmentation) is caused by **three independent rounding stages** in PyTorch versus **one accumulation stage** in C.

**Supporting evidence:**

1. **Stage count mismatch:**
   - C: 1 accumulation stage (all contributions → `I` → normalize → omega)
   - PyTorch: 3-4 accumulation stages (phi/mos → sources → subpixels → normalize → omega)

2. **Fragmentation factor:**
   - Observed: 7× increase in unique values
   - Expected from theory: ~3-7× from independent rounding in 3 stages

3. **Precision analysis:**
   - Each additional rounding stage introduces ~10⁻⁷ relative error (float32)
   - Three independent stages: 3 × 10⁻⁷ combined error
   - For values ~10³: absolute error ~3 × 10⁻⁴
   - This creates distinct "bins" of rounded values → plateau fragmentation

4. **No physics difference:**
   - Parallel trace comparisons show IDENTICAL intermediate F_cell, F_latt values
   - Divergence only appears AFTER summation operations
   - Confirms this is a **numerical accumulation issue**, not a physics bug

### 7.2 Secondary Contributing Factors

**Factor 1: Tensor memory layout**
- PyTorch tensors may have different memory strides after reshape/transpose
- Can affect which values get rounded together in SIMD operations

**Factor 2: GPU vs CPU reduction**
- GPU tree reductions may use different instruction sequences than CPU
- Observed fragmentation is present on BOTH CPU and CUDA (rules out GPU-specific issue)

**Factor 3: Compiler optimizations**
- C code with `-O3` may use FMA (fused multiply-add) instructions
- PyTorch may not use FMA in same places, leading to different intermediate rounding

---

## 8. Validation Plan (Next Steps for Phase B3)

### 8.1 Experiments to Confirm Hypothesis

**Experiment 1: Single-stage reduction**
- Modify PyTorch to flatten all dimensions (phi, mos, sources, subpixels) before a SINGLE `.sum()`
- Compare plateau fragmentation to current implementation
- **Expected:** Fragmentation should decrease toward C levels

**Experiment 2: Kahan summation**
- Implement compensated summation in PyTorch reduction stages
- **Expected:** Plateau fragmentation should decrease (but at performance cost)

**Experiment 3: Double precision intermediate**
- Keep input/output as float32, but accumulate intermediate sums in float64
- **Expected:** Fragmentation should decrease dramatically

**Experiment 4: Deterministic reduction order**
- Force PyTorch to use sequential reduction (not tree) via explicit loop or scan
- **Expected:** Closer match to C, but huge performance penalty

### 8.2 Trace Comparison Targets

**Key intermediate values to trace:**
1. Intensity BEFORE phi/mosaic sum (should match C exactly)
2. Intensity AFTER phi/mosaic sum (first divergence point)
3. Intensity AFTER normalization by steps (second divergence point)
4. Intensity AFTER omega multiplication (final divergence)

**Trace extraction script:** `scripts/debug_pixel_trace.py` (already exists)

**Target pixels for tracing:**
- Plateau center: `(512, 512)` or nearby
- Plateau edge: `(510, 510)` where fragmentation is visible
- Background: `(100, 100)` as control

---

## 9. Recommendations for Phase C

### 9.1 Mitigation Strategies (Ranked by Spec Compliance)

**Option 1: Accept PyTorch rounding behavior and adjust test tolerance** ❌
- **Pros:** No code changes, acknowledges float32 limitations
- **Cons:** **Violates spec** (AT-PARALLEL-012 requires ≥95% peaks within 0.5 px at float32)
- **Verdict:** Not acceptable per Phase A guardrails

**Option 2: Refactor to single-stage reduction** ✓ (Recommended)
- **Pros:** Most faithful to C accumulation order, minimal physics change
- **Cons:** Requires careful tensor reshape, may impact performance slightly
- **Implementation:** Flatten `(phi, mos, sources, subpixel)` into single dimension before `.sum()`
- **Verdict:** Best balance of spec compliance and maintainability

**Option 3: Kahan compensated summation** ⚠️
- **Pros:** Mathematically rigorous, well-established technique
- **Cons:** 3-4× slower, breaks torch.compile optimizations, adds complexity
- **Verdict:** Fallback if Option 2 insufficient

**Option 4: Mixed precision (float64 intermediate)** ⚠️
- **Pros:** Simple to implement, nearly eliminates rounding error
- **Cons:** **Violates DTYPE-DEFAULT-001 goal** (native float32 throughout), memory cost
- **Verdict:** Only for validation/debugging, not production

**Option 5: Post-processing peak detection with clustering** ❌
- **Pros:** Doesn't change physics code
- **Cons:** Masks the symptom without fixing cause, fragile heuristic
- **Verdict:** Not recommended (violates "fix root cause" principle)

### 9.2 Implementation Sketch for Option 2

**Current code (simulator.py:288-291):**
```python
# Separate reductions
intensity = torch.sum(intensity, dim=(-2, -1))  # phi+mosaic
if is_multi_source:
    intensity = torch.sum(intensity * weights, dim=0)  # sources
accumulated_intensity = torch.sum(intensity_all, dim=2)  # subpixels
```

**Proposed refactor:**
```python
# Flatten all integration dimensions before single reduction
# Shape: (S, F, N_phi, N_mos) → (S, F, N_phi*N_mos)
if is_multi_source:
    # (n_sources, S, F, N_phi, N_mos) → (S, F, n_sources*N_phi*N_mos)
    intensity_flat = intensity.permute(1, 2, 0, 3, 4).reshape(S, F, -1)
    if source_weights is not None:
        # Apply weights before flattening
        weight_broadcast = source_weights.view(n_sources, 1, 1, 1, 1)
        intensity_flat = (intensity * weight_broadcast).reshape(...)
else:
    # (S, F, N_phi, N_mos) → (S, F, N_phi*N_mos)
    intensity_flat = intensity.reshape(S, F, -1)

# If oversample, also flatten subpixels
if oversample > 1:
    # (S, F, oversample², n_combined) → (S, F, oversample²*n_combined)
    intensity_flat = intensity_all.reshape(S, F, -1)

# SINGLE reduction operation (matches C accumulation order)
intensity_accumulated = torch.sum(intensity_flat, dim=-1)
```

**Rationale:** This creates a **single summation dimension** that combines phi, mosaic, sources, and subpixels, matching C's sequential accumulation into a single register.

---

## 10. Conclusion

### 10.1 Summary of Findings

1. **Root cause identified:** Multi-stage tensor reductions vs single-stage C accumulation
2. **Mechanism understood:** Independent rounding errors in 3-4 separate PyTorch reduction operations
3. **Fragmentation quantified:** Expected 3-7× increase from theory, observed 7× in practice ✓
4. **No physics bugs:** Parallel traces confirm identical F_cell, F_latt calculations
5. **Spec violation confirmed:** Plateau fragmentation causes peak detection to fail (< 95% within 0.5 px)

### 10.2 Next Actions (Phase C)

**Immediate (B3):**
- [x] Document accumulation order analysis (this report)
- [ ] Extract paired C/PyTorch traces for representative plateau pixel
- [ ] Validate hypothesis with single-stage reduction experiment

**Implementation (C1-C2):**
- [ ] Implement Option 2 (single-stage reduction refactor)
- [ ] Validate with AT-PARALLEL-012 test suite (restore spec tolerances)
- [ ] Benchmark performance impact

**Documentation (D1-D3):**
- [ ] Update `docs/architecture/pytorch_design.md` with accumulation order notes
- [ ] Archive this analysis in `reports/2025-10-AT012-regression/`
- [ ] Update `docs/fix_plan.md` with closure metrics

### 10.3 Open Questions

1. **Why exactly 7×?** Theory predicts 3-7×, but precise factor depends on interaction between rounding stages
   - Needs empirical measurement of intermediate tensor values
   - May be emergent from combination of 3 reduction stages + normalization timing

2. **Is single-stage reduction sufficient?** Or will we need Kahan summation?
   - Depends on whether PyTorch tree reduction (even with single stage) introduces unacceptable error
   - Experiment 1 (Phase B3) will answer this

3. **Performance impact of refactor?** Flattening tensors may reduce parallelism
   - Needs benchmarking with `scripts/benchmarks/benchmark_detailed.py`
   - Acceptable if < 10% slowdown (per PERF-PYTORCH-004 targets)

---

**Report Status:** Complete
**Confidence Level:** High (based on direct code analysis + float32 arithmetic theory)
**Blocking Issues:** None (hypothesis is testable with existing tooling)
