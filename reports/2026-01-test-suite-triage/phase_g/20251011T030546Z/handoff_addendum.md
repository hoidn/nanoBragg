# Phase G Handoff Addendum — Test Suite Triage (20251011T030546Z)

**Initiative:** [TEST-SUITE-TRIAGE-001]  
**Compiled by:** galph (supervisor)  
**Source artifacts:**
- Phase F bundle: `reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/{triage_summary.md,cluster_deltas.md,pending_actions.md}`
- Fix plan ledger: `docs/fix_plan.md` (snapshot after Attempt #8)
- Active plans: `plans/active/test-suite-triage.md`, `plans/active/dtype-neutral.md`, `plans/active/determinism.md`

## Summary
- Phase F classified 49 failing tests across 17 active clusters; C1 (CLI defaults) resolved via `[CLI-DEFAULTS-001]` Attempt #6.
- Critical path now centres on `[DTYPE-NEUTRAL-001]` Phase E validation followed by `[DETERMINISM-001]` Phase A reruns (post dtype fix) and `[DEBUG-TRACE-001]` plan authoring.
- This addendum replaces the Phase D ladder (20260113T000000Z) with status-aware priorities aligned to January 2026 fixes and outstanding work.

## Priority Ladder (supersedes Phase D table)
| Rank | Fix Plan ID | Owner | Status (2025-10-11) | Reproduction Command | Immediate Next Step |
| --- | --- | --- | --- | --- | --- |
| P0 | [VECTOR-PARITY-001] Restore 4096² Benchmark Parity | galph | in_progress (Tap 5.3 pending) | `See docs/fix_plan.md` §VECTOR-PARITY-001 | Deliver Tap 5.3 oversample instrumentation before scheduling `[DETECTOR-GRAZING-001]` |
| P1.1 | [DTYPE-NEUTRAL-001] dtype neutrality guardrail | ralph | in_progress (Phase E outstanding) | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_006.py` (validation once fix re-run) | Produce Phase E validation bundle (`reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_e/`) per plan checklist; update docs + guardrail notes |
| P1.2 | [DETERMINISM-001] PyTorch RNG determinism | ralph | in_progress | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py` | After dtype Phase E, apply Dynamo workaround (CPU-only or disable `torch.compile`), fix AT-024 dtype harmonisation, rerun Phase A selectors |
| P1.3 | [DEBUG-TRACE-001] Debug flag support | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py` | Draft trace instrumentation plan (Phase A/B) covering `--printout` + `--trace_pixel`; cite trace SOP and Protected Assets |
| P2 | [SOURCE-WEIGHT-002] Simulator source weighting | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py` | Author follow-up plan verifying simulator weighting and normalization; reuse SOURCE-WEIGHT guardrails |
| P2 | [DETECTOR-CONFIG-001] Detector defaults audit | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py` | Draft audit checklist vs spec §4; document required config/architecture updates |
| P2 | [LATTICE-SHAPE-001] Lattice shape models | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels` | Build plan covering GAUSS/TOPHAT parity with C interpreter |
| P2 | [GRADIENT-FLOW-001] Gradient flow regression | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation` | Capture gradient graph evidence (Phase A) then isolate detach/item misuse per ADR-08 |
| P2 | [DETECTOR-GRAZING-001] Extreme detector angles | ralph | in_planning (blocked) | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_017.py` | Await `[VECTOR-PARITY-001]` Tap 5 closure; prepare to reuse detector geometry trace tooling once unblocked |
| P3 | [CLI-FLAGS-003] CLI flags (-nonoise, -pix0_vector_mm) | ralph | in_progress | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py` | Continue Phase L/N validation per plan (`reports/2025-10-cli-flags/phase_l/` cadence) |
| P3 | [TOOLING-DUAL-RUNNER-001] Restore dual-runner parity | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration` | Author tooling reinstatement plan under `plans/active/dual-runner.md` |
| P3 | [VECTOR-TRICUBIC-002] Vectorization relaunch backlog | galph | in_progress | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py` | Resume once Tap 5 parity gap resolved (see VECTOR plan Phase E/F) |
| P3 | [CUDA-GRAPHS-001] CUDA graphs compatibility | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py` | Capture profiler evidence + guardrail before implementation |
| P4 | [UNIT-CONV-001] Mixed unit conversion parity | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive` | Draft unit audit plan referencing ADR-01 hybrid meter/Å contract |
| P4 | [DENZO-CONVENTION-001] DENZO convention support | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping` | Document convention mapping updates in detector plan before implementation |
| P4 | [LEGACY-SUITE-001] Legacy translation suite upkeep | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness -k "sensitivity or performance or extreme or rotation_compatibility"` | Decide refresh vs deprecation; capture recommendation in Phase D attempts |
| P4 | [TRICLINIC-PARITY-001] Triclinic parity alignment | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c` | Schedule trace-driven audit after Tap 5 / detector work stabilises |

## Coordination Notes
- `[DTYPE-NEUTRAL-001]` Phase E deliverables (validation report + checklist updates) unblock `[DETERMINISM-001]` and should be delegated immediately via `input.md`.
- Retain `reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/pending_actions.md` as authoritative reference for cluster-to-fix-plan mapping; this addendum only updates status/priority signals.
- Supervisor input templates must cite the new addendum path when steering future loops.

## Artifact Expectations
- Store future Phase G updates under `reports/2026-01-test-suite-triage/phase_g/<STAMP>/` with `handoff_addendum.md`, `commands.txt`, and any supplementary summaries.
- Update `docs/fix_plan.md` Attempts History (Attempt #9) to reference this addendum and note the priority adjustments.

