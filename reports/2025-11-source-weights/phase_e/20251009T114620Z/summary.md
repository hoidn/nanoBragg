# SOURCE-WEIGHT-001 Phase E - Warning Guard Implementation

## Timestamp
20251009T114620Z

## Objective
Implement Option B warning guard: replace stderr print with `warnings.warn` in CLI, update TC-D2 test to assert warning correctly.

## Changes Made

### 1. __main__.py (lines 732-741)
- Replaced `print(..., file=sys.stderr)` with `warnings.warn(..., UserWarning, stacklevel=2)`
- Added spec citation comment referencing specs/spec-a-core.md:151
- Warning message unchanged: "Divergence/dispersion parameters ignored when sourcefile is provided. Sources are loaded from file only (see specs/spec-a-core.md:151-162)."

### 2. test_cli_scaling.py (lines 586-653)
- Updated TC-D2 `test_sourcefile_divergence_warning` to check for UserWarning in stderr
- Added "UserWarning" to expected fragments (warnings module emits class name in subprocess stderr)
- Test now correctly validates warning guard per Phase E requirements

## Test Results

### TC-D2 (Warning Guard Test) - **PASSED** ✓
- Command: `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_divergence_warning -v`
- Status: PASSED in 5.62s
- Verification: Warning correctly emitted when `-sourcefile` + `-hdivrange` both present
- Output file created successfully

### TC-D1, TC-D3, TC-D4 (Parity Tests) - FAILED (Pre-existing Issue)
These tests fail with parity discrepancies (sum_ratio ~300× and ~142×). This is a **known physics/normalization issue unrelated to the warning guard**. These failures were expected per fix_plan.md Attempt #4 (galph loop — planning review) which identified the remaining divergence after commit 321c91e.

#### TC-D1 Metrics:
- Correlation: -0.297 (< 0.999 threshold)
- Sum ratio: 302.6 (should be ~1.0)
- C sum: 179.6, PyTorch sum: 54352.6

#### TC-D3 Metrics:
- Correlation: 0.070 (< 0.999 threshold)
- Sum ratio: 141.7 (should be ~1.0)
- C sum: 358.2, PyTorch sum: 50745.9

## Phase E1 Exit Criteria Status
✓ **E1 Complete**: Warning guard implemented using `warnings.warn` with stacklevel=2
✓ **TC-D2 Passing**: Warning test validates correct UserWarning emission

## Next Actions (Per Plan Phase E2-E4)
1. **E2**: Physics debugging required for TC-D1/D3/D4 parity (separate debugging loop needed)
2. **E3**: Capture parity metrics after physics fix
3. **E4**: Update documentation

## Artifacts
- `pytest.log`: Full test suite output
- `summary.md`: This file
- `commands.txt`: Reproduction commands (see below)

