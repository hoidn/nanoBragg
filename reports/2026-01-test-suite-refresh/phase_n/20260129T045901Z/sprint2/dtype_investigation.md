# Sprint 2: CLUSTER-VEC-001 dtype Investigation

**STAMP:** 20260129T045901Z
**Cluster:** VEC-001 (dtype mismatch in tricubic vectorized tests)

## Original Failure

When `test_at_parallel_013.py::test_pytorch_determinism_same_seed` runs before
`test_tricubic_vectorized.py`, the global default dtype is left as `torch.float64`.
Tricubic gather tests then create internal tensors via `torch.zeros(...)` (which
inherit the global default) producing float64 tensors that clash with explicit
float32 inputs, causing:

```
RuntimeError: Float did not match Double
```

**Phase M cluster mapping reference:**
`reports/2026-01-test-suite-refresh/phase_m/20251015T201831Z/analysis/cluster_mapping.md`

## Root Cause

AT-PARALLEL-013 calls `torch.set_default_dtype(torch.float64)` to exercise
determinism under float64 but does not restore the previous dtype. This is
global mutable state that leaks across test modules when pytest collection
order places AT-PARALLEL-013 before the tricubic module.

## Fix Applied

1. **Autouse fixture `reset_default_dtype`** (module-level, `tests/test_tricubic_vectorized.py`):
   Forces `torch.float32` before each test and restores the previous dtype after.
   Covers both `TestTricubicGather` and `TestTricubicPoly` classes.

2. **Regression test `test_vectorized_respects_float32_when_global_dtype_changes`**:
   Explicitly sets float64, calls `_tricubic_interpolation` with float32 inputs,
   and asserts the output is float32. Proves the guard works.

## Evidence

- **17/17 tests passed** in full module run (`pytest -vv tests/test_tricubic_vectorized.py`)
- Root-cause demo: AT-PARALLEL-013 runs first (sets float64), then tricubic
  `test_vectorized_matches_scalar` passes (guard resets to float32).
- Logs: `pytest_at013.log`, `pytest_vec.log`

## Guidance for Future Contributors

Tests that manipulate `torch.set_default_dtype` MUST restore it in a `finally`
block or use a fixture. The `reset_default_dtype` autouse fixture in this module
provides a safety net, but the root cause (AT-PARALLEL-013 leaking dtype state)
should ideally be fixed at the source as well.

Per `docs/development/testing_strategy.md` section 1.4: all test modules touching
dtype should be dtype-neutral and not depend on global state.

## Finding

No new finding added to `docs/findings.md`. The principle (tests must reset
global dtype after manipulating it) is already captured under existing CONVENTION
entries and the testing strategy dtype discipline section. This investigation
confirms the existing guidance is correct but was not followed by AT-PARALLEL-013.
