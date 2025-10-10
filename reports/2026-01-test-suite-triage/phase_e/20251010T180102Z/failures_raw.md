# Phase E Failures

**Timestamp:** 2025-10-10T18:01:02Z
**Log:** logs/pytest_full.log
**Total Failures:** 49

## Failed Tests

- `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_same_seed`
- `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_different_seeds`
- `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_consistency_across_runs`
- `tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`
- `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts`
- `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_twotheta`
- `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_combined_extreme_angles`
- `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_near_90_degree_incidence`
- `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_pytorch_determinism`
- `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_seed_independence`
- `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_mosaic_rotation_umat_determinism`
- `tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`
- `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_all_columns`
- `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_missing_columns`
- `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_default_position`
- `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_multiple_sources_normalization`
- `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_weighted_sources_integration`
- `tests/test_at_src_001_simple.py::test_sourcefile_parsing`
- `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model`
- `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_shape_model_comparison`
- `tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration`
- `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]`
- `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cuda]`
- `tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip`
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag`
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_trace_pixel_flag`
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_combined_debug_flags`
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_out_of_bounds_pixel`
- `tests/test_detector_config.py::TestDetectorInitialization::test_default_initialization`
- `tests/test_detector_config.py::TestDetectorInitialization::test_custom_config_initialization`
- `tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping`
- `tests/test_detector_pivots.py::test_beam_pivot_keeps_beam_indices_and_alignment`
- `tests/test_detector_pivots.py::test_sample_pivot_moves_beam_indices_with_twotheta`
- `tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation`
- `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution[cpu]`
- `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution[cuda]`
- `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cuda_multiple_runs`
- `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_gradient_flow_preserved`
- `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cpu_cuda_correlation[cpu]`
- `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cpu_cuda_correlation[cuda]`
- `tests/test_perf_pytorch_006.py::test_dtype_support[dtype1]`
- `tests/test_perf_pytorch_006.py::test_float32_float64_correlation`
- `tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params`
- `tests/test_suite.py::TestTier1TranslationCorrectness::test_performance_simple_cubic`
- `tests/test_suite.py::TestTier1TranslationCorrectness::test_performance_triclinic`
- `tests/test_suite.py::TestTier1TranslationCorrectness::test_extreme_cell_parameters`
- `tests/test_suite.py::TestTier1TranslationCorrectness::test_rotation_compatibility`
- `tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar`
- `tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire`
