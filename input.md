Plan: docs/plans/2026-01-29-m2-amortized-mosaicity.md
References:
- docs/strategy/mainstrategy.md §7 — authoritative success criteria for M2 (per-image σ recovery ≥1.5° plus gradient growth with dataset size)
- docs/specs/duck_multi_image_dataset.md — dataset layout, per-image metadata contract, observation scaling guarantees
- docs/development/testing_strategy.md §CLI Workflows — canonical pytest/CLI selectors and artifact expectations for Duck demos
- docs/fix_plan.md — STRAT-M2-001 ledger with task breakdown + exit criteria to update after landing evidence
Summary:
Execute Tasks 3–4 of the M2 plan: (1) add the `ConditionedMosaicPosterior` helper and overhaul `MultiImageTrainer` so it supports an amortized encoder path with orientation features, per-image sigma stats, gradient logging, and optional dataset sub-selection, and (2) wire focused pytest coverage (`test_amortized_trainer_recovers_per_image_spread`, CLI smoke) plus update `tests/test_vi_mosaic.py` to record the new diagnostics. Then extend `scripts/demo_recover_duck.py` with `--mode {shared,amortized}`, `--log-gradients`, and dataset-size sweeps, emit artifacts under `plans/active/strat-m2-001/reports/2026-01-29T230500Z/amortized_demo/` + `demo_outputs/duck_amortized/`, and refresh docs (strategy/testing/fix-plan/index) so Strategy §7’s amortized workflow is documented with citations to the new evidence bundle.
Summary: Land the amortized Duck trainer + CLI evidence bundle per Strategy §7, proving per-image σ inference and gradient amplification.
Focus: STRAT-M2-001 — Duck multi-image demo
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_vi_mosaic.py::test_multi_image_trainer_batches_duck -v; pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_smoke -v; pytest tests/test_vi_mosaic.py::test_amortized_trainer_recovers_per_image_spread -v (new); pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_amortized -v (new)
Artifacts: plans/active/strat-m2-001/reports/2026-01-29T230500Z/
Next Up: 1) After amortized CLI lands, add GPU smoke + gradient plots; 2) Start documenting dataset-size gradient scaling results in docs/strategy/mainstrategy.md.
