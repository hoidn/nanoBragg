# Scaling Chain Comparison: C vs PyTorch

**Phase L3e Validation** (CLI-FLAGS-003)

**Tolerance:** ≤1.00e-06 relative

## Summary

Comparing scaling factors for supervisor command pixel (685, 1039).

## Detailed Comparison

| Factor | C Value | PyTorch Value | Δ (abs) | Δ (rel) | Status |
|--------|---------|---------------|---------|---------|--------|
| I_before_scaling | 1.480792e+15 | 5.873564e+08 | -1.480791e+15 | -9.999996e-01 | CRITICAL |
| r_e_sqr | 7.940792e-30 | 7.940792e-30 | 0.000000e+00 | +0.000000e+00 | PASS |
| fluence_photons_per_m2 | 1.000000e+24 | 1.000000e+24 | 0.000000e+00 | +0.000000e+00 | PASS |
| steps | 10 | 10 | 0.000000e+00 | +0.000000e+00 | PASS |
| capture_fraction | 1 | 1 | 0.000000e+00 | +0.000000e+00 | PASS |
| polar | 0.912575819 | 0.912575953 | 1.343606e-07 | +1.472322e-07 | PASS |
| omega_pixel | 4.158679e-07 | 4.158679e-07 | 5.789501e-14 | +1.392149e-07 | PASS |
| cos_2theta | 0.908378576 | 0.908378717 | 1.408599e-07 | +1.550674e-07 | PASS |
| I_pixel_final | 446.254111 | 466.40756 | 20.1534491 | +4.516137e-02 | CRITICAL |

## First Divergence

**I_before_scaling** (Raw accumulated intensity before normalization)

- C value: `1.480792e+15`
- PyTorch value: `5.873564e+08`
- Absolute delta: `-1.480791e+15`
- Relative delta: `-9.999996e-01`
- Status: **CRITICAL**

## All Divergent Factors

### I_before_scaling
- Description: Raw accumulated intensity before normalization
- C: `1.480792e+15`
- PyTorch: `5.873564e+08`
- Δ: `-1.480791e+15` (rel: -9.999996e-01)
- Status: **CRITICAL**

### I_pixel_final
- Description: Final normalized pixel intensity
- C: `446.254111`
- PyTorch: `466.40756`
- Δ: `20.1534491` (rel: +4.516137e-02)
- Status: **CRITICAL**

## Next Actions

1. Investigate root cause of I_before_scaling mismatch
2. Implement fix in Phase L3
3. Regenerate PyTorch trace after fix
4. Rerun this comparison to verify