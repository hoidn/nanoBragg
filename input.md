Plan: docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md
References:
- docs/strategy/mainstrategy.md §9 (VI benchmark + Poisson ELBO context)
- docs/findings.md (FND-VI-2026-01 observation-scale notes)
- docs/fix_plan.md (STRAT-VI-001 status, Tasks 7–9)
- docs/plans/2026-01-29-vi-mosaic-implementation-plan.md §Model Definition (normative Poisson ELBO math)
- src/nanobrag_torch/vi/observation_utils.py
- scripts/benchmark_vi_mosaic.py
- scripts/analysis/vi_poisson_diagnostics.py
- tests/test_vi_mosaic.py
Summary:
- Implement Tasks 7–9 of the Poisson likelihood rescaling plan: add adaptive observation scaling in `observation_utils`, thread the new controls/metadata through the benchmark + diagnostics CLIs, then rerun the canonical VI benchmark and refresh docs/artifacts so observation counts carry signal again.
Summary (1-liner): Restore VI Poisson benchmarks by auto-normalising simulator intensities before sampling counts and regenerating evidence.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped Tests:
- pytest tests/test_vi_mosaic.py::test_poisson_observation_helper_auto_scale_hits_target_mean -v
- pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v
- pytest tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T100500Z/
Next Up (optional):
- If benchmark still stalls <1.5°, capture extra diagnostics on observation stats vs gradients for FND-VI-2026-01.
