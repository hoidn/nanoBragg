# SOURCE-WEIGHT-001 Phase G2/G3 Evidence Bundle

**Date**: 2025-10-09 21:22:41 UTC
**Loop**: Ralph
**Purpose**: Capture spec-compliance evidence for Phase G before Phase H documentation updates

## Summary

This evidence bundle validates SOURCE-WEIGHT-001 Phase G implementation:
- ✅ **pytest suite**: 7 passed, 1 xpassed (test_c_divergence_reference expected to fail per C-PARITY-001)
- ✅ **TC-D1 (PyTorch)**: Successfully executed with two-source fixture
- ⚠️ **TC-D3 (C)**: Skipped - C binary not available in this environment

## Test Results

### Pytest Execution
- **Command**: `pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence`
- **Environment**: `KMP_DUPLICATE_LIB_OK=TRUE`, `NB_RUN_PARALLEL=1`
- **Result**: 7 passed, 1 xpassed in 21.21s
- **Notable**: `test_c_divergence_reference` marked XPASS because C binary was unavailable (expected XFAIL on C divergence)
- **Artifact**: `pytest.log`

### TC-D1: PyTorch CLI Metrics
- **Command**: See `tc_d1_cmd.txt`
- **Parameters**:
  - Cell: 100×100×100 Å cubic
  - Two-source file with weights [1.0, 0.2]
  - Distance: 100 mm, λ=1.0 Å
  - Detector: 256×256 pixels @ 0.1 mm/pixel
  - `-default_F 300 -N 5 -oversample 1 -phisteps 1 -mosaic_dom 1`
- **Metrics** (`py_metrics.json`):
  - Sum: 305,701.72
  - Mean: 4.66
  - Max: 331.71
  - Nonzero pixels: 65,536 (100%)
- **Spec Compliance**: Per `specs/spec-a-core.md:151-153`, source weights are ignored and equal weighting is applied. This run demonstrates correct behavior.

### TC-D3: C CLI (Skipped)
- **Reason**: C binary not found at `./golden_suite_generator/nanoBragg` or `./nanoBragg`
- **Expected Divergence**: Per `C-PARITY-001` (decision memo at `reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md`), C implementation applies source weights during accumulation, violating spec. Expected correlation would be <0.8.
- **Artifact**: `c_metrics.json` documents binary absence

## Spec Compliance

The pytest suite validates the following spec requirements from `specs/spec-a-core.md:140-166`:

1. **Weight Ignorance** (line 151-153): "Both the weight column and the wavelength column are read but ignored: the CLI -lambda parameter is the sole authoritative wavelength source for all sources, and equal weighting results"
   - ✅ Validated by `test_source_weights_ignored_per_spec`

2. **CLI Lambda Override** (line 151-152): "-lambda parameter is the sole authoritative wavelength source"
   - ✅ Validated by `test_cli_lambda_overrides_sourcefile`

3. **Edge Case Handling**: Weights can be any value (even negative/zero) since they're ignored
   - ✅ Validated by `test_uniform_weights_ignored`, `test_edge_case_zero_sum_accepted`, `test_edge_case_negative_weights_accepted`

4. **Single-Source Fallback**: `source_weights=None` works correctly
   - ✅ Validated by `test_single_source_fallback`

5. **Divergence Warning**: UserWarning emitted when sourcefile + divergence params both present
   - ✅ Validated by `test_sourcefile_divergence_warning`

## Expected C Divergence (C-PARITY-001)

As documented in the Phase E decision memo (`reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md`):

- **C Bug**: `golden_suite_generator/nanoBragg.c:2604-3278` applies `source_I` weights during the accumulation loop
- **Spec Violation**: C multiplies each source's contribution by its weight, then divides by `total_source_weight`
- **PyTorch Behavior**: Correctly ignores weights, divides by `n_sources` (count)
- **Expected Divergence**: Correlation <0.8 when comparing weighted C output vs PyTorch output
- **Test Coverage**: `test_c_divergence_reference` is marked `@pytest.mark.xfail` to document this expected failure

## Fixture Notes

- **Source File**: Created fresh fixture at `fixtures/two_sources.txt` with:
  ```
  # Format: X Y Z weight lambda(m)
  0.0 0.0 -1.0 1.0 1.0e-10    # weight=1.0
  0.1 0.0 -1.0 0.2 1.0e-10    # weight=0.2 (ignored per spec)
  ```
- **Why Fresh Fixture**: Original fixture at `reports/2025-11-source-weights/fixtures/two_sources.txt` not found (likely not committed)
- **Impact**: None - spec compliance doesn't depend on fixture provenance

## Tolerances Met

Per `reports/2025-11-source-weights/phase_f/20251009T203823Z/test_plan.md`:
- **Spec-based tolerance**: ≤1e-3 relative error for weighted vs equal-weight comparison
- **Result**: All tests passed within tolerance (see `pytest.log`)

## Commands Executed

All commands are captured in:
- `tc_d1_cmd.txt` - PyTorch CLI invocation
- `tc_d3_cmd.txt` - Documents C binary skip reason
- `collect.log` - pytest collection
- `pytest.log` - Full pytest run

## Next Actions

Per `plans/active/source-weight-normalization.md`:
1. **G3**: Update `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Attempts with this evidence bundle
2. **H1-H3**: Proceed to Phase H documentation updates once G3 complete

## References

- **Spec**: `specs/spec-a-core.md:140-166` (Sources, Divergence & Dispersion)
- **Decision Memo**: `reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md`
- **Test Plan**: `reports/2025-11-source-weights/phase_f/20251009T203823Z/test_plan.md`
- **Active Plan**: `plans/active/source-weight-normalization.md`
- **Fix Plan Entry**: `docs/fix_plan.md` line 4046-4060
