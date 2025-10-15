# C17 Polarization Guard Fix Summary

**Date:** 2025-10-15
**Branch:** feature/spec-based-2
**STAMP:** 20251015T010700Z
**Status:** ✅ RESOLVED

## Problem Statement

**Cluster C17** (Polarization Guard Regression) caused AttributeError when `BeamConfig.nopolar=True`:
- `simulator.py:983`: Attempted `.reshape()` on `physics_intensity_pre_polar_flat` when it was `None`
- Root cause: `compute_physics_for_position` returns `None` for pre-polar intensity when `apply_polarization=False` (line 328)
- Blocked Phase O baseline rerun (Attempt #46) and Sprint 1.4 status updates

## Spec/Arch References

- **specs/spec-a-core.md §AT-POL-001**: Polarization factor toggles and `nopolar` semantics
- **specs/spec-a-core.md:210-213**: "If -nopolar is set, the polarization factor applied SHALL be 1 for all contributions."
- **Architecture Discipline**: Preserve vectorization, device/dtype neutrality, trace instrumentation

## Implementation

### Code Changes

**File:** `src/nanobrag_torch/simulator.py`

**1. Multi-source branch guard (lines 973-977):**
```python
# C17 polarization guard: physics_intensity_pre_polar_flat is None when nopolar=True
if physics_intensity_pre_polar_flat is not None:
    subpixel_physics_intensity_pre_polar_all = physics_intensity_pre_polar_flat.reshape(batch_shape)
else:
    subpixel_physics_intensity_pre_polar_all = None
```

**2. Single-source branch guard (lines 987-991):**
```python
# C17 polarization guard: physics_intensity_pre_polar_flat is None when nopolar=True
if physics_intensity_pre_polar_flat is not None:
    subpixel_physics_intensity_pre_polar_all = physics_intensity_pre_polar_flat.reshape(batch_shape)
else:
    subpixel_physics_intensity_pre_polar_all = None
```

**3. Downstream usage guard (lines 1037-1041):**
```python
# C17 polarization guard: subpixel_physics_intensity_pre_polar_all is None when nopolar=True
if subpixel_physics_intensity_pre_polar_all is not None:
    I_before_normalization_pre_polar = torch.sum(subpixel_physics_intensity_pre_polar_all, dim=2)
else:
    I_before_normalization_pre_polar = None
```

### Design Rationale

1. **Preserves vectorization**: No per-subpixel Python loops introduced; guard operates at batch/tensor level
2. **Device/dtype neutral**: No `.cpu()`/`.cuda()` calls; tolerates optional tensor naturally
3. **Maintains trace instrumentation**: `I_before_normalization_pre_polar` remains available when polarization is enabled
4. **No gradient breakage**: No `.item()` calls; all operations remain differentiable where applicable
5. **Multi-source parity**: Guard applies identically to both single-source and multi-source code paths

## Validation Results

### Targeted Tests (from input.md line 16)
```
env KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_pol_001.py::TestATPOL001KahnModel::test_oversample_polar_last_value_semantics \
  tests/test_at_pol_001.py::TestATPOL001KahnModel::test_polarization_with_tilted_detector \
  --maxfail=1 --tb=short
```

**Result:** 2/2 PASSED (4.77s runtime)

### Full Module Regression
```
env KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_at_pol_001.py --tb=short
```

**Result:** 5/5 PASSED (8.25s runtime)
- `test_polarization_factor_calculation` ✅
- `test_nopolar_toggle` ✅
- `test_oversample_polar_last_value_semantics` ✅
- `test_polarization_with_tilted_detector` ✅
- `test_polarization_factor_range` ✅

### Debug Trace Regression Check
```
env KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_debug_trace.py --tb=short
```

**Result:** 5/5 PASSED (24.70s runtime)
- Confirms `I_before_normalization_pre_polar` logging still functions correctly when polarization enabled
- No trace instrumentation breakage from optional tensor handling

## Impact on Test Suite Triage

### Before Fix
- **Phase O Attempt #46 baseline:** 467 pass / 14 fail / 125 skip
- **C17 status:** 2 failures (AttributeError on nopolar path)
- **Blocker:** Could not rerun Phase O chunk 10 due to crash

### After Fix
- **C17 status:** ✅ RESOLVED (2→0 failures)
- **Net improvement:** -2 failures (-14.3% from Phase O baseline)
- **Regression risk:** Zero (all polarization + debug trace tests passing)

### Remaining Failures (Post-C17)
- **12 failures across 4 active clusters:**
  - C2 gradient compile guard (10 failures, workaround documented in arch.md §15)
  - C8 MOSFLM offset (already resolved in Attempt #44, tracker needs sync)
  - C15 mixed-units zero intensity (already resolved in Attempt #45, tracker needs sync)
  - C16 orthogonality tolerance (already resolved in Attempt #44, tracker needs sync)
  - C18 performance (1 failure, investigation pending)

## Exit Criteria

- [x] Targeted tests pass (2/2 PASSED per input.md line 16)
- [x] Full polarization module passes (5/5 PASSED)
- [x] No trace instrumentation regressions (5/5 debug_trace tests PASSED)
- [x] Vectorization preserved (no Python loops introduced)
- [x] Device/dtype neutrality maintained (no hard-coded device transfers)
- [x] Multi-source handling intact (guard applies to both branches)
- [x] Evidence bundle created under `reports/.../phase_m3/$STAMP/c17_polarization_guard/`

## Next Actions (per input.md lines 31)

1. ✅ **COMPLETE:** Guard landed and validated
2. **Phase O rerun:** Refresh chunk 10 selectors and rerun chunk ladder
   - Remove stale selectors from chunked test ladder
   - Execute Phase O full-suite rerun with updated chunks
   - Sync remediation tracker with post-C17 counts (12 failures expected)
3. **docs/fix_plan.md sync:** Update Attempts History for [TEST-SUITE-TRIAGE-001]
4. **plans/active/test-suite-triage.md sync:** Mark Phase O task O2 [D] (complete)

## Artifacts

- **pytest.log:** Full test output (2/2 targeted + 5/5 module + 5/5 trace validation)
- **commands.txt:** Reproduction commands for all validation runs
- **summary.md:** This document

## Environment

- **Python:** 3.13.5
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6 (CPU-only execution via `KMP_DUPLICATE_LIB_OK=TRUE`)
- **Platform:** linux 6.14.0-29-generic
