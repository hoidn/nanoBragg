# Scaling Chain Comparison: C vs PyTorch

**Phase L3e Validation** (CLI-FLAGS-003)

**Tolerance:** ≤1.00e-06 relative

## Summary

Comparing scaling factors for supervisor command pixel (685, 1039).

## Detailed Comparison

| Factor | C Value | PyTorch Value | Δ (abs) | Δ (rel) | Status |
|--------|---------|---------------|---------|---------|--------|
| I_before_scaling | 943654.809 | 0.511304203 | -943654.298 | -9.999995e-01 | CRITICAL |
| r_e_sqr | 7.940792e-30 | 7.940792e-30 | 0.000000e+00 | +0.000000e+00 | PASS |
| fluence_photons_per_m2 | 1.000000e+24 | 1.000000e+24 | 0.000000e+00 | +0.000000e+00 | PASS |
| steps | 10 | 10 | 0.000000e+00 | +0.000000e+00 | PASS |
| capture_fraction | 1 | 1 | 0.000000e+00 | +0.000000e+00 | PASS |
| polar | 0.914639699 | 0.914423324 | -0.000216375246 | -2.365688e-04 | DIVERGENT |
| omega_pixel | 4.204127e-07 | 4.200881e-07 | -3.245738e-10 | -7.720361e-04 | DIVERGENT |
| cos_2theta | 0.91064779 | 0.910410146 | -0.000237643929 | -2.609614e-04 | DIVERGENT |
| I_pixel_final | 2.881395e-07 | 4.060161e-07 | 1.178765e-07 | +4.090952e-01 | CRITICAL |

## First Divergence

**I_before_scaling** (Raw accumulated intensity before normalization)

- C value: `943654.809`
- PyTorch value: `0.511304203`
- Absolute delta: `-943654.298`
- Relative delta: `-9.999995e-01`
- Status: **CRITICAL**

## All Divergent Factors

### I_before_scaling
- Description: Raw accumulated intensity before normalization
- C: `943654.809`
- PyTorch: `0.511304203`
- Δ: `-943654.298` (rel: -9.999995e-01)
- Status: **CRITICAL**

### polar
- Description: Kahn polarization factor
- C: `0.914639699`
- PyTorch: `0.914423324`
- Δ: `-0.000216375246` (rel: -2.365688e-04)
- Status: **DIVERGENT**

### omega_pixel
- Description: Solid angle (steradians)
- C: `4.204127e-07`
- PyTorch: `4.200881e-07`
- Δ: `-3.245738e-10` (rel: -7.720361e-04)
- Status: **DIVERGENT**

### cos_2theta
- Description: Cosine of scattering angle 2θ
- C: `0.91064779`
- PyTorch: `0.910410146`
- Δ: `-0.000237643929` (rel: -2.609614e-04)
- Status: **DIVERGENT**

### I_pixel_final
- Description: Final normalized pixel intensity
- C: `2.881395e-07`
- PyTorch: `4.060161e-07`
- Δ: `1.178765e-07` (rel: +4.090952e-01)
- Status: **CRITICAL**

## Next Actions

1. Investigate root cause of I_before_scaling mismatch
2. Implement fix in Phase L3
3. Regenerate PyTorch trace after fix
4. Rerun this comparison to verify