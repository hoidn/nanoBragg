Plan: docs/plans/2026-01-29-vi-elbo-decomposition.md
References:
- docs/strategy/mainstrategy.md §9 (defines the canonical VI benchmark target ≥1.5° and the evidence bundle we must refresh)
- docs/findings.md (FND-VI-2026-01 describes the σ collapse symptoms we are instrumenting against; cite new sweep results there)
- docs/plans/2026-01-29-vi-elbo-decomposition.md §Task 2 (authoritative steps for the observation-count sweep harness)
- docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md §Task 7 (normative definition of adaptive Poisson observation scaling / metadata that the sweep must report)
- scripts/analysis/vi_poisson_diagnostics.py (add `run_observation_sweep`, CLI grid plumbing, JSON/Markdown schema updates)
- scripts/benchmark_vi_mosaic.py (ensure sweep metadata mirrors benchmark formats so later comparisons stay consistent)
- tests/test_vi_mosaic.py (new `test_vi_observation_sweep_runs_multiple_means` + refreshed snapshot assertions)
- src/nanobrag_torch/vi/observation_utils.py (reuse adaptive scaling helpers without diverging from the spec)
Summary:
- Implement Task 2 from `docs/plans/2026-01-29-vi-elbo-decomposition.md`: add a reusable `run_observation_sweep()` helper plus CLI flags (`--observation-mean-grid`, `--observation-grid-outdir`) in `scripts/analysis/vi_poisson_diagnostics.py` so we can loop over multiple observation-count targets with the adaptive scaling defined in `docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md §Task 7` and emit combined JSON/Markdown tables of log-likelihood, KL, σ trajectories, and gradient ratios.
- Add pytest coverage in `tests/test_vi_mosaic.py` (author `test_vi_observation_sweep_runs_multiple_means`) that calls the helper with two means, asserts deterministic metadata (mean counts increase monotonically, seeds propagate), and verifies artifacts land in a temporary outdir; keep existing diagnostics tests passing.
- After implementation, run the CLI sweep (`python scripts/analysis/vi_poisson_diagnostics.py --iterations 25 --k-samples 4 --observation-mean-grid 25,100,300,1000 --observation-grid-outdir plans/active/strat-vi-001/reports/2026-01-29T093224Z/observation_sweep`) and update `docs/findings.md` FND-VI-2026-01 plus `docs/strategy/mainstrategy.md §9` with the new evidence summary.
Summary (1-liner): Build and exercise the VI observation-count sweep harness so we can quantify how Poisson count levels change ELBO gradients.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped Tests:
- pytest tests/test_vi_mosaic.py::test_vi_diagnostics_beta_schedule -v
- pytest tests/test_vi_mosaic.py::test_vi_observation_sweep_runs_multiple_means -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T093224Z/
Next Up (optional):
- Once the sweep lands, continue Task 3 (non-centered posterior experiment) from the same plan so we can compare parameterizations under identical observation stats.
