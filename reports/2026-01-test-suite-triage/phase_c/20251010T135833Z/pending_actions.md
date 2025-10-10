# Pending Actions - Test Suite Triage Phase C
## Cluster-to-Fix-Plan Mapping

**Date:** 2025-10-10
**Timestamp:** 20251010T135833Z
**Source:** Phase C triage summary covering 50 failures across 18 clusters

## Status Summary

| Status | Count | Description |
| --- | --- | --- |
| in_progress | 3 | Active work underway |
| in_planning | 8 | Fix plan exists, awaiting implementation |
| unassigned | 8 | Fix plan creation required |
| **TOTAL** | **19** | **18 clusters + 1 blocker** |

## Active Work (in_progress)

### 1. [VECTOR-TRICUBIC-002] Tricubic Vectorization (C6)
- **Owner:** galph
- **Cluster:** C6 (2 failures)
- **Reproduction:** `pytest -v tests/test_tricubic_vectorized.py`
- **Blocker:** None
- **Next Action:** Fix vectorized tricubic parity; resolve OOB warning logic
- **Priority:** High (vectorization parity guardrail)

### 2. [CLI-FLAGS-003] CLI Flags (C10)
- **Owner:** ralph
- **Cluster:** C10 (3 failures)
- **Reproduction:** `pytest -v tests/test_cli_flags.py`
- **Blocker:** None
- **Next Action:** Implement CLI parsing for `-pix0_vector_mm`, HKL Fdump roundtrip
- **Priority:** High (CLI completeness)

### 3. [VECTOR-PARITY-001] Restore 4096² Benchmark Parity
- **Owner:** galph
- **Cluster:** Blocker for C4
- **Reproduction:** See fix_plan.md lines 169-234
- **Blocker:** None
- **Next Action:** Complete Tap 5.3 oversample instrumentation
- **Priority:** Critical (blocks C4 and other work per input.md)

## Planned Work (in_planning - 8 items)

### 4. [CLI-DEFAULTS-001] Minimal -default_F CLI (C1)
- **Owner:** ralph
- **Cluster:** C1 (1 failure)
- **Reproduction:** `pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F`
- **Next Action:** Reproduce targeted command; identify HKL fallback logic
- **Priority:** High (minimal CLI usage pattern)

### 5. [DETERMINISM-001] PyTorch RNG Determinism (C2)
- **Owner:** ralph
- **Cluster:** C2 (6 failures)
- **Reproduction:** `pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py`
- **Next Action:** Instrument RNG seeding path; enforce seed propagation
- **Priority:** High (reproducibility blocker)

### 6. [DETECTOR-GRAZING-001] Extreme Detector Angles (C4)
- **Owner:** ralph
- **Cluster:** C4 (4 failures)
- **Reproduction:** `pytest -v tests/test_at_parallel_017.py`
- **Blocker:** [VECTOR-PARITY-001] Tap 5 completion
- **Next Action:** Schedule after Tap 5 complete; audit pivot/obliquity math
- **Priority:** High (spec compliance)

### 7. [SOURCE-WEIGHT-002] Simulator Source Weighting (C7)
- **Owner:** ralph
- **Cluster:** C7 (6 failures)
- **Reproduction:** `pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py`
- **Next Action:** Author follow-up ensuring Simulator multiplies weights
- **Priority:** High (regression fix from [SOURCE-WEIGHT-001])

### 8. [TOOLING-DUAL-RUNNER-001] Restore Dual Runner (C9)
- **Owner:** ralph
- **Cluster:** C9 (1 failure)
- **Reproduction:** `pytest -v tests/test_at_tools_001.py::test_script_integration`
- **Next Action:** Restore dual-runner C vs PyTorch harness
- **Priority:** High (testing infrastructure)

### 9. [DEBUG-TRACE-001] Debug Flag Support (C11)
- **Owner:** ralph
- **Cluster:** C11 (4 failures)
- **Reproduction:** `pytest -v tests/test_debug_trace.py`
- **Next Action:** Implement `--printout` and `--trace_pixel` flags
- **Priority:** High (debugging infrastructure)

### 10. [DETECTOR-CONFIG-001] Detector Defaults Audit (C12)
- **Owner:** ralph
- **Cluster:** C12 (2 failures)
- **Reproduction:** `pytest -v tests/test_detector_config.py`
- **Next Action:** Audit detector config defaults vs spec-a-core.md §4
- **Priority:** High (baseline detector correctness)

