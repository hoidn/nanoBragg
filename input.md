Plan: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md
References:
- docs/strategy/mainstrategy.md §8 (VI replacement context)
- docs/plans/2026-01-29-vi-mosaic-implementation-plan.md §Task 5 (deprecation steps)
- docs/plans/2026-01-29-probabilistic-simulator-design.md (analytic simulator spec)
- README_PYTORCH.md §Probabilistic Mosaic Benchmark (user-facing guidance)
- docs/development/testing_strategy.md §6.0.1 (benchmark + env contract)
- src/nanobrag_torch/simulators/probabilistic.py (warning insertion point)
- tests/test_vi_mosaic.py (VI suite housing the new warning test)
Summary:
- Land Task 5 from the VI plan: add a deterministic DeprecationWarning on ProbabilisticSimulator construction so users know the analytic mosaic flow is legacy, cover it with a targeted pytest, and refresh the README + design doc sections to steer people toward the VI path.
Summary: Emit a DeprecationWarning for ProbabilisticSimulator and update docs/tests so VI is the endorsed mosaic workflow.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped tests: none — author tests/test_vi_mosaic.py::test_probabilistic_simulator_deprecated_warning first and capture a collect-only log once it exists.
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T075217Z/
Next Up: (1) If warning plumbing proves noisy, add opt-out flag per docs/prompt; (2) Update README_PYTORCH quickstart mosaic section once docs settle.
