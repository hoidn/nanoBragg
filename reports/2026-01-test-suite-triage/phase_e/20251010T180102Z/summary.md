# Phase E Test Suite Run Summary

**Timestamp:** 2025-10-10T18:01:02Z
**Initiative:** TEST-SUITE-TRIAGE-001
**Phase:** E (2026 Refresh)
**Attempt:** #7

## Environment

**Python:** 3.13.5
**PyTorch:** 2.7.1+cu126
**CUDA:** 12.6 (available)
**Device:** NVIDIA GeForce RTX 3090
**Platform:** Linux 6.14.0-29-generic

## Test Execution

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/artifacts/pytest_full.xml
```

**Runtime:** 1860.74s (31 min 0 s)
**Exit Code:** 0 (pytest completed successfully)

## Results Summary

**Total Tests:** 692 collected (1 skipped during collection) = 691 executed
**Passed:** 516 (74.6%)
**Failed:** 49 (7.1%)
**Skipped:** 126 (18.2%)
**XFailed:** 2 (0.3%)
**Warnings:** 19

## Top 25 Slowest Tests

1. `1098.33s` - tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability
2. `144.24s` - tests/test_gradients.py::TestAdvancedGradients::test_joint_gradcheck
3. `127.89s` - tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_b
4. `71.14s` - tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_c
5. `62.31s` - tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_alpha
6. `50.56s` - tests/test_gradients.py::TestAdvancedGradients::test_gradgradcheck_cell_params
7. `48.43s` - tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_gamma
8. `48.32s` - tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_beta
9. `46.51s` - tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_a
10. `8.29s` - tests/test_at_perf_005.py::TestATPERF005CompilationOptimization::test_torch_compile_speedup
11. `8.07s` - tests/test_at_perf_005.py::TestATPERF005CompilationOptimization::test_gpu_kernel_compilation
12. `7.45s` - tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_float32_vs_float64_performance
13. `5.46s` - tests/test_at_perf_005.py::TestATPERF005CompilationOptimization::test_compilation_amortization
14. `5.42s` - tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_peak_memory_usage
15. `3.04s` - tests/test_at_parallel_001.py::TestATParallel001::test_cli_beam_center_calculation
16. `3.03s` - tests/test_at_cli_007.py::TestATCLI007NoiseDeterminism::test_overload_count_determinism
17. `3.02s` - tests/test_at_cli_003.py::TestATCLI003::test_convention_header_keys_consistency
18. `2.60s` - tests/test_at_perf_001.py::TestATPERF001VectorizationPerformance::test_vectorization_scaling
19. `2.35s` - tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant
20. `2.04s` - tests/test_at_cli_008.py::TestATCLI008DminFiltering::test_dmin_zero_has_no_effect
21. `2.02s` - tests/test_at_cli_005.py::test_cli_roi_different_conventions
22. `2.02s` - tests/test_at_cli_007.py::TestATCLI007NoiseDeterminism::test_different_seed_produces_different_noise
23. `2.02s` - tests/test_at_cli_007.py::TestATCLI007NoiseDeterminism::test_seed_determinism_without_roi
24. `2.02s` - tests/test_at_cli_008.py::TestATCLI008DminFiltering::test_dmin_filtering_reduces_intensity
25. `2.02s` - tests/test_at_cli_005.py::test_cli_roi_edge_cases

## Comparison vs Phase B (Attempt #5)

**Phase B Baseline (2025-10-10T13:58:33Z):**
- Total: 692 tests collected, 691 executed (1 skipped during collection)
- Passed: 515 (74.4%)
- Failed: 50 (7.2%)
- Skipped: 126 (18.2%)
- XFailed: 2
- Runtime: 1864.76s (31 min 4 s)

**Phase E Results (2025-10-10T18:01:02Z):**
- Total: 692 tests collected, 691 executed (1 skipped during collection)
- Passed: 516 (74.6%) — **+1 test** ✅
- Failed: 49 (7.1%) — **-1 failure** ✅
- Skipped: 126 (18.2%) — no change
- XFailed: 2 (0.3%) — no change
- Runtime: 1860.74s (31 min 0 s) — **4s faster**

**Delta Summary:**
- **Net improvement:** +1 passed, -1 failed (49 failures vs 50 in Phase B)
- Test composition identical (same 692 tests collected, same skip pattern)
- Runtime virtually identical (~4s difference, within noise)
- One test that was failing in Phase B is now passing

## Notes

- The test suite shows slight improvement over Phase B baseline (October 2025):
  - One fewer failure (49 vs 50)
  - Same test coverage and skip patterns
  - Equivalent runtime performance
- Gradient tests continue to dominate runtime (>1600s of 1860s total)
- Primary failure clusters remain consistent with Phase B/C triage:
  - Determinism issues (AT-PARALLEL-013, AT-PARALLEL-024): 6 failures
  - Grazing incidence (AT-PARALLEL-017): 4 failures
  - Source weighting (test_at_src_001*): 6 failures
  - CLI flags (test_cli_flags): 3 failures
  - Debug/trace (test_debug_trace): 4 failures
  - Detector config (test_detector_*): 5 failures
  - CUDA graphs (test_perf_pytorch_005): 6 failures
  - dtype support (test_perf_pytorch_006): 2 failures
  - Legacy suite (test_suite): 5 failures
  - Tricubic (test_tricubic_vectorized): 2 failures
  - Other: 6 failures

## Artifacts

- **Full Log:** `logs/pytest_full.log` (1860.74s runtime, 49 failures)
- **JUnit XML:** `artifacts/pytest_full.xml`
- **Failures List:** `failures_raw.md` (49 failed test nodes)
- **Failures Raw:** `failures_raw.txt` (pytest node paths)
- **Environment:** `env.txt` (Python 3.13.5, PyTorch 2.7.1+cu126, CUDA 12.6)
- **Disk Usage:** `disk_usage.txt`
- **Commands:** `commands.txt` (exact Phase E execution commands)
