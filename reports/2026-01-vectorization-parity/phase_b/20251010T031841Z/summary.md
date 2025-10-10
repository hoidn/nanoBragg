# Phase B2 Parity Selector Summary

- Prior benchmark bundle: reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/summary.md
- pytest command: KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_*.py -k 4096

## Results

- Exit status: 5 (no tests collected)
- Collection result: 128 items collected, 128 deselected, 0 selected
- Notable outputs: NO tests matched the '4096' selector

## Analysis

The pytest selector `-k 4096` did not match any test functions in the AT-PARALLEL suite.

Investigation revealed:
- Only reference to 4096 is in `tests/test_at_parallel_012.py::test_high_resolution_variant`
- This test is marked with `@pytest.mark.skip(reason="High-resolution variant requires large memory and golden data generation")`
- Test docstring describes 4096×4096 detector requirement but is not executable

## Conclusion

**There is no authoritative 4096² pytest parity test currently active in the test suite.**

The vectorization parity regression is detected by:
- `scripts/benchmarks/benchmark_detailed.py` (correlation ~0.721)
- `nb-compare` tool (correlation ~0.060, sum_ratio ~225-236x)

But NOT by any pytest-based acceptance test.

## Thresholds

- Target thresholds: correlation ≥0.999, |sum_ratio−1| ≤5e-3 (specs/spec-a-core.md:151-155)
- Current state: No pytest baseline exists for 4096² detector size

## Next Actions

Phase B2 is BLOCKED by missing test infrastructure:
1. Either un-skip and implement `test_high_resolution_variant` with golden data generation
2. OR add a new parametrized parity case to `tests/parity_cases.yaml` for 4096² detector
3. OR acknowledge that 4096² validation relies on benchmark/nb-compare tools only (not pytest)

For now, Phase B2 evidence shows: **pytest suite has no active 4096² parity validation**.
The regression remains documented via Phase B1 benchmark artifacts only.
