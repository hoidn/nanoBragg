# Phase M1e Summary: Cluster C7 Lattice Shape Fixtures

**Date:** 2025-10-11
**Cluster:** C7 (NoneType Detector)
**Scope:** `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels`
**Status:** ✅ RESOLVED

## Root Cause

Tests in `test_at_str_003.py` passed `detector=None` to `Simulator` instantiation, causing `AttributeError: 'NoneType' object has no attribute 'get_pixel_coords'` at `simulator.py:569`.

The Simulator requires a valid Detector instance because it calls `self.detector.get_pixel_coords()` during initialization to pre-cache pixel coordinates.

## Implementation

Updated two test methods to instantiate `Detector` from `self.detector_config`:

1. **test_gauss_shape_model** (line 135)
2. **test_shape_model_comparison** (line 184)

### Changes Made

**File:** `tests/test_at_str_003.py`

1. Added Detector import (line 22):
   ```python
   from nanobrag_torch.models.detector import Detector
   ```

2. Replaced `detector=None` with proper instantiation in both methods:
   ```python
   detector=Detector(self.detector_config, device="cpu", dtype=torch.float32),
   ```

## Validation Results

### Before Fix
- **Command:** `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model`
- **Result:** 1 FAILED
- **Error:** `AttributeError: 'NoneType' object has no attribute 'get_pixel_coords'`
- **Log:** `pytest_before.log`

### After Fix
- **Command:** `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py`
- **Result:** 7 passed in 4.82s
- **Log:** `pytest_full.log`

## Cluster C7 Resolution

**Failures:** 2 → 0 (100% reduction)

### Affected Tests
1. `test_gauss_shape_model` - ✅ PASSING
2. `test_shape_model_comparison` - ✅ PASSING

### Module-Level Verification
All 7 tests in `test_at_str_003.py` pass:
- test_square_shape_model
- test_round_shape_model
- test_gauss_shape_model
- test_tophat_shape_model
- test_shape_model_comparison
- test_fudge_parameter_scaling
- test_shape_models_at_bragg_peak

## Net Impact

**Phase M0 Baseline:** 46 failures
**After C1-C5:** 13 failures remaining
**After C7:** 11 failures remaining (-2, -15% reduction)

## Sprint 0 Progress

**Completed Clusters:** C1, C3, C4, C5, C7 (5/5 = 100%)
**Failures Retired:** 31/46 (67%)
**Remaining:** 15 failures (Clusters C2, C6, C8, C9)

## Code Changes

**Modified Files:**
- `tests/test_at_str_003.py` (3 insertions: 1 import line + 2 detector instantiations)

**No Production Code Changes** - Test-fixture only (as intended for Sprint 0)

## Artifacts

- `env.txt` - Environment snapshot
- `pytest_before.log` - Pre-fix failure reproduction
- `pytest_module.log` - Targeted 2-test validation
- `pytest_full.log` - Full module regression check
- `summary.md` - This document

## References

- `plans/active/test-suite-triage.md` Phase M1e (lines 213)
- `reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md` (lines 218-243)
- `input.md` Do Now section (line 7)

## Next Actions

1. ✅ Phase M1e complete - all C7 tests passing
2. Update `remediation_tracker.md` and `docs/fix_plan.md` with C7 closure
3. Proceed to Phase M1f ledger refresh per `plans/active/test-suite-triage.md`
