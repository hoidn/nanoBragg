Plan: docs/plans/2026-01-29-vi-flow-posterior.md
References:
- docs/strategy/mainstrategy.md §9 — benchmark success criteria + mitigation decision tree (flow vs hybrid)
- docs/plans/2026-01-29-vi-flow-posterior.md — Task 4 commands for diagnostics/benchmark artifacts
- plans/active/strat-vi-001/reports/2026-01-29T122511Z/flow_diagnostics/vi_diagnostics_summary.md — current flow-only evidence showing σ blow-up then collapse
- demo_outputs/vi_vs_mc_summary.json — latest canonical run configured with `posterior_parameterization="flow"`
- docs/findings.md (FND-VI-2026-01 family) — baseline collapse history + sections to update once flow evaluation lands
- docs/development/testing_strategy.md §1.4 — runtime guardrails for running diagnostics/benchmarks on CPU w/ `KMP_DUPLICATE_LIB_OK`
Summary:
- Re-run the observation sweep in `scripts/analysis/vi_poisson_diagnostics.py` for both `posterior_parameterization=flow` and `log_normal` (25 iters, 32×32 detector, obs_mean=25, k=4) and archive `{flow.json, baseline.json, summary.md}` under `plans/active/strat-vi-001/reports/2026-01-29T235959Z/flow_diagnostics/` comparing σ trajectories + gradient ratios.
- Execute the canonical 150-iter benchmark with the flow posterior (`--posterior-flow-layers 4 --posterior-flow-hidden 32 --k-samples 4 --observation-mean 25 --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120 --prior-spread-start 2.0 --prior-spread-end 0.5 --prior-warmup-steps 120`) and store the console log, PNG, and `vi_vs_mc_summary.json` under `.../flow_benchmark/` (copy artifacts to `demo_outputs/` too).
- Update `docs/findings.md` (FND-VI-2026-01) and `docs/strategy/mainstrategy.md §9` with the new flow-vs-log-normal evidence plus the conclusion (still collapses or ≥1.5° success), then refresh `docs/fix_plan.md` + this `input.md` with the recorded outcome and next mitigation decision (hybrid MC-VI if flow fails).
Summary (one sentence): Capture the missing flow-vs-log-normal diagnostics + 150-iter benchmark artifacts and propagate the go/no-go decision through findings, strategy, and fix_plan so Task 26 can close or escalate to the hybrid plan.
Focus: STRAT-VI-001 — Task 26 flow posterior / hybrid pathfinding
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "flow_parameterization or coupling" -v  # ensures flow modules & posterior sampling tests still pass
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v  # guard the CLI plumbing used for diagnostics/benchmark commands
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T235959Z/{flow_diagnostics/,flow_benchmark/,summary.md}
Next Up (optional):
1. If flow still collapses, draft the hybrid MC-VI mitigation plan (new `docs/plans/2026-01-29-vi-hybrid-mc-vi.md`) and register its fix-plan entry.
2. If flow succeeds, update README_PYTORCH + CLI docs to make the flow posterior the recommended VI configuration.
Normative Math/Physics: See `docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family` for the log-normal/log-σ flow sampling equations and `docs/strategy/mainstrategy.md §9` for the ≥1.5° benchmark criterion while interpreting diagnostics.
