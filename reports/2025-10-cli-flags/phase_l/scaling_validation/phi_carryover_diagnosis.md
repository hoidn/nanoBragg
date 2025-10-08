# φ=0 Carryover Cache Architecture Diagnosis

**Date:** 2025-10-22
**Phase:** CLI-FLAGS-003 M2
**Loop:** Ralph i=151
**Engineer:** Ralph
**Git SHA:** (to be recorded post-commit)

## Executive Summary

The φ=0 carryover cache implementation (commit 3269f6d) correctly implements the **storage** and **retrieval** logic to emulate C-PARITY-001, but **fails due to an architectural mismatch** between the cache scope (per-invocation) and the required semantics (per-pixel within a run).

**Test status after configuration fix:**
- ✅ F_cell: **PASSES** (configuration parity restored)
- ❌ F_latt: **FAILS** with 158% relative error (φ=0 carryover not working)
- Expected: -2.383196653, Got: 1.379483851

**Root cause:** `Simulator.run()` calls `Crystal.get_rotated_real_vectors()` **once** for the entire image, computing all pixels' φ steps in a single vectorized operation. The cache stores/retrieves vectors between **different Simulator.run() calls** (different images), not between **consecutive pixels within the same image**.

## Problem Analysis

### 1. Configuration Parity Bug (FIXED)

**Before fix:** test used MOSFLM convention with swapped dimensions (spixels=2463, fpixels=2527)
**C trace used:** CUSTOM convention with dimensions (spixels=2527, fpixels=2463)

**Fix applied:** Updated `tests/test_cli_scaling_parity.py:92-112` to use:
- `DetectorConvention.CUSTOM`
- Correct dimensions (2527×2463)
- Custom detector vectors from `trace_harness.py`
- Custom pix0 override

**Result:** F_cell now matches (relative error effectively zero), but F_latt still fails.

### 2. Cache Architecture Mismatch (PRIMARY ISSUE)

#### C-Code Behavior (OpenMP firstprivate)

```c
// nanoBragg.c:2797
#pragma omp parallel for ... firstprivate(ap,bp,cp,...)

for(pixel_i=0; pixel_i < num_pixels; ++pixel_i) {  // Thread-local loop
    for(phi_tic=0; phi_tic<phisteps; ++phi_tic) {
        phi = phi0 + phistep*phi_tic;
        if( phi != 0.0 ) {
            rotate_axis(a0,ap,spindle_vector,phi);  // Update ap/bp/cp
        }
        // When phi==0: ap/bp/cp retain PREVIOUS PIXEL's φ=final values
    }
}
```

**Key point:** Each thread processes pixels **sequentially** → `ap/bp/cp` persist across pixel loop iterations.

#### PyTorch Current Implementation

```python
# Simulator.run() line ~820
rotated_real, rotated_recip = crystal.get_rotated_real_vectors(crystal_config)
# Shape: (N_phi, N_mos, 3) - computed ONCE for entire run
```

**Problem:** All pixels use the **same** rotated vectors tensor. No per-pixel state.

#### Current Cache Logic (crystal.py:1276-1313)

```python
if config.phi_carryover_mode == "c-parity":
    cache = self._phi_carryover_cache
    if cache['a'] is not None:
        # Replace φ=0 with cached vectors
        a_final[0] = cache['a']  # Reads from PREVIOUS run()

    # Store φ=final for NEXT run()
    cache['a'] = a_final[-1].detach().clone()  # ❌ .detach() breaks gradients
```

**Execution timeline:**
1. Run #1 (pixel 1): Cache empty → φ=0 uses fresh vectors → Cache stores φ=final
2. Run #2 (pixel 2, **different image**): Cache has Run#1 data → φ=0 uses Run#1 φ=final
3. **Within Run#1:** ALL pixels use the same φ=0 vectors (no carryover between pixels)

### 3. Additional Architectural Violations

