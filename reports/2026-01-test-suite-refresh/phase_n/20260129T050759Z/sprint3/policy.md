# Sprint 3 — Slow-Gradient Chunk Policy

**STAMP:** 20260129T050759Z
**Cluster:** GRAD-001

## Background

Phase P/Q/R evidence (905s tolerance, baseline ~845s) established that
`test_property_gradient_stability` routinely runs 14+ minutes on CPU with
float64 precision and compile guard enabled. Under full-suite load, thermal
throttling and memory pressure push runtime past the 905s ceiling, causing
spurious timeout failures (observed in Phases E, G, L).

## Policy

Slow-gradient tests (decorated `@pytest.mark.slow_gradient`) are **skipped
by default**. They execute only when explicitly opted in via:

- **CLI flag:** `--run-slow-gradient-chunk`
- **Env var:** `NB_RUN_SLOW_GRADIENT=1`

Both mechanisms are registered in `tests/conftest.py` via `pytest_addoption`
and `pytest_collection_modifyitems`.

## Recommended Workflow

1. **Dedicated chunk (before main suite):**
   ```bash
   env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
     NB_RUN_SLOW_GRADIENT=1 pytest -vv \
     tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability \
     --run-slow-gradient-chunk --maxfail=1 --durations=25
   ```

2. **Full suite (slow gradients skipped):**
   ```bash
   timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
     NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" \
     pytest -vv tests/
   ```

## References

- `docs/development/testing_strategy.md` §4.1
- `docs/development/pytorch_runtime_checklist.md` §3, §5
- Phase R uplift: `reports/2026-01-test-suite-triage/phase_r/` (905s ceiling)
- Phase Q validation: 839.14s runtime confirmed
