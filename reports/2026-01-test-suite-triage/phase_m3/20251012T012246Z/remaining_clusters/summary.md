# Phase M3 Remaining Clusters Evidence Bundle

**STAMP:** 20251012T012246Z
**Loop:** Ralph Attempt #41
**Focus:** Phase M3 Next Actions item #2 - Evidence gathering for remaining failures

## Executive Summary

**Current Status (post-Phase M2):** 561/13/112 (pass/fail/skip), 81.7% pass rate

**Validated Cluster Status:**
- ✅ **C8 (MOSFLM Beam Center):** RESOLVED - test now passes
- ❌ **C15 (Mixed Units):** ACTIVE - zero intensity bug persists
- ❌ **C16 (Orthogonality):** ACTIVE - tolerance too strict for large rotations
- ℹ️ **C2 (Gradients):** DOCUMENTED - workaround in place (NANOBRAGG_DISABLE_COMPILE=1)

**Net Active Failures:** 2 implementation bugs (C15, C16) + 10 infrastructure items (C2 with documented workaround)

---

## Cluster C8: MOSFLM Beam Center Offset [✅ RESOLVED]

**Status:** ✅ PASSING (as of 2025-10-12)

**Test:** `tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`

**Validation Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```

**Result:**
```
PASSED [100%]
1 passed in 1.92s
```

**Root Cause (Historical):** Detector class was applying MOSFLM +0.5 pixel offset to ALL beam centers, including explicit user-provided values.

**Resolution:** Fixed in prior loops (Attempts #42-57 per archived plan). Conditional offset now applies ONLY to auto-calculated beam centers when `beam_center_source==AUTO` and `convention==MOSFLM`.

**Evidence:** Test passes cleanly, no assertion errors, output as expected.

**Next Actions:** None - mark cluster RESOLVED in remediation_tracker.md.

---

## Cluster C15: Mixed Units Comprehensive [❌ ACTIVE BUG]

**Status:** ❌ FAILING - Zero intensity output

**Test:** `tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`

**Validation Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive
```

**Result:**
```
FAILED [100%]
AssertionError: Zero maximum intensity
assert tensor(0.) > 0
Runtime: 3.84s
```

**Root Cause:** Unknown - unit conversions appear correct but simulation produces all-zero output.

**Failure Point:** `tests/test_at_parallel_015.py:274` - assertion `intensity.max() > 0`

**Symptoms:**
- Output tensor is all zeros: `tensor([[0., 0., 0., ..., 0., 0., 0.], ...])`
- No numerical instability warnings
- No device/dtype errors
- Test configuration appears valid

**Hypothesis:** Possible issues:
1. Unit conversion error in a critical path (wavelength, distance, cell parameters)
2. Geometry configuration causing all pixels to be out-of-range
3. Structure factor access returning zeros/defaults
4. Miller index calculation producing no valid reflections

**Priority:** P2 (edge case but spec compliance issue)

**Next Actions:**
1. Read test source to understand exact configuration
2. Generate parallel trace comparing C vs PyTorch step-by-step
3. Check intermediate values: scattering vectors, Miller indices, F_cell, F_latt
4. Verify unit conversions at all boundaries (mm→m, deg→rad, Å consistency)
5. Document findings under `reports/.../phase_m3/20251012T012246Z/remaining_clusters/c15_mixed_units/`

**Reproduction Selectors:**
- Targeted: `pytest -v tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`
- Module: `pytest -v tests/test_at_parallel_015.py`

---

## Cluster C16: Detector Orthogonality Tolerance [❌ ACTIVE - TOLERANCE ADJUSTMENT]

**Status:** ❌ FAILING - Numerical precision issue, not physics bug

**Test:** `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts`

