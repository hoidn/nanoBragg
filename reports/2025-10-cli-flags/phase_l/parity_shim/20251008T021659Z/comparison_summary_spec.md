# CLI-FLAGS-003 Phase K3e: Per-φ Parity Comparison

**PyTorch:** `trace_py_spec_per_phi.json`  
**C:**       `c_trace_phi.log`  

## Comparison Table

| φ_tic | φ (deg) | C k_frac | PyTorch k_frac | Δk | Status |
|-------|---------|----------|----------------|-------|--------|
| 0 | 0.000000 | -0.607256 | -0.589139 | 1.811649e-02 | ❌ |
| 1 | 0.010000 | -0.591178 | -0.591149 | 2.830201e-05 | ✅ |
| 2 | 0.020000 | -0.593188 | -0.593159 | 2.832070e-05 | ✅ |
| 3 | 0.030000 | -0.595198 | -0.595169 | 2.833938e-05 | ✅ |
| 4 | 0.040000 | -0.597208 | -0.597179 | 2.835807e-05 | ✅ |
| 5 | 0.050000 | -0.599217 | -0.599189 | 2.837675e-05 | ✅ |
| 6 | 0.060000 | -0.601227 | -0.601199 | 2.839543e-05 | ✅ |
| 7 | 0.070000 | -0.603237 | -0.603208 | 2.841411e-05 | ✅ |
| 8 | 0.080000 | -0.605246 | -0.605218 | 2.843279e-05 | ✅ |
| 9 | 0.090000 | -0.607256 | -0.607227 | 2.845147e-05 | ✅ |

## Summary

**❌ DIVERGENCE DETECTED**

- First divergence: φ_tic=0 (φ=0.000000°)
- Max Δk: 1.811649e-02

### Root Cause

The C and PyTorch implementations compute **different k_frac values** at all φ steps.

**Evidence:**
- C k_frac @ φ=0°: `-0.607255839576692`
- PyTorch k_frac @ φ=0°: `-0.589139352775903`
- Δk @ φ=0°: `1.811649e-02`

This indicates a **fundamental difference** in either:
1. The φ rotation matrix calculation
2. The base lattice vectors before φ rotation
3. The scattering vector S calculation


## Next Actions

1. Compare base lattice vectors (a, b, c) before φ rotation in both implementations
2. Compare scattering vector S calculation
3. Verify φ rotation matrix formulation (Rodrigues vs axis-angle)
4. Check spindle_axis sign convention
5. Proceed to Phase K3f with identified fix
