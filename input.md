Plan: docs/plans/2026-01-29-vi-multiscale-geometry.md
References:
- docs/strategy/mainstrategy.md §9 — σ≥1.5° benchmark gate + multi-geometry rationale
- docs/plans/2026-01-29-vi-multiscale-geometry.md — required tasks, commands, artifact layout
- docs/findings.md (FND-VI-2026-01 family) — baseline collapse evidence to extend with geometry results
- docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family — normative ELBO/posterior math for σ interpretation
- docs/development/testing_strategy.md §1.4 — device/dtype + logging guardrails for PyTorch runs
- scripts/analysis/vi_poisson_diagnostics.py & scripts/benchmark_vi_mosaic.py — CLIs to modify and execute
Summary:
- Task 1: add `scripts/vi_geometry_presets.py` plus CLI plumbing so both diagnostics and benchmark commands accept `--geometry-preset` overriding cell/wavelength/detector defaults, with tests covering preset resolution and metadata wiring.
- Task 2: implement `run_geometry_sweep()` + CLI flags in `scripts/analysis/vi_poisson_diagnostics.py`, ensure JSON/Markdown capture per-preset σ trajectories + grad ratios, and add pytest coverage so new helpers serialize geometry metadata.
- Task 3: execute the geometry sweep (default, hi_res_small_cell, hi_res_micro), write summaries under `plans/active/strat-vi-001/reports/2026-01-29T234500Z/geometry_sweep/`, rerun the 150-iter benchmark with the best preset into `/geometry_benchmark/`, then update docs/findings/strategy/fix_plan with outcomes and comment on whether σ≥1.5° is achieved; keep logs + PNG/JSON artifacts.
Summary (one sentence): Add VI geometry presets + sweep tooling, run the multiscale diagnostics/benchmark, and document whether smaller-cell/shorter-wavelength setups recover σ≥1.5°.
Focus: STRAT-VI-001 — Task 25 multiscale geometry sweep
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_benchmark_geometry_preset_overrides_defaults -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_geometry_sweep_returns_all_presets -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T234500Z/{geometry_dev/,geometry_sweep/,geometry_benchmark/}
Next Up (optional):
1. If multiscale still collapses, draft docs/plans entry for flow posterior / hybrid MC-VI mitigation.
2. If σ≥1.5° succeeds, schedule follow-up plan to port presets into CLI docs + update README benchmarks.
Normative Math/Physics: Reference docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family for posterior math and docs/strategy/mainstrategy.md §9 for σ thresholds when interpreting ELBO results.