**Validation Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts
```

**Result:**
```
FAILED [100%]
AssertionError: fdet and sdet not orthogonal
assert tensor(1.4901e-08) < 1e-10
Runtime: 3.76s
```

**Root Cause:** Tolerance too strict for accumulated floating-point errors in large rotation compositions.

**Failure Point:** `tests/test_at_parallel_017.py:95` - assertion `torch.abs(torch.dot(fdet, sdet)) < 1e-10`

**Measured Error:** 1.4901e-08 (measured) vs 1e-10 (threshold) = **149× above threshold**

**Configuration:**
- Detector rotations: `detector_rotx=50°, detector_roty=45°, detector_rotz=40°`
- Large combined rotations (135° total across 3 axes)
- Float32 precision (default)

**Analysis:**
- Measured error (1.49e-08) is within float32 machine epsilon (~1.2e-07) for 3-rotation composition
- Physical misalignment: ~0.00001° (negligible)
- This is a **numerical precision issue**, not a physics bug
- C-code likely has similar precision characteristics

**Priority:** P3 (tolerance adjustment needed, cosmetic issue)

**Recommended Fix:**
1. Relax tolerance from 1e-10 to **1e-7** (conservative, accommodates float32 precision)
2. Update `tests/test_at_parallel_017.py:95` threshold
3. Document rationale in test docstring (large rotation composition, float32 precision)
4. Add reference to this analysis in commit message

**Alternative Approaches (if precision critical):**
- Option B: Add explicit orthonormalization step after rotation composition (2-3h implementation)
- Option C: Use float64 for detector geometry calculations (impacts performance)
- Option D: Add rotation magnitude check and use stricter tolerance for small rotations only

**Next Actions:**
1. Update test threshold to 1e-7
2. Add docstring note explaining float32 precision for large rotations
3. Verify no regressions with updated threshold
4. Mark C16 RESOLVED in tracker

**Reproduction Selectors:**
- Targeted: `pytest -v tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts`
- Module: `pytest -v tests/test_at_parallel_017.py`
- Suite: `pytest -v tests/test_at_parallel_017.py` (includes 5 other grazing incidence tests)

---

## Cluster C2: Gradient Testing Infrastructure [ℹ️ DOCUMENTED]

**Status:** ℹ️ WORKAROUND DOCUMENTED - Not blocking, requires env flag

**Tests:** 10 gradcheck tests in `tests/test_gradients.py`

**Root Cause:** torch.compile donated buffers interfere with gradcheck numerical differentiation

**Solution:** Environment guard `NANOBRAGG_DISABLE_COMPILE=1` documented in:
- `arch.md` §15 (lines 367-373)
- `testing_strategy.md` §4.1 (lines 513-523)
- `testing_strategy.md` §1.4 (line 28)
- `docs/development/pytorch_runtime_checklist.md` §3 (line 29)

**Validation:** Phase M2 Attempt #29 (STAMP 20251011T172830Z) confirmed 10/10 gradcheck tests pass with flag

**Canonical Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_gradients.py -k "gradcheck" --tb=short
```

**Priority:** P1 (infrastructure, workaround in place)

**Next Actions:** None - documentation complete, tests pass with documented env flag

---

## Recommendations

### Immediate (Sprint 1.2 - 2h)

1. **Fix C16 Orthogonality Tolerance** (30min implementation + validation)
   - Update `tests/test_at_parallel_017.py:95` threshold from 1e-10 to 1e-7
   - Add docstring explaining float32 precision for large rotations
   - Run module tests to verify no regressions
   - Commit with reference to this analysis

### High Priority (Sprint 1.3 - 4-6h)

2. **Debug C15 Mixed Units Zero Intensity** (4-6h investigation)
   - Read test source to understand configuration
   - Generate parallel C trace for same parameters
   - Compare PyTorch trace step-by-step
   - Identify first divergence point
   - Fix root cause (likely unit conversion or geometry setup)
   - Validate fix with targeted test

### Documentation Updates (Sprint 1.4 - 30min)

3. **Update Remediation Tracker**
   - Mark C8 ✅ RESOLVED with validation timestamp
   - Update C16 with tolerance adjustment recommendation
   - Add C15 investigation plan with estimated timeline
   - Refresh Executive Summary with net 2 active bugs

---

## Validation Artifact Inventory

**Directory:** `reports/2026-01-test-suite-triage/phase_m3/20251012T012246Z/remaining_clusters/`

**Files:**
- `summary.md` - This document
- `commands.txt` - Reproduction commands executed
- `c8_mosflm/pytest.log` - C8 passing test output
- `c15_mixed_units/pytest.log` - C15 failing test output
- `c16_orthogonality/pytest.log` - C16 failing test output

**Phase M2 Reference:**
- Baseline: `reports/2026-01-test-suite-triage/phase_m/20251011T193829Z/summary.md`
- Chunk logs: `reports/2026-01-test-suite-triage/phase_m/20251011T193829Z/chunks/chunk_NN/pytest.log`

---

## Exit Criteria Met

✅ Validated C8 resolution (test passes)
✅ Confirmed C15 active bug (zero intensity)
✅ Confirmed C16 active tolerance issue (1.49e-08 vs 1e-10)
✅ Documented C2 workaround status
✅ Provided reproduction commands for all clusters
✅ Generated recommendations with time estimates
✅ Created artifact inventory

**Next Step:** Update docs/fix_plan.md Attempts History with Phase M3 evidence bundle completion (Attempt #41), refresh remediation_tracker.md with updated cluster statuses, and proceed to Sprint 1.2 (C16 tolerance fix) or Sprint 1.3 (C15 investigation) per supervisor priority.
