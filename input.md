Plan: docs/plans/2026-01-29-m2-scale-study-stability.md
References:
- docs/strategy/mainstrategy.md §7 — Defines M2 expectations, gradient-scaling goals, and artifact requirements you are extending with the scale study
- docs/development/testing_strategy.md §6.2 — Canonical amortized CLI commands plus mapped selectors you must run after each run/test addition
- docs/specs/duck_multi_image_dataset.md — Dataset schema + generator parameters for the 20/50/100-image Duck variants used in this study
- docs/fix_plan.md §[STRAT-M2-001] — Current ledger status, next actions, and FSM state you are advancing with this work
Summary: Execute the new scale-study stability plan: rerun the 500-iter baseline with safer learning rates, complete the 50- and 100-image amortized runs, add the summarizer script/tests, and feed the resulting metrics into docs + findings.
Summary (Goal): Stabilize and document the amortized Duck scale-study evidence bundle (baseline + 50/100 images) so STRAT-M2-001 can move toward closure.
Focus: STRAT-M2-001 — Duck multi-image demo
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_amortized -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k amortized -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_analysis_duck_summary.py::test_summarize_runs_extracts_metrics -v  # author this test in Task 3 before implementation
Artifacts: plans/active/strat-m2-001/reports/2026-01-29T235959Z/scale_study/ (create amortized_longrun_20/, amortized_scale_50/, amortized_scale_100/, summary/ and mirror PNG/JSON to demo_outputs/*)
Next Up:
1. If the stabilized runs still fail to raise σ≥1.5°, draft FND-M2-2026-01 documenting the limitation and cite the new summary CSV.
2. Begin outlining mitigation options (gradient clipping vs curriculum) for a follow-on plan if evidence warrants.
