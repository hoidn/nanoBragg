# SOURCE-WEIGHT-001 Phase G: Pytest Collection Validation

**Timestamp:** 2025-10-09T21:55:16Z
**Task:** Validate pytest selectors for Phase G evidence capture
**Status:** ✅ PASS - All expected tests collected successfully

## Collection Command

```bash
NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q \
  tests/test_cli_scaling.py::TestSourceWeights \
  tests/test_cli_scaling.py::TestSourceWeightsDivergence
```

## Collection Results

**Total Tests Collected:** 8

### TestSourceWeights (6 tests)
1. `test_source_weights_ignored_per_spec` - TC-Spec-1: Weighted vs equal-weight comparison
2. `test_cli_lambda_overrides_sourcefile` - TC-Spec-2: CLI lambda override validation
3. `test_uniform_weights_ignored` - TC-B: Three sources with uniform weights
4. `test_edge_case_zero_sum_accepted` - TC-D: Zero-sum weights edge case
5. `test_edge_case_negative_weights_accepted` - TC-D: Negative weights edge case
6. `test_single_source_fallback` - TC-C: Single source behavior

### TestSourceWeightsDivergence (2 tests)
1. `test_c_divergence_reference` - C-PARITY-001 divergence documentation (XFAIL)
2. `test_sourcefile_divergence_warning` - TC-D2: UserWarning validation

## Test Coverage Mapping

The collected tests cover all Phase G objectives:

| Test Case ID | Test Method | Phase G Requirement |
|-------------|-------------|---------------------|
| TC-Spec-1 | `test_source_weights_ignored_per_spec` | Verify equal weighting per spec-a-core.md:151 |
| TC-Spec-2 | `test_cli_lambda_overrides_sourcefile` | Verify CLI lambda override with warning |
| TC-B | `test_uniform_weights_ignored` | Uniform weights acceptance |
| TC-C | `test_single_source_fallback` | Single source fallback (source_weights=None) |
| TC-D | `test_edge_case_*` | Edge case validation (zero-sum, negative) |
| TC-D2 | `test_sourcefile_divergence_warning` | Divergence parameter warning |
| C-PARITY-001 | `test_c_divergence_reference` | Document expected C divergence (XFAIL) |

## Validation Status

✅ **All pytest selectors are valid**
✅ **No collection errors or warnings**
✅ **Test structure matches Phase G2 plan requirements**

## Next Steps

Per `plans/active/source-weight-normalization.md` Phase G2:
1. Execute full test suite: `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence -v`
2. Capture execution logs to this timestamped directory
3. Update plan status to COMPLETE

## Artifacts Location

All Phase G evidence artifacts stored in:
```
reports/2025-11-source-weights/phase_g/20251009T215516Z/
```
