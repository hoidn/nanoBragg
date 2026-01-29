Plan: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md
References:
- docs/strategy/mainstrategy.md §8 (VI ownership + evidence expectations)
- docs/plans/2026-01-29-vi-mosaic-implementation-plan.md §Task 6 (canonical benchmark artifact steps)
- docs/fix_plan.md §STRAT-VI-001 (current state + next action)
- docs/development/testing_strategy.md §6.0.1 (benchmark contract)
Summary:
- Run the canonical VI benchmark (`KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 python scripts/benchmark_vi_mosaic.py --iterations 150 --outdir demo_outputs`) so we regenerate the vi_vs_mc PNG+JSON with the documented settings.
- Tee stdout/stderr into `plans/active/strat-vi-001/reports/2026-01-29T080653Z/benchmark_vi_mosaic.log`, then copy `demo_outputs/vi_vs_mc_loss.png` and `demo_outputs/vi_vs_mc_summary.json` into that directory and generate `benchmark_summary.md` from the JSON stats (per Task 6 Step 4).
- After archiving the artifacts, rerun the benchmark smoke test to confirm the CLI still produces the PNG/JSON pair as expected.
Summary: Capture and archive the canonical VI benchmark artifacts plus verification log.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped tests:
- pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -q
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T080653Z/
Next Up: (1) Repeat the canonical benchmark on CUDA once a GPU node frees up, (2) Inspect VI benchmark JSON for non-zero gradient trends beyond mean loss.
