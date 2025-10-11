# Phase M0 Triage Summary

**Initiative:** TEST-SUITE-TRIAGE-001
**Phase:** M0 - Directive Compliance Baseline
**Timestamp:** 20251011T153931Z
**Date:** 2025-10-11

## Executive Summary

Full test suite rerun completed per 2026-01-20 directive. Captured 687 tests with 46 failures requiring immediate triage before MOSFLM remediation can proceed.

**Key Metrics:**
- **Collected:** 687 tests
- **Executed:** 616 tests (chunks 01-10)
- **Passed:** 504 (81.8%)
- **Failed:** 46 (7.5%)
- **Skipped:** 136 (22.1%)
- **Duration:** ~502s (~8.4 minutes)

**Comparison with Phase K Baseline (20251011T072940Z):**
- Passed: 512 → 504 (-8, -1.6%)
- Failed: 31 → 46 (+15, +48.4%)
- Skipped: 143 → 136 (-7, -4.9%)

**Regression Analysis:** Significant failure increase (+48.4%) requires immediate classification and remediation planning.

---

## Failure Classification

### Cluster C1: CLI Test Setup Issues (17 failures, Priority P1)

**Cluster ID:** [CLI-TEST-SETUP-001]
**Status:** NEW (not in Phase K)
**Root Cause:** Test fixtures missing required `-hkl` or `-default_F` parameters, causing SystemExit(1) during CLI arg parsing.

**Affected Tests:**
- `test_cli_flags.py`: 16 tests
  - TestPix0VectorAlias: 7 tests
  - TestNoiseSuppressionFlag: 4 tests
  - TestCLIIntegrationSanity: 4 tests
  - TestCLIPix0Override: 1 test
- `test_cli_scaling.py`: 1 test

**Specification Reference:** `specs/spec-a-cli.md` §3.1 (required inputs)

**Remediation:**
- Update test fixtures to include `-default_F 100` or `-hkl` parameter
- Estimated effort: 1-2 hours (simple fixture fix)
- Owner: Ralph next loop

**Reproduction Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py::TestPix0VectorAlias::test_pix0_meters_alias
```

---

### Cluster C2: Gradient Testing Infrastructure (10 failures, Priority P2)

**Cluster ID:** [GRADIENT-DONATED-BUFFERS-001]
**Status:** NEW (not in Phase K)
**Root Cause:** PyTorch AOT compilation with `donated_buffers` requires `create_graph=False`, incompatible with `gradcheck`'s gradient computation.

**Affected Tests:**
- `test_gradients.py`: 10 tests
  - 6 cell parameter gradcheck tests
  - 2 advanced gradient tests
  - 1 property-based gradient test
  - 1 gradient flow test (different error: all gradients zero)

**Error Message:**
```
RuntimeError: donated buffers requires create_graph=False
```

**Specification Reference:** `arch.md` §15 (Differentiability Guidelines)

**Remediation:**
- Disable torch.compile or use `torch._dynamo.disable()` wrapper for gradcheck tests
- Add `NANOBRAGG_DISABLE_COMPILE=1` environment guard to gradient tests
- Estimated effort: 2-3 hours
- Owner: Gradients specialist

**Reproduction Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py::TestCellParameterGradients::test_gradcheck_cell_a
```

---

### Cluster C3: Detector Type Conversion (5 failures, Priority P1)

**Cluster ID:** [DETECTOR-DTYPE-CONVERSION-001]
**Status:** NEW (not in Phase K)
**Root Cause:** `DetectorConfig.beam_center_s/f` stored as Python float instead of torch.Tensor, causing AttributeError when calling `.to(device)`.

**Affected Tests:**
- `test_suite.py`: 5 tests
  - test_sensitivity_to_cell_params
  - test_performance_simple_cubic
  - test_performance_triclinic
  - test_extreme_cell_parameters
  - test_rotation_compatibility

**Error Message:**
```
AttributeError: 'float' object has no attribute 'to'
```

**Specification Reference:** `arch.md` §ADR-08 (Differentiability Preservation), `CLAUDE.md` Core Rule #16 (Device & Dtype Neutrality)

**Remediation:**
- Ensure `beam_center_s/f` are always tensors in `DetectorConfig.__post_init__`
- Convert float inputs to tensors: `self.beam_center_s = torch.tensor(beam_center_s) if isinstance(beam_center_s, (int, float)) else beam_center_s`
- Estimated effort: 1 hour
- Owner: Ralph next loop

