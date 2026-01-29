Plan: docs/plans/2026-01-29-vi-observation-scale-parity.md
References:
- docs/strategy/mainstrategy.md §9 — canonical VI benchmark success criteria & narrative that must cite the new run
- docs/findings.md (FND-VI-2026-01) — collapse record to amend once scaled benchmark results are known
- docs/plans/2026-01-29-vi-observation-scale-parity.md §Task 4–5 — canonical benchmark rerun + documentation updates workflow
- docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md §Adaptive Scaling Definition — normative description of observation scaling metadata
- docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family — definitive Poisson ELBO/mosaic posterior equations for citing in docs
- docs/fix_plan.md §STRAT-VI-001 — supervisor state + exit criteria to refresh once evidence lands
- scripts/benchmark_vi_mosaic.py — canonical 150-iteration benchmark CLI for VI/MC/analytic comparison
- demo_outputs/vi_vs_mc_*.{png,json} — public artifacts that must be replaced with the scaled run outputs
Summary:
- Follow Task 4 of the observation-scale parity plan: capture observation metadata, run the 150-iteration `scripts/benchmark_vi_mosaic.py` command with adaptive scaling + KL warmup, and stash diagnostics plus PNG/JSON outputs under a fresh timestamped `plans/active/strat-vi-001/reports/.../scale_parity/` directory.
- Copy the refreshed PNG/JSON into `demo_outputs/`, summarize sigma/log-likelihood metrics, and document the applied `observation_scale` so we can compare against the Poisson counts.
- Execute Task 5 after the run succeeds: update `docs/findings.md`, `docs/strategy/mainstrategy.md §9`, `docs/fix_plan.md`, and the plan report with the new evidence, clearly stating whether σ≥1.5° was achieved and what the next mitigation is if not.
Summary (Goal): Run and archive the scaled canonical VI benchmark, then propagate the results through findings/strategy/fix-plan documentation.
Focus: STRAT-VI-001 — Variational mosaic simulator (Task 17 observation scale parity)
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_observation_scale_matches_manual_loglik -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T193000Z/scale_parity/
Next Up (optional): If the scaled run still collapses, pivot to docs/plans/2026-01-29-vi-elbo-decomposition.md §Task 3 (non-centered posterior) for the next engineer slot.
Normative Math/Physics: Reference docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family for the Poisson ELBO form and docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md §Adaptive Scaling Definition for the observation scaling equation instead of paraphrasing.
