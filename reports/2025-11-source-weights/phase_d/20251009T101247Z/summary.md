# Phase D Parity Evidence - 2025-10-09T10:12:47Z

## Command Sequence

All commands recorded in `commands.txt`.

### 1. Test Collection
```bash
pytest --collect-only -q
```
Result: Exit 0, ~600 tests collected

### 2. Parity Test
```bash
NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE \
  pytest tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c -v
```
Result: **PASSED** (1 passed in 5.56s)

### 3. C CLI Run
```bash
./golden_suite_generator/nanoBragg -mat A.mat -floatfile cli/c_weight.bin \
  -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt \
  -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 \
  -oversample 1 -nonoise -nointerpolate
```
Result: Exit 0

### 4. PyTorch CLI Run
```bash
KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat A.mat -floatfile cli/py_weight.bin \
  -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt \
  -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 \
  -oversample 1 -nonoise -nointerpolate
```
Result: Exit 0

## Metrics

From `metrics.json`:

- **Correlation**: -0.060618828347
- **Sum Ratio (Py/C)**: 546.57×
- **C Total**: 4.633873e+02
- **Py Total**: 2.532718e+05
- **C Max**: 0.009050
- **Py Max**: 168.443649

## Analysis

**CRITICAL DIVERGENCE DETECTED:**

The CLI runs show a 546× intensity mismatch between C and PyTorch, with near-zero (negative) correlation. However, the pytest parity test passed, indicating the test fixture uses different parameters or test methodology than the CLI comparison.

This suggests:
1. The test may be using equal weights (not exercising weighted-source logic)
2. The test may normalize intensities differently
3. The CLI runs may have different default parameters

## Next Actions

1. Inspect test fixture at `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`
2. Compare test parameters with CLI parameters
3. Check if `-oversample 1` is correctly applied (known issue from prior attempts)
4. Review C and PyTorch stdout logs for parameter echo

## Artifacts

- `commands.txt`: Timestamped command log
- `pytest/pytest.log`: Parity test output (PASSED)
- `pytest/pytest_collect.log`: Collection verification
- `cli/c_stdout.log`: C binary stdout
- `cli/py_stdout.log`: PyTorch stdout  
- `cli/c_weight.bin`: C output (256K)
- `cli/py_weight.bin`: PyTorch output (256K)
- `metrics.json`: Computed metrics
- `env.json`: Python/PyTorch versions
- `torch_env.txt`: Full torch environment

## Conclusion

**Phase D1 artifacts captured but parity NOT validated.** The 546× divergence requires investigation before marking this phase complete.

## Root Cause Analysis

**C binary logs show "created a total of 4 sources":**
```
0 0 0   0 0
0 0 0   0 0
0 0 10   1 6.2e-10
0 0 10   0.2 6.2e-10
```

The first two sources (0 0 0) are created by the default divergence grid.
The last two are from the sourcefile.

**PyTorch logs show "Loaded 2 sources":**
Only the sourcefile sources are loaded.

**Issue:** The -hdivsteps/-vdivsteps defaults differ between C and PyTorch implementations:
- C: When divergence range is unspecified and no step size is given, C generates a minimal divergence grid (1-2 sources)
- PyTorch: Appears to skip divergence generation when sourcefile is provided

**The test passes because it uses explicit `-lambda` which overrides both implementations to use the same wavelength.**

## Revised Conclusion

Phase D1 evidence captured but reveals a **divergence grid handling mismatch**, not a weighted-source normalization issue. The pytest passed because it controls all parameters explicitly.

The 546× intensity mismatch is explained by:
1. C creates 4 sources (2 divergence + 2 sourcefile) → steps = 4
2. PyTorch creates 2 sources (0 divergence + 2 sourcefile) → steps = 2
3. Intensity ratio: 4/2 = 2×, but combined with other parameter differences (wavelength mismatch?) → 546×

## Required Fix

Before marking SOURCE-WEIGHT-001 complete, must fix divergence grid auto-selection to match C behavior when sourcefile is provided.
