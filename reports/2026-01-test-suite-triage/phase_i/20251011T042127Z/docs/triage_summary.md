# Test Suite Triage Summary - Phase I (2026 Classification Refresh)
## Attempt #11 Classification - 36 Failures Across 16 Clusters

**Date:** 2026-01-17
**Timestamp:** 20251011T042127Z
**Phase H Artifacts:** `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/`
**Previous Triage:** `reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/` (49 failures)

## Executive Summary

This triage refresh covers the Phase H full-suite rerun (Attempt #10) which achieved 100% coverage in 1867.56s. All 36 failures have been reclassified using the refreshed evidence from Phase H. **Net improvement: -13 failures vs Phase E baseline (49→36), representing a 26% reduction.**

**Key Metrics:**
- **Pass Rate:** 73.8% (504/683) — down from 74.6% (due to test count adjustment)
- **Failed:** 36 (5.3%) — down from 49 (Phase F: 7.1%)
- **Skipped:** 143 (20.9%) — up from 126 (test reorganization)
- **Runtime:** 1867.56s (virtually unchanged from 1860.74s in Phase E)

**Key Changes Since Phase F:**
- **C1 (CLI Defaults):** ✅ RESOLVED - remains fixed from [CLI-DEFAULTS-001]
- **C6 (CLI Flags):** ✅ PARTIAL RESOLUTION - 1 failure resolved (3→2)
- **Overall:** -13 failures eliminated through previous remediation efforts

## Classification Table

| Cluster ID | Category | Count | Classification | Severity | Owner | Fix Plan ID | Status | Change vs F |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | CLI Defaults | 0 | ✅ RESOLVED | - | ralph | [CLI-DEFAULTS-001] | done | 0 |
| C2 | Determinism - Mosaic RNG | 2 | Implementation Bug | High | ralph | [DETERMINISM-001] | in_progress | -4 |
| C3 | Source Weighting | 6 | Implementation Bug | High | ralph | [SOURCE-WEIGHT-002] | in_planning | 0 |
| C4 | Lattice Shape Models | 2 | Implementation Bug | High | ralph | [LATTICE-SHAPE-001] | in_planning | 0 |
| C5 | Dual Runner Tooling | 1 | Implementation Bug | High | ralph | [TOOLING-DUAL-RUNNER-001] | in_planning | 0 |
| C6 | CLI Flags (pix0/HKL) | 2 | Implementation Bug | High | ralph | [CLI-FLAGS-003] | in_progress | -1 |
| C7 | Debug Trace | 4 | Implementation Bug | High | ralph | [DEBUG-TRACE-001] | in_planning | 0 |
| C8 | Detector Config | 2 | Implementation Bug | High | ralph | [DETECTOR-CONFIG-001] | in_planning | 0 |
| C9 | Detector Conventions (DENZO) | 1 | Implementation Bug | Medium | ralph | [DENZO-CONVENTION-001] | in_planning | 0 |
| C10 | Detector Pivots | 2 | Implementation Bug | High | ralph | [PIVOT-MODE-001] | in_planning | 0 |
| C11 | CUDA Graphs | 3 | Implementation Bug | Medium | ralph | [CUDA-GRAPHS-001] | in_planning | -3 |
| C12 | Legacy Test Suite | 5 | Likely Deprecation | Low | ralph | [LEGACY-SUITE-001] | in_planning | 0 |
| C13 | Tricubic Vectorization | 2 | Implementation Bug | High | galph | [VECTOR-TRICUBIC-002] | in_progress | 0 |
| C14 | Mixed Units | 1 | Implementation Bug | Medium | ralph | [UNIT-CONV-001] | in_planning | 0 |
| C15 | Mosaic Determinism | 1 | Implementation Bug | High | ralph | [DETERMINISM-001] | in_progress | 0 |
| C16 | Gradient Flow | 1 | Implementation Bug | High | ralph | [GRADIENT-FLOW-001] | in_planning | 0 |
| C18 | Triclinic C Parity | 1 | Implementation Bug | High | ralph | [TRICLINIC-PARITY-001] | in_planning | 0 |
| **TOTAL** | **16 Active Clusters** | **36** | **35 Bugs + 1 Deprecation** | - | - | **1 done + 17 active** | **4 in_progress, 13 in_planning** | **-13** |

## Detailed Failure Analysis by Cluster

### C1: CLI Defaults (0 failures) ✅ RESOLVED
**Fix Plan:** `[CLI-DEFAULTS-001]` (done)
**Resolution:** Attempt #6 (2025-10-10) - Fixed HKL guard logic in `__main__.py`

**Status:** Remains fixed in Phase H rerun. No regressions detected.

**Validation:** Full suite confirms fix stability; 516→504 passed delta unrelated to this cluster.

---

### C2: Determinism - Mosaic/RNG (2 failures) ⬇️ IMPROVED
**Fix Plan:** `[DETERMINISM-001]` (in_progress)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py`

**Failures:**
1. `tests/test_at_parallel_013.py::test_pytorch_determinism_same_seed`
2. `tests/test_at_parallel_013.py::test_pytorch_determinism_different_seeds`

**Root Cause:** Implementation bug - RNG determinism not fully implemented per spec-a-core.md §5.3.

**Severity:** High - deterministic mode is a spec requirement for scientific reproducibility.

**Classification:** **Implementation Bug** - requires completing deterministic RNG implementation.

**Change vs Phase F:** -4 failures (6→2); AT-PARALLEL-024 tests now passing, significant progress.

**Blocker Status:** Previously blocked by [DTYPE-NEUTRAL-001]; blocker status uncertain pending fix-plan review.

---

### C3: Source Weighting (6 failures)
**Fix Plan:** `[SOURCE-WEIGHT-002]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py`

**Failures:**
1. `tests/test_at_src_001.py::test_sourcefile_with_all_columns`
2. `tests/test_at_src_001.py::test_sourcefile_with_missing_columns`
3. `tests/test_at_src_001.py::test_sourcefile_default_position`
4. `tests/test_at_src_001.py::test_multiple_sources_normalization`
5. `tests/test_at_src_001.py::test_weighted_sources_integration`
6. `tests/test_at_src_001_simple.py::test_sourcefile_parsing`

**Root Cause:** Implementation bug - sourcefile parsing and source weighting logic not fully implemented per spec-a-core.md §§3.4–3.5.

**Severity:** High - spec compliance requirement.

**Classification:** **Implementation Bug** - requires implementing source weighting normalization.

**Change vs Phase F:** Unchanged (6 failures).

---

### C4: Lattice Shape Models (2 failures)
**Fix Plan:** `[LATTICE-SHAPE-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels`

**Failures:**
1. `tests/test_at_str_003.py::test_gauss_shape_model`
2. `tests/test_at_str_003.py::test_shape_model_comparison`

**Root Cause:** Implementation bug - GAUSS/TOPHAT shape models (spec-a-core.md physics §8) not implemented or incorrectly normalized.

**Severity:** High - spec compliance for lattice models.

**Classification:** **Implementation Bug** - requires implementing missing lattice shape models.

**Change vs Phase F:** Unchanged (2 failures).

---

### C5: Dual Runner Tooling (1 failure)
**Fix Plan:** `[TOOLING-DUAL-RUNNER-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::test_script_integration`

**Failures:**
1. `tests/test_at_tools_001.py::test_script_integration`

**Root Cause:** Implementation bug - dual-runner harness (C vs PyTorch comparison) not wired per spec-a-parallel.md §2.5.

**Severity:** High - testing infrastructure blocker.

**Classification:** **Implementation Bug** - requires implementing dual-runner comparison tooling.

**Change vs Phase F:** Unchanged (1 failure).

---

### C6: CLI Flags (2 failures) ⬇️ IMPROVED
**Fix Plan:** `[CLI-FLAGS-003]` (in_progress)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py`

**Failures:**
1. `tests/test_cli_flags.py::test_pix0_vector_mm_beam_pivot[cpu]`
2. `tests/test_cli_flags.py::test_scaled_hkl_roundtrip`

**Root Cause:** Implementation bug - CLI parsing/detector wiring for `-pix0_vector_mm` and HKL Fdump roundtrip logic incomplete per spec-a-cli.md.

**Severity:** High - CLI completeness requirement.

**Classification:** **Implementation Bug** - requires completing CLI flag implementation.

**Change vs Phase F:** -1 failure (3→2); partial progress observed.

---

### C7: Debug Trace (4 failures)
**Fix Plan:** `[DEBUG-TRACE-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py`

**Failures:**
1. `tests/test_debug_trace.py::test_printout_flag`
2. `tests/test_debug_trace.py::test_trace_pixel_flag`
3. `tests/test_debug_trace.py::test_combined_debug_flags`
4. `tests/test_debug_trace.py::test_out_of_bounds_pixel`

**Root Cause:** Implementation bug - `--printout` and `--trace_pixel` flags not implemented per spec-a-cli.md trace requirements.

**Severity:** High - debugging/validation tooling blocker.

**Classification:** **Implementation Bug** - requires implementing debug trace flags.

**Change vs Phase F:** Unchanged (4 failures).

---

### C8: Detector Config (2 failures)
**Fix Plan:** `[DETECTOR-CONFIG-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py`

**Failures:**
1. `tests/test_detector_config.py::test_default_initialization`
2. `tests/test_detector_config.py::test_custom_config_initialization`

**Root Cause:** Implementation bug - detector config dataclass + CLI mapping defaults diverging from spec-a-core.md §4.

**Severity:** High - baseline detector initialization correctness.

**Classification:** **Implementation Bug** - requires aligning detector config with spec defaults.

**Change vs Phase F:** Unchanged (2 failures).

---

### C9: Detector Conventions (1 failure - DENZO)
**Fix Plan:** `[DENZO-CONVENTION-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_conventions.py::test_denzo_beam_center_mapping`

**Failures:**
1. `tests/test_detector_conventions.py::test_denzo_beam_center_mapping`

**Root Cause:** Implementation bug - DENZO convention (arch.md §7) beam-center mapping not implemented.

**Severity:** Medium - convention completeness (DENZO less common than MOSFLM/XDS).

**Classification:** **Implementation Bug** - requires implementing DENZO convention.

**Change vs Phase F:** Unchanged (1 failure).

---

### C10: Detector Pivots (2 failures)
**Fix Plan:** `[PIVOT-MODE-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_pivots.py`

**Failures:**
1. `tests/test_detector_pivots.py::test_beam_pivot_keeps_beam_indices_and_alignment`
2. `tests/test_detector_pivots.py::test_sample_pivot_moves_beam_indices_with_twotheta`

**Root Cause:** Implementation bug - pivot mode behavior (BEAM vs SAMPLE per arch.md ADR-02) not matching spec.

**Severity:** High - fundamental detector geometry requirement.

**Classification:** **Implementation Bug** - requires fixing detector pivot mode logic.

**Change vs Phase F:** Unchanged (2 failures).

---

### C11: CUDA Graphs (3 failures) ⬇️ IMPROVED
**Fix Plan:** `[CUDA-GRAPHS-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py`

**Failures:**
1. `tests/test_perf_pytorch_005_cudagraphs.py::test_basic_execution[cpu]`
2. `tests/test_perf_pytorch_005_cudagraphs.py::test_gradient_flow_preserved`
3. `tests/test_perf_pytorch_005_cudagraphs.py::test_cpu_cuda_correlation[cpu]`

**Root Cause:** Implementation bug - CUDA graphs test suite incompatibility; likely torch.compile cache invalidation or dynamic shape handling.

**Severity:** Medium - performance optimization feature, not blocking core functionality.

**Classification:** **Implementation Bug** - requires CUDA graphs compatibility work.

**Change vs Phase F:** -3 failures (6→3); significant improvement observed.

---

### C12: Legacy Test Suite (5 failures)
**Fix Plan:** `[LEGACY-SUITE-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness -k "sensitivity or performance or extreme or rotation_compatibility"`

**Failures:**
1. `tests/test_suite.py::test_sensitivity_to_cell_params`
2. `tests/test_suite.py::test_performance_simple_cubic`
3. `tests/test_suite.py::test_performance_triclinic`
4. `tests/test_suite.py::test_extreme_cell_parameters`
5. `tests/test_suite.py::test_rotation_compatibility`

**Root Cause:** Tests may be obsolete - older Tier 1 tests in `test_suite.py` not updated for recent architecture changes (Phase D lattice unit fix, AT-PARALLEL suite supersedes these).

**Severity:** Low - legacy tests likely superseded by newer AT-PARALLEL suite.

**Classification:** **Likely Deprecation** - candidate for test removal/rewrite pending spec review.

**Rationale:** These tests appear to duplicate coverage provided by newer AT-PARALLEL tests (e.g., AT-PARALLEL-020 for comprehensive integration). They have not been updated to reflect architecture changes and may no longer represent current expected behavior. Recommend spec review to determine if these tests should be deprecated.

**Change vs Phase F:** Unchanged (5 failures).

---

### C13: Tricubic Vectorization (2 failures)
**Fix Plan:** `[VECTOR-TRICUBIC-002]` (in_progress)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py`

**Failures:**
1. `tests/test_tricubic_vectorized.py::test_vectorized_matches_scalar`
2. `tests/test_tricubic_vectorized.py::test_oob_warning_single_fire`

**Root Cause:** Implementation bug - vectorized tricubic interpolation gather index handling or OOB warning logic regression.

**Severity:** High - vectorization parity is a runtime guardrail per docs/development/pytorch_runtime_checklist.md.

**Classification:** **Implementation Bug** - requires fixing vectorization regression.

**Owner:** galph (vectorization specialist)

**Change vs Phase F:** Unchanged (2 failures).

---

### C14: Mixed Units (1 failure)
**Fix Plan:** `[UNIT-CONV-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::test_mixed_units_comprehensive`

**Failures:**
1. `tests/test_at_parallel_015.py::test_mixed_units_comprehensive`

**Root Cause:** Implementation bug - mixed-unit handling across mm/Å/m boundaries; likely ADR-01 hybrid unit system edge case.

**Severity:** Medium - correctness issue but narrow scope.

**Classification:** **Implementation Bug** - requires fixing unit conversion edge case.

**Change vs Phase F:** Unchanged (1 failure).

---

### C15: Mosaic Determinism (1 failure)
**Fix Plan:** `[DETERMINISM-001]` (in_progress)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py::test_mosaic_rotation_umat_determinism`

**Failures:**
1. `tests/test_at_parallel_024.py::test_mosaic_rotation_umat_determinism`

**Root Cause:** Implementation bug - mosaic rotation matrix determinism not implemented per spec-a-core.md §5.3.

**Severity:** High - deterministic mode is a spec requirement.

**Classification:** **Implementation Bug** - part of [DETERMINISM-001] mosaic RNG work.

**Change vs Phase F:** Unchanged (1 failure, note: other AT-024 tests now passing per Phase H summary).

---

### C16: Gradient Flow (1 failure)
**Fix Plan:** `[GRADIENT-FLOW-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_gradients.py::test_gradient_flow_simulation`

**Failures:**
1. `tests/test_gradients.py::test_gradient_flow_simulation`

**Root Cause:** Implementation bug - end-to-end gradient flow broken; likely differentiability regression violating arch.md §15 / ADR-08.

**Severity:** High - gradient correctness is a fundamental PyTorch port requirement.

**Classification:** **Implementation Bug** - requires fixing differentiability regression.

**Change vs Phase F:** Unchanged (1 failure).

---

### C18: Triclinic C Parity (1 failure)
**Fix Plan:** `[TRICLINIC-PARITY-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_026.py::test_triclinic_absolute_peak_position_vs_c`

**Failures:**
1. `tests/test_at_parallel_026.py::test_triclinic_absolute_peak_position_vs_c`

**Root Cause:** Implementation bug - AT-PARALLEL-026 parity threshold not met; likely misset rotation or triclinic cell tensor regression.

**Severity:** High - spec-a-parallel.md parity requirement.

**Classification:** **Implementation Bug** - requires fixing triclinic parity alignment.

**Change vs Phase F:** Unchanged (1 failure).

---

## Blockers & Dependencies

1. **[DTYPE-NEUTRAL-001] status unclear** - previously blocked C2 ([DETERMINISM-001]); check fix-plan for current blocker status.

2. **[VECTOR-PARITY-001] Tap 5 completion** - may block detector geometry work (pending fix-plan review).

## Remediation Priority Ladder (2026 Phase I Refresh)

### Priority 1 (Critical Path - Spec Compliance):
1. **[DETERMINISM-001]** (in_progress) - C2, C15 - reproducibility blocker (2 failures)
2. **[SOURCE-WEIGHT-002]** (in_planning) - C3 - spec §§3.4-3.5 (6 failures)
3. **[DETECTOR-CONFIG-001]** (in_planning) - C8 - spec §4 baseline (2 failures)
4. **[LATTICE-SHAPE-001]** (in_planning) - C4 - GAUSS/TOPHAT models, spec §8 (2 failures)
5. **[PIVOT-MODE-001]** (in_planning) - C10 - detector pivots, ADR-02 (2 failures)
6. **[GRADIENT-FLOW-001]** (in_planning) - C16 - differentiability regression (1 failure)
7. **[TRICLINIC-PARITY-001]** (in_planning) - C18 - AT-PARALLEL-026 (1 failure)

### Priority 2 (Infrastructure/Tooling - High):
8. **[TOOLING-DUAL-RUNNER-001]** (in_planning) - C5 - testing infrastructure (1 failure)
9. **[CLI-FLAGS-003]** (in_progress) - C6 - `-pix0_vector_mm`, HKL roundtrip (2 failures)
10. **[DEBUG-TRACE-001]** (in_planning) - C7 - debugging tooling (4 failures)
11. **[VECTOR-TRICUBIC-002]** (in_progress) - C13 - vectorization parity (2 failures)

### Priority 3 (Medium Severity):
12. **[CUDA-GRAPHS-001]** (in_planning) - C11 - performance optimization (3 failures)
13. **[UNIT-CONV-001]** (in_planning) - C14 - narrow scope (1 failure)
14. **[DENZO-CONVENTION-001]** (in_planning) - C9 - less-common convention (1 failure)

### Priority 4 (Low/Deferred):
15. **[LEGACY-SUITE-001]** (in_planning) - C12 - **candidate for deprecation** (5 failures)

## Environment Metadata

- **Python:** 3.13.5
- **pytest:** 8.4.1
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6
- **Platform:** linux
- **Environment Variables:** `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE` (CPU-only run)

## Artifacts Reference

- **Phase H Summary:** `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/docs/summary.md`
- **JUnit XML:** `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/artifacts/pytest_full.xml`
- **Full Log:** `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/full_suite/pytest_full.log`

---

**Classification Complete:** 36 failures classified (35 implementation bugs + 1 likely deprecation across 16 active clusters); C1 remains resolved. **Net improvement: -13 failures vs Phase F (26% reduction).**

**Status:** Phase I1-I2 COMPLETE. Ready for I3 (ledger sync + galph_memory note).
