Plan: docs/plans/2026-01-29-vi-prior-geometry.md
References:
- docs/strategy/mainstrategy.md §9 — strategy mandate for replacing analytic mosaicity with VI plus evidence expectations for Task 24
- docs/plans/2026-01-29-vi-prior-geometry.md — step-by-step instructions for the prior schedule + multi-geometry diagnostics workflow
- docs/findings.md (FND-VI-2026-01 / FND-VI-2026-01b / FND-VI-2026-01c) — captures the structural collapse evidence we must improve and cites existing artifacts
- docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family — normative definition of the mosaic posterior, KL, and Poisson ELBO math we must preserve
- scripts/analysis/vi_poisson_diagnostics.py & scripts/benchmark_vi_mosaic.py — CLIs that need the new prior schedule knobs and metadata logging
- src/nanobrag_torch/vi/mosaic_posterior.py & src/nanobrag_torch/vi/poisson_elbo.py — posterior+diagnostics plumbing that must expose the schedule and capture prior metadata
- tests/test_vi_mosaic.py — regression targets for the new helper, CLI wiring, and smoke coverage
Summary:
- Implement Task 1 from the plan: add `LinearPriorSchedule` (new module) plus `MosaicPosterior.set_prior`, write/execute the targeted tests (`test_interpolates_spread`, `test_mosaic_posterior_set_prior_updates_buffers`), and stash pytest logs under `plans/active/strat-vi-001/reports/2026-01-29T105208Z/prior_schedule_dev/`.
- Execute Task 2: thread the prior schedule knobs through `run_diagnostics` / `run_benchmark`, emit prior metadata in JSON + Markdown summaries, update ELBO diagnostics if needed, and extend smoke tests so the new CLI options collect.
- After each task, rerun the mapped selectors, capture logs in the artifact directory, and leave docs untouched until Task 3 (diagnostics runs) delivers data; ensure CLI help text explains defaults so future sweeps are reproducible.
Summary (Goal): Land the prior-schedule plumbing (helper + CLI wiring) so VI experiments can sweep informative priors across detector sizes.
Focus: STRAT-VI-001 — Prior schedule & multi-geometry diagnostics (Task 24)
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestLinearPriorSchedule::test_interpolates_spread -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_mosaic_posterior_set_prior_updates_buffers -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_diagnostics_records_prior_schedule -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T105208Z/prior_schedule_dev/
Next Up (optional):
1. Run Task 3 multi-geometry diagnostics sweeps once the new knobs are validated.
2. Run Task 4 canonical 150-iter benchmark with the best prior schedule configuration.
Normative Math/Physics: See docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family for the authoritative posterior/ELBO equations and docs/strategy/mainstrategy.md §9 for the VI initiative objectives governing prior scheduling.
