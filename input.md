Plan: docs/plans/2026-01-29-vi-elbo-balancing.md
References: docs/strategy/mainstrategy.md; docs/findings.md#fnd-vi-2026-01; docs/plans/2026-01-29-vi-mosaic-implementation-plan.md; docs/development/testing_strategy.md; scripts/analysis/vi_poisson_diagnostics.py; scripts/benchmark_vi_mosaic.py; src/nanobrag_torch/vi/poisson_elbo.py; tests/test_vi_mosaic.py
Summary: Implement the VI ELBO rebalancing plan so KL weighting/annealing hooks exist end-to-end, diagnostics + benchmark tooling expose the beta schedule, and new artifacts prove sigma growth past 1.5° on the canonical benchmark.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped tests: tests/test_vi_mosaic.py::TestPoissonELBO::test_kl_weight_scales_loss; tests/test_vi_mosaic.py::test_kl_schedule_hits_start_mid_end; tests/test_vi_mosaic.py::test_vi_diagnostics_beta_schedule; tests/test_vi_mosaic.py::test_benchmark_script_smoke
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T082528Z/
Next Up: none
