# TEST-GOLDEN-001 Phase C Parity Validation Summary

**Date:** 2026-01-10
**Attempt:** #20 (Phase C validation)
**Owner:** ralph
**Status:** ✅ SUCCESS

## Executive Summary

Phase C parity validation PASSED all gates. Regenerated golden data from Attempt #19 (Phase B) meets spec thresholds for AT-PARALLEL-012.

## Validation Results

### ROI Parity Check (high_resolution_4096)

**Command:**
```bash
export NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE
python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 \
  --outdir reports/2026-01-golden-refresh/phase_c/20251010T090248Z/high_res_roi \
  -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 \
  -distance 500 -detpixels 4096 -pixel 0.05 \
  -floatfile tests/golden_data/high_resolution_4096/image.bin
```

**Metrics:**
- **Correlation:** 1.000000 (spec threshold: ≥0.95) ✅
- **Sum ratio:** 0.999987 (|ratio−1| = 0.000013 ≤ 5e-3) ✅
- **RMSE:** 0.000033
- **Max |Δ|:** 0.001254
- **C sum:** 34588.84
- **Py sum:** 34588.39
- **Mean peak distance:** 0.87 pixels
- **Max peak distance:** 1.41 pixels
- **Runtime:** C=0.519s, Py=5.856s (speedup 0.09×)

**Verdict:** PASS (both thresholds met)

### Targeted Pytest

**Command:**
```bash
export NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE
pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant
```

**Result:**
```
tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant PASSED [100%]
============================== 1 passed in 5.83s ===============================
```

**Verdict:** PASS

## Artifacts

- ROI comparison outputs: `reports/2026-01-golden-refresh/phase_c/20251010T090248Z/high_res_roi/`
  - `commands.txt` — full command + stdout/stderr
  - `summary.json` — metrics JSON
  - `c.png`, `py.png`, `diff.png` — visual artifacts
- Pytest log: `reports/2026-01-golden-refresh/phase_c/20251010T090248Z/pytest_highres.log`

## Exit Criteria Assessment

- [x] ROI correlation ≥0.95 (achieved: 1.000000)
- [x] |sum_ratio−1| ≤5e-3 (achieved: 0.000013)
- [x] Targeted pytest passing (test_high_resolution_variant PASSED)
- [x] Artifacts captured and documented

## Next Actions

1. Update `docs/fix_plan.md` [TEST-GOLDEN-001] Attempts History with Phase C results
2. Mark Phase C tasks C1/C2 as [D]one in `plans/active/test-golden-refresh.md`
3. Unblock `[VECTOR-PARITY-001]` Phase E by noting Phase C success in fix_plan
4. Proceed to Phase D ledger updates if no additional dependent tests are flagged

## References

- Plan: `plans/active/test-golden-refresh.md`
- Fix Plan Entry: `docs/fix_plan.md` [TEST-GOLDEN-001]
- Spec: `specs/spec-a-parallel.md` AT-PARALLEL-012
- Testing Strategy: `docs/development/testing_strategy.md` §2.5
