# Phase M3 MOSFLM Fix Evidence Bundle

## Summary

**Status:** ✅ **PASS** - All targeted tests passed
**Timestamp:** 20251011T190855Z
**Purpose:** Validate MOSFLM detector defaults implementation per [DETECTOR-CONFIG-001]
**Spec Reference:** `specs/spec-a-core.md:72` — MOSFLM defaults require (detsize + pixel)/2 before applying +0.5 mapping

## Test Results

### Test 1: Detector Configuration Unit Tests
- **Command:** `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py --maxfail=0`
- **Result:** ✅ 15 passed in 1.94s
- **Coverage:**
  - Default value initialization
  - Post-init defaults (MOSFLM beam center calculations)
  - Convention-specific defaults (XDS, MOSFLM)
  - Custom twotheta axis handling
  - Validation checks (invalid parameters)
  - Tensor parameter support
  - Device/dtype compatibility

### Test 2: AT-PARALLEL-002 Beam Center Scaling
- **Command:** `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size --maxfail=0`
- **Result:** ✅ 1 passed in 1.92s
- **Validation:** Confirms beam center scales correctly with pixel size under MOSFLM convention
- **Expected Behavior:**
  - 513.0 px beam center for 1024x1024 detector with 0.1mm pixels
  - 1024.5 px beam center for 2048x2048 detector with 0.1mm pixels
  - Correlation ≥0.9999 between different pixel size configurations

## Key Findings

1. **MOSFLM Default Formula Validated:**
   - Implementation correctly computes `(detsize_s + pixel) / 2` and `(detsize_f + pixel) / 2` for default beam centers
   - +0.5 pixel offset mapping correctly applied: `Sbeam = Xbeam + 0.5·pixel`, `Fbeam = Ybeam + 0.5·pixel`

2. **Beam Center Scaling Parity:**
   - AT-PARALLEL-002 confirms beam center scales proportionally with detector size
   - No regression in pixel size independence behavior

3. **Configuration Contract:**
   - All detector config validation checks pass (invalid distance, pixel size, oversample)
   - Tensor parameter support maintained (gradient flow preserved)
   - Device/dtype neutrality confirmed (CPU execution successful)

## Acceptance Criteria Met

- ✅ All `test_detector_config.py` tests pass (15/15)
- ✅ AT-PARALLEL-002 beam center scaling test passes (1/1)
- ✅ No import/collection errors
- ✅ Runtime acceptable (<5s total)
- ✅ Exit code 0 for both test commands

## Environment

- **Python:** 3.13.5
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6 (available, forced CPU-only via CUDA_VISIBLE_DEVICES=-1)
- **Device:** CPU
- **Dtype:** float32 (default)

## Next Actions

Per `input.md` directive and `plans/active/detector-config.md`:

1. **Tracker Sync:** Update `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md` with new MOSFLM validation status
2. **Remediation Tracker Update:** Update `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` cluster C7 row with Phase M3 evidence
3. **Fix Plan Append:** Add Attempt entry to `docs/fix_plan.md` [DETECTOR-CONFIG-001] with metrics and artifact paths
4. **Chunked Rerun:** Proceed to Phase M chunked test suite rerun per `plans/active/test-suite-triage.md` Phase M instructions

## Artifact Paths

- Commands: `reports/2026-01-test-suite-triage/phase_m3/20251011T190855Z/mosflm_fix/commands.txt`
- Test 1 Log: `reports/2026-01-test-suite-triage/phase_m3/20251011T190855Z/mosflm_fix/test_detector_config.log`
- Test 2 Log: `reports/2026-01-test-suite-triage/phase_m3/20251011T190855Z/mosflm_fix/test_at_parallel_002.log`
- This Summary: `reports/2026-01-test-suite-triage/phase_m3/20251011T190855Z/mosflm_fix/summary.md`
