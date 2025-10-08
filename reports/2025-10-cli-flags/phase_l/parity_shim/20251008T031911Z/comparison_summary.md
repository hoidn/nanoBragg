# CLI-FLAGS-003 Phase K3e: Per-φ Parity Comparison

**PyTorch:** `per_phi_pytorch_20251007-201915.json`  
**C:**       `c_trace_phi.log`  

## Comparison Table

| φ_tic | φ (deg) | C k_frac | PyTorch k_frac | Δk | Status |
|-------|---------|----------|----------------|-------|--------|
| 0 | 0.000000 | -0.607256 | -9.899110 | 9.291854e+00 | ❌ |
| 1 | 0.011111 | -0.591178 | -9.895139 | 9.303961e+00 | ❌ |
| 2 | 0.022222 | -0.593188 | -9.891167 | 9.297979e+00 | ❌ |
| 3 | 0.033333 | -0.595198 | -9.887194 | 9.291997e+00 | ❌ |
| 4 | 0.044444 | -0.597208 | -9.883221 | 9.286013e+00 | ❌ |
| 5 | 0.055556 | -0.599217 | -9.879247 | 9.280029e+00 | ❌ |
| 6 | 0.066667 | -0.601227 | -9.875271 | 9.274044e+00 | ❌ |
| 7 | 0.077778 | -0.603237 | -9.871296 | 9.268059e+00 | ❌ |
| 8 | 0.088889 | -0.605246 | -9.867319 | 9.262072e+00 | ❌ |
| 9 | 0.100000 | -0.607256 | -9.863341 | 9.256085e+00 | ❌ |

## Summary

**❌ DIVERGENCE DETECTED**

- First divergence: φ_tic=0 (φ=0.000000°)
- Max Δk: 9.303961e+00

### Root Cause

The C and PyTorch implementations compute **different k_frac values** at all φ steps.

**Evidence:**
- C k_frac @ φ=0°: `-0.607255839576692`
- PyTorch k_frac @ φ=0°: `-9.899109978860011`
- Δk @ φ=0°: `9.291854e+00`

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
