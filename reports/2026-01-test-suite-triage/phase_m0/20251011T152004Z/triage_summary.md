# Phase M0 Detailed Triage Summary

**Run ID:** 20251011T152004Z
**Purpose:** Establish baseline metrics for test suite health and identify failure clusters

## Executive Summary

- **Total Tests:** 687 collected, 649 executed (38 truly skipped)
- **Pass Rate:** 74.5% (512/687) - excluding legitimately skipped tests
- **Failure Rate:** 7.7% (53/687)
- **Health Status:** 🟡 MODERATE - Core functionality intact but critical regressions present

## Critical Blockers (P0)

### CB-1: Gradient Correctness Broken (10 failures)
**Location:** tests/test_gradients.py (Chunk 03)
**Status:** 🔴 BLOCKING - Core architectural requirement violated

**Failed Tests:**
1. `TestCellParameterGradients::test_gradcheck_cell_a`
2. `TestCellParameterGradients::test_gradcheck_cell_b`
3. `TestCellParameterGradients::test_gradcheck_cell_c`
4. `TestCellParameterGradients::test_gradcheck_cell_alpha`
5. `TestCellParameterGradients::test_gradcheck_cell_beta`
6. `TestCellParameterGradients::test_gradcheck_cell_gamma`
7. `TestAdvancedGradients::test_joint_gradcheck`
8. `TestAdvancedGradients::test_gradgradcheck_cell_params`
9. `TestAdvancedGradients::test_gradient_flow_simulation`
10. `TestPropertyBasedGradients::test_property_gradient_stability`

**Root Cause:** Likely broke differentiability contract (ADR-08) - possibly `.item()` usage or tensor detachment
**Impact:** Gradient-based optimization workflows completely broken
**Remediation:**
- Review recent changes to CrystalConfig/Crystal class
- Check for `.item()`, `.detach()`, or `.numpy()` calls on grad-enabled tensors
- Verify @property methods return tensors, not scalars
- Run `torch.autograd.gradcheck` on isolated crystal parameter updates

**Priority:** Fix BEFORE any other work - this violates arch.md § 15 (Differentiability Guidelines)

---

### CB-2: CLI Flag Implementation Incomplete (16 failures)
**Location:** tests/test_cli_flags.py (Chunk 10)
**Status:** 🔴 BLOCKING - New features non-functional

**Failed Tests:**
1-7. `TestPix0VectorAlias::test_pix0_*` (7 tests) - pix0 vector flag aliases
8-11. `TestNoiseSuppressionFlag::test_*` (4 tests) - --nonoise flag
12-15. `TestCLIIntegrationSanity::test_*` (4 tests) - integration with existing flags
16. `TestCLIPix0Override::test_*` (1 test) - pix0 override behavior

**Root Cause:** Recent CLI additions (`--pix0`, `--nonoise`) not fully integrated
**Impact:** Users cannot use new CLI features; regression in user-facing API
**Remediation:**
- Review `src/nanobrag_torch/__main__.py` argparse setup
- Verify flag handling in `parse_and_validate_args()`
- Test CLI invocations manually: `nanoBragg --pix0 1.0 2.0 3.0 --nonoise ...`

**Priority:** Fix before declaring CLI feature complete

---

## High Priority (P1)

### HP-1: Debug Output Path Broken (9 failures)
**Location:** tests/test_debug_trace.py, tests/test_oversample_autoselect.py (Chunk 06)
**Status:** 🟠 HIGH - Debugging workflows broken

**Failed Tests:**
1. `test_printout_flag` - UnboundLocalError: I_before_normalization_pre_polar
2. `test_trace_pixel_flag` - Same error
3. `test_combined_debug_flags` - Same error
4. `test_out_of_bounds_pixel` - Same error
5. `test_beam_center_scales_with_pixel_size` - MOSFLM offset issue
6. `test_beam_center_parameter_consistency` - MOSFLM offset issue
7. `test_gauss_shape_model` - Simulator requires detector
8. `test_shape_model_comparison` - Simulator requires detector
9. `test_sincg_throughput` - Performance 5.8 M/s vs 10 M/s threshold

**Root Cause (UnboundLocalError):** Variable `I_before_normalization_pre_polar` not initialized in debug code path
**Location:** Likely in simulator.py debug/trace output logic
**Remediation:**
- Search for `I_before_normalization_pre_polar` in src/
- Ensure variable initialized before conditional debug output
- Add smoke test for `--printout` and `--trace-pixel` flags

**Priority:** Fix before next debugging session - observability critical

---

### HP-2: Detector API Device Transfer Broken (6 failures)
**Location:** tests/test_suite.py (Chunk 04)
**Status:** 🟠 HIGH - Device neutrality violated

**Failed Tests:**
1. `test_sensitivity_to_cell_params` - AttributeError: 'float' has no 'to'
2. `test_performance_simple_cubic` - Same
3. `test_performance_triclinic` - Same
4. `test_extreme_cell_parameters` - Same
5. `test_rotation_compatibility` - Same
6. `test_cpu_thread_scaling` - Thread scaling 1.06x < 1.15x threshold

