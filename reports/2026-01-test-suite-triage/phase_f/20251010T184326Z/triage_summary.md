# Test Suite Triage Summary - Phase F (2026 Refresh)
## Attempt #7 Classification - 49 Failures Across 17 Clusters

**Date:** 2025-10-10
**Timestamp:** 20251010T184326Z
**Phase E Artifacts:** `reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/`
**Previous Triage:** `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/` (50 failures)

## Executive Summary

This triage refresh covers the complete 692-test suite re-execution (Phase E Attempt #7) which achieved 100% coverage in 1860.74s. All 49 failures are classified as **implementation bugs** requiring remediation. **Net improvement: +1 passed, -1 failure vs Phase B/C baseline.**

**Key Metrics:**
- **Pass Rate:** 74.6% (516/692) — up from 74.4%
- **Failed:** 49 (7.1%) — down from 50
- **Skipped:** 126 (18.2% - mostly C-parity tests requiring `NB_RUN_PARALLEL=1`)
- **Runtime:** 1860.74s (virtually unchanged from 1864.76s in Phase B)

**Key Changes Since Phase C:**
- **C1 (CLI Defaults):** ✅ RESOLVED - `[CLI-DEFAULTS-001]` implementation complete (Attempt #6)
- All other clusters remain active with identical failure counts

## Classification Table

| Cluster ID | Category | Count | Classification | Severity | Owner | Fix Plan ID | Status | Change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | CLI Defaults | 0 | ✅ RESOLVED | - | ralph | [CLI-DEFAULTS-001] | done | -1 |
| C2 | Determinism - Mosaic RNG | 6 | Implementation Bug | High | ralph | [DETERMINISM-001] | in_progress | 0 |
| C3 | CUDA Graphs | 6 | Implementation Bug | Medium | ralph | [CUDA-GRAPHS-001] | in_planning | 0 |
| C4 | Grazing Incidence | 4 | Implementation Bug | High | ralph | [DETECTOR-GRAZING-001] | in_planning | 0 |
| C5 | Unit Conversion | 1 | Implementation Bug | Medium | ralph | [UNIT-CONV-001] | in_planning | 0 |
| C6 | Tricubic Vectorization | 2 | Implementation Bug | High | galph | [VECTOR-TRICUBIC-002] | in_progress | 0 |
| C7 | Source Weighting | 6 | Implementation Bug | High | ralph | [SOURCE-WEIGHT-002] | in_planning | 0 |
| C8 | Lattice Shape Models | 2 | Implementation Bug | High | ralph | [LATTICE-SHAPE-001] | in_planning | 0 |
| C9 | Dual Runner Tooling | 1 | Implementation Bug | High | ralph | [TOOLING-DUAL-RUNNER-001] | in_planning | 0 |
| C10 | CLI Flags (pix0/HKL) | 3 | Implementation Bug | High | ralph | [CLI-FLAGS-003] | in_progress | 0 |
| C11 | Debug Trace | 4 | Implementation Bug | High | ralph | [DEBUG-TRACE-001] | in_planning | 0 |
| C12 | Detector Config | 2 | Implementation Bug | High | ralph | [DETECTOR-CONFIG-001] | in_planning | 0 |
| C13 | Detector Conventions (DENZO) | 1 | Implementation Bug | Medium | ralph | [DENZO-CONVENTION-001] | in_planning | 0 |
| C14 | Detector Pivots | 2 | Implementation Bug | High | ralph | [PIVOT-MODE-001] | in_planning | 0 |
| C15 | dtype Support | 2 | Implementation Bug | High | ralph | [DTYPE-NEUTRAL-001] | in_progress | 0 |
| C16 | Legacy Test Suite | 5 | Implementation Bug | Low | ralph | [LEGACY-SUITE-001] | in_planning | 0 |
| C17 | Gradient Flow | 1 | Implementation Bug | High | ralph | [GRADIENT-FLOW-001] | in_planning | 0 |
| C18 | Triclinic C Parity | 1 | Implementation Bug | High | ralph | [TRICLINIC-PARITY-001] | in_planning | 0 |
| **TOTAL** | **17 Active Clusters** | **49** | **49 Bugs** | - | - | **1 done + 18 active** | **3 in_progress, 15 in_planning** | **-1** |

## Detailed Failure Analysis by Cluster

### C1: CLI Defaults (0 failures) ✅ RESOLVED
**Fix Plan:** `[CLI-DEFAULTS-001]` (done)
**Resolution:** Attempt #6 (2025-10-10) - Fixed HKL guard logic in `__main__.py` (lines 442-447, 1088-1098)

**Previous Failures (now passing):**
1. `tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` ✅

**Root Cause:** HKL data assignment logic incorrectly triggered even when no `-hkl` file provided, preventing `default_F` fallback.

**Validation:** Targeted test now passes (4.81s runtime); full suite confirms no regression.

---

### C2: Determinism - Mosaic/RNG (6 failures)
**Fix Plan:** `[DETERMINISM-001]` (in_progress)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py`

**Failures (AT-PARALLEL-013):**
1. `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_same_seed`
2. `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_different_seeds`
3. `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_consistency_across_runs`

**Failures (AT-PARALLEL-024):**
4. `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_pytorch_determinism`
5. `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_seed_independence`
6. `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_mosaic_rotation_umat_determinism`

**Root Cause:** **BLOCKING** - dtype neutrality violations in `Detector` (basis vectors remain float32 when float64 requested). Tests cannot reach seed-dependent code until `[DTYPE-NEUTRAL-001]` is resolved.

**Severity:** High - deterministic mode is a spec requirement for scientific reproducibility.

**Blocker:** `[DTYPE-NEUTRAL-001]` must complete Phase C remediation plan first.

---

### C3: CUDA Graphs (6 failures)
**Fix Plan:** `[CUDA-GRAPHS-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py`

**Failures:**
1. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution[cpu]`
2. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution[cuda]`
3. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cuda_multiple_runs`
4. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_gradient_flow_preserved`
5. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cpu_cuda_correlation[cpu]`
6. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cpu_cuda_correlation[cuda]`

**Root Cause:** CUDA graphs test suite incompatibility; likely torch.compile cache invalidation or dynamic shape handling.

**Severity:** Medium - performance optimization feature, not blocking core functionality.

---

### C4: Grazing Incidence (4 failures)
**Fix Plan:** `[DETECTOR-GRAZING-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_017.py`

**Failures:**
1. `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts`
2. `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_twotheta`
3. `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_combined_extreme_angles`
4. `tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_near_90_degree_incidence`

**Root Cause:** Detector pivot/obliquity math for grazing incidence (near-90° detector angles) per spec-a-core.md §4.6.

**Severity:** High - spec compliance for detector rotations.

**Dependencies:** Blocked on `[VECTOR-PARITY-001]` Tap 5 completion per fix_plan.md.

---

### C5: Unit Conversion (1 failure)
**Fix Plan:** `[UNIT-CONV-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`

**Failures:**
1. `tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`

**Root Cause:** Mixed-unit handling across mm/Å/m boundaries; likely ADR-01 hybrid unit system edge case.

**Severity:** Medium - correctness issue but narrow scope.

---

### C6: Tricubic Vectorization (2 failures)
**Fix Plan:** `[VECTOR-TRICUBIC-002]` (in_progress)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py`

**Failures:**
1. `tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar`
2. `tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire`

**Root Cause:** Vectorized tricubic interpolation gather index handling or OOB warning logic regression.

**Severity:** High - vectorization parity is a runtime guardrail per docs/development/pytorch_runtime_checklist.md.

**Owner:** galph (vectorization specialist)

---

### C7: Source Weighting (6 failures)
**Fix Plan:** `[SOURCE-WEIGHT-002]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py`

**Failures:**
1. `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_all_columns`
2. `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_missing_columns`
3. `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_default_position`
4. `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_multiple_sources_normalization`
5. `tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_weighted_sources_integration`
6. `tests/test_at_src_001_simple.py::test_sourcefile_parsing`

**Root Cause:** Reopened after `[SOURCE-WEIGHT-001]` marked complete; simulator path broken per fix_plan.md line 110 note.

**Severity:** High - spec-a-core.md §§3.4–3.5 source weighting requirement.

---

### C8: Lattice Shape Models (2 failures)
**Fix Plan:** `[LATTICE-SHAPE-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels`

**Failures:**
1. `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model`
2. `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_shape_model_comparison`

**Root Cause:** GAUSS/TOPHAT shape models (spec-a-core.md physics §8) likely not wired or incorrectly normalized.

**Severity:** High - spec compliance for lattice models.

---

### C9: Dual Runner Tooling (1 failure)
**Fix Plan:** `[TOOLING-DUAL-RUNNER-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration`

**Failures:**
1. `tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration`

**Root Cause:** Dual-runner harness (C vs PyTorch comparison) not wired; tooling requirement per spec-a-parallel.md §2.5.

**Severity:** High - testing infrastructure blocker.

---

### C10: CLI Flags (3 failures)
**Fix Plan:** `[CLI-FLAGS-003]` (in_progress)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py`

**Failures:**
1. `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]`
2. `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cuda]`
3. `tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip`

**Root Cause:** CLI parsing/detector wiring for `-pix0_vector_mm` and HKL Fdump roundtrip logic per fix_plan.md lines 326-350.

**Severity:** High - CLI completeness per spec-a-cli.md.

---

### C11: Debug Trace (4 failures)
**Fix Plan:** `[DEBUG-TRACE-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py`

**Failures:**
1. `tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag`
2. `tests/test_debug_trace.py::TestDebugTraceFeatures::test_trace_pixel_flag`
3. `tests/test_debug_trace.py::TestDebugTraceFeatures::test_combined_debug_flags`
4. `tests/test_debug_trace.py::TestDebugTraceFeatures::test_out_of_bounds_pixel`

**Root Cause:** `--printout` and `--trace_pixel` flags not implemented per spec-a-cli.md trace requirements.

**Severity:** High - debugging/validation tooling blocker.

---

### C12: Detector Config (2 failures)
**Fix Plan:** `[DETECTOR-CONFIG-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py`

**Failures:**
1. `tests/test_detector_config.py::TestDetectorInitialization::test_default_initialization`
2. `tests/test_detector_config.py::TestDetectorInitialization::test_custom_config_initialization`

**Root Cause:** Detector config dataclass + CLI mapping defaults diverging from spec-a-core.md §4.

**Severity:** High - baseline detector initialization correctness.

---

### C13: Detector Conventions (1 failure - DENZO)
**Fix Plan:** `[DENZO-CONVENTION-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping`

**Failures:**
1. `tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping`

**Root Cause:** DENZO convention (arch.md §7 line 223) beam-center mapping not implemented; may require ADR update.

**Severity:** Medium - convention completeness (DENZO less common than MOSFLM/XDS).

---

### C14: Detector Pivots (2 failures)
**Fix Plan:** `[PIVOT-MODE-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_pivots.py`

**Failures:**
1. `tests/test_detector_pivots.py::test_beam_pivot_keeps_beam_indices_and_alignment`
2. `tests/test_detector_pivots.py::test_sample_pivot_moves_beam_indices_with_twotheta`

**Root Cause:** Pivot mode behavior (BEAM vs SAMPLE per arch.md ADR-02) not matching spec; related to detector rotation logic.

**Severity:** High - fundamental detector geometry requirement.

---

### C15: dtype Support (2 failures)
**Fix Plan:** `[DTYPE-NEUTRAL-001]` (in_progress)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_006.py`

**Failures:**
1. `tests/test_perf_pytorch_006.py::test_dtype_support[dtype1]`
2. `tests/test_perf_pytorch_006.py::test_float32_float64_correlation`

**Root Cause:** dtype neutrality (float32/float64) regression; violates docs/development/pytorch_runtime_checklist.md device/dtype discipline. **Blocks [DETERMINISM-001].**

**Severity:** High - runtime guardrail AND blocker for determinism tests.

---

### C16: Legacy Test Suite (5 failures)
**Fix Plan:** `[LEGACY-SUITE-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness -k "sensitivity or performance or extreme or rotation_compatibility"`

**Failures:**
1. `tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params`
2. `tests/test_suite.py::TestTier1TranslationCorrectness::test_performance_simple_cubic`
3. `tests/test_suite.py::TestTier1TranslationCorrectness::test_performance_triclinic`
4. `tests/test_suite.py::TestTier1TranslationCorrectness::test_extreme_cell_parameters`
5. `tests/test_suite.py::TestTier1TranslationCorrectness::test_rotation_compatibility`

**Root Cause:** Older Tier 1 tests in `test_suite.py` not updated for recent architecture changes (Phase D lattice unit fix, etc.).

**Severity:** Low - legacy tests may be superseded by newer AT-PARALLEL suite; candidate for deprecation/rewrite.

---

### C17: Gradient Flow (1 failure)
**Fix Plan:** `[GRADIENT-FLOW-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation`

**Failures:**
1. `tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation`

**Root Cause:** End-to-end gradient flow broken; likely differentiability regression violating arch.md §15 / ADR-08.

**Severity:** High - gradient correctness is a fundamental PyTorch port requirement.

---

### C18: Triclinic C Parity (1 failure)
**Fix Plan:** `[TRICLINIC-PARITY-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`

**Failures:**
1. `tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`

**Root Cause:** AT-PARALLEL-026 parity threshold not met; likely misset rotation or triclinic cell tensor regression.

**Severity:** High - spec-a-parallel.md parity requirement.

---

## Blockers & Dependencies

1. **[DTYPE-NEUTRAL-001] Phase C completion** blocks:
   - C2 ([DETERMINISM-001]) - tests cannot reach seed logic until dtype issue resolved

2. **[VECTOR-PARITY-001] Tap 5 completion** blocks:
   - C4 ([DETECTOR-GRAZING-001])

## Remediation Priority Ladder (2026 Refresh)

### Priority 1 (Critical Path - unblock other work):
1. **[DTYPE-NEUTRAL-001]** (in_progress) - BLOCKER for [DETERMINISM-001]
2. **[DETERMINISM-001]** (blocked by P1.1) - reproducibility blocker
3. **[DEBUG-TRACE-001]** (in_planning) - debugging infrastructure

### Priority 2 (Spec Compliance - High Severity):
4. **[DETECTOR-GRAZING-001]** (blocked by [VECTOR-PARITY-001]) - spec §4.6
5. **[SOURCE-WEIGHT-002]** (in_planning) - regression fix, spec §§3.4-3.5
6. **[DETECTOR-CONFIG-001]** (in_planning) - spec §4 baseline
7. **[LATTICE-SHAPE-001]** (in_planning) - GAUSS/TOPHAT models, spec §8
8. **[GRADIENT-FLOW-001]** (in_planning) - differentiability regression
9. **[PIVOT-MODE-001]** (in_planning) - detector pivots, ADR-02
10. **[TRICLINIC-PARITY-001]** (in_planning) - AT-PARALLEL-026

### Priority 3 (Infrastructure/Tooling):
11. **[TOOLING-DUAL-RUNNER-001]** (in_planning)
12. **[CLI-FLAGS-003]** (in_progress) - `-pix0_vector_mm`, HKL roundtrip
13. **[VECTOR-TRICUBIC-002]** (in_progress) - vectorization parity
14. **[CUDA-GRAPHS-001]** (in_planning) - performance optimization

### Priority 4 (Low/Deferred):
15. **[UNIT-CONV-001]** (in_planning) - narrow scope
16. **[DENZO-CONVENTION-001]** (in_planning) - less-common convention
17. **[LEGACY-SUITE-001]** (in_planning) - candidate for deprecation

## Environment Metadata

- **Python:** 3.13.5
- **pytest:** 8.4.1
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6
- **Platform:** linux
- **Environment Variables:** `KMP_DUPLICATE_LIB_OK=TRUE`

## Artifacts Reference

- **Phase E Summary:** `reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/summary.md`
- **Failure List:** `reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/failures_raw.md`
- **JUnit XML:** `reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/artifacts/pytest_full.xml`
- **Full Log:** `reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/logs/pytest_full.log`

---

**Classification Complete:** All 49 failures classified as implementation bugs; C1 resolved. 17 active clusters remain.

**Status:** Phase F1 COMPLETE. Ready for F2 (cluster_deltas.md) and F3 (pending_actions.md).
