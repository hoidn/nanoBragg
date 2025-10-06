# CLI-FLAGS-003 Phase K3e: Per-φ Parity Comparison

**PyTorch:** `per_phi_pytorch_20251006-151228.json`  
**C:**       `per_phi_c_20251006-151228.log`  

## Comparison Table

| φ_tic | φ (deg) | C k_frac | PyTorch k_frac | Δk | Status |
|-------|---------|----------|----------------|-------|--------|
| 0 | 0.000000 | -3.857043 | -9.899110 | 6.042067e+00 | ❌ |
| 1 | 0.011111 | -3.834197 | -9.895139 | 6.060942e+00 | ❌ |
| 2 | 0.022222 | -3.837054 | -9.891167 | 6.054113e+00 | ❌ |
| 3 | 0.033333 | -3.839910 | -9.887194 | 6.047284e+00 | ❌ |
| 4 | 0.044444 | -3.842767 | -9.883221 | 6.040454e+00 | ❌ |
| 5 | 0.055556 | -3.845623 | -9.879247 | 6.033624e+00 | ❌ |
| 6 | 0.066667 | -3.848478 | -9.875271 | 6.026793e+00 | ❌ |
| 7 | 0.077778 | -3.851333 | -9.871296 | 6.019962e+00 | ❌ |
| 8 | 0.088889 | -3.854188 | -9.867319 | 6.013130e+00 | ❌ |
| 9 | 0.100000 | -3.857043 | -9.863341 | 6.006298e+00 | ❌ |

## Summary

**❌ DIVERGENCE DETECTED**

- First divergence: φ_tic=0 (φ=0.000000°)
- Max Δk: 6.060942e+00

### Root Cause

The C and PyTorch implementations compute **different k_frac values** at all φ steps.

**Evidence:**
- C k_frac @ φ=0°: `-3.857042980453150`
- PyTorch k_frac @ φ=0°: `-9.899109978860009`
- Δk @ φ=0°: `6.042067e+00`

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
