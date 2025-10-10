# Test Suite Status

**Last Updated:** 2026-01-10
**Git Branch:** feature/spec-based-2
**Git Commit:** 21c42e73

## Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Tests Collected** | 692 | 100% |
| **Tests Completed** | 530 | 76.6% |
| **Passed** | 429 | 81.0% of completed |
| **Failed** | 35 | 6.6% of completed |
| **Skipped** | 65 | 12.3% of completed |
| **Expected Failures (XFAIL)** | 1 | 0.2% of completed |
| **Not Run (Gradient Tests)** | 162 | 23.4% |

**Test Run Duration:** 30+ minutes (interrupted during gradient tests)
**Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v --tb=short`

### Pass Rate
- **Overall:** 429/530 = 81.0% (of completed tests)
- **Target:** ≥95% for production readiness

### Status: ⚠️  **NEEDS ATTENTION**
- 35 test failures require investigation and fixes
- Gradient tests incomplete (expensive autograd.gradcheck tests)
- Multiple test modules affected (see breakdown below)

---

## Test Categories Breakdown

### ✅ Fully Passing Modules (Examples)
- `test_crystal_geometry.py`: All gradient and geometry tests passed
- `test_detector_basis_vectors.py`: All convention and rotation tests passed
- `test_divergence_culling.py`: All culling mode tests passed
- `test_at_parallel_001.py` through `test_at_parallel_004.py`: Beam center and pixel size tests passed
- `test_at_abs_001.py`: All absorption tests passed (CPU + CUDA)
- `test_at_bkg_001.py`: All background calculation tests passed
- `test_at_noise_001.py`: All Poisson noise regime tests passed

### ❌ Modules with Failures

#### Critical (Multiple Failures)
1. **`test_at_src_001.py` (6 failures)**
   - Sourcefile parsing and weighting issues
   - Affects multi-source simulations
   - Test nodes:
     - `test_sourcefile_with_all_columns`
     - `test_sourcefile_with_missing_columns`
     - `test_sourcefile_default_position`
     - `test_multiple_sources_normalization`
     - `test_weighted_sources_integration`
   - Related: `test_at_src_001_simple.py::test_sourcefile_parsing`

2. **`test_debug_trace.py` (4 failures)**
   - Debug/trace functionality issues
   - Test nodes:
     - `test_printout_flag`
     - `test_trace_pixel_flag`
     - `test_combined_debug_flags`
     - `test_out_of_bounds_pixel`

3. **`test_at_parallel_013.py` (3 failures)**
   - Cross-platform consistency issues
   - Determinism failures
   - Test nodes:
     - `test_pytorch_determinism_same_seed`
     - `test_pytorch_determinism_different_seeds`
     - `test_pytorch_consistency_across_runs`

4. **`test_at_parallel_017.py` (4 failures)**
   - Grazing incidence / extreme angle issues
   - Test nodes:
     - `test_large_detector_tilts`
     - `test_large_twotheta`
     - `test_combined_extreme_angles`
     - `test_near_90_degree_incidence`

5. **`test_at_parallel_024.py` (3 failures)**
   - Mosaic domain determinism issues
   - Test nodes:
     - `test_pytorch_determinism`
     - `test_seed_independence`
     - `test_mosaic_rotation_umat_determinism`

#### Moderate (1-2 Failures)
- `test_detector_config.py` (2): Detector initialization issues
- `test_detector_pivots.py` (2): Pivot mode beam/sample behavior
- `test_cli_flags.py` (3): pix0 override and HKL/fdump parity
- `test_at_str_003.py` (2): Gauss shape model issues
- `test_at_cli_002.py` (1): Minimal render with default_F
- `test_at_parallel_015.py` (1): Mixed units comprehensive test
- `test_at_parallel_026.py` (1): Triclinic absolute position vs C
- `test_at_tools_001.py` (1): Dual runner comparison script integration
- `test_detector_conventions.py` (1): DENZO beam center mapping
- `test_gradients.py` (1): Advanced gradient flow simulation

### ⏭️  Skipped Tests (65)

#### Reason: Requires C Binary (`NB_RUN_PARALLEL=1`)
- `test_at_parallel_005.py`: All beam center mapping tests (4)
- `test_at_parallel_007.py`: Peak position with rotations (3)
- `test_at_parallel_008.py`: Triclinic multi-peak pattern (3)
- `test_at_parallel_010.py`: Solid angle corrections (4)
- `test_at_parallel_011.py`: Polarization C/PyTorch equivalence (1)
- `test_at_parallel_013.py`: C/PyTorch equivalence (1)
- `test_at_parallel_016.py`: Extreme scale C comparison (1)
- `test_at_parallel_020.py`: Comprehensive integration (4)
- `test_at_parallel_021.py`: Crystal phi rotation (2)
- `test_at_parallel_022.py`: Detector rotation equivalence (3)
- `test_at_parallel_023.py`: Misset angles equivalence (11)
- `test_at_parallel_024.py`: C/PyTorch equivalence (1)
- `test_at_parallel_025.py`: Maximum intensity (3)
- `test_at_parallel_027.py`: Structure factor C equivalence (1)
- `test_at_parallel_029.py`: Subpixel sampling (2)
- `test_at_perf_001.py`: Performance parity (1)
- `test_at_perf_002.py`: Parallel execution (1)
- `test_at_perf_007.py`: Benchmark suite (1)
- `test_cli_scaling.py`: MOSFLM vectors, F_latt C parity, divergence (6)
- `test_cli_scaling_phi0.py`: Phi-zero C parity (2)

#### Reason: Other Conditions
- `test_cli_scaling.py::TestHKLDevice`: HKL tensor device tests (4, condition unclear)
- `test_configuration_consistency.py`: Configuration detection (4, infrastructure)
- `test_at_perf_006.py::test_tensor_shapes_include_all_dimensions` (1, profiling)
- `test_at_perf_008.py::test_skip_when_cuda_unavailable` (1, CUDA not available)

### ⏸️  Not Run (Gradient Tests, ~162 tests)
The test suite was interrupted during expensive gradient check tests after 30+ minutes of runtime. Remaining untested areas include:
- Advanced gradient tests in `test_gradients.py`
- Detector gradient tests
- Simulator end-to-end gradient tests
- Property-based gradient stability tests

---

## Failed Tests Detail

### By Category

#### Source File Handling (7 failures)
```
tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_all_columns
tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_missing_columns
tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_default_position
tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_multiple_sources_normalization
tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_weighted_sources_integration
tests/test_at_src_001_simple.py::test_sourcefile_parsing
```

#### Determinism / Reproducibility (6 failures)
```
tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_same_seed
tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_different_seeds
tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_consistency_across_runs
tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_pytorch_determinism
tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_seed_independence
tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_mosaic_rotation_umat_determinism
```

#### Extreme Angles / Edge Cases (4 failures)
```
tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts
tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_twotheta
tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_combined_extreme_angles
tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_near_90_degree_incidence
```

#### Debug / Trace Infrastructure (4 failures)
```
tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag
tests/test_debug_trace.py::TestDebugTraceFeatures::test_trace_pixel_flag
tests/test_debug_trace.py::TestDebugTraceFeatures::test_combined_debug_flags
tests/test_debug_trace.py::TestDebugTraceFeatures::test_out_of_bounds_pixel
```

#### CLI Flags / Configuration (4 failures)
```
tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]
tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cuda]
tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip
tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F
```

#### Detector Configuration (5 failures)
```
tests/test_detector_config.py::TestDetectorInitialization::test_default_initialization
tests/test_detector_config.py::TestDetectorInitialization::test_custom_config_initialization
tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping
tests/test_detector_pivots.py::test_beam_pivot_keeps_beam_indices_and_alignment
tests/test_detector_pivots.py::test_sample_pivot_moves_beam_indices_with_twotheta
```

#### Lattice Shape Models (2 failures)
```
tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model
tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_shape_model_comparison
```

#### Other (3 failures)
```
tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive
tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c
tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration
tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation
```

---

## Recommendations

### Priority 1 (Critical Path)
1. **Fix sourcefile handling** (`test_at_src_001.py`, 6 failures) - Blocks multi-source simulations
2. **Fix determinism issues** (`test_at_parallel_013.py`, `test_at_parallel_024.py`, 6 failures) - Essential for reproducibility
3. **Fix detector pivot modes** (`test_detector_pivots.py`, 2 failures) - Core geometry feature

### Priority 2 (High Impact)
4. **Debug/trace infrastructure** (`test_debug_trace.py`, 4 failures) - Developer tooling
5. **Extreme angle handling** (`test_at_parallel_017.py`, 4 failures) - Edge case robustness
6. **CLI flag handling** (4 failures) - User interface correctness

### Priority 3 (Moderate Impact)
7. **Detector config initialization** (2 failures)
8. **Lattice shape models** (2 failures)
9. **Gradient flow test** (1 failure in advanced tests)

### Future Work
- **Complete gradient test suite**: Re-run with extended timeout or targeted execution
- **C-parity tests**: Enable and verify all 65 skipped C↔PyTorch equivalence tests
- **Performance tests**: Execute skipped performance benchmarks

---

## Test Execution Notes

### Environment
```bash
KMP_DUPLICATE_LIB_OK=TRUE  # Required to prevent MKL conflicts
```

### Running Tests
```bash
# Full suite (warning: gradient tests are very slow)
KMP_DUPLICATE_LIB_OK=TRUE pytest -v

# Skip gradient tests
KMP_DUPLICATE_LIB_OK=TRUE pytest -v -m "not gradcheck"

# Specific module
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py

# With C-parity tests (requires C binary)
KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v
```

### Known Issues
- **Gradient tests timeout**: `torch.autograd.gradcheck` can take 1-5 minutes per test for complex functions
- **MKL library conflicts**: Must set `KMP_DUPLICATE_LIB_OK=TRUE`
- **CUDA availability**: Some tests skip gracefully if CUDA unavailable

---

## Historical Context
This status represents the state after:
- Attempt #36 (Tap 5.2 synthesis & hypothesis update)
- Phase E14 complete (HKL bounds parity validated)
- 692 total tests collected (1 skipped during collection = 691 active)

**Related Documentation:**
- [Testing Strategy](./development/testing_strategy.md)
- [Fix Plan](./fix_plan.md)
- [PyTorch Runtime Checklist](./development/pytorch_runtime_checklist.md)
