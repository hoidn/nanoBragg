Plan: docs/plans/2026-01-29-vi-prior-geometry.md §Tasks 3-4
References:
- docs/strategy/mainstrategy.md §9 — authoritative VI readiness criteria + prior-schedule context
- docs/plans/2026-01-29-vi-prior-geometry.md — canonical commands + artifact layout for detector sweeps & prior benchmark
- docs/findings.md (FND-VI-2026-01 family) — baseline collapse evidence you must extend with new data
- docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family — normative posterior/ELBO math for σ interpretations
- docs/development/testing_strategy.md §1.4 — device/dtype + logging expectations for PyTorch runs
- scripts/analysis/vi_poisson_diagnostics.py & scripts/benchmark_vi_mosaic.py — CLIs to execute for diagnostics/benchmark
Summary:
- Execute Task 3 detector sweeps exactly as specified: create `plans/active/strat-vi-001/reports/2026-01-29T113030Z/prior_schedule/{32x32,64x64,128x128}`, run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/analysis/vi_poisson_diagnostics.py ... --prior-*` for each size, tee stdout into each folder, and write `summary.md` capturing σ trajectories, gradient-ratio trends, and whether informative priors delay collapse.
- Parse each `vi_diagnostics.json` to extract σ_max, σ_last, mu/rho gradient norms, and append the findings (with artifact paths) to `docs/findings.md` under FND-VI-2026-01 plus `docs/strategy/mainstrategy.md §9` so the strategy reflects the new evidence.
- For Task 4 choose the detector/prior combo with the best σ from Task 3, run the 150-iter benchmark into `plans/active/strat-vi-001/reports/2026-01-29T113030Z/prior_benchmark/` (archive CLI log, PNG, JSON, summary.md), and update `docs/fix_plan.md` + docs/strategy/findings with the pass/fail result relative to the ≥1.5° σ criterion.
Summary (one sentence): Run the prior-schedule multi-geometry diagnostics and canonical benchmark to determine if informative priors recover VI σ ≥ 1.5°.
Focus: STRAT-VI-001 — Task 24 prior schedule + multi-geometry diagnostics (Steps 3–4)
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_diagnostics_records_prior_schedule -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T113030Z/{prior_schedule/,prior_benchmark/}
Next Up (optional):
1. If σ still collapses, draft mitigation options (e.g., detector slicing or posterior flows) under docs/plans.
2. If benchmark succeeds, prep docs/strategy updates to redefine VI readiness criteria and schedule follow-on sweeps.
Normative Math/Physics: Cite docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family whenever interpreting posterior math, and reference docs/strategy/mainstrategy.md §9 when discussing σ thresholds or benchmark exit criteria.
