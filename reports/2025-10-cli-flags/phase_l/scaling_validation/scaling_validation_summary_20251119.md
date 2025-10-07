# Scaling Chain Comparison: C vs PyTorch

**Phase L3e Validation** (CLI-FLAGS-003)

**Tolerance:** ≤1.00e-06 relative

## Summary

Comparing scaling factors for supervisor command pixel (685, 1039).

## Detailed Comparison

| Factor | C Value | PyTorch Value | Δ (abs) | Δ (rel) | Status |
|--------|---------|---------------|---------|---------|--------|
| I_before_scaling | 943654.809 | 713431 | -230223.809 | -2.439704e-01 | CRITICAL |
| r_e_sqr | 7.940792e-30 | 7.940793e-30 | 2.457168e-37 | +3.094361e-08 | PASS |
| fluence_photons_per_m2 | 1.000000e+24 | 1.000000e+24 | 1.384843e+16 | +1.384843e-08 | PASS |
| steps | 10 | 10 | 0.000000e+00 | +0.000000e+00 | PASS |
| capture_fraction | 1 | 1 | 0.000000e+00 | +0.000000e+00 | PASS |
| polar | 0.914639699 | 0.91464138 | 1.68136555e-06 | +1.838282e-06 | MINOR |
| omega_pixel | 4.204127e-07 | 4.204049e-07 | -7.825097e-12 | -1.861289e-05 | MINOR |
| cos_2theta | 0.91064779 | 0.910649598 | 1.80739381e-06 | +1.984734e-06 | MINOR |
| I_pixel_final | 2.881395e-07 | 2.381680e-07 | -4.997154e-08 | -1.734283e-01 | CRITICAL |

## First Divergence

**I_before_scaling** (Raw accumulated intensity before normalization)

- C value: `943654.809`
- PyTorch value: `713431`
- Absolute delta: `-230223.809`
- Relative delta: `-2.439704e-01`
- Status: **CRITICAL**

## All Divergent Factors

### I_before_scaling
- Description: Raw accumulated intensity before normalization
- C: `943654.809`
- PyTorch: `713431`
- Δ: `-230223.809` (rel: -2.439704e-01)
- Status: **CRITICAL**

### polar
- Description: Kahn polarization factor
- C: `0.914639699`
- PyTorch: `0.91464138`
- Δ: `1.68136555e-06` (rel: +1.838282e-06)
- Status: **MINOR**

### omega_pixel
- Description: Solid angle (steradians)
- C: `4.204127e-07`
- PyTorch: `4.204049e-07`
- Δ: `-7.825097e-12` (rel: -1.861289e-05)
- Status: **MINOR**

### cos_2theta
- Description: Cosine of scattering angle 2θ
- C: `0.91064779`
- PyTorch: `0.910649598`
- Δ: `1.80739381e-06` (rel: +1.984734e-06)
- Status: **MINOR**

### I_pixel_final
- Description: Final normalized pixel intensity
- C: `2.881395e-07`
- PyTorch: `2.381680e-07`
- Δ: `-4.997154e-08` (rel: -1.734283e-01)
- Status: **CRITICAL**

## Next Actions

1. Investigate root cause of I_before_scaling mismatch
2. Implement fix in Phase L3
3. Regenerate PyTorch trace after fix
4. Rerun this comparison to verify