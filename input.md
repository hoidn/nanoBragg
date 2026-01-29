Plan: docs/plans/2026-01-29-vi-temperature-iwae-followup.md
References:
- docs/strategy/mainstrategy.md §9 — canonical VI benchmark + mitigation thread for reporting context
- docs/findings.md (FND-VI-2026-01) — summarize new sweep evidence and extend conclusions
- docs/fix_plan.md §STRAT-VI-001 — current task + FSM metadata to update after artifacts land
- docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family — normative definition of Poisson ELBO / posterior math
- docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md §Adaptive Scaling Definition — authoritative observation-scaling workflow for CLI runs
- scripts/analysis/vi_poisson_diagnostics.py — temperature/IWAE sweep helper & CLI
- scripts/benchmark_vi_mosaic.py — canonical benchmark CLI for conditional IWAE run
- src/nanobrag_torch/vi/poisson_elbo.py — ensures the temperature + IWAE code paths stay in sync with diagnostics
- tests/test_vi_mosaic.py — regression selectors for sweeps + benchmark smoke
Summary:
- Run Task 1: extend likelihood-temperature sweep to include T∈{1,2,4,8} via diagnostics helper, archive artifacts, and capture σ/gradient trends.
- Run Task 2: repeat the sweep with `objective="iwae"`, k=8, summarize log-weight behavior, and only trigger the 150-iter benchmark if diagnostics hit σ ≥ 1.2°.
- Run Task 3: document outcomes in findings + strategy, refresh fix_plan/input, and ensure all mapped tests still pass.
Summary (Goal): Determine whether hotter likelihoods or IWAE+temperature improves VI σ recovery and capture the evidence bundle.
Focus: STRAT-VI-001 — Temperature × IWAE follow-up (Task 21)
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_temperature_sweep_runs_multiple_temperatures -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T213000Z/temperature_sweep_hot/
Next Up (optional):
1. Push IWAE+temperature combo into the full 150-iter benchmark even if σ<1.2° to characterize failure modes.
2. Instrument per-iteration IWAE log weights in docs/strategy if gradients destabilize.
Normative Math/Physics: See docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family (Poisson ELBO, posterior sampling) and docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md §Adaptive Scaling Definition for observation normalization requirements.
