Plan: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md#task-7-diagnose-vi-spread-collapse
References:
- docs/strategy/mainstrategy.md §8 (VI objectives + FND-VI-2026-01 context)
- docs/plans/2026-01-29-vi-mosaic-implementation-plan.md §Task 7 (diagnostics expectations)
- docs/findings.md (FND-VI-2026-01 evidence + gaps)
- docs/development/testing_strategy.md §6.0.1 (benchmark logging + artifact policy)
Summary:
- Extend `src/nanobrag_torch/vi/poisson_elbo.py` per Task 7 Step 1 so `return_components=True` (or a diagnostics callback) yields log-likelihood, KL, sampled `sigma` stats, and gradient norms without breaking differentiability; document the hook and update existing Poisson ELBO tests to cover the richer payload.
- Add `scripts/analysis/vi_poisson_diagnostics.py` plus a new pytest that exercises a short (≤5 iteration, 32×32 detector) run, emitting JSON with the logged metrics and verifying gradient norms are finite when `sigma_deg` is clamped below the 2° ground truth (Task 7 Step 2 + 3).
- Teach `scripts/benchmark_vi_mosaic.py` to accept `--diagnostics-log`, capture metrics every 10 iterations, and archive both the diagnostics JSON + a brief Markdown summary under `plans/active/strat-vi-001/reports/2026-01-29T081427Z/` for the canonical 150-iteration CPU run (Task 7 Step 4).
Summary: Instrument the VI Poisson ELBO and benchmark workflow so we can capture per-iteration log-likelihood/KL/gradient trends for diagnosing the mosaic spread collapse.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped tests:
- pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_seeded_runs_repeat -q
- pytest tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot -q
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T081427Z/
Next Up: (1) Analyze diagnostics to propose ELBO/likelihood fixes, (2) Draft mitigation mini-plan if gradients remain flat.