**Reproduction Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params
```

---

### Cluster C4: Debug Variable Scope (4 failures, Priority P2)

**Cluster ID:** [DEBUG-TRACE-SCOPE-001]
**Status:** NEW (not in Phase K)
**Root Cause:** `I_before_normalization_pre_polar` variable referenced in debug path before assignment when certain code branches skip its initialization.

**Affected Tests:**
- `test_debug_trace.py`: 4 tests
  - test_printout_flag
  - test_trace_pixel_flag
  - test_combined_debug_flags
  - test_out_of_bounds_pixel

**Error Message:**
```
UnboundLocalError: cannot access local variable 'I_before_normalization_pre_polar' where it is not associated with a value
```

**Remediation:**
- Initialize `I_before_normalization_pre_polar = None` before conditional branches
- Ensure debug printouts check `is not None` before accessing
- Estimated effort: 1 hour
- Owner: Ralph next loop

**Reproduction Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag
```

---

### Cluster C5: Simulator API Mismatch (3 failures, Priority P2)

**Cluster ID:** [SIMULATOR-API-KWARGS-001]
**Status:** NEW (not in Phase K)
**Root Cause:** Test code uses deprecated `detector_config=` kwarg; Simulator.__init__ expects positional `detector` argument.

**Affected Tests:**
- `test_perf_pytorch_005_cudagraphs.py`: 3 tests
  - test_basic_execution[cpu]
  - test_gradient_flow_preserved
  - test_cpu_cuda_correlation[cpu]

**Error Message:**
```
TypeError: Simulator.__init__() got an unexpected keyword argument 'detector_config'
```

**Remediation:**
- Update test fixtures to use `Simulator(crystal, detector, beam)` positional API
- Estimated effort: 30 minutes
- Owner: Ralph next loop

**Reproduction Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution
```

---

### Cluster C6: MOSFLM Beam Center Offset (3 failures, Priority P1)

**Cluster ID:** [DETECTOR-CONFIG-001] (existing from Phase K)
**Status:** ACTIVE
**Root Cause:** MOSFLM convention +0.5 pixel offset applied incorrectly, causing 0.5-pixel beam center mismatch.

**Affected Tests:**
- `test_at_parallel_002.py`: 2 tests
  - test_beam_center_scales_with_pixel_size
  - test_beam_center_parameter_consistency
- `test_at_parallel_003.py`: 1 test
  - test_detector_offset_preservation

**Error Message:**
```
AssertionError: Beam center S (pixels) mismatch (expected 128.0, got 128.5)
```

**Specification Reference:** `specs/spec-a-core.md` §4.2, `arch.md` §ADR-03, `docs/development/c_to_pytorch_config_map.md` Table 2

**Remediation:**
- Already identified in [DETECTOR-CONFIG-001] Phase C1-C3
- Awaiting MOSFLM offset fix implementation
- Owner: Blocked on current loop (Phase M0 directive)

**Reproduction Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size
```

---

### Cluster C7: NoneType Detector (2 failures, Priority P2)

**Cluster ID:** [SIMULATOR-DETECTOR-REQUIRED-001]
**Status:** NEW (not in Phase K)
**Root Cause:** Test code passes `detector=None` to Simulator; Simulator.run() requires non-None detector for pixel coordinate calculation.

**Affected Tests:**
- `test_at_str_003.py`: 2 tests
  - test_gauss_shape_model
  - test_shape_model_comparison

**Error Message:**
```
AttributeError: 'NoneType' object has no attribute 'get_pixel_coords'
```

**Remediation:**
- Update test fixtures to provide valid detector config
- Or add explicit error handling in Simulator.__init__ to reject None detector with clear message
- Estimated effort: 1 hour
- Owner: Ralph next loop

**Reproduction Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model
```

---

### Cluster C8: Detector Orthogonality Tolerance (1 failure, Priority P3)

**Cluster ID:** [DETECTOR-ORTHO-TOLERANCE-001]
**Status:** NEW (not in Phase K)
**Root Cause:** Detector basis vectors orthogonality check fails at 1e-10 tolerance with large rotations (got 1.49e-08).

**Affected Tests:**
- `test_at_parallel_017.py`: 1 test
  - test_large_detector_tilts

**Error Message:**
```
AssertionError: fdet and sdet not orthogonal (tolerance 1e-10, got 1.49e-08)
```

**Specification Reference:** `specs/spec-a-core.md` §4.1 (detector geometry)

**Remediation:**
- Relax orthogonality tolerance to 1e-7 for extreme rotation cases
- Or improve rotation matrix numerical stability
- Estimated effort: 2 hours (analysis + fix)
- Owner: Geometry specialist

**Reproduction Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts
```

---

### Cluster C9: Zero Intensity Output (1 failure, Priority P3)

**Cluster ID:** [PHYSICS-ZERO-INTENSITY-001]
**Status:** NEW (not in Phase K)
**Root Cause:** Simulation produces zero intensity for specific mixed-units configuration; likely unit conversion or geometric culling issue.

**Affected Tests:**
- `test_at_parallel_015.py`: 1 test
  - test_mixed_units_comprehensive

