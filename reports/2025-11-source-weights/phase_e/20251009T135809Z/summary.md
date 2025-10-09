# SOURCE-WEIGHT-001 Phase E Parity Evidence - Attempt #18 (ralph loop)

**Date:** 2025-10-09
**Mode:** Parity
**Result:** **BLOCKED** - TC-D1 parity FAILED; steps reconciliation not yet implemented

## Executive Summary

Option B (lambda override + warning) was successfully implemented in Attempt #17, and TC-E1/E2/E3 regression tests pass. However, TC-D1/TC-D3 parity validation reveals that the **steps normalization fix was NOT implemented** in Attempt #17, causing severe parity failures.

## Test Results

### Regression Tests (TC-E1/E2/E3)
- Status: **PASS** (7/7 tests passing)
- File: `tests/test_at_src_003.py`
- Collection: 693 tests total (no import errors)

### Parity Tests (TC-D1)
- Status: **FAIL**
- Correlation: **0.051** (threshold: ≥0.999)
- Sum ratio: **219.4** (threshold: |ratio-1| ≤ 0.001)
- |sum_ratio - 1|: **218.4** (threshold: ≤ 0.001)

## Root Cause Analysis

### Lambda Override (✅ WORKING)
The `read_sourcefile` function correctly:
1. Ignores sourcefile wavelength column (6.2e-10 m)
2. Uses CLI `-lambda` value (9.768e-11 m) for all sources
3. Emits UserWarning when wavelengths differ
4. All 2 sources have wavelength = 0.9768 Å

### Steps Normalization (❌ BROKEN - PRIMARY BLOCKER)
The simulator still divides by incorrect steps count:

**PyTorch:**
- Counts: 2 sources (from fixture file)
- Steps: 2 × 1 (mosaic) × 1 (phi) × 1² (oversample) = 2

**C Reference:**
- Counts: 4 sources (2 from file + 2 zero-weight divergence placeholders)
- Steps: 4 × 1 × 1 × 1 = 4

**Impact:** PyTorch intensities are NOT divided by enough → 2× inflation baseline.

### Additional Scaling Issues
The observed 219× discrepancy >> 2× expected from steps alone suggests:
1. ✅ Lambda override is correct (0.9768 Å vs 6.2 Å would cause spot shift, not uniform scaling)
2. ❌ Steps normalization is wrong (2 vs 4 = 2× factor)
3. ❓ Unknown additional scaling factor (~110×) - possible fluence/r_e²/capture issues

## C Binary Source Listing

From `c_tc_d1_stdout_full.log`:
```
created a total of 4 sources:
0 0 0   0 0          # Zero-weight divergence placeholder
0 0 0   0 0          # Zero-weight divergence placeholder
0 0 10   1 6.2e-10   # Actual source (weight=1.0)
0 0 10   0.2 6.2e-10 # Actual source (weight=0.2)
```

All 4 sources contribute to steps denominator even though 2 have zero weight.

## Artifacts

All artifacts stored in: `reports/2025-11-source-weights/phase_e/20251009T135809Z/`

### Primary Evidence
- `py_tc_d1.bin` - PyTorch output (256×256 float32, max=319.3)
- `c_tc_d1.bin` - C output (256×256 float32, max=0.009)
- `correlation.txt` - 0.050659
- `sum_ratio.txt` - 219.405197
- `metrics.txt` - Complete parity metrics

### Logs
- `pytest.log` - TC-E1/E2/E3 test run (7 passed, 1 warning)
- `collect.log` - Full test collection (693 tests)
- `c_tc_d1_stdout_full.log` - C binary execution trace
- `commands.txt` - Reproduction commands
- `env.json` - Environment metadata

## Next Actions (BLOCKING)

### 1. Implement Steps Reconciliation Fix (CRITICAL)
**File:** `src/nanobrag_torch/simulator.py`

**Required Change:**
```python
# Current (WRONG):
source_norm = n_sources  # Only counts actual sources

# Corrected (matches C):
source_norm = n_sources_total  # Counts ALL sources including zero-weight divergence
```

**C Reference:** `nanoBragg.c:2700-2720` (steps calculation includes all sources)

**Impact:** Will reduce PyTorch intensities by 2× (4/2 = 2) for this fixture.

### 2. Investigate Remaining 110× Discrepancy
After step 1 fix, sum_ratio should drop from 219× to ~110×. If still far from 1.0:
- Check fluence calculation
- Verify r_e² scaling
- Review capture_fraction logic
- Compare source weight application

### 3. Rerun TC-D1/TC-D3 Parity
After fixes, capture fresh metrics under new timestamp:
```bash
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
# Run both PyTorch and C commands
# Compute metrics
# Verify: correlation ≥ 0.999, |sum_ratio-1| ≤ 1e-3
```

### 4. Update Documentation
Once parity passes:
- Mark Phase E complete in fix_plan.md
- Update pytorch_design.md sources section
- Signal VECTOR-GAPS-002 / VECTOR-TRICUBIC-002 unblock

## Observations

1. **Lambda override is correct:** TC-E1/E2/E3 pass, warning emitted, all wavelengths = 0.9768 Å
2. **Steps count is wrong:** PyTorch counts 2, C counts 4 (includes divergence placeholders)
3. **Magnitude of error:** 219× is too large for steps alone; additional scaling issues likely present
4. **No regressions:** Test collection shows 693 tests (unchanged from baseline)
5. **C reference behavior:** Always creates divergence sources even when not requested via CLI

## Conclusion

Attempt #17 delivered Phase E1/E2 (lambda override + warning) successfully, but **explicitly deferred** the Phase E3 steps reconciliation. The current parity failure (correlation=0.05, sum_ratio=219×) confirms that PyTorch normalization remains broken due to incorrect steps count.

**Status:** Phase E1/E2 complete, Phase E3 BLOCKED on steps fix. Cannot mark SOURCE-WEIGHT-001 complete until correlation ≥ 0.999 and |sum_ratio-1| ≤ 1e-3.
