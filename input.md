Plan: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md (Task 3)
References: docs/strategy/mainstrategy.md §8; docs/plans/2026-01-29-vi-mosaic-design.md §Model Definition; docs/development/testing_strategy.md §1.4; tests/test_vi_mosaic.py; src/nanobrag_torch/simulators/variational_mosaic.py
Summary: Implement Task 3 by introducing the Poisson ELBO helper that ties the VariationalMosaicSimulator + MosaicPosterior together with deterministic seeding, KL tracking, and gradcheck-proven differentiability, then prove it with the new TestPoissonELBO suite.
Summary (Goal): Ship poisson_elbo with seeded determinism, gradient flow, and gradcheck coverage per VI design spec.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_seeded_runs_repeat -v; KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_gradients_flow -v; NANOBRAGG_DISABLE_COMPILE=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_gradcheck_mu_rho -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T073616Z/
Next Up: 1) scripts/benchmark_vi_mosaic.py + docs 2) analytic mosaic deprecation warning once VI validated
