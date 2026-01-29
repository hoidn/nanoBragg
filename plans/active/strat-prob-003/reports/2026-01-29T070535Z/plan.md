# STRAT-PROB-003 Task 3 Execution Plan

> Mirrors docs/plans/2026-01-29-probabilistic-gradient-recovery.md §Task 3.

1. **Update spec** — edit docs/plans/2026-01-29-probabilistic-simulator-design.md to replace the sigma paragraph with the Δθ-based formula (reference hi_res_b diagnostics and FND-PROB-2026-01).
2. **Kernel refactor** — in src/nanobrag_torch/simulators/probabilistic.py compute G = h0*a* + k0*b* + l0*c*, derive g_norm + delta_theta, replace gaussian envelope with exp(-0.5*(delta_theta/spread)^2), and extend diag_recorder payload with delta_theta + g_norm (keep sigma_q for ratio stats).
3. **Diagnostics script + tests** — update scripts/analysis/probabilistic_gaussian_diagnostics.py to record the new stats and recompute the FD gradient, refresh tests/scripts/test_probabilistic_gaussian_diag.py assertions.
4. **Regression coverage** — add the hi_res_b spread-intensity regression test plus the new tests/test_probabilistic_gradients.py (double precision ≥1e-4 gradient magnitude).
5. **Test sweep** — run `KMP_DUPLICATE_LIB_OK=TRUE pytest -k "probabilistic_simulator or probabilistic_gradients" -v` and `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/scripts/test_probabilistic_gaussian_diag.py -v`; stash logs in this report folder.
