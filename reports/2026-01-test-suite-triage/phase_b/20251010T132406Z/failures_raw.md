# Phase B Test Suite Failures (Partial Run)

**Execution Status:** TIMEOUT after 600s (10 minutes)
**Progress:** ~75% complete (reached `test_gradients.py::test_gradcheck_cell_alpha`)
**Collection:** 692 tests total, 1 skipped initially
**Timestamp:** 2025-10-10T13:24:06Z

## Blocker

Test suite exceeded 10-minute timeout limit. Partial results captured below represent failures observed before timeout.

## Failure Inventory (Partial - 34 failures observed)

### AT-CLI-002 (1 failure)
- `tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` FAILED [3%]

### AT-PARALLEL-013 Determinism (3 failures)
- `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_same_seed` FAILED [26%]
- `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_different_seeds` FAILED [26%]
- `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_consistency_across_runs` FAILED [26%]

### AT-PARALLEL-015 Mixed Units (1 failure)
- `tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive` FAILED [28%]

### AT-PARALLEL-017 Grazing Incidence (4 failures)
- `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts` FAILED [29%]
- `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_twotheta` FAILED [29%]
- `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_combined_extreme_angles` FAILED [29%]
- `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_near_90_degree_incidence` FAILED [29%]

### AT-PARALLEL-024 Determinism (3 failures)
- `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_pytorch_determinism` FAILED [34%]
- `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_seed_independence` FAILED [34%]
- `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_mosaic_rotation_umat_determinism` FAILED [34%]

### AT-PARALLEL-026 Triclinic Position (1 failure)
- `tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c` FAILED [35%]

### AT-SRC-001 Sourcefile Weighting (5 failures)
- `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_all_columns` FAILED [47%]
- `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_missing_columns` FAILED [47%]
- `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_default_position` FAILED [47%]
- `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_multiple_sources_normalization` FAILED [47%]
- `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_weighted_sources_integration` FAILED [48%]
- `tests/test_at_src_001_simple.py::test_sourcefile_parsing` FAILED [48%]

### AT-STR-003 Lattice Shape Models (2 failures)
- `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model` FAILED [53%]
- `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_shape_model_comparison` FAILED [53%]

### AT-TOOLS-001 Dual Runner (1 failure)
- `tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration` FAILED [55%]

### CLI Flags - pix0_vector (3 failures)
- `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]` FAILED [59%]
- `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cuda]` FAILED [59%]
- `tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip` FAILED [60%]

### Debug Trace (4 failures)
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag` FAILED [67%]
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_trace_pixel_flag` FAILED [67%]
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_combined_debug_flags` FAILED [67%]
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_out_of_bounds_pixel` FAILED [67%]

### Detector Config (2 failures)
- `tests/test_detector_config.py::TestDetectorInitialization::test_default_initialization` FAILED [70%]
- `tests/test_detector_config.py::TestDetectorInitialization::test_custom_config_initialization` FAILED [70%]

### Detector Conventions (1 failure)
- `tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping` FAILED [71%]

### Detector Pivots (2 failures)
- `tests/test_detector_pivots.py::test_beam_pivot_keeps_beam_indices_and_alignment` FAILED [73%]
- `tests/test_detector_pivots.py::test_sample_pivot_moves_beam_indices_with_twotheta` FAILED [74%]

## Summary Statistics (Partial)
- **Total failures observed:** 34
- **Progress at timeout:** ~75% (520+ tests executed of 692 collected)
- **Exit code:** Timeout (no clean pytest summary available)
- **Remaining tests:** ~172 tests not executed (25% of suite)

## Missing Data
- Final test counts (pass/fail/skip/xfail totals)
- Slowest 25 tests (--durations=25 incomplete)
- junit XML may be incomplete
- Tests after `test_gradients.py::test_gradcheck_cell_alpha` not executed

## Next Actions
1. Phase C triage must note partial coverage; 25% of suite status unknown
2. Consider splitting suite execution or increasing timeout for Phase D remediation run
3. Prioritize observed failures for classification
4. Re-run full suite with extended timeout once blockers are resolved
