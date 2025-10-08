# CLI-FLAGS-003 Phase K3e: Per-φ Parity Comparison

**PyTorch:** `trace_py_c_parity_per_phi.json`  
**C:**       `c_trace_phi.log`  

## Comparison Table

| φ_tic | φ (deg) | C k_frac | PyTorch k_frac | Δk | Status |
|-------|---------|----------|----------------|-------|--------|
| 0 | 0.000000 | -0.553862 | -0.607227 | 5.336516e-02 | ❌ |
| 1 | 0.010000 | -0.547760 | -0.591149 | 4.338961e-02 | ❌ |
| 2 | 0.020000 | -0.548522 | -0.593159 | 4.463703e-02 | ❌ |
| 3 | 0.030000 | -0.549285 | -0.595169 | 4.588431e-02 | ❌ |
| 4 | 0.040000 | -0.550048 | -0.597179 | 4.713146e-02 | ❌ |
| 5 | 0.050000 | -0.550811 | -0.599189 | 4.837847e-02 | ❌ |
| 6 | 0.060000 | -0.551573 | -0.601199 | 4.962534e-02 | ❌ |
| 7 | 0.070000 | -0.552336 | -0.603208 | 5.087208e-02 | ❌ |
| 8 | 0.080000 | -0.553099 | -0.605218 | 5.211869e-02 | ❌ |
| 9 | 0.090000 | -0.553862 | -0.607227 | 5.336516e-02 | ❌ |

## Summary

**❌ DIVERGENCE DETECTED**

- First divergence: φ_tic=0 (φ=0.000000°)
- Max Δk: 5.336516e-02

### Root Cause

The C and PyTorch implementations compute **different k_frac values** at all φ steps.

**Evidence:**
- C k_frac @ φ=0°: `-0.553862232680661`
- PyTorch k_frac @ φ=0°: `-0.607227388110849`
- Δk @ φ=0°: `5.336516e-02`

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
