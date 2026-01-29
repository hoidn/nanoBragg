Plan: docs/plans/2026-01-29-m2-amortized-scale-study.md
References:
- docs/strategy/mainstrategy.md §7 — canonical Duck M1–M3 requirements plus expectations for amortized gradient scaling with more images
- docs/development/testing_strategy.md §6.2 — normative commands / validation criteria for amortized mode and required selectors
- docs/specs/duck_multi_image_dataset.md — dataset contract and generator options (image counts, metadata schema) you will extend for new variants
- docs/fix_plan.md §[STRAT-M2-001] — current status + exit criteria you are advancing via the scale-study plan
Summary: Generate the 50- and 100-image Duck datasets, then run and archive the 500-iteration amortized baseline on the original 20-image set so we can kick off the scale-study evidence bundle.
Summary (Goal): Establish the data + long-run baseline required for STRAT-M2-001’s amortized scale study.
Focus: STRAT-M2-001 — Duck multi-image demo (Scale Study Tasks 1–2)
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_duck_dataset.py::test_duck_dataset_shapes -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_amortized -v
Artifacts: plans/active/strat-m2-001/reports/2026-01-29T230000Z/scale_study/ (subfolders: datasets/, amortized_longrun_20/; mirror PNG/JSON to demo_outputs/duck_amortized_longrun_20/)
Next Up:
1. After the baseline run, execute the 50-image and 100-image amortized experiments (Plan Task 3) and capture their metrics snapshots.
2. Implement `scripts/analysis/summarize_duck_amortized.py` with pytest coverage (Plan Task 4) once the new summaries exist.
