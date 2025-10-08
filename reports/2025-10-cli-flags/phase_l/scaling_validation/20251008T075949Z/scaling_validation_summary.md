# Scaling Chain Comparison: C vs PyTorch

**Phase L3e Validation** (CLI-FLAGS-003)

**Tolerance:** ≤1.00e-06 relative

## Summary

Comparing scaling factors for supervisor command pixel (685, 1039).

## Detailed Comparison

| Factor | C Value | PyTorch Value | Δ (abs) | Δ (rel) | Status |
|--------|---------|---------------|---------|---------|--------|
| I_before_scaling | 943654.809 | 941686.236 | -1968.57326 | -2.086116e-03 | DIVERGENT |
| r_e_sqr | 7.940792e-30 | 7.940792e-30 | 0.000000e+00 | +0.000000e+00 | PASS |
| fluence_photons_per_m2 | 1.000000e+24 | 1.000000e+24 | 0.000000e+00 | +0.000000e+00 | PASS |
| steps | 10 | 10 | 0.000000e+00 | +0.000000e+00 | PASS |
| capture_fraction | 1 | 1 | 0.000000e+00 | +0.000000e+00 | PASS |
| polar | 0.914639699 | 0.914639662 | -3.663390e-08 | -4.005282e-08 | PASS |
| omega_pixel | 4.204127e-07 | 4.204125e-07 | -2.026682e-13 | -4.820695e-07 | PASS |
| cos_2theta | 0.91064779 | 0.910647743 | -4.729859e-08 | -5.193950e-08 | PASS |
| I_pixel_final | 2.881395e-07 | 2.875383e-07 | -6.012426e-10 | -2.086637e-03 | DIVERGENT |

## First Divergence

**I_before_scaling** (Raw accumulated intensity before normalization)

- C value: `943654.809`
- PyTorch value: `941686.236`
- Absolute delta: `-1968.57326`
- Relative delta: `-2.086116e-03`
- Status: **DIVERGENT**

## All Divergent Factors

### I_before_scaling
- Description: Raw accumulated intensity before normalization
- C: `943654.809`
- PyTorch: `941686.236`
- Δ: `-1968.57326` (rel: -2.086116e-03)
- Status: **DIVERGENT**

### I_pixel_final
- Description: Final normalized pixel intensity
- C: `2.881395e-07`
- PyTorch: `2.875383e-07`
- Δ: `-6.012426e-10` (rel: -2.086637e-03)
- Status: **DIVERGENT**

## Next Actions

1. Investigate root cause of I_before_scaling mismatch
2. Implement fix in Phase L3
3. Regenerate PyTorch trace after fix
4. Rerun this comparison to verify