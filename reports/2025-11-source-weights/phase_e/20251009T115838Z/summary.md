# SOURCE-WEIGHT-001 Phase E Attempt (Failed)
**Timestamp:** 2025-10-09T11:58:38Z
**Status:** FAILED - Parity broken (sum_ratio 142-303×)

## Test Results

### TC-D1: Sourcefile-only parity
- **Status:** ❌ FAILED
- **Correlation:** -0.297 (threshold: ≥0.999)
- **Sum Ratio:** 302.6 (threshold: |ratio-1| ≤1e-3)
- **C Sum:** 179.6
- **PyTorch Sum:** 54352.6

### TC-D2: Warning guard
- **Status:** ✅ PASSED
- **Warning emitted:** UserWarning with expected fragments
- **Conversion:** Successfully migrated to in-process pytest.warns

### TC-D3: Divergence grid generation
- **Status:** ❌ FAILED
- **Correlation:** 0.070 (threshold: ≥0.999)
- **Sum Ratio:** 141.7 (threshold: |ratio-1| ≤1e-3)
- **C Sum:** 358.2
- **PyTorch Sum:** 50745.9

### TC-D4: Explicit oversample parity
- **Status:** ❌ FAILED (delegates to TC-D1)

## Observations

1. **TC-D2 Success:** The in-process pytest.warns conversion works correctly.
2. **Parity Failures:** Both sourcefile (TC-D1) and divergence grid (TC-D3) cases show massive intensity divergence (140-300×).
3. **Pattern:** PyTorch intensities are consistently 2-3 orders of magnitude higher than C reference.

## Hypothesis

The simulator may still be applying weighted accumulation despite Phase C implementation claiming to remove it. Need to:
1. Review `Simulator.run()` normalization logic
2. Check if `source_weights` is being used in the physics accumulation
3. Verify `steps` denominator calculation

## Next Actions

- Debug the normalization path in `src/nanobrag_torch/simulator.py`
- Compare C vs PyTorch `steps` calculation for sourcefile case
- Re-implement Phase C fixes if regression detected
