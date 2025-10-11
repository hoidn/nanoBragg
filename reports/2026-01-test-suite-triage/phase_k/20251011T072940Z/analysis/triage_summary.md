# Test Suite Triage Summary - Phase K (Final Classification)
## Attempt #15 Classification - 31 Failures Across 14 Clusters

**Date:** 2025-10-11
**Timestamp:** 20251011T072940Z
**Phase K Artifacts:** `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/`
**Previous Triage:** `reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/` (36 failures)

## Executive Summary

This triage refresh covers the Phase K full-suite rerun (Attempt #15) which achieved 100% coverage in 1841.28s. All 31 failures have been reclassified using the refreshed evidence from Phase K. **Net improvement: -5 failures vs Phase I baseline (36→31), representing a 13.9% reduction.**

**Key Metrics:**
- **Pass Rate:** 74.5% (512/687) — up from 73.8% in Phase I
- **Failed:** 31 (4.5%) — down from 36 (Phase I: 5.3%)
- **Skipped:** 143 (20.8%) — unchanged
- **Runtime:** 1841.28s (30 min 41 s) — slightly faster than Phase I (1867.56s)

**Key Changes Since Phase I:**
- **C2/C15 (Determinism):** ✅ RESOLVED - 3 failures eliminated (2+1)
- **C3 (Source Weighting):** ⬇️ IMPROVED - 2 failures resolved (6→4)
- **Overall:** -5 failures eliminated through continued remediation efforts

## Classification Table

| Cluster ID | Category | Count | Classification | Severity | Owner | Fix Plan ID | Status | Change vs I |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | CLI Defaults | 0 | ✅ RESOLVED | - | ralph | [CLI-DEFAULTS-001] | done | 0 |
| C2 | Determinism - Mosaic RNG | 0 | ✅ RESOLVED | - | ralph | [DETERMINISM-001] | done | -2 |
| C3 | Source Weighting | 4 | Implementation Bug | High | ralph | [SOURCE-WEIGHT-002] | paused | -2 |
| C4 | Lattice Shape Models | 2 | Implementation Bug | High | ralph | [LATTICE-SHAPE-001] | in_planning | 0 |
| C5 | Dual Runner Tooling | 1 | Implementation Bug | High | ralph | [TOOLING-DUAL-RUNNER-001] | in_planning | 0 |
| C6 | CLI Flags (pix0/HKL) | 2 | Implementation Bug | High | ralph | [CLI-FLAGS-003] | in_progress | 0 |
| C7 | Debug Trace | 4 | Implementation Bug | High | ralph | [DEBUG-TRACE-001] | in_planning | 0 |
| C8 | Detector Config | 2 | Implementation Bug | High | ralph | [DETECTOR-CONFIG-001] | in_planning | 0 |
| C9 | Detector Conventions (DENZO) | 1 | Implementation Bug | Medium | ralph | [DENZO-CONVENTION-001] | in_planning | 0 |
| C10 | Detector Pivots | 2 | Implementation Bug | High | ralph | [PIVOT-MODE-001] | in_planning | 0 |
| C11 | CUDA Graphs | 3 | Implementation Bug | Medium | ralph | [CUDA-GRAPHS-001] | in_planning | 0 |
| C12 | Legacy Test Suite | 5 | Likely Deprecation | Low | ralph | [LEGACY-SUITE-001] | in_planning | 0 |
| C13 | Tricubic Vectorization | 2 | Implementation Bug | High | galph | [VECTOR-TRICUBIC-002] | in_progress | 0 |
| C14 | Mixed Units | 1 | Implementation Bug | Medium | ralph | [UNIT-CONV-001] | in_planning | 0 |
| C15 | Mosaic Determinism | 0 | ✅ RESOLVED | - | ralph | [DETERMINISM-001] | done | -1 |
| C16 | Gradient Flow | 1 | Implementation Bug | High | ralph | [GRADIENT-FLOW-001] | in_planning | 0 |
| C18 | Triclinic C Parity | 1 | Implementation Bug | High | ralph | [TRICLINIC-PARITY-001] | in_planning | 0 |
| **TOTAL** | **14 Active Clusters** | **31** | **30 Bugs + 1 Deprecation** | - | - | **3 done + 14 active** | **3 in_progress, 11 in_planning** | **-5** |

## Detailed Failure Analysis by Cluster

### C1: CLI Defaults (0 failures) ✅ RESOLVED
**Fix Plan:** `[CLI-DEFAULTS-001]` (done)
**Resolution:** Attempt #6 (2025-10-10) - Fixed HKL guard logic in `__main__.py`

**Status:** Remains fixed in Phase K rerun. No regressions detected.

**Validation:** Full suite confirms fix stability across Phase H→I→K.

---

### C2: Determinism - Mosaic/RNG (0 failures) ✅ RESOLVED (NEW)
**Fix Plan:** `[DETERMINISM-001]` (done)
**Reproduction (historical):** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py`

**Historical Failures (Phase I):**
1. `tests/test_at_parallel_013.py::test_pytorch_determinism_same_seed`
2. `tests/test_at_parallel_013.py::test_pytorch_determinism_different_seeds`

**Root Cause:** RNG determinism not fully implemented per spec-a-core.md §5.3 (resolved in Attempt #10).

**Resolution:** Attempt #10 (2025-10-11) implemented:
- TorchDynamo guards (CUDA_VISIBLE_DEVICES='', TORCHDYNAMO_DISABLE=1) at module level
- Dtype propagation in `mosaic_rotation_umat()` to respect caller's dtype
- Documentation updates in arch.md ADR-05 and testing_strategy.md §2.7

**Status:** ✅ **FULLY RESOLVED** - All determinism tests passing in Phase K rerun.

**Validation:** Phase K confirms 5/5 AT-PARALLEL-013 tests passing with bitwise equality.

**Artifacts:**
- `reports/determinism-callchain/phase_e/20251011T060454Z/validation/`
- `docs/fix_plan.md:99-137` (complete remediation history)

**Change vs Phase I:** -2 failures (2→0); cluster fully resolved.

---

### C3: Source Weighting (4 failures) ⬇️ IMPROVED
**Fix Plan:** `[SOURCE-WEIGHT-002]` (paused — awaiting Phase K triage refresh)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py`

**Failures:**
1. `tests/test_at_src_001.py::test_sourcefile_with_all_columns`
2. `tests/test_at_src_001.py::test_sourcefile_default_position`
3. `tests/test_at_src_001.py::test_multiple_sources_normalization`
4. `tests/test_at_src_001_simple.py::test_sourcefile_parsing`

**Root Cause:** Implementation bug - sourcefile parsing and source weighting logic not fully implemented per spec-a-core.md §§3.4–3.5.

**Severity:** High - spec compliance requirement.

**Classification:** **Implementation Bug** - requires implementing source weighting normalization.

**Change vs Phase I:** ⬇️ -2 failures (6→4); **significant progress** observed.

**Status:** Paused per input.md directive - Phase B design complete (Option A semantics approved), awaiting Phase K triage confirmation before Phase C implementation.

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

**Change vs Phase I:** Unchanged (2 failures).

---

### C5: Dual Runner Tooling (1 failure)
**Fix Plan:** `[TOOLING-DUAL-RUNNER-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::test_script_integration`

**Failures:**
1. `tests/test_at_tools_001.py::test_script_integration`

**Root Cause:** Implementation bug - dual-runner harness (C vs PyTorch comparison) not wired per spec-a-parallel.md §2.5.

**Severity:** High - testing infrastructure blocker.

**Classification:** **Implementation Bug** - requires implementing dual-runner comparison tooling.

**Change vs Phase I:** Unchanged (1 failure).

---

### C6: CLI Flags (2 failures)
**Fix Plan:** `[CLI-FLAGS-003]` (in_progress)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py`

**Failures:**
1. `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]`
2. `tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip`

**Root Cause:** Implementation bug - CLI parsing/detector wiring for `-pix0_vector_mm` and HKL Fdump roundtrip logic incomplete per spec-a-cli.md.

**Severity:** High - CLI completeness requirement.

**Classification:** **Implementation Bug** - requires completing CLI flag implementation.

**Change vs Phase I:** Unchanged (2 failures).

---

### C7: Debug Trace (4 failures)
**Fix Plan:** `[DEBUG-TRACE-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py`

**Failures:**
1. `tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag`
2. `tests/test_debug_trace.py::TestDebugTraceFeatures::test_trace_pixel_flag`
3. `tests/test_debug_trace.py::TestDebugTraceFeatures::test_combined_debug_flags`
4. `tests/test_debug_trace.py::TestDebugTraceFeatures::test_out_of_bounds_pixel`

**Root Cause:** Implementation bug - `--printout` and `--trace_pixel` flags not implemented per spec-a-cli.md trace requirements.

**Severity:** High - debugging/validation tooling blocker.

**Classification:** **Implementation Bug** - requires implementing debug trace flags.

**Change vs Phase I:** Unchanged (4 failures).

---

### C8: Detector Config (2 failures)
**Fix Plan:** `[DETECTOR-CONFIG-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py`

**Failures:**
1. `tests/test_detector_config.py::TestDetectorInitialization::test_default_initialization`
2. `tests/test_detector_config.py::TestDetectorInitialization::test_custom_config_initialization`

**Root Cause:** Implementation bug - detector config dataclass + CLI mapping defaults diverging from spec-a-core.md §4.

**Severity:** High - baseline detector initialization correctness.

**Classification:** **Implementation Bug** - requires aligning detector config with spec defaults.

**Change vs Phase I:** Unchanged (2 failures).

---

### C9: Detector Conventions (1 failure - DENZO)
**Fix Plan:** `[DENZO-CONVENTION-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_conventions.py::test_denzo_beam_center_mapping`

**Failures:**
1. `tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping`

**Root Cause:** Implementation bug - DENZO convention (arch.md §7) beam-center mapping not implemented.

**Severity:** Medium - convention completeness (DENZO less common than MOSFLM/XDS).

**Classification:** **Implementation Bug** - requires implementing DENZO convention.

**Change vs Phase I:** Unchanged (1 failure).

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

**Change vs Phase I:** Unchanged (2 failures).

---

### C11: CUDA Graphs (3 failures)
**Fix Plan:** `[CUDA-GRAPHS-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py`

**Failures:**
1. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution[cpu]`
2. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_gradient_flow_preserved`
3. `tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cpu_cuda_correlation[cpu]`

**Root Cause:** Implementation bug - CUDA graphs test suite incompatibility; likely torch.compile cache invalidation or dynamic shape handling.

**Severity:** Medium - performance optimization feature, not blocking core functionality.

**Classification:** **Implementation Bug** - requires CUDA graphs compatibility work.

**Change vs Phase I:** Unchanged (3 failures).

---

### C12: Legacy Test Suite (5 failures)
**Fix Plan:** `[LEGACY-SUITE-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness -k "sensitivity or performance or extreme or rotation_compatibility"`

**Failures:**
1. `tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params`
2. `tests/test_suite.py::TestTier1TranslationCorrectness::test_performance_simple_cubic`
3. `tests/test_suite.py::TestTier1TranslationCorrectness::test_performance_triclinic`
4. `tests/test_suite.py::TestTier1TranslationCorrectness::test_extreme_cell_parameters`
5. `tests/test_suite.py::TestTier1TranslationCorrectness::test_rotation_compatibility`

**Root Cause:** Tests may be obsolete - older Tier 1 tests in `test_suite.py` not updated for recent architecture changes (Phase D lattice unit fix, AT-PARALLEL suite supersedes these).

**Severity:** Low - legacy tests likely superseded by newer AT-PARALLEL suite.

**Classification:** **Likely Deprecation** - candidate for test removal/rewrite pending spec review.

**Rationale:** These tests appear to duplicate coverage provided by newer AT-PARALLEL tests (e.g., AT-PARALLEL-020 for comprehensive integration). They have not been updated to reflect architecture changes and may no longer represent current expected behavior. Recommend spec review to determine if these tests should be deprecated.

**Change vs Phase I:** Unchanged (5 failures).

---

### C13: Tricubic Vectorization (2 failures)
**Fix Plan:** `[VECTOR-TRICUBIC-002]` (in_progress)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py`

**Failures:**
1. `tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar`
2. `tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire`

**Root Cause:** Implementation bug - vectorized tricubic interpolation gather index handling or OOB warning logic regression.

**Severity:** High - vectorization parity is a runtime guardrail per docs/development/pytorch_runtime_checklist.md.

**Classification:** **Implementation Bug** - requires fixing vectorization regression.

**Owner:** galph (vectorization specialist)

**Change vs Phase I:** Unchanged (2 failures).

---

### C14: Mixed Units (1 failure)
**Fix Plan:** `[UNIT-CONV-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::test_mixed_units_comprehensive`

**Failures:**
1. `tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`

**Root Cause:** Implementation bug - mixed-unit handling across mm/Å/m boundaries; likely ADR-01 hybrid unit system edge case.

**Severity:** Medium - correctness issue but narrow scope.

**Classification:** **Implementation Bug** - requires fixing unit conversion edge case.

**Change vs Phase I:** Unchanged (1 failure).

---

### C15: Mosaic Determinism (0 failures) ✅ RESOLVED (NEW)
**Fix Plan:** `[DETERMINISM-001]` (done)
**Reproduction (historical):** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py::test_mosaic_rotation_umat_determinism`

**Historical Failures (Phase I):**
1. `tests/test_at_parallel_024.py::test_mosaic_rotation_umat_determinism`

**Root Cause:** Mosaic rotation matrix determinism not implemented per spec-a-core.md §5.3 (resolved in Attempt #10).

**Resolution:** Part of [DETERMINISM-001] Attempt #10 - dtype propagation fix in `mosaic_rotation_umat()` resolved this test alongside C2 failures.

**Status:** ✅ **FULLY RESOLVED** - Test passing in Phase K rerun.

**Validation:** Phase K confirms 5/5 AT-PARALLEL-024 tests passing including mosaic determinism check.

**Change vs Phase I:** -1 failure (1→0); cluster fully resolved.

---

### C16: Gradient Flow (1 failure)
**Fix Plan:** `[GRADIENT-FLOW-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_gradients.py::test_gradient_flow_simulation`

**Failures:**
1. `tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation`

**Root Cause:** Implementation bug - end-to-end gradient flow broken; likely differentiability regression violating arch.md §15 / ADR-08.

**Severity:** High - gradient correctness is a fundamental PyTorch port requirement.

**Classification:** **Implementation Bug** - requires fixing differentiability regression.

**Change vs Phase I:** Unchanged (1 failure).

---

### C18: Triclinic C Parity (1 failure)
**Fix Plan:** `[TRICLINIC-PARITY-001]` (in_planning)
**Reproduction:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_026.py::test_triclinic_absolute_peak_position_vs_c`

**Failures:**
1. `tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`

**Root Cause:** Implementation bug - AT-PARALLEL-026 parity threshold not met; likely misset rotation or triclinic cell tensor regression.

**Severity:** High - spec-a-parallel.md parity requirement.

**Classification:** **Implementation Bug** - requires fixing triclinic parity alignment.

**Change vs Phase I:** Unchanged (1 failure).

---

## Blockers & Dependencies

1. **[DETERMINISM-001] ✅ COMPLETE** - C2 and C15 fully resolved; no remaining blockers.

2. **[SOURCE-WEIGHT-002] paused** - Awaiting Phase K triage confirmation before Phase C implementation.

3. **[VECTOR-PARITY-001] Tap 5 completion** - May block detector geometry work (pending fix-plan review).

## Remediation Priority Ladder (2025-10-11 Phase K Refresh)

### Priority 1 (Critical Path - Spec Compliance):
1. **[SOURCE-WEIGHT-002]** (paused → resume post-K2/K3) - C3 - spec §§3.4-3.5 (4 failures, -2 vs I)
2. **[DETECTOR-CONFIG-001]** (in_planning) - C8 - spec §4 baseline (2 failures)
3. **[LATTICE-SHAPE-001]** (in_planning) - C4 - GAUSS/TOPHAT models, spec §8 (2 failures)
4. **[PIVOT-MODE-001]** (in_planning) - C10 - detector pivots, ADR-02 (2 failures)
5. **[GRADIENT-FLOW-001]** (in_planning) - C16 - differentiability regression (1 failure)
6. **[TRICLINIC-PARITY-001]** (in_planning) - C18 - AT-PARALLEL-026 (1 failure)

### Priority 2 (Infrastructure/Tooling - High):
7. **[TOOLING-DUAL-RUNNER-001]** (in_planning) - C5 - testing infrastructure (1 failure)
8. **[CLI-FLAGS-003]** (in_progress) - C6 - `-pix0_vector_mm`, HKL roundtrip (2 failures)
9. **[DEBUG-TRACE-001]** (in_planning) - C7 - debugging tooling (4 failures)
10. **[VECTOR-TRICUBIC-002]** (in_progress) - C13 - vectorization parity (2 failures)

### Priority 3 (Medium Severity):
11. **[CUDA-GRAPHS-001]** (in_planning) - C11 - performance optimization (3 failures)
12. **[UNIT-CONV-001]** (in_planning) - C14 - narrow scope (1 failure)
13. **[DENZO-CONVENTION-001]** (in_planning) - C9 - less-common convention (1 failure)

### Priority 4 (Low/Deferred):
14. **[LEGACY-SUITE-001]** (in_planning) - C12 - **candidate for deprecation** (5 failures)

## Environment Metadata

- **Python:** 3.13.5
- **pytest:** 8.4.1
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6
- **Platform:** linux
- **Environment Variables:** `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE` (CPU-only run)

## Artifacts Reference

- **Phase K Summary:** `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/summary.md`
- **JUnit XML:** `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/artifacts/pytest_full.xml`
- **Full Log:** `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/logs/pytest_full.log`

---

**Classification Complete:** 31 failures classified (30 implementation bugs + 1 likely deprecation across 14 active clusters); C1, C2, C15 remain resolved. **Net improvement: -5 failures vs Phase I (13.9% reduction).**

**Status:** Phase K2 COMPLETE. Ready for K3 (tracker refresh).
