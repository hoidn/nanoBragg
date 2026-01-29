# Engineer Summary — VI Poisson Likelihood Rescaling (Tasks 1–4)

**Date:** 2026-01-29
**Focus:** STRAT-VI-001, `docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md`
**Branch:** feature/spec-based-2

## What I Did

Executed Tasks 1–4 of the Poisson likelihood rescaling plan:

1. **Task 1 — Observation sampling utilities:** Created `src/nanobrag_torch/vi/observation_utils.py` with `poisson_sample_observations()` that scales simulator intensities by a fluence factor and draws deterministic Poisson counts. Added two unit tests.

2. **Task 2 — Benchmark wiring:** Updated `scripts/benchmark_vi_mosaic.py` with `--fluence` and `--observation-seed` CLI flags. Ground truth is Poisson-sampled when fluence is provided; `observations` metadata included in summary JSON. Updated smoke test to validate.

3. **Task 3 — Diagnostics wiring:** Updated `scripts/analysis/vi_poisson_diagnostics.py` with matching CLI flags. Per-record metadata (`observation_seed`, `observation_mean_counts`, `observation_max_counts`) logged. Updated beta schedule test to validate.

4. **Task 4 — Documentation:** Updated FND-VI-2026-01 in `docs/findings.md` with observation scale bug, `docs/strategy/mainstrategy.md` §9 with Poisson observation pipeline description, and `docs/fix_plan.md` item 12 + supervisor state.

## Files Changed

- **Created:** `src/nanobrag_torch/vi/observation_utils.py`
- **Modified:** `scripts/benchmark_vi_mosaic.py`, `scripts/analysis/vi_poisson_diagnostics.py`, `tests/test_vi_mosaic.py`, `docs/findings.md`, `docs/strategy/mainstrategy.md`, `docs/fix_plan.md`, `engineer_summary.md`
- **Created dir:** `plans/active/strat-vi-001/reports/2026-01-29T084456Z/`

## Tests Run

All 5 mapped tests pass:
- `test_benchmark_script_smoke` ✅
- `test_vi_diagnostics_beta_schedule` ✅
- `test_poisson_observation_helper_reproducible` ✅
- `test_poisson_observation_helper_mean_matches_lambda` ✅
- `test_vi_diagnostics_snapshot` ✅

## Blockers / Open Questions

- **Remaining:** Run canonical benchmark with `--fluence 1e13` and archive artifacts to confirm σ recovery. This is a long-running benchmark not executed in this turn. Supervisor should schedule as next action.
