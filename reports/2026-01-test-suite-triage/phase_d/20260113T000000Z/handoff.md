# Phase D Handoff — Test Suite Triage
**Initiative:** [TEST-SUITE-TRIAGE-001]  
**Timestamp:** 20260113T000000Z  
**Source Artifacts:**
- Phase C triage summary: `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/triage_summary.md`
- Pending actions ledger: `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/pending_actions.md`

## Priority Ladder (from Phase C Attempt #6)
| Rank | Fix Plan ID | Cluster | Owner | Status | Pytest Reproduction |
| --- | --- | --- | --- | --- | --- |
| P0 | [VECTOR-PARITY-001] Restore 4096² Benchmark Parity | Blocker for C4 | galph | in_progress | `See docs/fix_plan.md` (§VECTOR-PARITY-001, Tap 5.3 instrumentation checklist) |
| P1 | [CLI-DEFAULTS-001] Minimal -default_F CLI | C1 (1 failure) | ralph | in_planning | `pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` |
| P1 | [DETERMINISM-001] PyTorch RNG Determinism | C2 (6 failures) | ralph | in_planning | `pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py` |
| P1 | [DEBUG-TRACE-001] Debug Flag Support | C11 (4 failures) | ralph | in_planning | `pytest -v tests/test_debug_trace.py` |
| P2 | [SOURCE-WEIGHT-002] Simulator Source Weighting | C7 (6 failures) | ralph | in_planning | `pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py` |
| P2 | [DETECTOR-CONFIG-001] Detector Defaults Audit | C12 (2 failures) | ralph | in_planning | `pytest -v tests/test_detector_config.py` |
| P2 | [LATTICE-SHAPE-001] Lattice Shape Models | C8 (2 failures) | ralph | pending | `pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels` |
| P2 | [GRADIENT-FLOW-001] Gradient Flow Regression | C17 (1 failure) | ralph | pending | `pytest -v tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation` |
| P3 | [TOOLING-DUAL-RUNNER-001] Dual Runner Tooling | C9 (1 failure) | ralph | in_planning | `pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration` |
| P3 | [CLI-FLAGS-003] CLI Flags (-pix0_vector_mm, HKL roundtrip) | C10 (3 failures) | ralph | in_progress | `pytest -v tests/test_cli_flags.py` |
| P3 | [VECTOR-TRICUBIC-002] Tricubic Vectorization | C6 (2 failures) | galph | in_progress | `pytest -v tests/test_tricubic_vectorized.py` |
| P3 | [CUDA-GRAPHS-001] CUDA Graph Compatibility | C3 (6 failures) | ralph | pending | `pytest -v tests/test_perf_pytorch_005_cudagraphs.py` |
| P3 | [DTYPE-NEUTRAL-001] dtype Neutrality | C15 (2 failures) | ralph | pending | `pytest -v tests/test_perf_pytorch_006.py` |
| P4 | [UNIT-CONV-001] Unit Conversion Edge Case | C5 (1 failure) | ralph | pending | `pytest -v tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive` |
| P4 | [DENZO-CONVENTION-001] DENZO Convention Support | C13 (1 failure) | ralph | pending | `pytest -v tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping` |
| P4 | [PIVOT-MODE-001] Detector Pivot Modes | C14 (2 failures) | ralph | pending | `pytest -v tests/test_detector_pivots.py` |
| P4 | [LEGACY-SUITE-001] Legacy Translation Suite Maintenance | C16 (5 failures) | ralph | pending | `pytest -v tests/test_suite.py::TestTier1TranslationCorrectness` |
| P4 | [TRICLINIC-PARITY-001] Triclinic Absolute Position Parity | C18 (1 failure) | ralph | pending | `pytest -v tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c` |

## Immediate Supervisor Actions (Phase D milestones)
1. **Ledger Refresh (D3):**
   - Add the nine new fix-plan IDs (CUDA, UNIT-CONV, LATTICE-SHAPE, DENZO-CONVENTION, PIVOT-MODE, DTYPE-NEUTRAL, LEGACY-SUITE, GRADIENT-FLOW, TRICLINIC-PARITY) to `docs/fix_plan.md` (index + stub sections).
   - Update `[TEST-SUITE-TRIAGE-001]` Next Actions to reflect Phase D focus and cross-link this handoff bundle.
   - Note dependencies (e.g., `[VECTOR-PARITY-001]` gating `[DETECTOR-GRAZING-001]`).
2. **Supervisor Input (D4):**
   - Once ledger refresh is committed, issue `input.md` directing Ralph to tackle `[CLI-DEFAULTS-001]` first (author failing test already exists). Include authoritative command and artifact expectations.

## Reporting Expectations for Implementation Loops
- Capture attempt logs under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/attempt_<NN>/` (mirror Phase A–C structure).
- For each remediation attempt, append a short summary to the corresponding fix-plan section (result, artifacts, next action).
- Maintain consistent Attempt numbering in `docs/fix_plan.md` to preserve the triage timeline.

## Notes & Dependencies
- `[VECTOR-PARITY-001]` Tap 5.3 remains a prerequisite for `[DETECTOR-GRAZING-001]` — do not schedule that cluster until Tap 5 instrumentation is complete.
- Follow `docs/development/testing_strategy.md` §1.5 for test execution cadence (targeted tests first; full suite at end of loop if code changed).
- Continue to set `KMP_DUPLICATE_LIB_OK=TRUE` for every PyTorch invocation.

---
Use this document as the authoritative reference when prioritising remediation work until Phase D is complete and the ledger is fully updated.
