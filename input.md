Summary: Execute the hi-res probabilistic benchmark realignment plan (docs/plans/2026-01-29-probabilistic-benchmark-realignment.md) so scripts/benchmark_probabilistic.py gains scenario presets, gradient diagnostics, and ≥4× speedup evidence per docs/strategy/mainstrategy.md §4.
Focus: STRAT-PROB-002 — Probabilistic benchmark artifacts
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest -k benchmark_probabilistic_cli -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_probabilistic_simulator.py
- KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmark_probabilistic.py --iterations 100 --device cpu --scenario hi_res_b --diagnose-gradients
Artifacts: plans/active/strat-prob-002/reports/2026-01-29T062136Z/
Next Up (optional): STRAT-PROB-001 — CUDA log capture for gradcheck evidence after the benchmark uplifts land.
