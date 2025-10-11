# Phase M0 Test Failures

**Timestamp:** 20251011T153931Z
**Total Failures:** 46

## Failures by Chunk

### Chunk 01 (2 failures)
- `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts` - AssertionError: fdet and sdet not orthogonal (tolerance 1e-10, got 1.49e-08)
- `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_divergence_warning` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)

### Chunk 03 (10 failures)
- `tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_a` - RuntimeError: donated buffers requires create_graph=False
- `tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_b` - RuntimeError: donated buffers requires create_graph=False
- `tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_c` - RuntimeError: donated buffers requires create_graph=False
- `tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_alpha` - RuntimeError: donated buffers requires create_graph=False
- `tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_beta` - RuntimeError: donated buffers requires create_graph=False
- `tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_gamma` - RuntimeError: donated buffers requires create_graph=False
- `tests/test_gradients.py::TestAdvancedGradients::test_joint_gradcheck` - RuntimeError: donated buffers requires create_graph=False
- `tests/test_gradients.py::TestAdvancedGradients::test_gradgradcheck_cell_params` - RuntimeError: donated buffers requires create_graph=False
- `tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation` - AssertionError: At least one gradient should be non-zero
- `tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability` - RuntimeError: donated buffers requires create_graph=False

### Chunk 04 (5 failures)
- `tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params` - AttributeError: 'float' object has no attribute 'to' (beam_center_s)
- `tests/test_suite.py::TestTier1TranslationCorrectness::test_performance_simple_cubic` - AttributeError: 'float' object has no attribute 'to' (beam_center_s)
- `tests/test_suite.py::TestTier1TranslationCorrectness::test_performance_triclinic` - AttributeError: 'float' object has no attribute 'to' (beam_center_s)
- `tests/test_suite.py::TestTier1TranslationCorrectness::test_extreme_cell_parameters` - AttributeError: 'float' object has no attribute 'to' (beam_center_s)
- `tests/test_suite.py::TestTier1TranslationCorrectness::test_rotation_compatibility` - AttributeError: 'float' object has no attribute 'to' (beam_center_s)

