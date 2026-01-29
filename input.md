Summary: Build and land the probabilistic benchmark workflow (scripts/benchmark_probabilistic.py + docs) to prove the analytic kernel wins outlined in docs/strategy/mainstrategy.md §4 and docs/plans/2026-01-29-probabilistic-simulator-implementation.md Task 3.
Focus: STRAT-PROB-002 — Probabilistic benchmark artifacts
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_probabilistic_simulator.py
Artifacts: plans/active/strat-prob-002/reports/2026-01-29T061003Z/
Next Up (optional): STRAT-PROB-001 — CUDA log capture for gradcheck evidence once benchmark artifacts are merged.