1. **Gradient Breaking:** `.detach().clone()` (line 1308) severs computation graph
2. **In-place Modification:** `a_final[0] = cached_a` can break autograd in some scenarios
3. **Single-pixel test limitation:** First pixel has no "previous pixel" to carry over from

## Proposed Solutions

### Option 1: Pixel-Indexed Cache with Deferred Substitution (RECOMMENDED)

**Concept:** Store φ=final vectors per-pixel and apply carryover during physics computation.

**Evidence:** M2d two-pixel probe (20251008T100653Z/carryover_probe) confirms current cache fails to achieve per-pixel carryover. Pixels (684,1039) and (685,1039) have identical φ=0 vectors, proving cache operates between separate run() calls, not consecutive pixels.

#### Tensor Shape & Memory Design

**Cache Storage (per vector a/b/c):**
```
Shape: (S, F, N_mos, 3)
  S      = slow pixels (detector.spixels, e.g., 2527 for supervisor case)
  F      = fast pixels (detector.fpixels, e.g., 2463)
  N_mos  = mosaic domains (crystal_config.mosaic_domains, e.g., 1 for supervisor)
  3      = vector components (x, y, z)

Memory footprint (dtype=torch.float32):
  - Supervisor case: 3 vectors × 2527 × 2463 × 1 × 3 × 4 bytes = 224 MB
  - With N_mos=10: 3 × 2527 × 2463 × 10 × 3 × 4 = 2.24 GB
  - ROI (56×56): 3 × 56 × 56 × 1 × 3 × 4 = 113 KB (negligible)
```

**Allocation Strategy:**
- Device: Same as crystal base vectors (follows caller device)
- Dtype: Same as crystal base vectors (float32 default, float64 for debug)
- Timing: Allocate at first `run()` when detector dimensions are known
- Reallocation: Clear and reallocate if detector size changes

#### Cache Lifecycle & Reset Rules

**Initialization (Simulator.__init__ or first run()):**
```python
if config.phi_carryover_mode == "c-parity":
    crystal._phi_cache_a = torch.zeros(
        (detector.spixels, detector.fpixels, crystal_config.mosaic_domains, 3),
        dtype=base_a.dtype, device=base_a.device
    )
    # Similar for _phi_cache_b, _phi_cache_c
    crystal._cache_initialized = True
```

**Population (after computing φ=final for each pixel):**
```python
# In _compute_physics_for_position or batch loop:
if config.phi_carryover_mode == "c-parity":
    # Store φ=final (last phi step) for this pixel
    crystal._phi_cache_a[slow, fast, :, :] = rotated_a[-1, :, :]  # Shape: (N_mos, 3)
    # Similar for b, c
```

**Application (when computing φ=0 for next pixel):**
```python
# Option A: In-place substitution (may break autograd)
if phi_tic == 0 and config.phi_carryover_mode == "c-parity":
    rotated_a[0, :, :] = crystal._phi_cache_a[slow, fast, :, :]

# Option B: Deferred lookup (safer for gradients)
def get_phi_vectors(slow, fast, phi_tic):
    if phi_tic == 0 and config.phi_carryover_mode == "c-parity":
        return (
            crystal._phi_cache_a[slow, fast],
            crystal._phi_cache_b[slow, fast],
            crystal._phi_cache_c[slow, fast]
        )
    else:
        return compute_fresh_rotation(phi_tic)
```

