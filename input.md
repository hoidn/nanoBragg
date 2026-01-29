Plan: docs/plans/2026-01-29-m2-closeout.md
References:
- docs/strategy/mainstrategy.md §7 — Canonical STRAT-M2 metrics + artifact references that must be cited verbatim
- docs/findings.md (FND-M2-2026-01) — Authoritative record of the σ-collapse evidence bundle you are surfacing
- docs/user/known_limitations.md — Add the new amortized mosaicity limitation entry with exact CLI commands
- docs/fix_plan.md §[STRAT-M2-001] — Update ledger status + FSM line once the close-out narrative lands
- docs/development/testing_strategy.md §6.2 — Canonical amortized CLI/test coverage (normative commands to reference)
Summary: Promote the amortized Duck evidence (canonical 150-iter run, scale study, stabilization toolkit) into strategy + fix-plan docs, add a Known Limitations section explaining the σ-collapse with reproduction commands, and reset STRAT-M2-001’s status so strategy work can pivot to STRAT-M3-001; all references must stay aligned with the artifact bundles cited in FND-M2-2026-01 and strategy §7.
Summary (1-liner): Document the STRAT-M2 close-out (strategy + fix-plan + Known Limitations) using the recorded artifacts so we can officially retire amortized σ recovery work.
Focus: STRAT-M2-001 — Duck multi-image demo
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_amortized -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_curriculum_runner_two_phase_smoke -v
Artifacts: plans/active/strat-m2-001/reports/2026-01-29T131500Z/closeout/
Next Up:
1. If docs drift emerges while editing, add a follow-up card for STRAT-M3-001 evidence refresh.
2. Should the Known Limitations entry uncover missing user guidance, open docs/user issue to track UX fixes.
