# Phase D2 Regression Test Summary — Source Weighting

**Timestamp:** 2025-10-11T09:18:44Z
**Environment:** CPU-only (`CUDA_VISIBLE_DEVICES=-1`)
**Command:** `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ --maxfail=5`

---

## Test Results

| Metric | Count |
|--------|-------|
| **Total Tests** | 367 (collected 687, 57 skipped at collection) |
| **Passed** | 305 |
| **Failed** | 5 |
| **Skipped** | 57 |
| **Errors** | 0 |
| **Warnings** | 6 |
| **Runtime** | 122.96s (2m 02s) |

**Pass Rate:** 305/367 = 83.1%
**Failure Rate:** 5/367 = 1.4%

---

## Failures (5 Total)

### 1. `test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`
**Error Type:** AssertionError
**Root Cause:** Zero maximum intensity (expected > 0)
**Location:** `tests/test_at_parallel_015.py`

### 2. `test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`
**Error Type:** AttributeError
**Root Cause:** `'NoneType' object has no attribute 'get_pixel_coords'` (detector is None)
**Location:** `src/nanobrag_torch/simulator.py:569`

### 3. `test_at_src_001_simple.py::test_sourcefile_parsing`
**Error Type:** AssertionError
**Root Cause:** Unknown (test stopped at --maxfail=5)

### 4. `test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model`
**Error Type:** Unknown
**Root Cause:** Test stopped at --maxfail=5

### 5. `test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_shape_model_comparison`
**Error Type:** Unknown
**Root Cause:** Test stopped at --maxfail=5

---

## Source-Weighting Specific Tests

### AT-SRC-001 Tests
- `test_at_src_001.py` — **NOT FULLY RUN** (maxfail limit reached)
- `test_at_src_001_simple.py` — **FAILED** (1 failure)

**Status:** Source-weighting regression incomplete due to --maxfail=5 cutoff.

---

## Warnings

1. **Unknown pytest mark:** `pytest.mark.parallel_validation` (2 occurrences in `test_at_parallel_026.py`)
2. **Unknown pytest mark:** `pytest.mark.requires_c_binary` (1 occurrence)
3. **DeprecationWarning:** `__array_wrap__` NumPy 2.0 deprecation (3 occurrences in `test_at_crystal_absolute.py`)
4. **UserWarning:** Sourcefile wavelength column differs from CLI `-lambda` value (1 occurrence in `test_at_src_001.py:51`)

---

## Key Observations

1. **Source-weighting cluster (C3) NOT cleared:** Cannot confirm C3 resolution because full suite stopped early at 5 failures. Need to rerun without `--maxfail=5` or fix the blocking failures first.

2. **Regression introduced:** `test_at_parallel_026.py` fails with `detector=None` AttributeError. This test was **NOT** in the baseline Phase K analysis, suggesting a **new regression** introduced since then.

3. **Pre-existing failures:** Several failures appear unrelated to source-weighting (mixed units, lattice shape models).

4. **Test collection:** 687 tests collected, but only 367 executed before hitting failure limit.

---

## Next Steps

### Option A: Run Full Suite (no maxfail)
Execute `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/` to capture complete failure count and identify all source-weighting test outcomes.

### Option B: Fix Blocking Failures First
1. Investigate `test_at_parallel_026.py` detector=None regression
2. Fix `test_at_src_001_simple.py::test_sourcefile_parsing` failure
3. Rerun regression after fixes

### Option C: Targeted AT-SRC-001 Run
Execute `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py` without maxfail to isolate source-weighting outcomes.

---

## Artifact Locations

- **JUnit XML:** `artifacts/pytest_full.xml` (84K, 367 testcases)
- **Environment:** `env/torch_env.txt`, `env/pip_freeze.txt`
- **This Summary:** `logs/summary.md`
- **Raw Output:** Console log above (not saved to file due to directory creation failure during tee)

---

## Conclusion

**Phase D2 regression run INCOMPLETE.** The `--maxfail=5` flag stopped execution before AT-SRC-001 suite fully ran. **Cannot confirm C3 cluster resolution** without complete test run. Recommend Option C (targeted AT-SRC-001 run) to validate source-weighting fixes independently, followed by full-suite run to update global failure count.

**Estimated C3 Impact:** Unknown (requires full suite run or targeted AT-SRC-001 execution).
