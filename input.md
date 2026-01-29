Plan: docs/plans/2026-01-29-vi-observation-scale-parity.md
References:
- docs/strategy/mainstrategy.md §9 — canonical VI benchmark expectations & narration that must be updated
- docs/findings.md (FND-VI-2026-01) — documented collapse symptoms to be amended with new evidence
- docs/plans/2026-01-29-vi-elbo-decomposition.md §Task 2 — observation diagnostics context
- docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family — normative ELBO/likelihood definitions
- scripts/analysis/vi_poisson_diagnostics.py — diagnostics harness to update with scaling metadata
- scripts/benchmark_vi_mosaic.py — canonical benchmark wiring for MC/analytic/VI
- src/nanobrag_torch/vi/poisson_elbo.py — ELBO implementation to accept observation_scale and record diagnostics
- tests/test_vi_mosaic.py — regression + CLI tests to extend for scaling support
Summary:
- Add explicit `observation_scale` handling to `poisson_elbo`/diagnostics/benchmark flows so MC, analytic, and VI paths operate on the scaled counts returned by `poisson_sample_observations()`.
- Ensure diagnostics + observation sweep JSON/markdown capture the applied scale and that MC/analytic loss functions multiply predictions before comparing to Poisson counts.
- Re-run the canonical 150-iteration VI benchmark with adaptive scaling, archive artifacts under the new timestamp, and update docs/fix_plan once results are collected.
Summary (one-liner): Enforce observation-scale parity throughout the VI ELBO stack and capture a refreshed benchmark run with the corrected scaling.
Focus: STRAT-VI-001 — Variational mosaic simulator (Task 17 observation scale parity)
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_observation_scale_matches_manual_loglik -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_diagnostics_beta_schedule -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T181200Z/scale_parity/
Next Up (optional): Once parity work is green, re-run the observation-count sweep with scaled ELBOs to confirm gradient ratios remain consistent.
Normative Math/Physics: See docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family for the definitive Poisson ELBO and mosaic posterior equations.