**Root Cause:** `Detector.to()` method trying to call `.to()` on float beam_center attributes
**Location:** src/nanobrag_torch/models/detector.py:Detector.to() method
**Remediation:**
- Convert float attributes to tensors before calling .to()
- Or: use `isinstance(attr, torch.Tensor)` guard before .to()
- Review CLAUDE.md rule 16 (PyTorch Device & Dtype Neutrality)

**Priority:** Fix to restore device-agnostic operation

---

### HP-3: Simulator Initialization API Inconsistency (4 failures)
**Location:** tests/test_perf_pytorch_005_cudagraphs.py, tests/test_at_parallel_015.py (Chunk 09)
**Status:** 🟠 HIGH - API confusion

**Failed Tests:**
1. `test_basic_execution[cpu]` - TypeError: unexpected 'detector_config'
2. `test_gradient_flow_preserved` - Same
3. `test_cpu_cuda_correlation[cpu]` - Same
4. `test_mixed_units_comprehensive` - Mixed units handling

**Root Cause:** Simulator.__init__() signature changed; some tests use old API
**Remediation:**
- Standardize on `Simulator(crystal, detector, beam, ...)` OR config-based init
- Update all test files to use consistent initialization pattern
- Add deprecation warnings for old API if backward compat needed

**Priority:** Fix for API consistency

---

## Medium Priority (P2)

### MP-1: Source Weights and Divergence (2 failures - Chunk 01)
**Tests:**
1. `test_large_detector_tilts` (test_at_parallel_017.py)
2. `test_sourcefile_divergence_warning` (test_cli_scaling.py) - SystemExit on missing inputs

**Impact:** LOW - Edge cases in tilted detector and sourcefile handling
**Remediation:** Review spec-a-core.md sourcefile semantics; fix validation logic

---

### MP-2: Detector Offset Preservation (1 failure - Chunk 07)
**Test:** `test_detector_offset_preservation` (test_at_parallel_003.py)
**Impact:** LOW - Specific to detector offset edge case
**Remediation:** Review detector geometry calculation with large offsets

---

### MP-3: Performance Regressions (2 failures - Chunks 04, 06)
**Tests:**
1. `test_cpu_thread_scaling` - 1.06x vs 1.15x threshold
2. `test_sincg_throughput` - 5.8 M/s vs 10 M/s threshold

**Impact:** MEDIUM - Performance below targets but not blocking
**Remediation:** Profile and optimize hot paths; consider vectorization improvements

---

## Known Issues (Not Bugs)

### Skipped Tests Breakdown
- **59 skipped** (Chunk 08): Parity matrix tests requiring `NB_RUN_PARALLEL=1` ✅ Expected
- **9-13 skipped per chunk**: Tests requiring CUDA, C binary, or specific environment ✅ Expected
- **1 xfailed** (Chunk 03): Known gradient check issue marked as expected failure ✅ Expected

---

## Remediation Tracker

| ID | Description | Priority | Status | Owner | ETA |
|----|-------------|----------|--------|-------|-----|
| CB-1 | Fix gradient correctness | P0 | 🔴 TODO | - | - |
| CB-2 | Complete CLI flag implementation | P0 | 🔴 TODO | - | - |
| HP-1 | Fix debug output UnboundLocalError | P1 | 🟠 TODO | - | - |
| HP-2 | Fix Detector.to() device transfer | P1 | 🟠 TODO | - | - |
| HP-3 | Standardize Simulator init API | P1 | 🟠 TODO | - | - |
| MP-1 | Source weights edge cases | P2 | 🟡 TODO | - | - |
| MP-2 | Detector offset preservation | P2 | 🟡 TODO | - | - |
| MP-3 | Performance optimization | P2 | 🟡 TODO | - | - |

---

## Comparison to Previous Runs

**Baseline:** This IS the baseline (Phase M0 Attempt #19)
**Next Steps:**
- Fix P0 blockers (CB-1, CB-2)
- Rerun Phase M0 to establish "clean baseline" metrics
- Track remediation progress in docs/fix_plan.md

---

## Environment Details

**Python:** 3.11.x
**PyTorch:** 2.x
**Platform:** Linux 6.14.0-29-generic
**CUDA:** Disabled (CUDA_VISIBLE_DEVICES=-1)
**KMP_DUPLICATE_LIB_OK:** TRUE

**Full environment:** See `preflight/env.txt` and `preflight/pip_freeze.txt`

---

## Next Actions for Supervisor (galph)

1. Update docs/fix_plan.md `[TEST-SUITE-TRIAGE-001]` Attempts History with:
   - STAMP: 20251011T152004Z
   - Results: 512 passed / 53 failed / 136 skipped
   - Artifacts: reports/2026-01-test-suite-triage/phase_m0/20251011T152004Z/
   - Triage clusters: CB-1 (gradients), CB-2 (CLI flags), HP-1 (debug output)

2. Create fix_plan items for each cluster:
   - [GRAD-FIX-001] Restore gradient correctness (CB-1)
   - [CLI-FIX-001] Complete CLI flag implementation (CB-2)
   - [DEBUG-FIX-001] Fix UnboundLocalError in debug paths (HP-1)

3. Prioritize next ralph loop: Start with CB-1 (gradient correctness) as highest priority

---

**Report Generated:** 2025-10-11T15:30:00Z
**Phase:** M0 (Baseline Capture)
**Status:** ✅ COMPLETE - Ready for remediation planning
