# Scaling Chain Comparison: C vs PyTorch

**Phase L2c Analysis** (CLI-FLAGS-003)

## Summary

Comparing scaling factors for supervisor command pixel (685, 1039).

## Detailed Comparison

| Factor | C Value | PyTorch Value | Δ (abs) | Δ (%) | Status |
|--------|---------|---------------|---------|-------|--------|
| I_before_scaling | 943654.809 | NOT_EXTRACTED | N/A | N/A | MISSING |
| r_e_sqr | 7.940792e-30 | 7.940792e-30 | 0.000000e+00 | +0.000 | MATCH |
| fluence_photons_per_m2 | 1.000000e+24 | 1.000000e+24 | 1.384843e+16 | +0.000 | MATCH |
| steps | 10 | 10 | 0.000000e+00 | +0.000 | MATCH |
| capture_fraction | 1 | 1 | 0.000000e+00 | +0.000 | MATCH |
| polar | 0.914639699 | 0.000000e+00 | -0.914639699 | -100.000 | CRITICAL |
| omega_pixel | 4.204127e-07 | 4.204127e-07 | 0.000000e+00 | +0.000 | MATCH |
| cos_2theta | 0.91064779 | NOT_EXTRACTED | N/A | N/A | MISSING |
| I_pixel_final | 2.881395e-07 | 0.000000e+00 | -2.881395e-07 | -100.000 | CRITICAL |

## First Divergence

**I_before_scaling** (Raw accumulated intensity before normalization)

- C value: `943654.809`
- PyTorch value: `NOT_EXTRACTED`
- Status: **MISSING**

## All Divergent Factors

### I_before_scaling
- Description: Raw accumulated intensity before normalization
- C: `943654.809`
- PyTorch: `NOT_EXTRACTED`
- Status: **MISSING**

### polar
- Description: Kahn polarization factor
- C: `0.914639699`
- PyTorch: `0.000000e+00`
- Δ: `-0.914639699` (-100.000% if available)
- Status: **CRITICAL**

### cos_2theta
- Description: Cosine of scattering angle 2θ
- C: `0.91064779`
- PyTorch: `NOT_EXTRACTED`
- Status: **MISSING**

### I_pixel_final
- Description: Final normalized pixel intensity
- C: `2.881395e-07`
- PyTorch: `0.000000e+00`
- Δ: `-2.881395e-07` (-100.000% if available)
- Status: **CRITICAL**

## Next Actions

1. Investigate root cause of I_before_scaling mismatch
2. Implement fix in Phase L3
3. Regenerate PyTorch trace after fix
4. Rerun this comparison to verify