### 11. PENDING: Remediation Sequencing
- **Next Step:** Await Phase D handoff (plans/active/test-suite-triage.md D1-D4)
- **Blocker:** `input.md` lines 5-6 suspend engineering work until Phase D ready

## Unassigned Work (8 items - requires fix plan creation)

### 12. NEW: [CUDA-GRAPHS-001] CUDA Graphs (C3)
- **Cluster:** C3 (6 failures)
- **Reproduction:** `pytest -v tests/test_perf_pytorch_005_cudagraphs.py`
- **Root Cause:** torch.compile cache invalidation or dynamic shape handling
- **Priority:** Medium (performance optimization)

### 13. NEW: [UNIT-CONV-001] Unit Conversion (C5)
- **Cluster:** C5 (1 failure)
- **Reproduction:** `pytest -v tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`
- **Root Cause:** ADR-01 hybrid unit system edge case
- **Priority:** Medium (narrow scope)

### 14. NEW: [LATTICE-SHAPE-001] Lattice Shape Models (C8)
- **Cluster:** C8 (2 failures)
- **Reproduction:** `pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels`
- **Root Cause:** GAUSS/TOPHAT models not wired per spec-a-core.md §8
- **Priority:** High (spec compliance)

### 15. NEW: [DENZO-CONVENTION-001] DENZO Convention (C13)
- **Cluster:** C13 (1 failure)
- **Reproduction:** `pytest -v tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping`
- **Root Cause:** DENZO beam-center mapping not implemented (arch.md §7 line 223)
- **Priority:** Medium (less-common convention)

### 16. NEW: [PIVOT-MODE-001] Detector Pivots (C14)
- **Cluster:** C14 (2 failures)
- **Reproduction:** `pytest -v tests/test_detector_pivots.py`
- **Root Cause:** Pivot mode behavior (BEAM vs SAMPLE) not matching ADR-02
- **Priority:** High (fundamental detector geometry)

### 17. NEW: [DTYPE-NEUTRAL-001] dtype Support (C15)
- **Cluster:** C15 (2 failures)
- **Reproduction:** `pytest -v tests/test_perf_pytorch_006.py`
- **Root Cause:** dtype neutrality regression (float32/float64)
- **Priority:** Medium (runtime guardrail)

### 18. NEW: [LEGACY-SUITE-001] Legacy Test Suite (C16)
- **Cluster:** C16 (5 failures)
- **Reproduction:** `pytest -v tests/test_suite.py::TestTier1TranslationCorrectness`
- **Root Cause:** Tests not updated for Phase D lattice fix
- **Priority:** Low (candidate for deprecation)

### 19. NEW: [GRADIENT-FLOW-001] Gradient Flow (C17)
- **Cluster:** C17 (1 failure)
- **Reproduction:** `pytest -v tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation`
- **Root Cause:** Differentiability regression violating arch.md §15 / ADR-08
- **Priority:** High (gradient correctness requirement)

### 20. NEW: [TRICLINIC-PARITY-001] Triclinic C Parity (C18)
- **Cluster:** C18 (1 failure)
- **Reproduction:** `pytest -v tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`
- **Root Cause:** AT-PARALLEL-026 parity threshold not met
- **Priority:** High (spec-a-parallel.md parity requirement)

---

## Action Items for Phase D

1. **D1 (Prioritization):** ✅ COMPLETE in triage_summary.md
   - Priority 1-4 sequences defined covering all 18 clusters

2. **D2 (Reproduction Commands):** ✅ COMPLETE in triage_summary.md
   - Each cluster section includes pytest reproduction command

3. **D3 (Documentation Touchpoints):**
   - [ ] Update `docs/fix_plan.md` with 8 new fix plan IDs (items 12-20 above)
   - [ ] Cross-link this pending_actions.md from fix_plan.md [TEST-SUITE-TRIAGE-001]
   - [ ] Update `plans/active/test-suite-triage.md` Phase C table (C5-C6 → [D])

4. **D4 (Supervisor Input):**
   - [ ] Await supervisor review of triage artifacts
   - [ ] Publish input.md for highest-priority remediation (likely [DETERMINISM-001] or [CLI-DEFAULTS-001])

---

**Status:** Phase C7 ready for fix_plan.md ledger updates and plan table refresh.
