Plan: docs/plans/2026-01-29-m2-amortized-mosaicity.md
References:
- docs/strategy/mainstrategy.md §7 — defines Duck multi-image milestones and amortized-gradient success metrics
- docs/development/testing_strategy.md §CLI Workflows — canonical pytest/CLI commands + artifact expectations
- docs/index.md — authoritative doc list; ensures new Duck dataset spec is linked once written
- docs/fix_plan.md — STRAT-M2-001 ledger + exit criteria for the amortized encoder phase
Summary:
Tackle M2 Tasks 1–2. First, finish the Duck dataset contract: extend `scripts/generate_duck_multi_image.py` + `DuckDataset` to store per-image mosaic truth and observation scaling metadata, regenerate `demo_inputs/duck_multi_image/`, and author `docs/specs/duck_multi_image_dataset.md` so §7 remains the normative reference. Then, build the amortized encoder module that maps photon-count tiles + orientation context to posterior parameters (new `DuckMosaicEncoder`), expose it via `vi.__init__`, and add focused tests showing shape + grad flow; this encoder will feed directly into the conditioned posterior plumbing in Task 3. Keep all numerical conventions aligned with Strategy §7 (fixed orientations, shared F_hkl) and cite that section rather than paraphrasing equations.
Summary: Publish Duck dataset spec with mosaic truth and land the amortized encoder module to kick off Strategy §7 M2.
Focus: STRAT-M2-001 — Duck multi-image demo
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_duck_dataset.py::test_duck_dataset_shapes -v; pytest tests/test_vi_mosaic.py::test_multi_image_trainer_batches_duck -v
Artifacts: plans/active/strat-m2-001/reports/2026-01-29T210500Z/
Next Up: 1) Task 3 — conditioned MultiImageTrainer amortized plumbing; 2) Task 4 — CLI/docs refresh + amortized evidence bundle