### Chunk 06 (8 failures)
- `tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size` - AssertionError: Beam center S (pixels) mismatch (expected 128.0, got 128.5)
- `tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_parameter_consistency` - AssertionError: Detector beam_center_s incorrect (expected 128.0, got 128.5)
- `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model` - AttributeError: 'NoneType' object has no attribute 'get_pixel_coords' (detector=None)
- `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_shape_model_comparison` - AttributeError: 'NoneType' object has no attribute 'get_pixel_coords' (detector=None)
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag` - UnboundLocalError: cannot access local variable 'I_before_normalization_pre_polar'
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_trace_pixel_flag` - UnboundLocalError: cannot access local variable 'I_before_normalization_pre_polar'
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_combined_debug_flags` - UnboundLocalError: cannot access local variable 'I_before_normalization_pre_polar'
- `tests/test_debug_trace.py::TestDebugTraceFeatures::test_out_of_bounds_pixel` - UnboundLocalError: cannot access local variable 'I_before_normalization_pre_polar'

### Chunk 07 (1 failure)
- `tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation` - AssertionError: Beam center S pixels incorrect (expected 200.0, got 200.5)

### Chunk 09 (4 failures)
- `tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive` - AssertionError: Zero maximum intensity
- `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution[cpu]` - TypeError: Simulator.__init__() got an unexpected keyword argument 'detector_config'
- `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_gradient_flow_preserved` - TypeError: Simulator.__init__() got an unexpected keyword argument 'detector_config'
- `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cpu_cuda_correlation[cpu]` - TypeError: Simulator.__init__() got an unexpected keyword argument 'detector_config'

### Chunk 10 (16 failures)
- `tests/test_cli_flags.py::TestPix0VectorAlias::test_pix0_meters_alias` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestPix0VectorAlias::test_pix0_millimeter_alias` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestPix0VectorAlias::test_pix0_meters_and_mm_equivalence` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestPix0VectorAlias::test_dual_pix0_flag_rejection` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestPix0VectorAlias::test_pix0_signed_combinations[pix0_m0-pix0_mm0]` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestPix0VectorAlias::test_pix0_signed_combinations[pix0_m1-pix0_mm1]` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestPix0VectorAlias::test_pix0_signed_combinations[pix0_m2-pix0_mm2]` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestNoiseSuppressionFlag::test_nonoise_suppresses_noise_output` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestNoiseSuppressionFlag::test_noisefile_without_nonoise` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestNoiseSuppressionFlag::test_nonoise_preserves_seed` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestNoiseSuppressionFlag::test_nonoise_without_noisefile` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestCLIIntegrationSanity::test_pix0_does_not_alter_beam_vector` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestCLIIntegrationSanity::test_pix0_triggers_custom_convention` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestCLIIntegrationSanity::test_roi_unaffected_by_new_flags` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestCLIIntegrationSanity::test_convention_preserved_without_pix0` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)
- `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]` - SystemExit: 1 (missing -hkl/-default_F during arg parsing)

---

## Failures by Test File

### tests/test_gradients.py (10 failures)
All related to PyTorch AOT compilation with donated buffers incompatible with gradcheck's create_graph requirement:
- test_gradcheck_cell_a
- test_gradcheck_cell_b
- test_gradcheck_cell_c
- test_gradcheck_cell_alpha
- test_gradcheck_cell_beta
- test_gradcheck_cell_gamma
- test_joint_gradcheck
- test_gradgradcheck_cell_params
- test_property_gradient_stability
- test_gradient_flow_simulation (different error: gradients all zero)

### tests/test_cli_flags.py (16 failures)
All SystemExit failures due to missing -hkl/-default_F in test setup:
- 7 TestPix0VectorAlias tests
- 4 TestNoiseSuppressionFlag tests
- 4 TestCLIIntegrationSanity tests
- 1 TestCLIPix0Override test

### tests/test_suite.py (5 failures)
All AttributeError: 'float' object has no attribute 'to' in Detector.to() method:
- test_sensitivity_to_cell_params
- test_performance_simple_cubic
- test_performance_triclinic
- test_extreme_cell_parameters
- test_rotation_compatibility

### tests/test_debug_trace.py (4 failures)
All UnboundLocalError for 'I_before_normalization_pre_polar' variable:
- test_printout_flag
- test_trace_pixel_flag
- test_combined_debug_flags
- test_out_of_bounds_pixel

### tests/test_perf_pytorch_005_cudagraphs.py (3 failures)
All TypeError for unexpected keyword argument 'detector_config':
- test_basic_execution[cpu]
- test_gradient_flow_preserved
- test_cpu_cuda_correlation[cpu]

### tests/test_at_parallel_002.py (2 failures)
Beam center off by 0.5 pixels (MOSFLM offset issue):
- test_beam_center_scales_with_pixel_size
- test_beam_center_parameter_consistency

### tests/test_at_str_003.py (2 failures)
AttributeError for NoneType detector in Simulator init:
- test_gauss_shape_model
- test_shape_model_comparison

### tests/test_at_parallel_003.py (1 failure)
Beam center off by 0.5 pixels:
- test_detector_offset_preservation

### tests/test_at_parallel_015.py (1 failure)
Zero intensity output:
- test_mixed_units_comprehensive

### tests/test_at_parallel_017.py (1 failure)
Detector basis vectors not orthogonal to required tolerance:
- test_large_detector_tilts

### tests/test_cli_scaling.py (1 failure)
SystemExit during warning test setup:
- test_sourcefile_divergence_warning

---

## Failure Pattern Summary

**Top failure causes:**
1. **CLI test setup issues (17 failures):** Missing -hkl/-default_F requirement
2. **Gradient testing issues (10 failures):** PyTorch donated buffers incompatibility
3. **Detector type conversion (5 failures):** beam_center stored as float instead of tensor
4. **Debug variable scope (4 failures):** UnboundLocalError in simulator.run()
5. **Simulator API mismatch (3 failures):** detector_config kwarg not recognized
6. **Beam center offset (3 failures):** MOSFLM +0.5 pixel offset applied incorrectly
7. **NoneType detector (2 failures):** Simulator init requires detector
8. **Orthogonality tolerance (1 failure):** Numerical precision issue
9. **Zero intensity (1 failure):** Physics simulation issue

**Total validation:** 46 failures identified across 7 chunks ✓
