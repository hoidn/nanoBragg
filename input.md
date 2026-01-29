Plan: docs/plans/2026-01-29-m2-amortized-multi-image.md
References:
- docs/strategy/mainstrategy.md §7 — defines Duck multi-image milestones (M1–M3) and success metrics
- docs/plans/2026-01-29-m2-amortized-multi-image.md — step-by-step tasks for dataset, trainer, and demo CLI
- docs/development/testing_strategy.md — CLI + artifact expectations and pytest workflow guardrails
- docs/fix_plan.md — authoritative initiative status + exit criteria for STRAT-M2-001
- notebooks/refinement_tutorial.ipynb — source geometry/orientation logic for Duck slice generation
Summary: Build the amortized multi-image “Duck” demo end-to-end: publish the dataset contract + generator, implement the shared MultiImageTrainer aggregator, and ship a CLI that outputs PNG/JSON evidence so Strategy §7 (M1) has reproducible artifacts.
Summary: Ship Duck dataset + trainer + CLI so we can execute Strategy §7 M1.
Focus: STRAT-M2-001 — Duck multi-image demo
Branch: feature/spec-based-2
Mapped tests: author minimal targeted tests then run `pytest tests/test_duck_dataset.py::test_duck_dataset_shapes -v`, `pytest tests/test_vi_mosaic.py::test_multi_image_trainer_batches_duck -v`, `pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_smoke -v`
Artifacts: plans/active/strat-m2-001/reports/2026-01-29T230500Z/
Next Up: 1) Prototype amortized encoder for per-image mosaic posteriors once demo lands; 2) Extend dataset generator to multi-slice volumes for Strategy §7 M2
