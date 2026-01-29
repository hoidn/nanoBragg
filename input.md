Summary: Bootstrap STRAT-VI-001 by landing MosaicPosterior + tests as the first slice of the VariationalMosaicSimulator pivot.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_probabilistic_simulator.py::TestProbabilisticMatchesMonteCarlo::test_probabilistic_matches_high_domain_limit -v; pytest tests/test_vi_mosaic.py::test_mosaic_posterior_shapes_and_kl -v (new test—write it first)
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T071658Z/
Next Up: 1) wire VariationalMosaicSimulator run loop with k-sample averaging 2) add Poisson ELBO helper + gradcheck
