# Tap 5 Hypotheses & Follow-Up Evidence Plan

**Generated:** 2025-10-10T11:36:08Z
**Last Updated:** 2026-01-10T12:35:00Z (Tap 5.2 synthesis)
**Phase:** E14 closure → E15 pivot
**Scope:** Ranked hypotheses for Tap 5 I_before_scaling discrepancies
**References:** `intensity_pre_norm.md` (Phase E10 comparison), `tap5_hkl_bounds.md` (Tap 5.2 evidence)

---

## Hypothesis Summary

| ID | Hypothesis | Confidence | Required Evidence | Status |
|----|------------|------------|-------------------|--------|
| **H1** | HKL Grid Indexing Bug in PyTorch | ~~95%~~ **REFUTED** | ✅ Tap 5.1 + 5.2 complete | **CLOSED** |
| **H2** | Subpixel Loop Accumulation Order | 80% → **PRIMARY** | Tap 5.3 (per-subpixel intensity) | **ACTIVE** |
| **H3** | Water Background Implicit Scaling | 10% → **DEFERRED** | Tap 6 (water background taps) | P2 (after H2) |

---

## H1: HKL Grid Indexing Bug in PyTorch ~~(95% confidence)~~ — **REFUTED**

### Original Evidence (Phase E10)

1. **Centre pixel (2048,2048) critical divergence:**
   - C: F_cell = 0 (in-bounds HKL lookup) for all 4 subpixels
   - PyTorch: F_cell = 100 (default_F fallback) for all 4 subpixels
   - Miller indices: h,k,l ≈ (−1e-7, 0.015, −0.015) → rounded to (0,0,0)

2. **Spec violation concern:**
   - `specs/spec-a-core.md:239-240` states: "Nearest-neighbor lookup of F_cell at (h0, k0, l0) if in-range; else F_cell = default_F."
   - The origin (0,0,0) **MUST** be in-range for both implementations.

3. **Tap 4 consistency:**
   - Edge pixel: both C and PyTorch use default_F = 100 (correct out-of-bounds behavior).
   - Centre pixel: only PyTorch uses default_F (incorrect in-bounds treatment).

### Tap 5.1 + 5.2 Refutation (Phase E12-E14)

