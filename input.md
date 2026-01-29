Plan: docs/plans/2026-01-29-vi-canonical-benchmark-refresh.md
References:
- docs/strategy/mainstrategy.md §9 (Canonical VI benchmark expectations + ELBO context)
- docs/findings.md (FND-VI-2026-01 observation-scale + benchmark gap)
- docs/fix_plan.md (STRAT-VI-001 status, Tasks 7–9 + new execution plan reference)
- docs/plans/2026-01-29-vi-mosaic-implementation-plan.md §Model Definition (normative Poisson ELBO math)
- docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md (background on adaptive scaling + diagnostics)
- scripts/benchmark_vi_mosaic.py, scripts/analysis/vi_poisson_diagnostics.py
- src/nanobrag_torch/vi/observation_utils.py, tests/test_vi_mosaic.py
Summary:
- Follow `docs/plans/2026-01-29-vi-canonical-benchmark-refresh.md` to re-run the 150-iteration VI benchmark with the adaptive observation scaling, capture observation statistics + diagnostics, refresh demo artifacts, and update docs/findings/fix-plan with the measured σ trajectory (per `docs/plans/2026-01-29-vi-mosaic-implementation-plan.md §Model Definition` and strategy §9).
- Archive `vi_vs_mc_loss.png`, `vi_vs_mc_summary.json`, `vi_observation_stats.json`, observation-scale logs, and diagnostics JSON under the new artifacts timestamp plus `demo_outputs/`, then summarize whether σ≥1.5° and what follow-up is needed for FND-VI-2026-01.
- After the run, refresh `docs/findings.md`, `docs/strategy/mainstrategy.md`, and `docs/fix_plan.md` so STRAT-VI-001 reflects the new evidence; regenerate `plans/active/strat-vi-001/reports/<ts>/benchmark_fluence_summary.md` + `summary.md`, and keep canonical CLI tests (`tests/test_vi_mosaic.py`) green.
Summary (1-liner): Reproduce the canonical VI benchmark with adaptive Poisson scaling, archive the full evidence bundle, and update docs/fix-plan with the observed σ outcome.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped Tests:
- pytest tests/test_vi_mosaic.py::test_poisson_observation_helper_auto_scale_hits_target_mean -v
- pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v
- pytest tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T104900Z/
Next Up (optional):
- If σ still <1.5°, extend diagnostics (per FND-VI-2026-01) to log likelihood vs KL curves for mid-iteration slices.
