Plan: docs/plans/2026-01-29-vi-noncentered-iwae.md
References:
- docs/strategy/mainstrategy.md §9 — canonical VI benchmark target (≥1.5°) and narrative that must be updated with new parameterization/IWAE evidence
- docs/findings.md (FND-VI-2026-01) — symptoms we are mitigating; append the non-centered + IWAE diagnostics there
- docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family — normative definition of the posterior variables/log-normal prior that both parameterizations must honor
- docs/plans/2026-01-29-vi-elbo-decomposition.md §§Task 3-4 — authoritative steps for non-centered posterior and IWAE objective
- scripts/analysis/vi_poisson_diagnostics.py — wire `--posterior-parameterization` + `--elbo-objective`, emit metadata/JSON rows, capture artifacts for Task 3 & 4
- scripts/benchmark_vi_mosaic.py — CLI + summary JSON; keep benchmark outputs comparable when toggling parameterization/objective
- src/nanobrag_torch/vi/mosaic_posterior.py & src/nanobrag_torch/vi/__init__.py — add parameterization switch, log-density helpers for IWAE
- src/nanobrag_torch/simulators/variational_mosaic.py — surface the new parameterization flag and per-sample outputs for IWAE weights
- src/nanobrag_torch/vi/poisson_elbo.py — implement the IWAE objective + diagnostics fields
- tests/test_vi_mosaic.py — add parameterization + IWAE unit tests / gradcheck coverage
Summary:
- Extend `MosaicPosterior` with `parameterization={"log_normal","noncentered"}`, add `log_prob_sigma()` / `log_prior_sigma()` helpers, and plumb the choice through `VariationalMosaicSimulator`, `vi_poisson_diagnostics.py`, and `benchmark_vi_mosaic.py` (CLI flag `--posterior-parameterization`, JSON metadata, Markdown tables). For non-centered mode follow Task 3’s softplus-based sampling guidance, ensure gradients/gradcheck still pass, and update `docs/plans/2026-01-29-vi-mosaic-design.md` with the new variational family note.
- Implement Task 4’s IWAE objective inside `poisson_elbo`: add `objective={"standard","iwae"}`, capture per-sample log-likelihoods (extend the simulator if necessary to return per-sample images), compute log-weights with the new `log_prob_sigma`/`log_prior_sigma` helpers, warn when `iwae` is requested with `k_samples<2`, and log the chosen objective plus summary stats in `ELBODiagnostics`/CLI outputs. Add pytest coverage for both the parameterization class and IWAE behaviors per the plan (new `TestMosaicPosteriorParameterizations`, IWAE regression tests, CLI smoke updates).
- Run two evidence-gathering diagnostics: (1) `noncentered` vs `log_normal` runs (25 iters, `observation_mean=25`, `k=4`) with artifacts under `plans/active/strat-vi-001/reports/2026-01-29T155200Z/noncentered/`, (2) IWAE sweep (≥8 samples) with logs under `.../iwae/`. Summarize their gradient ratios in `docs/findings.md` + `docs/strategy/mainstrategy.md §9`, citing the artifact paths. Update `vi_vs_mc_summary.json` formats only if necessary.
Summary (1-liner): Ship VI ELBO Tasks 3–4 (non-centered posterior option + IWAE objective) with full CLI/tests/docs coverage and fresh diagnostic artifacts.
Focus: STRAT-VI-001 — Variational mosaic simulator (VI ELBO Task 3–4)
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestMosaicPosteriorParameterizations::test_noncentered_sampling_positive -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_poisson_elbo_iwae_matches_standard_when_k1 -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_diagnostics_beta_schedule -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T155200Z/
Next Up (optional): Explore IWAE sample-count vs runtime trade-offs (k=4→16) once baseline implementation lands.
Normative Math/Physics: See docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family and docs/plans/2026-01-29-vi-elbo-decomposition.md §§Task 3-4 for the required sampling + IWAE equations.