**Tap 5.1 Results (Attempts #32-#34):**
- ✅ PyTorch **correctly** marks centre pixel `(0,0,0)` as `out_of_bounds=False`
- ✅ C **identically** marks centre pixel `(0,0,0)` as `out_of_bounds=0`
- ✅ Both return `F_cell=100` because **no HKL file was loaded** (test configuration)
- ✅ HKL indexing parity confirmed for both edge (-8,39,-39) and centre (0,0,0) pixels

**Tap 5.2 Results (Attempt #35):**
- ❌ Bounds semantics differ: PyTorch reports **per-pixel** ranges, C reports **global grid** extents
- ✅ Both treat `(0,0,0)` as in-bounds when no HKL file is present
- ✅ Both apply `default_F=100` uniformly across all lookups in no-HKL-file mode
- 📋 See `tap5_hkl_bounds.md` for detailed comparison

**Root Cause Identified:**
The centre pixel `F_cell=100` vs `F_cell=0` mismatch was **NOT** an indexing bug but a test configuration artifact:
- When no HKL file is loaded, PyTorch correctly falls back to `default_F` for all lookups
- The C value of `F_cell=0` represents an in-bounds HKL lookup that returned a stored value of zero
- Both behaviors are spec-compliant; the discrepancy stems from whether HKL data was actually loaded

**Conclusion:** H1 is **REFUTED**. The 4× intensity discrepancy must originate from a different source (H2 accumulation logic).

### Required Evidence (Tap 5.1 + Tap 5.2)

#### Tap 5.1: Per-Subpixel HKL Audit

**Objective:** Capture fractional Miller indices, rounded integers, and retrieved F_cell for each of the 4 subpixels at centre pixel (2048,2048).

**PyTorch implementation:**
- Extend `scripts/debug_pixel_trace.py --taps hkl_subpixel`.
- For each subpixel `i` in [0,3]:
  - Log: `h_frac[i]`, `k_frac[i]`, `l_frac[i]`
  - Log: `h0[i]`, `k0[i]`, `l0[i]` (rounded)
  - Log: `F_cell[i]` (retrieved value)
  - Log: `out_of_bounds[i]` (boolean: did we use default_F?)

**C implementation:**
- Add `TRACE_C_TAP5_1` guards in `golden_suite_generator/nanoBragg.c` around the HKL lookup logic (lines 3300–3340, near the `Fhkl = stol_of(...)` block).
- Print identical schema.

**Expected Output (JSON/log):**
```json
{
  "tap_id": "hkl_subpixel",
  "pixel_coords": [2048, 2048],
  "subpixels": [
    {
      "subpixel_idx": 0,
      "h_frac": -1.125000004265e-07,
      "k_frac": 0.014999999915623,
      "l_frac": -0.014999999915623,
      "h0": 0,
      "k0": 0,
      "l0": 0,
      "F_cell": 0.0,  // C expects 0, PyTorch currently reports 100
      "out_of_bounds": false
    },
    // ... 3 more subpixels
  ]
}
```

**Acceptance Criteria:**
- If PyTorch's `out_of_bounds` flags are `true` for centre pixel but C's are `false`, H1 is confirmed.
- Document the exact `(h0, k0, l0)` values and compare grid index computation logic in both implementations.

---

#### Tap 5.2: HKL Grid Bounds Check

**Objective:** Print the HKL grid extents in both C and PyTorch to verify (0,0,0) is in-range.

**PyTorch implementation:**
- In `src/nanobrag_torch/models/crystal.py`, add debug log after HKL grid loading:
  ```python
  print(f"TRACE_PY_HKL_BOUNDS: h_min={self.h_min}, h_max={self.h_max}, "
        f"k_min={self.k_min}, k_max={self.k_max}, l_min={self.l_min}, l_max={self.l_max}")
  ```

**C implementation:**
- Add `TRACE_C_HKL_BOUNDS` in `golden_suite_generator/nanoBragg.c` after `read_text_file()` or `read_Fdump()` completes (around line 1800):
  ```c
  printf("TRACE_C_HKL_BOUNDS: h_min=%d h_max=%d k_min=%d k_max=%d l_min=%d l_max=%d\n",
         h_min, h_max, k_min, k_max, l_min, l_max);
  ```

**Expected Output:**
```
TRACE_C_HKL_BOUNDS: h_min=-50 h_max=50 k_min=-50 k_max=50 l_min=-50 l_max=50
TRACE_PY_HKL_BOUNDS: h_min=-50 h_max=50 k_min=-50 k_max=50 l_min=-50 l_max=50
```

**Acceptance Criteria:**
- Both implementations must report identical bounds.
- Verify that `0 ∈ [h_min, h_max]`, `0 ∈ [k_min, k_max]`, `0 ∈ [l_min, l_max]`.
- If bounds match but PyTorch still treats (0,0,0) as out-of-bounds, the bug is in the indexing arithmetic.

---

### Code Audit Focus (if Tap 5.1/5.2 confirm H1)

**PyTorch suspect lines:**
- `src/nanobrag_torch/models/crystal.py:get_structure_factor()` — nearest-neighbor lookup logic.
- Look for off-by-one errors in index computation (e.g., `h0 < h_min` vs. `h0 <= h_min`).

**C reference:**
- `golden_suite_generator/nanoBragg.c` lines 3300–3340 — `Fhkl = stol_of(...)` and grid indexing.
- Compare rounding logic (`ceil(h - 0.5)` vs. `round(h)`).

---

## H2: Subpixel Loop Accumulation Order — **PRIMARY HYPOTHESIS** (80% confidence)

### Evidence

1. **Edge pixel raw intensity (Phase E9-E10):**
   - C: I_before_scaling = 141520.166
   - PyTorch: I_before_scaling = 35428.870
   - Ratio: 3.9945× (C higher)

2. **Omega/polar factors match (Phase E8-E9):**
   - Omega: C=8.8611e-09, PyTorch=8.8614e-09 (0.003% delta)
   - Polar: C=0.96128, PyTorch=0.96129 (0.001% delta)

3. **Default_F usage identical (Phase E5-E7):**
   - Tap 4 confirmed both use default_F = 100 for edge pixel.

4. **H1 refuted (Phase E12-E14):**
   - Tap 5.1 + 5.2 ruled out HKL indexing as root cause
   - Centre pixel parity explained by no-HKL-file configuration
   - Edge pixel 4× discrepancy remains unexplained

### Hypothesis (Updated)

With H1 eliminated, the 4× intensity gap **must** stem from how `I_term = (F_cell²) × (F_latt²)` is accumulated across the oversample=2 grid (4 subpixels). Potential mechanisms:

1. **Accumulation order:** C vs PyTorch may iterate subpixels in different orders, causing systematic bias
2. **Weighting differences:** One implementation may multiply by omega/capture/polar per-subpixel while the other applies once
3. **Early termination:** One implementation may skip subpixels under certain conditions

**Supporting Evidence:**
- The 4× ratio is suspiciously close to the number of subpixels (oversample² = 4)
- Omega, polar, and steps match → discrepancy must be in the per-subpixel intensity contribution loop
- Centre pixel shows no discrepancy (both zero) → issue is triggered only when Bragg intensity is present

**Counter-Evidence:**
- ~~FP rounding should produce ≤1e-6 relative error, not 4×~~ (argument weakened by H1 refutation)
- ~~The centre pixel's H1 divergence may explain systematic bias~~ (H1 now refuted)

### Required Evidence (Tap 5.1 edge)

**Objective:** Log per-subpixel `I_term` contributions for edge pixel (0,0).

**PyTorch implementation:**
- Extend `scripts/debug_pixel_trace.py --taps subpixel_intensity`.
- For each subpixel `i` in [0,3]:
  - Log: `F_cell[i]`, `F_latt[i]`, `I_term[i] = F_cell² × F_latt²`
  - Log: `I_accumulated[i] = sum(I_term[0:i+1])`

**C implementation:**
- Add `TRACE_C_TAP5_1_EDGE` in the oversample loop (nanoBragg.c:3400–3500).
- Print identical schema.

**Acceptance Criteria:**
- If per-subpixel `I_term` values match but cumulative `I_accumulated` diverges, the issue is summation order.
- If `I_term` values differ, the issue is in F_latt computation (unlikely given Tap 4 F_cell parity).

**Decision:** **Defer until H1 is resolved.** If centre pixel fix restores edge pixel parity, H2 becomes moot.

---

## H3: Water Background Implicit Scaling (10% confidence)

### Evidence

1. **Test case:** Both pixels use `-water 0`, so `I_bg = 0`.
2. **Centre pixel:** C reports `I_before_scaling = 0`, consistent with no background.
3. **Spec:** `specs/spec-a-core.md:245-249` states background is added before Bragg terms.

### Hypothesis

PyTorch might add a latent background term even when `-water 0`, inflating `I_before_scaling`.

**Counter-Evidence:**
- Centre pixel's `I_before_scaling = 1.538e8` matches `(F_cell²) × (F_latt²)` with `F_cell = 100`, `F_latt ≈ 124` (per C Tap 5 log).
- This is Bragg intensity, not background.
- Edge pixel shows no evidence of background inflation.

### Required Evidence (Tap 6)

**Objective:** Audit background term application in both implementations.

**Defer until:** H1 is resolved and centre pixel parity is restored.

---

## Recommended Action (Phase E15 Decision)

### Priority: Execute Tap 5.3 Oversample Accumulation Instrumentation (H2)

**Rationale:**
- ✅ Tap 5.1 + 5.2 complete (Attempts #32-#35) — H1 **REFUTED**
- ✅ HKL indexing parity confirmed for both implementations
- ❌ Edge pixel 4× intensity gap remains unexplained
- 🎯 H2 (oversample accumulation) is now the **PRIMARY** hypothesis (80% confidence)
- 🎯 The 4× ratio strongly suggests per-subpixel accumulation logic differs between C and PyTorch

**Next Evidence Required (Tap 5.3):**
1. **Instrumentation brief** (`tap5_accum_plan.md`): Define logging schema for per-subpixel `F_cell²·F_latt²`, capture weights, and accumulation order
2. **PyTorch capture** (E16): Extend `scripts/debug_pixel_trace.py` with `--taps intensity_accum` to log all 4 subpixels at edge pixel (0,0)
3. **C mirror** (E17): Add `TRACE_C_TAP5_ACCUM` guards to `golden_suite_generator/nanoBragg.c` oversample loop
4. **Comparison** (E18): Merge logs into `tap5_accum_comparison.md` and quantify contribution deltas

**Blockers:**
- ✅ Tap 5.1/5.2 complete — H1 gate lifted
- ❌ Do NOT implement Phase F fixes until Tap 5.3 confirms or refutes H2
- ❌ Do NOT pursue Tap 6 (water background) until H2 is resolved

**Next Actions:**
1. 📋 Author Tap 5.3 instrumentation brief per plan task E15
2. 🛠️ Extend trace script for per-subpixel intensity logging (E16)
3. 🧪 Mirror instrumentation in C code (E17)
4. 📊 Compare outputs and update hypothesis ranking (E18)
5. 📝 Update `docs/fix_plan.md` Attempt History with Tap 5.2 synthesis outcome

---

## Next Steps: Tap 5.3 Instrumentation Plan (Phase E15-E18)

### E15: Author Instrumentation Brief

**Deliverable:** `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/tap5_accum_plan.md`

**Required Content:**
1. **Logging Schema:**
   - Per-subpixel variables: `subpixel_idx`, `h_frac`, `k_frac`, `l_frac`, `F_cell`, `F_latt`, `I_term = F_cell² × F_latt²`, `omega_subpixel`, `capture_fraction`, `polar_factor`
   - Cumulative accumulation: `I_accumulated[i] = sum(I_term[0:i+1])`
   - Final pre-scaling intensity: `I_before_scaling`

2. **Guard Names:**
   - PyTorch: `--taps intensity_accum` (CLI flag for `scripts/debug_pixel_trace.py`)
   - C: `TRACE_C_TAP5_ACCUM` (environment variable guard in `nanoBragg.c`)

3. **Target Pixels:**
   - Edge pixel: `(0,0)` — where 4× discrepancy exists
   - Centre pixel: `(2048,2048)` — baseline (both implementations report zero)

4. **Acceptance Checks:**
   - Per-subpixel `I_term` must match within 1e-6 relative error OR identify exact divergence point
   - Cumulative `I_accumulated` trajectory must align OR explain accumulation order difference
   - Final `I_before_scaling` must converge OR quantify missing/extra contributions

5. **References:**
   - `specs/spec-a-core.md:232-259` — oversample accumulation semantics
   - Plan tasks E15-E18 in `plans/active/vectorization-parity-regression.md`

### E16-E18: Implementation & Comparison

**E16 (PyTorch):**
- Extend `scripts/debug_pixel_trace.py` with `collect_intensity_accum_tap()` helper
- Log JSON output to `reports/.../py_taps/pixel_0_0_intensity_accum.json`
- Record commands and environment metadata

**E17 (C):**
- Add `#ifdef TRACE_C_TAP5_ACCUM` guard in `golden_suite_generator/nanoBragg.c` oversample loop (around lines 3400-3500)
- Print matching schema to stderr
- Rebuild binary (`make clean && make nanoBragg` in `golden_suite_generator/`)
- Capture logs with `TRACE_C_TAP5_ACCUM=1 ...` environment variable

**E18 (Comparison):**
- Merge PyTorch + C logs into `tap5_accum_comparison.md`
- Build side-by-side table: subpixel_idx | F_cell | F_latt | I_term | I_accumulated (cumulative)
- Quantify deltas at each step
- Update `tap5_hypotheses.md` with final H2 verdict: CONFIRMED or REFUTED
- Document next remediation steps for Phase F if H2 confirmed

---

**End of Hypotheses Memo**