**Error Message:**
```
AssertionError: Zero maximum intensity
```

**Specification Reference:** `specs/spec-a-core.md` §5 (physics model)

**Remediation:**
- Debug with parallel trace comparison (C vs PyTorch)
- Check unit conversions in test configuration
- Estimated effort: 3-4 hours (investigation)
- Owner: Physics specialist

**Reproduction Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive
```

---

## Failure Summary Table

| Cluster | ID | Failures | Priority | Status | Effort | Owner |
|---------|----|---------:|----------|--------|--------|-------|
| C1 | CLI-TEST-SETUP-001 | 17 | P1 | NEW | 1-2h | Ralph |
| C2 | GRADIENT-DONATED-BUFFERS-001 | 10 | P2 | NEW | 2-3h | Specialist |
| C3 | DETECTOR-DTYPE-CONVERSION-001 | 5 | P1 | NEW | 1h | Ralph |
| C4 | DEBUG-TRACE-SCOPE-001 | 4 | P2 | NEW | 1h | Ralph |
| C5 | SIMULATOR-API-KWARGS-001 | 3 | P2 | NEW | 30min | Ralph |
| C6 | DETECTOR-CONFIG-001 | 3 | P1 | ACTIVE | TBD | Blocked |
| C7 | SIMULATOR-DETECTOR-REQUIRED-001 | 2 | P2 | NEW | 1h | Ralph |
| C8 | DETECTOR-ORTHO-TOLERANCE-001 | 1 | P3 | NEW | 2h | Specialist |
| C9 | PHYSICS-ZERO-INTENSITY-001 | 1 | P3 | NEW | 3-4h | Specialist |
| **TOTAL** | **9 clusters** | **46** | - | - | **~14-18h** | - |

---

## Priority Ladder

### Sprint 0 (Immediate - Ralph)
Quick fixes to clear low-hanging fruit (estimated 4-5 hours):
1. **C1: CLI-TEST-SETUP-001** (17 failures) - Add `-default_F` to test fixtures
2. **C3: DETECTOR-DTYPE-CONVERSION-001** (5 failures) - Tensorize beam_center fields
3. **C4: DEBUG-TRACE-SCOPE-001** (4 failures) - Initialize debug variables
4. **C5: SIMULATOR-API-KWARGS-001** (3 failures) - Update API calls
5. **C7: SIMULATOR-DETECTOR-REQUIRED-001** (2 failures) - Fix test fixtures

**Expected Impact:** Clear 31/46 failures (67.4%)

### Sprint 1 (Infrastructure)
Gradient testing infrastructure (estimated 2-3 hours):
1. **C2: GRADIENT-DONATED-BUFFERS-001** (10 failures) - Disable compile for gradcheck

**Expected Impact:** Clear additional 10/46 failures (21.7%)

### Sprint 2 (Blocked - MOSFLM)
MOSFLM beam center fix (blocked on directive):
1. **C6: DETECTOR-CONFIG-001** (3 failures) - Implement +0.5 pixel offset fix

**Expected Impact:** Clear additional 3/46 failures (6.5%)

### Sprint 3 (Investigation)
Deep investigation required (estimated 5-6 hours):
1. **C8: DETECTOR-ORTHO-TOLERANCE-001** (1 failure) - Numerical stability analysis
2. **C9: PHYSICS-ZERO-INTENSITY-001** (1 failure) - Parallel trace debugging

**Expected Impact:** Clear remaining 2/46 failures (4.3%)

---

## Recommendations

1. **Immediate Action (Sprint 0):** Execute quick fixes for C1, C3, C4, C5, C7 to clear 67% of failures
2. **Infrastructure Fix (Sprint 1):** Address gradient testing compilation issues
3. **Directive Compliance:** MOSFLM remediation (C6) remains blocked per 2026-01-20 directive until this triage completes
4. **Investigation Queue:** Schedule C8/C9 for specialist review after Sprint 0/1 completion

---

## Artifacts

- **Summary:** `summary.md`
- **Failures:** `failures_raw.md`
- **Commands:** `commands.txt`
- **Preflight:** `preflight/{collect_only.log, env.txt, pip_freeze.txt}`
- **Chunk Logs:** `chunks/chunk_NN/{pytest.log, pytest.xml}` (01-10)

---

## Next Steps

1. ✅ Phase M0a complete: Preflight checks captured
2. ✅ Phase M0b complete: All 10 chunks executed
3. ✅ Phase M0c complete: This triage summary
4. ⏳ Phase M0 closure: Update `docs/fix_plan.md` with Attempt #20 metadata
5. ⏳ Sprint 0 execution: Begin quick-fix remediation (C1, C3, C4, C5, C7)

---

**Generated:** 2025-10-11
**Triage Analyst:** Ralph (Loop #1 Phase M0)
**Review Status:** Ready for supervisor handoff
