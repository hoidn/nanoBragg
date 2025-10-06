# Phase H5 Parity Summary

**Date:** 2025-10-21
**Task:** CLI-FLAGS-003 Phase H5 — Restore pix0 override in custom-vector path
**Goal:** Ensure PyTorch applies `-pix0_vector_mm` override even when custom detector vectors are present, matching C behavior

## Implementation Summary

### Code Changes
**File:** `src/nanobrag_torch/models/detector.py`

1. **Removed custom-vector gate** (line ~540):
   - OLD: `if pix0_override_tensor is not None and not has_custom_vectors:`
   - NEW: `if pix0_override_tensor is not None:`

2. **Updated documentation** (lines 518-531):
   - Removed outdated "C code IGNORES" comment
   - Added Phase J evidence reference (2025-10-21)
   - Documented correct override workflow

### Regression Test Results
**Command:** `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py tests/test_detector_geometry.py tests/test_crystal_geometry.py -v`

**Results:** ✅ **57 passed, 1 warning in 5.41s**

**Breakdown:**
- CLI flags tests: 26/26 passed
- Detector geometry tests: 12/12 passed
- Crystal geometry tests: 19/19 passed

**No regressions introduced.**

## Expected Physics Impact

### Before Change (Phase H3b implementation)
When custom detector vectors were present, PyTorch:
- Skipped pix0_override application
- Used default beam center calculations
- Resulted in Fbeam/Sbeam ≈ 0.037 m (wrong)
- Caused 1.14 mm pix0 Y-axis error
- Produced F_latt mismatch: PyTorch -2.4/11.8/-2.7 vs C 35.9/38.6/25.7

### After Change (Phase H5b implementation)
With custom detector vectors present, PyTorch now:
- Applies pix0_override → derives Fbeam/Sbeam ≈ 0.218 m
- Should match C geometry
- Expected to close 1.14 mm pix0 gap
- Expected to align F_latt components

## Verification Status

✅ **Code implementation complete** - Removed gate, preserved device/dtype neutrality
✅ **Regression suite green** - All 57 tests passing
⏳ **Parity verification pending** - Need to run supervisor command and compare C vs PyTorch traces

## Next Actions

1. **Generate full parity comparison** (Phase H5c):
   - Run supervisor command with C binary
   - Run with PyTorch implementation
   - Extract pix0_vector, Fbeam, Sbeam, h/k/l, F_latt from both
   - Document deltas in `phase_h5/trace_comparison.md`

2. **Update fix_plan** (Phase H5d):
   - Record Attempt #29 in `docs/fix_plan.md`
   - Include metrics and artifact paths
   - Note remaining normalization gaps for Phase K

3. **Test expectation update** (if parity achieved):
   - Update `tests/test_cli_flags.py::test_pix0_vector_mm_beam_pivot`
   - Change from "override has NO EFFECT" to "override IS applied"
   - Tighten tolerance back to 5e-5 m

## References

- Implementation notes: `reports/2025-10-cli-flags/phase_h5/implementation_notes.md`
- Test log: `reports/2025-10-cli-flags/phase_h5/pytest_regression.log`
- Plan: `plans/active/cli-noise-pix0/plan.md` Phase H5
- Evidence base: Phase J traces (2025-10-21) showing C honors override
