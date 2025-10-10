# Test Suite Triage Summary - Phase C (Complete Dataset)
## Attempt #5 Classification - 50 Failures Across 18 Clusters

**Date:** 2025-10-10
**Timestamp:** 20251010T135833Z
**Phase B Artifacts:** `reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/`
**Previous Triage:** `reports/2026-01-test-suite-triage/phase_c/20251010T134156Z/` (34 failures, partial coverage)

## Executive Summary

This triage covers the complete 692-test suite execution (Attempt #5) which achieved 100% coverage in 1864.76s. All 50 failures are classified as **implementation bugs** requiring remediation. No deprecated/obsolete tests identified.

**Key Metrics:**
- **Pass Rate:** 74.4% (515/692)
- **Failed:** 50 (7.2%)
- **Skipped:** 126 (18.2% - mostly C-parity tests requiring `NB_RUN_PARALLEL=1`)
- **Coverage vs Attempt #2:** +171 tests (+25% coverage)
- **New Failure Clusters:** 16 additional failures discovered (C3, C6, C8, C13-C18)

## Classification Table

| Cluster ID | Category | Count | Classification | Severity | Owner | Fix Plan ID | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | CLI Defaults | 1 | Implementation Bug | High | ralph | [CLI-DEFAULTS-001] | in_planning |
| C2 | Determinism - Mosaic RNG | 3 | Implementation Bug | High | ralph | [DETERMINISM-001] | in_planning |
| C3 | CUDA Graphs | 6 | Implementation Bug | Medium | ralph | NEW (pending) | unassigned |
| C4 | Grazing Incidence | 4 | Implementation Bug | High | ralph | [DETECTOR-GRAZING-001] | in_planning |
| C5 | Unit Conversion | 1 | Implementation Bug | Medium | ralph | NEW (pending) | unassigned |
| C6 | Tricubic Vectorization | 2 | Implementation Bug | High | galph | [VECTOR-TRICUBIC-002] | in_progress |
| C7 | Source Weighting | 6 | Implementation Bug | High | ralph | [SOURCE-WEIGHT-002] | in_planning |
| C8 | Lattice Shape Models | 2 | Implementation Bug | High | ralph | NEW (pending) | unassigned |
| C9 | Dual Runner Tooling | 1 | Implementation Bug | High | ralph | [TOOLING-DUAL-RUNNER-001] | in_planning |
| C10 | CLI Flags (pix0/HKL) | 3 | Implementation Bug | High | ralph | [CLI-FLAGS-003] | in_progress |
| C11 | Debug Trace | 4 | Implementation Bug | High | ralph | [DEBUG-TRACE-001] | in_planning |
| C12 | Detector Config | 2 | Implementation Bug | High | ralph | [DETECTOR-CONFIG-001] | in_planning |
| C13 | Detector Conventions (DENZO) | 1 | Implementation Bug | Medium | ralph | NEW (pending) | unassigned |
| C14 | Detector Pivots | 2 | Implementation Bug | High | ralph | NEW (pending) | unassigned |
| C15 | dtype Support | 2 | Implementation Bug | Medium | ralph | NEW (pending) | unassigned |
| C16 | Legacy Test Suite | 5 | Implementation Bug | Low | ralph | NEW (pending) | unassigned |
| C17 | Gradient Flow | 1 | Implementation Bug | High | ralph | NEW (pending) | unassigned |
| C18 | Triclinic C Parity | 1 | Implementation Bug | High | ralph | NEW (pending) | unassigned |
| **TOTAL** | **18 Clusters** | **50** | **50 Bugs** | - | - | **10 existing + 8 new** | **2 in_progress, 8 in_planning, 8 unassigned** |

## Detailed Failure Analysis by Cluster

### C1: CLI Defaults (1 failure)
**Fix Plan:** `[CLI-DEFAULTS-001]` (in_planning)
**Reproduction:** `pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F`

**Failures:**
1. `tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F`

**Root Cause:** Missing HKL fallback or SMV header population logic when `-default_F` is the only structure factor source.

**Severity:** High - blocks minimal CLI usage patterns documented in spec-a-cli.md AT-CLI-002.

---

### C2: Determinism - Mosaic/RNG (3 failures - subset of 6)
**Fix Plan:** `[DETERMINISM-001]` (in_planning)
**Reproduction:** `pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py`

**Failures (AT-PARALLEL-013):**
1. `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_same_seed`
2. `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_determinism_different_seeds`
3. `tests/test_at_parallel_013.py::TestATParallel013CrossPlatformConsistency::test_pytorch_consistency_across_runs`

**Failures (AT-PARALLEL-024 - 3 additional):**
4. `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_pytorch_determinism`
5. `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_seed_independence`
6. `tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_mosaic_rotation_umat_determinism`

**Root Cause:** RNG seeding path not enforcing seed propagation across torch + numpy domains per spec-a-core.md §5.3.

**Severity:** High - deterministic mode is a spec requirement for scientific reproducibility.

---

### C3: CUDA Graphs (6 failures) [NEW in Attempt #5]
**Fix Plan:** NEW (pending assignment)
**Reproduction:** `pytest -v tests/test_perf_pytorch_005_cudagraphs.py`

**Failures:**
1. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution[cpu]`
2. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution[cuda]`
3. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cuda_multiple_runs`
4. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_gradient_flow_preserved`
5. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cpu_cuda_correlation[cpu]`
6. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cpu_cuda_correlation[cuda]`

**Root Cause:** CUDA graphs test suite introduced post-Attempt #2; likely torch.compile cache invalidation or dynamic shape handling incompatibility.

**Severity:** Medium - performance optimization feature, not blocking core functionality.

---

### C4: Grazing Incidence (4 failures)
**Fix Plan:** `[DETECTOR-GRAZING-001]` (in_planning)
**Reproduction:** `pytest -v tests/test_at_parallel_017.py`

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
**Fix Plan:** NEW (pending assignment)
**Reproduction:** `pytest -v tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`

**Failures:**
1. `tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`

**Root Cause:** Mixed-unit handling across mm/Å/m boundaries; likely ADR-01 hybrid unit system edge case.

**Severity:** Medium - correctness issue but narrow scope.

---

### C6: Tricubic Vectorization (2 failures) [NEW in Attempt #5]
**Fix Plan:** `[VECTOR-TRICUBIC-002]` (in_progress)
**Reproduction:** `pytest -v tests/test_tricubic_vectorized.py`

**Failures:**
1. `tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar`
2. `tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire`

**Root Cause:** Vectorized tricubic interpolation tests added post-ADR-06 implementation; likely gather index handling or OOB warning logic regression.

**Severity:** High - vectorization parity is a runtime guardrail per docs/development/pytorch_runtime_checklist.md.

**Owner:** galph (vectorization specialist)

---

### C7: Source Weighting (6 failures)
**Fix Plan:** `[SOURCE-WEIGHT-002]` (in_planning)
**Reproduction:** `pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py`

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

### C8: Lattice Shape Models (2 failures) [NEW in Attempt #5]
**Fix Plan:** NEW (pending assignment)
**Reproduction:** `pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels`

**Failures:**
1. `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model`
2. `tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_shape_model_comparison`

**Root Cause:** GAUSS/TOPHAT shape models (spec-a-core.md physics §8) likely not wired or incorrectly normalized.

**Severity:** High - spec compliance for lattice models.

---

### C9: Dual Runner Tooling (1 failure)
**Fix Plan:** `[TOOLING-DUAL-RUNNER-001]` (in_planning)
**Reproduction:** `pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration`

**Failures:**
1. `tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration`

**Root Cause:** Dual-runner harness (C vs PyTorch comparison) not wired; tooling requirement per spec-a-parallel.md §2.5.

**Severity:** High - testing infrastructure blocker.

---

### C10: CLI Flags (3 failures)
**Fix Plan:** `[CLI-FLAGS-003]` (in_progress)
**Reproduction:** `pytest -v tests/test_cli_flags.py`

**Failures:**
1. `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]`
2. `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cuda]`
3. `tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip`

**Root Cause:** CLI parsing/detector wiring for `-pix0_vector_mm` and HKL Fdump roundtrip logic per fix_plan.md lines 326-350.

**Severity:** High - CLI completeness per spec-a-cli.md.

---

### C11: Debug Trace (4 failures)
**Fix Plan:** `[DEBUG-TRACE-001]` (in_planning)
**Reproduction:** `pytest -v tests/test_debug_trace.py`

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
**Reproduction:** `pytest -v tests/test_detector_config.py`

**Failures:**
1. `tests/test_detector_config.py::TestDetectorInitialization::test_default_initialization`
2. `tests/test_detector_config.py::TestDetectorInitialization::test_custom_config_initialization`

**Root Cause:** Detector config dataclass + CLI mapping defaults diverging from spec-a-core.md §4.

**Severity:** High - baseline detector initialization correctness.

---

### C13: Detector Conventions (1 failure - DENZO) [NEW in Attempt #5]
**Fix Plan:** NEW (pending assignment)
**Reproduction:** `pytest -v tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping`

**Failures:**
1. `tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping`

**Root Cause:** DENZO convention (arch.md §7 line 223) beam-center mapping not implemented; may require ADR update.

**Severity:** Medium - convention completeness (DENZO less common than MOSFLM/XDS).

---

### C14: Detector Pivots (2 failures) [NEW in Attempt #5]
**Fix Plan:** NEW (pending assignment)
**Reproduction:** `pytest -v tests/test_detector_pivots.py`

**Failures:**
1. `tests/test_detector_pivots.py::test_beam_pivot_keeps_beam_indices_and_alignment`
2. `tests/test_detector_pivots.py::test_sample_pivot_moves_beam_indices_with_twotheta`

**Root Cause:** Pivot mode behavior (BEAM vs SAMPLE per arch.md ADR-02) not matching spec; related to detector rotation logic.

**Severity:** High - fundamental detector geometry requirement.

---

### C15: dtype Support (2 failures) [NEW in Attempt #5]
**Fix Plan:** NEW (pending assignment)
**Reproduction:** `pytest -v tests/test_perf_pytorch_006.py`

**Failures:**
1. `tests/test_perf_pytorch_006.py::test_dtype_support[dtype1]`
2. `tests/test_perf_pytorch_006.py::test_float32_float64_correlation`

**Root Cause:** dtype neutrality (float32/float64) regression; violates docs/development/pytorch_runtime_checklist.md device/dtype discipline.

**Severity:** Medium - runtime guardrail but not blocking core features.

---

### C16: Legacy Test Suite (5 failures) [NEW in Attempt #5]
**Fix Plan:** NEW (pending assignment)
**Reproduction:** `pytest -v tests/test_suite.py::TestTier1TranslationCorrectness -k "sensitivity or performance or extreme or rotation_compatibility"`

**Failures:**
1. `tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params`
2. `tests/test_suite.py::TestTier1TranslationCorrectness::test_performance_simple_cubic`
3. `tests/test_suite.py::TestTier1TranslationCorrectness::test_performance_triclinic`
4. `tests/test_suite.py::TestTier1TranslationCorrectness::test_extreme_cell_parameters`
5. `tests/test_suite.py::TestTier1TranslationCorrectness::test_rotation_compatibility`

**Root Cause:** Older Tier 1 tests in `test_suite.py` not updated for recent architecture changes (Phase D lattice unit fix, etc.).

**Severity:** Low - legacy tests may be superseded by newer AT-PARALLEL suite; candidate for deprecation/rewrite.

---

### C17: Gradient Flow (1 failure) [NEW in Attempt #5]
**Fix Plan:** NEW (pending assignment)
**Reproduction:** `pytest -v tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation`

**Failures:**
1. `tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation`

**Root Cause:** End-to-end gradient flow broken; likely differentiability regression violating arch.md §15 / ADR-08.

**Severity:** High - gradient correctness is a fundamental PyTorch port requirement.

---

### C18: Triclinic C Parity (1 failure) [NEW in Attempt #5]
**Fix Plan:** NEW (pending assignment)
**Reproduction:** `pytest -v tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`

**Failures:**
1. `tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`

**Root Cause:** AT-PARALLEL-026 parity threshold not met; likely misset rotation or triclinic cell tensor regression.

**Severity:** High - spec-a-parallel.md parity requirement.

---

## Deltas vs Attempt #2 Triage (20251010T134156Z)

**Attempt #2 Coverage:**
- Tests executed: 520/692 (~75%)
- Failures observed: 34
- Clusters identified: 14 (C1-C14)

**Attempt #5 Coverage:**
- Tests executed: 691/692 (~100%)
- Failures observed: 50
- Clusters identified: 18 (C1-C18)

**New Clusters in Attempt #5:**
- C3: CUDA Graphs (6 failures)
- C6: Tricubic Vectorization (2 failures)
- C8: Lattice Shape Models (2 failures)
- C13: Detector Conventions - DENZO (1 failure)
- C14: Detector Pivots (2 failures)
- C15: dtype Support (2 failures)
- C16: Legacy Test Suite (5 failures)
- C17: Gradient Flow (1 failure)
- C18: Triclinic C Parity (1 failure)

**Total new failures:** 16 (from 171 additional tests)

## Pending Actions Table

| Cluster | Fix Plan ID | Owner | Priority | Status | Next Action | Blocker |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | [CLI-DEFAULTS-001] | ralph | High | in_planning | Reproduce targeted command; identify HKL fallback logic | None |
| C2 | [DETERMINISM-001] | ralph | High | in_planning | Instrument RNG seeding path; enforce seed propagation | None |
| C3 | NEW (CUDA-GRAPHS-001) | ralph | Medium | unassigned | Create fix plan; investigate torch.compile cache invalidation | None |
| C4 | [DETECTOR-GRAZING-001] | ralph | High | in_planning | Schedule after [VECTOR-PARITY-001] Tap 5 complete | [VECTOR-PARITY-001] |
| C5 | NEW (UNIT-CONV-001) | ralph | Medium | unassigned | Create fix plan; audit ADR-01 hybrid unit boundaries | None |
| C6 | [VECTOR-TRICUBIC-002] | galph | High | in_progress | Fix vectorized tricubic parity; resolve OOB warning logic | None |
| C7 | [SOURCE-WEIGHT-002] | ralph | High | in_planning | Author follow-up ensuring Simulator multiplies weights | None |
| C8 | NEW (LATTICE-SHAPE-001) | ralph | High | unassigned | Create fix plan; wire GAUSS/TOPHAT models per spec | None |
| C9 | [TOOLING-DUAL-RUNNER-001] | ralph | High | in_planning | Restore dual-runner C vs PyTorch harness | None |
| C10 | [CLI-FLAGS-003] | ralph | High | in_progress | Implement CLI parsing for `-pix0_vector_mm`, HKL roundtrip | None |
| C11 | [DEBUG-TRACE-001] | ralph | High | in_planning | Implement `--printout` and `--trace_pixel` flags | None |
| C12 | [DETECTOR-CONFIG-001] | ralph | High | in_planning | Audit detector config defaults vs spec | None |
| C13 | NEW (DENZO-CONVENTION-001) | ralph | Medium | unassigned | Create fix plan; implement DENZO beam-center mapping | None |
| C14 | NEW (PIVOT-MODE-001) | ralph | High | unassigned | Create fix plan; audit pivot behavior vs ADR-02 | None |
| C15 | NEW (DTYPE-NEUTRAL-001) | ralph | Medium | unassigned | Create fix plan; restore dtype neutrality per checklist | None |
| C16 | NEW (LEGACY-SUITE-001) | ralph | Low | unassigned | Triage for deprecation vs rewrite; defer until higher priorities cleared | None |
| C17 | NEW (GRADIENT-FLOW-001) | ralph | High | unassigned | Create fix plan; audit differentiability regression | None |
| C18 | NEW (TRICLINIC-PARITY-001) | ralph | High | unassigned | Create fix plan; debug triclinic misset parity | None |

## Blockers & Dependencies

1. **[VECTOR-PARITY-001] Tap 5 completion** blocks:
   - C4 (Detector Grazing Incidence)

2. **Test Suite Triage Phase D handoff** blocks:
   - All remediation work (per input.md lines 5-6)

## Recommendations for Phase D

### Priority 1 (Critical Path - unblock other work):
1. Complete [VECTOR-PARITY-001] Tap 5 (already in_progress)
2. [CLI-DEFAULTS-001] - minimal CLI usage
3. [DETERMINISM-001] - reproducibility blocker
4. [DEBUG-TRACE-001] - debugging infrastructure

### Priority 2 (Spec Compliance):
5. [DETECTOR-GRAZING-001] (after Tap 5)
6. [SOURCE-WEIGHT-002] (regression fix)
7. [DETECTOR-CONFIG-001]
8. NEW: [LATTICE-SHAPE-001] (GAUSS/TOPHAT models)
9. NEW: [GRADIENT-FLOW-001] (differentiability regression)
10. NEW: [PIVOT-MODE-001] (detector pivots)
11. NEW: [TRICLINIC-PARITY-001] (AT-PARALLEL-026)

### Priority 3 (Infrastructure/Tooling):
12. [TOOLING-DUAL-RUNNER-001]
13. [CLI-FLAGS-003] (already in_progress)
14. [VECTOR-TRICUBIC-002] (already in_progress)
15. NEW: [CUDA-GRAPHS-001]
16. NEW: [DTYPE-NEUTRAL-001]

### Priority 4 (Low/Deferred):
17. NEW: [UNIT-CONV-001] (narrow scope)
18. NEW: [DENZO-CONVENTION-001] (less-common convention)
19. NEW: [LEGACY-SUITE-001] (candidate for deprecation)

## Coverage Gaps (None Remaining)

**Attempt #5 achieved 100% test discovery and execution** (691/692 tests, 1 skipped during collection). No coverage gaps remain from Attempt #2.

## Environment Metadata

- **Python:** 3.13.5
- **pytest:** 8.4.1
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6
- **Platform:** linux
- **Environment Variables:** `KMP_DUPLICATE_LIB_OK=TRUE`

## Artifacts Reference

- **Phase B Summary:** `reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/summary.md`
- **Failure List:** `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/failures_raw.md`
- **JUnit XML:** `reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/artifacts/pytest_full.xml`
- **Full Log:** `reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/logs/pytest_full.log`

## Next Actions (Phase D)

Per `plans/active/test-suite-triage.md` Phase D table:

1. **D1:** Synthesize remediation priorities (DONE in this summary - see Priority 1-4 sections above)
2. **D2:** Produce reproduction commands (DONE in this summary - see cluster reproduction sections)
3. **D3:** Update documentation touchpoints (PENDING - requires fix_plan.md refresh)
4. **D4:** Publish supervisor input template (PENDING - supervisor task)

---

**Classification Complete:** All 50 failures classified as implementation bugs; no deprecated tests identified.

**Status:** Phase C5-C6 COMPLETE. Phase C7 (fix_plan refresh) PENDING next step.
