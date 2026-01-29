Plan: docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md
References:
  - docs/strategy/mainstrategy.md
  - docs/findings.md
  - docs/fix_plan.md
  - docs/plans/2026-01-29-vi-elbo-balancing.md
  - scripts/benchmark_vi_mosaic.py
  - scripts/analysis/vi_poisson_diagnostics.py
  - src/nanobrag_torch/vi/poisson_elbo.py
Summary: Lower benchmark/dianostics fluence and Poisson-sample ground truth so Poisson ELBO regains mosaic curvature at 64×64.
Summary (1-sentence): Poisson observation helper + fluence knobs for VI scripts to restore ELBO signal.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped tests:
  - tests/test_vi_mosaic.py::test_benchmark_script_smoke
  - tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot
  - tests/test_vi_mosaic.py::test_poisson_observation_helper_reproducible
Mapped Tests Guardrail: All listed selectors already collect >0 tests; add helper test if missing
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T084456Z/
Next Up:
  - Investigate likelihood rescaling curve fitting
  - Prototype alternative Gaussian/MSE likelihood