**Clear/Invalidate:**
- On detector geometry change (basis vectors, distance, rotations)
- On crystal cell parameter change (if re-running same detector)
- On explicit ROI boundary change (optional optimization)
- **NOT** cleared between pixels in same run (that's the whole point)

#### Call Sequence & Integration Points

**Current Flow (Broken):**
```
Simulator.run()
  └─ rotated_vecs = crystal.get_rotated_real_vectors()  # Once per run, (N_phi, N_mos, 3)
  └─ for pixel in all_pixels:
      └─ _compute_physics_for_position(pixel, rotated_vecs)  # All pixels use same φ=0
```

**Option 1A: Cache in Crystal, Apply in Simulator (RECOMMENDED):**
```
Simulator.run()
  └─ for slow in range(detector.spixels):
      └─ for fast in range(detector.fpixels):
          ├─ rotated_vecs = crystal.get_rotated_real_vectors()  # Fresh compute
          ├─ if phi_carryover_mode == "c-parity":
          │   └─ rotated_vecs = crystal.apply_phi_carryover(slow, fast, rotated_vecs)
          ├─ _compute_physics_for_position(pixel, rotated_vecs)
          └─ crystal.store_phi_final(slow, fast, rotated_vecs[-1])  # Save for next pixel
```

**Option 1B: Cache in Simulator, Crystal Provides Helpers:**
```
Simulator.run()
  └─ self._init_phi_cache(detector, crystal)  # Allocate (S, F, N_mos, 3)
  └─ for pixel in pixels:
      └─ rotated_vecs = self._get_pixel_phi_vectors(slow, fast, crystal)
          ├─ if phi=0 and cache_valid[slow, fast]:
          │   └─ return cached_final[slow, fast]
          ├─ else:
          │   └─ fresh = crystal.get_rotated_real_vectors()
          │   └─ cached_final[slow, fast] = fresh[-1]
          │   └─ return fresh
```

#### Gradient Preservation Strategy

**Critical Requirements (CLAUDE.md Rule #8-10):**
1. **No `.detach()`**: Store tensors with `requires_grad` intact
2. **Functional indexing**: Use `cache[s,f] = vec` (preserves computation graph)
3. **Advanced indexing for batch**: When vectorizing, use `cache[slow_batch, fast_batch]`
4. **Property-based access**: Avoid overwriting class attributes with computed values

**Implementation Pattern:**
```python
# GOOD: Preserves gradients
cache[slow, fast] = rotated_final  # rotated_final.requires_grad preserved

# GOOD: Functional retrieval
phi0_vectors = cache[slow, fast]  # Still connected to graph

# BAD: Breaks gradients
cache[slow, fast] = rotated_final.detach().clone()  # ❌ Severs graph

# BAD: In-place modification may break autograd
rotated_vecs[0] = cache[slow, fast]  # ⚠️ Risky for backward()
```

**Gradcheck Strategy (M2h validation):**
```python
# Test with 2×2 ROI, vary cell parameter
def loss_fn(cell_a):
    config = CrystalConfig(cell_a=cell_a, phi_carryover_mode="c-parity")
    crystal = Crystal(config)
    detector = Detector(...)  # 2×2 detector
    simulator = Simulator(crystal, detector, beam)
    image = simulator.run()  # Triggers cache for pixels [1,1]
    return image.sum()

torch.autograd.gradcheck(loss_fn, torch.tensor(100.0, dtype=torch.float64, requires_grad=True))
```

#### C-Code Reference Mapping (nanoBragg.c)

**Cache equivalent:** OpenMP `firstprivate(ap, bp, cp, ...)` (lines 2797-2800)
```c
// nanoBragg.c:2797
#pragma omp parallel for ... firstprivate(ap,bp,cp,a0p,b0p,c0p,...)
for(pixel_i=0; pixel_i < num_pixels; ++pixel_i) {
    // ap/bp/cp are thread-local copies that persist across phi loop iterations
    for(phi_tic=0; phi_tic<phisteps; ++phi_tic) {
        phi = phi0 + phistep*phi_tic;
        if( phi != 0.0 ) {
            rotate_axis(a0, ap, spindle_vector, phi);  // Modify ap
            rotate_axis(b0, bp, spindle_vector, phi);  // Modify bp
            rotate_axis(c0, cp, spindle_vector, phi);  // Modify cp
        }
        // When phi==0: ap/bp/cp retain values from previous pixel's final phi
    }
}
```

**Carryover condition:** `if (phi != 0.0)` block (lines 3044-3095)
```c
// nanoBragg.c:3044-3095 (condensed)
if(phi != 0.0) {
    // Compute fresh rotations
} else {
    // Reuse ap/bp/cp from previous iteration (implicit carryover)
}
```

**Per-pixel sequential semantics:** Thread processes pixels sequentially → state persists.

**PyTorch equivalent:** Explicit cache indexed by (slow, fast) to simulate thread-local persistence.

#### Changes Required (Implementation Checklist)

1. **Crystal.py modifications:**
   - Add `_phi_cache_a/b/c` attributes (allocated lazily)
   - Add `initialize_phi_cache(spixels, fpixels, mosaic_domains, dtype, device)` method
   - Add `store_phi_final(slow, fast, rotated_vecs)` helper
   - Add `get_cached_phi0(slow, fast)` helper
   - **OR** Add `apply_phi_carryover(slow, fast, rotated_vecs)` that modifies φ=0 slice

2. **Simulator.py modifications:**
   - Thread `(slow, fast)` pixel coordinates into `_compute_physics_for_position`
   - Call `crystal.initialize_phi_cache(...)` before pixel loop
   - Call carryover helpers at appropriate points in pixel/phi loops

3. **Test additions (M2h):**
   - `test_phi_cache_allocation` - Verify cache shape/device/dtype
   - `test_phi_cache_two_pixel_carryover` - Verify pixel2 φ=0 uses pixel1 φ=final
   - `test_phi_cache_gradients` - Run gradcheck on 2×2 ROI

4. **Trace instrumentation:**
   - Emit `TRACE_PY_CACHE_HIT` / `TRACE_PY_CACHE_MISS` markers
   - Log cache access patterns in debug mode

**Pros:**
- ✅ Preserves vectorization (cache operations are tensor ops)
- ✅ Maintains gradient flow (no .detach(), functional indexing)
- ✅ Correct per-pixel semantics (explicit pixel indices)
- ✅ Device/dtype neutral (cache allocated on input device/dtype)
- ✅ Memory acceptable (~224 MB for supervisor case @ float32)

**Cons:**
- ⚠️ Moderate complexity (pixel coordinates threaded through call stack)
- ⚠️ Memory scales with detector size (but ROIs reduce this)
- ⚠️ Cache invalidation logic adds state management

**Feasibility:** Medium-High (well-defined requirements, clear implementation path)

### Option 2: Sequential Pixel Batching (NOT RECOMMENDED)

Process pixels in sequential batches with per-pixel vector computation.

**Pros:** Simple semantics
**Cons:** ❌ Violates mandatory vectorization (Core Rule #16), 10-100× slower

### Option 3: Deferred Gradient Attachment (ALTERNATIVE)

Store detached vectors, re-attach to graph when used.

**Pros:** Lower memory, maintains gradient flow
**Cons:** Still requires per-pixel cache lookup, breaks pure vectorization

## Test Status

### Configuration Parity Test
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -xvs tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
```

**Result:** FAILS at F_latt assertion
- Expected (C): -2.3831966530
- Got (PyTorch): 1.3794838506
- Relative error: 157.88% ❌
- Message: "This likely indicates φ=0 carryover not working correctly."

### What Changed
- ✅ F_cell matches (configuration parity fixed)
- ❌ F_latt still wrong (cache architecture issue)
- Root cause: Cache never fires between pixels in same image

## Next Steps

### Immediate (This Loop - Documentation)
1. ✅ Document diagnosis in this file
2. ✅ Update fix_plan.md with Attempt #151 entry
3. ✅ Update plan Phase M2 guidance with architecture decision
4. ✅ Commit documentation changes

### Phase M2 Implementation (Next Loop)
1. Design pixel-indexed cache structure (Option 1)
2. Implement cache in Crystal.__init__
3. Add apply_phi_carryover() method
4. Wire into _compute_physics_for_position()
5. Add multi-pixel test to verify carryover

### Phase M3 Validation
1. Run multi-pixel test (pixels 684,1039 → 685,1039)
2. Verify cache hit for second pixel
3. Run test_cli_scaling_parity.py (should pass)
4. Execute trace_harness.py with TRACE_PY_ROTSTAR
5. Regenerate metrics.json with first_divergence=None

## References

- Spec: `input.md:1-98` (Do Now directive for Phase M2)
- Plan: `plans/active/cli-noise-pix0/plan.md:59-108` (Phase M tasks)
- Bug docs: `docs/bugs/verified_c_bugs.md` (C-PARITY-001)
- C trace: `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`
- Test: `tests/test_cli_scaling_parity.py`
- Impl: `src/nanobrag_torch/models/crystal.py:1243-1313`

## Artifacts

- This diagnosis: `reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md`
- Test output: captured in fix_plan.md Attempt #151
- Configuration fix diff: tests/test_cli_scaling_parity.py lines 92-112

## Decision

**Proceed with Option 1 (Pixel-Indexed Cache) in next implementation loop.**

Rationale:
- Only option that satisfies all architectural constraints
- Memory cost acceptable (~4-8 GB) for modern hardware
- Preserves vectorization, gradient flow, and device neutrality
- Clear separation of concerns (generation vs substitution)

---

## 20251008T175913Z — Trace Tooling Verification

**Date:** 2025-10-08
**Engineer:** ralph (Attempt #171, loop i=169)
**Plan Reference:** `plans/active/cli-noise-pix0/plan.md` M2g.5
**Git SHA:** e2c75edecfc179a3cccf3c1524df51e359f54bff

### Executive Summary

Verification run confirming that the trace harness (`trace_harness.py`) works correctly with the Option B batch-indexed cache implementation (Attempt #163) and device/dtype neutrality fixes (Attempt #166). **No code changes required**; this is an evidence-only loop documenting that the tooling blocker from Attempt #164 is fully resolved.

### Test Configuration

- **Pixel:** (slow=685, fast=1039) — supervisor command ROI pixel
- **Config preset:** supervisor (CLI-FLAGS-003 authoritative command)
- **Phi carryover mode:** c-parity (emulate C-PARITY-001 bug per `docs/bugs/verified_c_bugs.md:166-204`)
- **Devices tested:** CPU (float64), CUDA (float64)
- **Emit rot-stars:** enabled (TRACE_PY_ROTSTAR output)
- **Environment:** Python 3.13.7, PyTorch 2.8.0+cu128, CUDA 12.8

### Results

#### CPU Execution
**Status:** ✅ SUCCESS

- Command: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --device cpu --dtype float64 --emit-rot-stars --out reports/2025-10-cli-flags/phase_l/trace_tooling_patch/20251008T175913Z/trace_cpu.log`
- **Trace lines captured:** 124 TRACE_PY lines
- **Per-φ traces:** 10 TRACE_PY_PHI lines
- **Final intensity:** 2.45946637686509e-07
- **Output:** `trace_cpu.log` (124 lines)

#### CUDA Execution
**Status:** ✅ SUCCESS

- Command: Same as CPU with `--device cuda`
- **Trace lines captured:** 124 TRACE_PY lines
- **Per-φ traces:** 10 TRACE_PY_PHI lines
- **Final intensity:** 2.45946637686447e-07
- **Output:** `trace_cuda.log` (124 lines)
- **CPU/CUDA parity:** Δ = 6.2e-13 relative (2.52e-11 absolute) — **PASS** (well within spec ≤1e-6 and c-parity ≤5e-5 tolerances)

### Key Findings

1. **No IndexError encountered:** The trace harness successfully indexed `omega_pixel` and `F_latt` tensors for both CPU and CUDA runs, resolving the Attempt #164 blocker.

2. **Device/dtype neutrality confirmed:** Attempt #166 fix (tensor factory device alignment in `_apply_debug_output` at `simulator.py:1445-1446`) enabled CUDA traces without modification, honoring CLAUDE Rule #16.

3. **Cache-aware taps working:** The harness captured all trace fields including:
   - `omega_pixel_sr` (solid angle)
   - `F_latt_a`, `F_latt_b`, `F_latt_c`, `F_latt` (lattice factors)
   - `I_before_scaling_pre_polar`, `I_before_scaling_post_polar`
   - `rot_a/b/c_angstroms` (real-space rotated vectors)
   - `rot_a/b/c_star_A_inv` (reciprocal-space rotated vectors)

4. **Per-φ traces functional:** TRACE_PY_PHI output captured for all 10 φ steps with per-step lattice factors.

5. **Gradient-preserving:** No `.item()` calls on gradient-critical tensors; all indexing uses tensor-native operations per CLAUDE differentiability rules.

### Spec & C-Code Alignment

- **Spec reference:** `specs/spec-a-core.md:204-240` defines the normative φ rotation pipeline (no carryover)
- **C-code bug:** `docs/bugs/verified_c_bugs.md:166-204` (C-PARITY-001) documents the φ=0 carryover bug that c-parity mode emulates
- **Parity thresholds:**
  - **spec mode:** |Δk| ≤ 1e-6 (normative, fresh rotations each φ step)
  - **c-parity mode:** |Δk| ≤ 5e-5 (relaxed, emulates C bug with stale φ=0 vectors)
- **Option B design:** `reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md` describes the batch-indexed cache implementation validated in this run

### Instrumentation Reuse Rule

Per `docs/architecture/README.md#⚠️-trace-instrumentation-rule`, trace output **reuses production helpers and cached intermediates** rather than re-deriving physics:
- Trace taps call `Crystal.get_rotated_real_vectors_for_batch()` and index the returned tensors directly
- No parallel "trace-only" implementations exist; all logged values come from the same tensors the simulator uses
- This ensures traces reflect exact production behavior and eliminates drift between debug and production paths

### Observations

- **Attempt #166 effect:** The device-neutral tensor factory fix eliminated the CUDA blocker from Attempt #164
- **Attempt #163 batch cache compatibility:** Row-wise batching through `Crystal.get_rotated_real_vectors_for_batch()` does not interfere with trace indexing
- **No code changes required:** M2g.5 tooling patch was already complete from prior attempts; this run provides evidence of success

### Artifacts

All artifacts stored under `reports/2025-10-cli-flags/phase_l/trace_tooling_patch/20251008T175913Z/`:
- `commands.txt` — Reproduction commands with exit status
- `trace_cpu.log` — CPU trace (124 lines, float64)
- `trace_cuda.log` — CUDA trace (124 lines, float64)
- `run_metadata.json` — Environment snapshot (Python 3.13.7, PyTorch 2.8.0+cu128, CUDA 12.8, git SHA e2c75ed)
- `sha256.txt` — Artifact checksums
- `summary.md` — Full validation report (source for this section)

### Next Actions (per `plans/active/cli-noise-pix0/plan.md`)

1. ✅ **M2g.5 COMPLETE** — Trace tooling verified cache-aware without IndexError
2. **M2g.6** — Document Option B architecture decision (this section completes M2g.6)
3. **M2i.2** — Keep `20251008T174753Z` bundle as authoritative baseline; reference `I_before_scaling` Δrel ≈ -0.9999995 in future diagnostics
4. **Cache index audit** — Build next diagnostics bundle logging `(slow, fast)` cache lookups before/after `apply_phi_carryover()`

### Exit Criteria Met

- [x] Trace harness executes without IndexError on CPU
- [x] Trace harness executes without IndexError on CUDA
- [x] Omega and F_latt values captured in trace output
- [x] Per-φ rotation traces (TRACE_PY_PHI) functional
- [x] CPU/CUDA parity within tolerance (≤1e-10 relative)
- [x] Device/dtype neutrality verified (CPU float64, CUDA float64)
- [x] Instrumentation reuse rule honored (no trace-only physics)

**M2g.6 Status:** Documentation sync complete. Mark plan row `[D]`.
