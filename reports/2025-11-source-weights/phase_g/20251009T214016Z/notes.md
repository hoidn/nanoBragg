# SOURCE-WEIGHT-001 Phase G2/G3 Evidence Bundle - CRITICAL FINDINGS

**Date:** 2025-10-09
**Timestamp:** 20251009T214016Z
**Mode:** Docs+Parity (Evidence-only, per input.md)

## Summary

Phase G2/G3 evidence collection revealed **TWO CRITICAL ANOMALIES**:

1. **XPASS on `test_c_divergence_reference`**: Expected C-PARITY-001 divergence NOT observed
2. **C binary segfault**: TC-D3 command crashed with segmentation fault

## Pytest Results

**Command:** `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence`

**Result:** 7 passed, 1 xpassed in 21.20s

### Expected vs Actual

- **Expected:** 7 passed, 1 xfail
- **Actual:** 7 passed, 1 **XPASS** ❌

### XPASS Details

Test `test_c_divergence_reference` was marked `@pytest.mark.xfail` with reason:
> "C-PARITY-001: C applies source weights during accumulation, violating spec requirement for equal weighting"

**This test PASSED when it should have FAILED**, indicating:
- C and PyTorch now produce nearly identical results (correlation=0.9999886, sum_ratio=1.0038)
- Either C behavior changed, PyTorch behavior changed, or the original C-PARITY-001 assessment was incorrect

### Metrics from XPASS (unexpected_c_parity/metrics.json)

```json
{
  "c_sum": 125522.6171875,
  "py_sum": 126004.640625,
  "sum_ratio": 1.0038400888442993,
  "correlation": 0.9999886333899755,
  "expected": "correlation < 0.8 (C-PARITY-001)",
  "decision_memo": "reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md"
}
```

**Analysis:**
- Correlation: 0.999989 (essentially perfect agreement)
- Sum ratio: 1.0038 (~0.38% difference, well within tolerance)
- **This contradicts the documented C-PARITY-001 bug**

## TC-D1 PyTorch CLI Execution

**Command:** See `tc_d1_cmd.txt`

**Status:** ✅ SUCCESS

**Metrics:** (py_metrics.json)
```json
{
  "sum": 43161.9921875,
  "mean": 0.6585997343063354,
  "max": 76.97444152832031,
  "nonzero": 65536
}
```

## TC-D3 C CLI Execution

**Command:** See `tc_d3_cmd.txt`

**Status:** ❌ **SEGMENTATION FAULT**

The C binary crashed during execution:
```
/bin/bash: line 31: 468567 Segmentation fault      (core dumped)
```

**No C metrics captured** - c_tc_d3.bin was not generated.

## Implications

### XPASS Anomaly

Per input.md instructions:
> "if it XPASSes, document immediately and halt further Phase H work"

**Actions Required:**
1. Investigate whether C code in `./golden_suite_generator/nanoBragg` was modified
2. Review git history for any PyTorch changes affecting source weight handling
3. Re-examine the C-PARITY-001 decision memo validity
4. **BLOCK Phase H** until XPASS is explained

### C Segfault

**Blocker for Phase G2/G3 completion:**
- Cannot compute correlation/sum_ratio without C output
- TC-D3 command is invalid or C binary has regression
- Need to debug C segfault before proceeding

**Possible Causes:**
- Missing `-default_F` previously caused "Need -hkl" error (fixed in this run)
- Sourcefile format incompatibility
- Memory corruption in C code
- C binary built with wrong flags

## Next Actions

1. **URGENT:** Check git log for changes to `golden_suite_generator/nanoBragg.c` or `golden_suite_generator/nanoBragg` binary
2. **URGENT:** Re-examine C-PARITY-001 decision memo (`reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md`)
3. Debug C segfault:
   - Verify sourcefile format is correct
   - Try minimal command without sourcefile
   - Rebuild C binary with debug symbols
   - Run under gdb/valgrind
4. **DO NOT PROCEED** to Phase H until:
   - XPASS is explained and test expectation updated
   - C segfault is resolved and TC-D3 metrics captured
   - Supervisor reviews these findings

## Artifacts

- `collect.log` - pytest collection (8 tests)
- `pytest.log` - test execution log (7 pass, 1 xpass)
- `tc_d1_cmd.txt` - PyTorch CLI command
- `py_stdout.txt` - PyTorch execution output
- `py_tc_d1.bin` - PyTorch float image
- `py_metrics.json` - PyTorch metrics
- `tc_d3_cmd.txt` - C CLI command (failed)
- `c_stdout.txt` - C error output (segfault)
- `../unexpected_c_parity/metrics.json` - XPASS metrics

## References

- input.md - Phase G2/G3 instructions
- plans/active/source-weight-normalization.md - Plan reference
- reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md - C-PARITY-001 decision
- reports/2025-11-source-weights/phase_f/20251009T203823Z/ - Design packet
