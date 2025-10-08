# Scaling Chain Comparison: C vs PyTorch

**Phase L3e Validation** (CLI-FLAGS-003)

**Tolerance:** ≤1.00e-06 relative

## Summary

Comparing scaling factors for supervisor command pixel (685, 1039).

## Detailed Comparison

| Factor | C Value | PyTorch Value | Δ (abs) | Δ (rel) | Status |
|--------|---------|---------------|---------|---------|--------|
| I_before_scaling | 943654.809 | 861314.812 | -82339.9967 | -8.725648e-02 | CRITICAL |
| r_e_sqr | 7.940792e-30 | 7.940793e-30 | 2.457168e-37 | +3.094361e-08 | PASS |
| fluence_photons_per_m2 | 1.000000e+24 | 1.000000e+24 | 1.384843e+16 | +1.384843e-08 | PASS |
| steps | 10 | 10 | 0.000000e+00 | +0.000000e+00 | PASS |
| capture_fraction | 1 | 1 | 0.000000e+00 | +0.000000e+00 | PASS |
| polar | 0.914639699 | 0.914639652 | -4.716915e-08 | -5.157129e-08 | PASS |
| omega_pixel | 4.204127e-07 | 4.204126e-07 | -6.596993e-14 | -1.569171e-07 | PASS |
| cos_2theta | 0.91064779 | 0.91064775 | -4.035018e-08 | -4.430931e-08 | PASS |
| I_pixel_final | 2.881395e-07 | 2.875420e-07 | -5.975063e-10 | -2.073670e-03 | DIVERGENT |

## First Divergence

**I_before_scaling** (Raw accumulated intensity before normalization)

- C value: `943654.809`
- PyTorch value: `861314.812`
- Absolute delta: `-82339.9967`
- Relative delta: `-8.725648e-02`
- Status: **CRITICAL**

## All Divergent Factors

### I_before_scaling
- Description: Raw accumulated intensity before normalization
- C: `943654.809`
- PyTorch: `861314.812`
- Δ: `-82339.9967` (rel: -8.725648e-02)
- Status: **CRITICAL**

### I_pixel_final
- Description: Final normalized pixel intensity
- C: `2.881395e-07`
- PyTorch: `2.875420e-07`
- Δ: `-5.975063e-10` (rel: -2.073670e-03)
- Status: **DIVERGENT**

## Next Actions

1. Investigate root cause of I_before_scaling mismatch
2. Implement fix in Phase L3
3. Regenerate PyTorch trace after fix
4. Rerun this comparison to verify