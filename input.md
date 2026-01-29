Summary: Deliver the analytic ProbabilisticSimulator kernel plus regression/gradcheck coverage per docs/strategy/mainstrategy.md §§2–4 and the new implementation plan.
Focus: STRAT-PROB-001 — ProbabilisticSimulator kernel
Branch: feature/spec-based-2
Mapped tests:
- none — first Do Now step is to author `tests/test_probabilistic_simulator.py` (per docs/plans/2026-01-29-probabilistic-simulator-implementation.md Task 1) and run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_probabilistic_simulator.py` to capture the new selector before implementation.
Artifacts: plans/active/strat-prob-001/reports/2026-01-29T060113Z/
Next Up (optional): STRAT-PROB-002 — Probabilistic benchmark artifacts once the kernel + tests are green.
