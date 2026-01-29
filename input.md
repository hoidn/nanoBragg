Plan: docs/plans/2026-01-29-vi-likelihood-temperature.md
References:
- docs/strategy/mainstrategy.md §9 — canonical VI benchmark narrative and latest mitigation experiments to cross-reference when summarizing temperature sweep outcomes
- docs/findings.md (FND-VI-2026-01) — needs a new paragraph for likelihood-temperature results and artifact links
- docs/fix_plan.md §STRAT-VI-001 — update Task 18 state + supervisor FSM entry after evidence is captured
- docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family — normative definition of Poisson ELBO / posterior parameterization to cite when describing temperature knob math in documentation
- scripts/analysis/vi_poisson_diagnostics.py — diagnostics CLI to extend with temperature sweep helper + flags
- scripts/benchmark_vi_mosaic.py — benchmark CLI to expose `--likelihood-temperature`
- src/nanobrag_torch/vi/poisson_elbo.py — Poisson ELBO implementation to add the temperature scaling
- tests/test_vi_mosaic.py — add regression tests and update smoke coverage for the new knob + sweeps
Summary:
- Implement Task 1: add a `likelihood_temperature` parameter to `poisson_elbo`, extend diagnostics payloads, and cover with the new regression.
- Implement Task 2: plumb the temperature flag through diagnostics + benchmark CLIs and update their smoke tests.
- Implement Task 3: create `run_likelihood_temperature_sweep` with CLI trigger, plus tests.
- Execute Task 4: run a 25-iteration temperature sweep (temps {1.0,2.0,4.0}), archive artifacts under `plans/active/strat-vi-001/reports/2026-01-29T102251Z/temperature_sweep/`, and update docs/fix-plan/findings with conclusions.
Summary (Goal): Add likelihood-temperature support for the VI Poisson ELBO, expose it through tooling, and capture sweep evidence to determine if hotter likelihoods alleviate σ collapse.
Focus: STRAT-VI-001 — Variational mosaic simulator (Task 18 likelihood-temperature sweep)
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_poisson_elbo_likelihood_temperature_scales_loglik -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_temperature_sweep_runs_multiple_temperatures -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T102251Z/
Next Up (optional):
1. Temperature sweep follow-up — if T∈{1,2,4} still collapses, extend sweep to include T=8 and document gradient divergence limits.
2. IWAE + temperature hybrid — re-run IWAE objective with likelihood tempering to see if combining both levers yields ≥1.5° σ.
Normative Math/Physics: Reference docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family for Poisson ELBO equations and docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md §Adaptive Scaling Definition for observation scaling instead of restating formulas.
