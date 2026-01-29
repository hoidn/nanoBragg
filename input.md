Plan: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md (Task 4)
References: docs/strategy/mainstrategy.md §4 & §8; docs/plans/2026-01-29-vi-mosaic-design.md §Architecture Plan; docs/development/testing_strategy.md §1.4; scripts/benchmark_probabilistic.py (pattern + CLI expectations); tests/test_vi_mosaic.py (add new benchmark smoke test)
Summary: Implement Task 4 by creating scripts/benchmark_vi_mosaic.py with MC vs analytic vs VI comparison, seeded reproducibility, JSON+PNG artifacts, and a reusable run_benchmark() entry point plus matching documentation updates.
Summary (Goal): Land the VI benchmark script + docs so we can evidence VI replacing analytic mosaicity.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -q
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T081720Z/
Next Up: 1) Deprecate analytic ProbabilisticSimulator once VI validated 2) Update README_PYTORCH with VI-first guidance
