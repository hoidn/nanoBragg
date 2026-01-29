Plan: docs/plans/2026-01-29-m3-joint-global-local.md
References:
- docs/strategy/mainstrategy.md §7 — strategy acceptance criteria + narrative that must be updated with joint-mode evidence
- docs/development/testing_strategy.md §6 — Duck workflows directory; add the joint-mode testing/benchmark instructions here
- docs/specs/duck_multi_image_dataset.md §Structure Factor Payload — canonical dataset schema for the new structure-factor tensor
- specs/spec-a-core.md §Structure Factors & Fdump — normative rules for injecting HKL tensors into Crystal
- docs/fix_plan.md — initiative status + exit criteria that must be satisfied this loop
Summary: Run the canonical joint-mode Duck benchmark, capture structured artifacts (loss plot, summary JSON, run.log) under plans/active/strat-m3-001/reports/2026-01-29T150845Z/joint_demo and demo_outputs/duck_joint/, then refresh docs/strategy §7 and docs/development/testing_strategy.md §6 so the joint workflow, commands, and validation expectations are documented with references to the new report.
Summary (Goal): Land joint-mode evidence + doc updates so STRAT-M3-001 Task 4 can close.
Focus: STRAT-M3-001 — Duck joint global-local refinement
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_joint -v
Artifacts: plans/active/strat-m3-001/reports/2026-01-29T150845Z/
Next Up:
1. If joint CLI evidence looks noisy, prototype a short 25-iter run to tune logging before rerunning the 150-iter benchmark.
2. Add a lightweight GPU smoke (e.g., 5 iterations) for joint mode once CPU evidence lands.
