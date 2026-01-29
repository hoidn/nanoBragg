# Engineer Summary — VI Poisson Benchmark (Tasks 5–6)

**Date:** 2026-01-29
**Focus:** STRAT-VI-001, `docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md`
**Branch:** feature/spec-based-2

## What I Did

Executed Tasks 5–6 of the Poisson likelihood rescaling plan:

1. **Task 5 — Canonical benchmark:** Ran `scripts/benchmark_vi_mosaic.py --iterations 150 --fluence 1e13 --observation-seed 321 --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120` on CPU (64x64 detector). Archived PNG/JSON/stats under `plans/active/strat-vi-001/reports/2026-01-29T085512Z/`.

2. **Task 6 — Documentation:** Updated FND-VI-2026-01 in `docs/findings.md`, `docs/strategy/mainstrategy.md` §9, and `docs/fix_plan.md` STRAT-VI-001 with the benchmark outcome.

## Unexpected Finding

The Poisson observation pipeline produced **all-zero observations** (mean_counts=0, max_counts=0). The fluence_scale = 1e13 / BeamConfig().fluence = 7.9e-16. Raw simulator intensities multiplied by this factor round to zero before `torch.poisson`. VI diverged to sigma=7.49 deg (target 2.0 deg); MC reached 1.35 deg.

**Root cause:** The fluence scaling formula assumes raw intensities are proportional to BeamConfig().fluence (~1.26e28), but they are small dimensionless values. The normalization denominator is incorrect.

## Files Changed

- `docs/findings.md` — appended Poisson benchmark result to FND-VI-2026-01
- `docs/strategy/mainstrategy.md` — appended benchmark result and next action to §9
- `docs/fix_plan.md` — updated STRAT-VI-001 Task 12 status and supervisor state
- `plans/active/strat-vi-001/reports/2026-01-29T085512Z/` — new artifact directory with benchmark_fluence_summary.md, vi_observation_stats.json, summary.md, and benchmark/ subdirectory
- `demo_outputs/vi_vs_mc_loss.png` — refreshed
- `demo_outputs/vi_vs_mc_summary.json` — refreshed

## Tests Run

- `test_benchmark_script_smoke` PASSED
- `test_vi_diagnostics_snapshot` PASSED

## Blockers

- **Blocker:** Fluence scaling formula in `observation_utils.py` needs correction — normalize intensities to actual range before applying target count level. Supervisor state set to `blocked` with `next_action=fix_fluence_scaling_formula`.
