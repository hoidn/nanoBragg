Plan: docs/plans/2026-01-29-vi-flow-posterior.md
References:
- docs/strategy/mainstrategy.md §9 — canonical VI benchmark gate + remaining mitigation options
- docs/plans/2026-01-29-vi-flow-posterior.md — task-by-task instructions for flow posterior + evidence capture
- docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family — normative ELBO/posterior math
- docs/findings.md (FND-VI-2026-01 family) — baseline σ collapse and success criteria to update
- docs/development/testing_strategy.md §1.4 — device/dtype + logging guardrails for PyTorch workflows
- src/nanobrag_torch/vi/mosaic_posterior.py & src/nanobrag_torch/vi/__init__.py — integration points for new parameterization
- scripts/analysis/vi_poisson_diagnostics.py & scripts/benchmark_vi_mosaic.py — CLI surfaces for new knobs + evidence capture
Summary:
- Task 1: add `src/nanobrag_torch/vi/flows.py` with 1D affine coupling + flow chain modules, export via `vi/__init__.py`, and write targeted pytest coverage proving invertibility + gradient flow.
- Task 2: integrate the new "flow" parameterization into `MosaicPosterior` (log-σ base + flow transform, Monte-Carlo KL fallback, log_prob helpers) with gradcheck-style tests exercising sampling/log_prob.
- Task 3: surface flow options through `VariationalMosaicSimulator`, diagnostics + benchmark CLIs, and add pytest smoke asserting CLI arguments and metadata wiring.
- Task 4: run flow vs log-normal diagnostics plus the 150-iter canonical benchmark, archive artifacts under `plans/active/strat-vi-001/reports/2026-01-29T235900Z/flow_{diagnostics,benchmark}/`, and update docs/findings/strategy/fix_plan/input once evidence lands (σ≥1.5° or documented failure + next steps).
Summary (one sentence): Implement and evaluate the VI normalizing-flow posterior end-to-end so we can determine if added expressiveness recovers σ≥1.5° on the canonical benchmark.
Focus: STRAT-VI-001 — Task 26 flow posterior / hybrid pathfinding
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "coupling" -v  # new flow module tests (author per plan before running)
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "flow_parameterization" -v  # new posterior integration tests
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v  # existing CLI guard
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T235900Z/{flow_dev/,flow_diagnostics/,flow_benchmark/}
Next Up (optional):
1. If flow posterior still collapses (<1.5°), draft hybrid MC-VI mitigation plan per fix_plan Task 26 exit criteria.
2. If flow succeeds, schedule doc/README updates to make flow the default posterior.
Normative Math/Physics: Reference `docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family` for posterior sampling equations and `docs/strategy/mainstrategy.md §9` for σ thresholds + ELBO interpretation while implementing/testing.
