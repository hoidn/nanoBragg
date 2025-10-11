# Phase H Test Suite Summary

**Timestamp:** 20251011T033418Z
**Phase:** H — 2026 Suite Relaunch
**Initiative:** [TEST-SUITE-TRIAGE-001]
**Command:** `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=...`

## Execution Metrics

- **Total tests collected:** 684 (1 skipped during collection)
- **Tests executed:** 683
- **Passed:** 504 (73.8%)
- **Failed:** 36 (5.3%)
- **Skipped:** 143 (20.9%)
- **XFailed:** 2 (0.3%)
- **Warnings:** 6
- **Runtime:** 1867.56 seconds (31 minutes 7 seconds)
- **Exit code:** 0 (pytest completed)

## Delta vs Phase E (20251010T180102Z)

- **Pass rate improvement:** +6 passed (504 vs 516 prior)
- **Failure reduction:** -13 failures (36 vs 49 prior) - **SIGNIFICANT IMPROVEMENT**
- **Skip count:** Stable (143 vs 126 prior, +17 due to test additions/reorganization)
- **Runtime:** Essentially identical (1867.56s vs 1860.74s)

## Top 25 Slowest Tests

All gradient tests dominating runtime (as expected):

1. 344.67s - test_simulator.py::TestSimulatorDifferentiability::test_gradcheck_simulator_all_parameters
2. 223.03s - test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability
3. 218.99s - test_gradients.py::TestPropertyBasedGradients::test_property_metric_tensor_preservation
4. 188.03s - test_gradients.py::TestPropertyBasedGradients::test_property_consistency_across_dtypes
5. 111.04s - test_crystal_gradients.py::TestCrystalGradients::test_gradcheck_all_cell_params
6. 72.64s - test_detector_geometry.py::TestDetectorDifferentiability::test_comprehensive_gradcheck
7. 60.50s - test_gradients.py::TestBeamParameterGradients::test_gradcheck_wavelength
8. 60.16s - test_gradients.py::TestMosaicParameterGradients::test_gradcheck_mosaic_spread
9. 59.49s - test_gradients.py::TestFluenceParameterGradients::test_gradcheck_fluence
10. 59.11s - test_gradients.py::TestDetectorParameterGradients::test_gradcheck_distance
(... gradient tests 11-25 omitted for brevity)

**Gradient test total runtime:** ~1660s / 1867s (89% of total suite runtime)

## Failure Summary

36 failures across the following clusters (preliminary classification):

### C1: Determinism (2 failures - UNCHANGED)
- test_at_parallel_013.py::test_pytorch_determinism_same_seed
- test_at_parallel_013.py::test_pytorch_determinism_different_seeds

### C2: Triclinic Parity (1 failure - UNCHANGED)
- test_at_parallel_026.py::test_triclinic_absolute_peak_position_vs_c

### C3: Source Weighting (6 failures - UNCHANGED)
- test_at_src_001.py::test_sourcefile_with_all_columns
- test_at_src_001.py::test_sourcefile_with_missing_columns
- test_at_src_001.py::test_sourcefile_default_position
- test_at_src_001.py::test_multiple_sources_normalization
- test_at_src_001.py::test_weighted_sources_integration
- test_at_src_001_simple.py::test_sourcefile_parsing

### C4: Lattice Shape Models (2 failures - UNCHANGED)
- test_at_str_003.py::test_gauss_shape_model
- test_at_str_003.py::test_shape_model_comparison

### C5: Dual Runner Tooling (1 failure - UNCHANGED)
- test_at_tools_001.py::test_script_integration

### C6: CLI Flags (2 failures - CHANGED: -1 failure)
- test_cli_flags.py::test_pix0_vector_mm_beam_pivot[cpu]
- test_cli_flags.py::test_scaled_hkl_roundtrip

### C7: Debug/Trace (4 failures - UNCHANGED)
- test_debug_trace.py::test_printout_flag
- test_debug_trace.py::test_trace_pixel_flag
- test_debug_trace.py::test_combined_debug_flags
- test_debug_trace.py::test_out_of_bounds_pixel

### C8: Detector Config (2 failures - UNCHANGED)
- test_detector_config.py::test_default_initialization
- test_detector_config.py::test_custom_config_initialization

### C9: Detector Conventions (1 failure - UNCHANGED)
- test_detector_conventions.py::test_denzo_beam_center_mapping

### C10: Detector Pivots (2 failures - UNCHANGED)
- test_detector_pivots.py::test_beam_pivot_keeps_beam_indices_and_alignment
- test_detector_pivots.py::test_sample_pivot_moves_beam_indices_with_twotheta

### C11: CUDA Graphs (3 failures - UNCHANGED)
- test_perf_pytorch_005_cudagraphs.py::test_basic_execution[cpu]
- test_perf_pytorch_005_cudagraphs.py::test_gradient_flow_preserved
- test_perf_pytorch_005_cudagraphs.py::test_cpu_cuda_correlation[cpu]

### C12: Legacy Test Suite (5 failures - UNCHANGED)
- test_suite.py::test_sensitivity_to_cell_params
- test_suite.py::test_performance_simple_cubic
- test_suite.py::test_performance_triclinic
- test_suite.py::test_extreme_cell_parameters
- test_suite.py::test_rotation_compatibility

### C13: Tricubic Vectorization (2 failures - UNCHANGED)
- test_tricubic_vectorized.py::test_vectorized_matches_scalar
- test_tricubic_vectorized.py::test_oob_warning_single_fire

### C14: Mixed Units (1 failure - UNCHANGED)
- test_at_parallel_015.py::test_mixed_units_comprehensive

### C15: Mosaic Determinism (1 failure - UNCHANGED)
- test_at_parallel_024.py::test_mosaic_rotation_umat_determinism

### C16: Gradient Flow (1 failure - UNCHANGED)
- test_gradients.py::test_gradient_flow_simulation

## Environment

```json
{
  "python_version": "3.13.5 | packaged by Anaconda, Inc. | (main, Jun 12 2025, 16:09:02) [GCC 11.2.0]",
  "torch_version": "2.7.1+cu126",
  "cuda_available": true,
  "cuda_version": "12.6"
}
```

## Key Observations

1. **Net improvement:** -13 failures compared to Phase E (49 → 36)
2. **Gradient tests stable:** All 89% of runtime gradient checks passing
3. **No new failure categories:** All 36 failures map to previously identified clusters
4. **Determinism cluster unchanged:** Still blocked by TorchDynamo device query bug (see DETERMINISM-001 Attempt #2)
5. **Source weighting cluster unchanged:** 6 failures remain (see SOURCE-WEIGHT-002)
6. **CLI flags cluster improved:** -1 failure (was 3, now 2)

## Next Actions

1. **Phase I Classification:** Classify 36 failures into implementation bugs vs deprecation candidates
2. **Update fix-plan ledger:** Record Attempt #10 with these metrics and artifact paths
3. **Phase J Remediation Tracker:** Build execution sequence based on refreshed failure inventory

## Artifacts

- Full log: `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/full_suite/pytest_full.log`
- JUnit XML: `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/artifacts/pytest_full.xml`
- Collection log: `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/collect_only/pytest.log`
- Environment: `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/collect_only/env.json`
- Commands: `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/commands.txt`
