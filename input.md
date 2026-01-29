Plan: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md
References:
- docs/strategy/mainstrategy.md §8 (VI roll-out status + analytic deprecation context)
- docs/plans/2026-01-29-vi-mosaic-implementation-plan.md §Task 5 (warning + doc requirements)
- docs/fix_plan.md §STRAT-VI-001 (current next-action + evidence path)
- README_PYTORCH.md §Mosaic Modelling (user-facing VI vs analytic guidance)
- tests/test_vi_mosaic.py::test_probabilistic_simulator_deprecated_warning (targeted warning guard)
Summary:
- Capture a CPU pytest log for the new `ProbabilisticSimulator` deprecation guard, stash it under the active STRAT-VI-001 artifacts directory, and ensure the warning fires exactly once so the fix-plan exit criteria have evidence.
Summary: Run the new DeprecationWarning guard test and archive its log under STRAT-VI-001.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped tests:
- pytest tests/test_vi_mosaic.py::test_probabilistic_simulator_deprecated_warning -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T075930Z/
Next Up: (1) rerun `pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke` to refresh the VI benchmark artifact bundle if time allows
