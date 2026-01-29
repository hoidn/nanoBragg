Summary: Implement Task 3 of STRAT-PROB-003 by swapping the Gaussian width to the Δθ formulation, extending diagnostics, and adding hi_res_b regression + gradient tests.
Focus: STRAT-PROB-003 — Probabilistic gradient recovery
Branch: feature/spec-based-2
Mapped tests: pytest -k "probabilistic_simulator or probabilistic_gradients" -v; pytest tests/scripts/test_probabilistic_gaussian_diag.py -v
Artifacts: plans/active/strat-prob-003/reports/2026-01-29T070535Z/
Next Up: 1) refresh hi_res_b JSON/markdown after kernel update 2) rerun benchmark hi_res_b/hi_res_c per Task 4
