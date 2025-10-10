# Phase D3 Summary - F_latt Trace Script Fix

**Timestamp:** 20251010T071935Z
**Task:** [VECTOR-PARITY-001] Phase D3 - Fix H3 (F_latt normalization)
**Status:** ✅ TRACE SCRIPT FIXED | ⚠️ SIMULATOR BLOCKER DISCOVERED

## Scope Completed

Phase D3 was scoped to fix the F_latt calculation in the trace script (`scripts/debug_pixel_trace.py`) to match nanoBragg.c. This has been successfully completed.

## Changes Made

### File Modified: `scripts/debug_pixel_trace.py`

**Lines 335-353:** Replaced incorrect local `sincg` implementation with import from production code

**Before (WRONG):**
```python
def sincg(x):
    """Sine cardinal function: sin(x)/x with limit at x=0."""
    x_abs = torch.abs(x)
    result = torch.where(
        x_abs < 1e-6,
        torch.ones_like(x),
        torch.sin(x) / x
    )
    return result

F_latt_a = sincg(np.pi * h_frac) / sincg(np.pi * h_frac / Na) if Na > 1 else torch.tensor(Na, dtype=dtype, device=device)
```

**After (CORRECT):**
```python
# Import the production sincg function to ensure trace matches simulator
from nanobrag_torch.utils.physics import sincg

# C-Code Reference (from nanoBragg.c, lines 15026-15029):
# ```c
# double sincg(double x,double N) {
#     if(x==0.0) return N;
#     return sin(x*N)/sin(x);
# }
# ```
# Formula: sincg(π·h, Na) = sin(Na·π·h) / sin(π·h)
# This is NOT the same as sincg(π·h) / sincg(π·h/Na)!

F_latt_a = sincg(torch.pi * h_frac, torch.tensor(Na, dtype=dtype, device=device))
F_latt_b = sincg(torch.pi * k_frac, torch.tensor(Nb, dtype=dtype, device=device))
F_latt_c = sincg(torch.pi * l_frac, torch.tensor(Nc, dtype=dtype, device=device))
```

## Results

### F_latt Parity Table

| Component | C Reference | PyTorch (Post-Fix) | Relative Error | Status |
|-----------|-------------|-------------------|----------------|--------|
| F_latt_a | 4.186802197313e+0 | 4.186802197313e+0 | 9.554e-16 | ✅ PASS |
| F_latt_b | 2.301221333639e+0 | 2.301221333639e+0 | 8.691e-16 | ✅ PASS |
| F_latt_c | 4.980295808863e+0 | 4.980295808863e+0 | 4.417e-15 | ✅ PASS |
| F_latt | 4.798394755717e+1 | 4.798394755717e+1 | 4.585e-15 | ✅ PASS |

**Tolerance:** ≤1e-2 (spec requirement)
**Achieved:** <1e-12 (machine precision)

## Blocker Discovered

Testing revealed that while the trace script now produces correct F_latt values, the **production simulator** has a separate issue:

### Symptom
- **Trace script final intensity:** 0.229 photons/pixel (within 15% of C)
- **Simulator output:** 0.00827 photons/pixel (32× too small!)
- **C reference:** 0.269 photons/pixel

### Evidence
```bash
# Simulator produces 32× lower intensity
$ KMP_DUPLICATE_LIB_OK=TRUE python -c "..."
Simulator pixel (1792, 2048): 8.272659271741050e-03

# ROI comparison shows complete failure
$ nb-compare --roi 1792 2304 1792 2304 ...
Correlation: -0.001090 (threshold: ≥0.999)
Sum ratio: 12.539824 (threshold: ≤1.005)
```

### Root Cause Analysis Status
- ✅ **Confirmed:** `utils/physics.py::sincg` function is correct (tested in isolation)
- ✅ **Confirmed:** `simulator.py:252-255` uses correct formula: `F_latt_a = sincg(torch.pi * h, Na)`
- ❌ **Unknown:** Where 32× discrepancy originates in simulator pipeline

### Hypothesis
The 32× factor (≈ 5³/4 = 125/4) suggests:
- Oversampling normalization error
- Incorrect scaling elsewhere in pipeline
- Miller index calculation feeding wrong values to F_latt
- Accumulation bug in main simulation loop

## Artifacts Generated

1. **F_latt parity table:** `f_latt_parity.md`
2. **Blocker documentation:** `blockers.md`
3. **Post-fix trace:** `../py_traces_post_fix/pixel_1792_2048.log`
4. **Post-fix metadata:** `../py_traces_post_fix/pixel_1792_2048_metadata.json`
5. **ROI comparison:** `roi_compare/summary.json` (FAILING)

## Recommendations

### Immediate Actions

1. **Document Phase D3 completion** in `docs/fix_plan.md` Attempt #13:
   - Status: ✅ Partial (trace script fixed, simulator blocked)
   - Trace F_latt parity: Machine precision (<1e-15)
   - Simulator blocker: 32× intensity discrepancy

2. **Create Phase D5** (or expand D4) to address simulator bug:
   - Add detailed F_latt logging to `Simulator.run()`
   - Trace through `_compute_physics_for_position()` with known test case
   - Validate Miller indices (h,k,l) match trace script values
   - Unit test F_latt pathway in isolation

3. **Regression investigation:** Attempt #7 achieved corr=0.999999999 before D1/D2/D3. Verify whether:
   - D1 scattering_vec fix was applied correctly to simulator (appears YES)
   - D2 fluence fix was applied correctly to simulator (appears YES)
   - Some interaction between fixes introduced the regression

### Exit Criteria for Phase D Overall

Per `docs/fix_plan.md` Phase D3 spec:
> "Capture comparison table in `f_latt_parity.md` (tolerance ≤1e-2) and confirm ROI parity still ≥0.999."

- ✅ F_latt parity table captured (tolerance met: <1e-12)
- ❌ ROI parity confirmation failed (corr=-0.001, sum_ratio=12.5×)

**Decision:** Phase D3 trace fix is complete. Simulator issue must be addressed separately before proceeding to Phase D4/E.

## References

- Input memo: `input.md` Phase D3 scope
- Fix plan: `docs/fix_plan.md` [VECTOR-PARITY-001] H3
- C trace reference: `../../../phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log`
- Spec: `specs/spec-a-core.md` §4.3 SQUARE shape F_latt formula
