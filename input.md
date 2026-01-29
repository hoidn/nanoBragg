Plan: docs/plans/2026-01-29-m2-stabilization.md
References:
- docs/strategy/mainstrategy.md §7 — Defines STRAT-M2 milestones plus stabilization success criteria and artifact expectations
- docs/development/testing_strategy.md §6.2 — Canonical Duck amortized CLI/test workflow + mapped selectors to keep current
- docs/specs/duck_multi_image_dataset.md — Normative dataset schema / observation scaling contract for amortized experiments
- docs/fix_plan.md §[STRAT-M2-001] — Ledger status + FSM state you are advancing with this stabilization pass
Summary: Land the new stabilization toolkit: add configurable gradient clipping to `MultiImageTrainer`, expose it through the Duck CLI/tests/docs, build the curriculum runner + fixtures, then capture a 500-iter clipped run and curriculum sweep so we can document whether σ ever moves off the 0.5° floor (per `docs/specs/duck_multi_image_dataset.md` dataset contract).
Summary (Goal): Deliver the Duck amortized stabilization toolkit (grad clipping + curriculum) plus fresh evidence bundles so STRAT-M2-001 can proceed toward closure.
Focus: STRAT-M2-001 — Duck multi-image demo
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_multi_image_trainer_enforces_grad_clip -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_amortized -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k curriculum -v  # add test_curriculum_runner_two_phase_smoke first
Artifacts: plans/active/strat-m2-002/reports/2026-01-29T235959Z/
Next Up:
1. If gradient clipping + curriculum still fail, extend FND-M2-2026-01 with the new metrics deltas.
2. Draft follow-on plan for alternative losses (e.g., Gaussian) if evidence suggests no σ movement.
