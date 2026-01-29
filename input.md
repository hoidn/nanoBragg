Plan: docs/plans/2026-01-29-vi-elbo-decomposition.md
References:
- docs/strategy/mainstrategy.md §9 (canonical VI benchmark + ELBO acceptance criteria)
- docs/findings.md (FND-VI-2026-01 context + required evidence types)
- docs/fix_plan.md (STRAT-VI-001 Task 16 metadata)
- docs/plans/2026-01-29-vi-mosaic-implementation-plan.md §Model Definition (normative Poisson ELBO math)
- src/nanobrag_torch/vi/poisson_elbo.py, src/nanobrag_torch/vi/mosaic_posterior.py
- scripts/analysis/vi_poisson_diagnostics.py, scripts/benchmark_vi_mosaic.py
- tests/test_vi_mosaic.py
Summary:
- Implement Task 1 from `docs/plans/2026-01-29-vi-elbo-decomposition.md`: extend `poisson_elbo` diagnostics so we capture per-iteration log-likelihood vs KL gradient magnitudes (μ and ρ), expose the data through `scripts/analysis/vi_poisson_diagnostics.py` and `scripts/benchmark_vi_mosaic.py`, and add pytest guards that assert the new fields populate (see `docs/plans/2026-01-29-vi-mosaic-implementation-plan.md §Model Definition` for the normative ELBO definition).
- Introduce CLI knobs (`--diagnostics-stride`, `capture_component_grads` plumbing) so the canonical benchmark can emit every-step diagnostics into `vi_diagnostics.json`, then refresh the JSON/Markdown schemas to include the gradient components for future analysis tied to FND-VI-2026-01.
- Keep existing behaviors backward compatible (k-sample averaging, device/dtype neutrality) and prove the changes via the targeted pytest selectors plus whichever smoke tests you touch.
Summary (1-liner): Add per-iteration log-likelihood vs KL gradient diagnostics to the VI tooling so we can decompose the collapsed σ behavior.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped Tests:
- pytest tests/test_vi_mosaic.py::test_poisson_elbo_reports_component_gradients -v
- pytest tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T092513Z/
Next Up (optional):
- After instrumentation, run Task 2 (observation-count sweep) from the same plan to see whether higher mean counts change the gradient balance.
