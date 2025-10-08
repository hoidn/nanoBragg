# Scaling Chain Comparison: C vs PyTorch

Evidence run (manual harness) — 20251008T055257Z pixel (685,1039)

## Detailed Comparison

| Factor | C Value | PyTorch Value | Δ (abs) | Δ (rel) | Status |
|--------|---------|---------------|---------|---------|--------|
| I_before_scaling | 943654.809 | 805473.787 | -138181.022 | -1.464317e-01 | CRITICAL |
| r_e_sqr | 7.940792e-30 | 7.940792e-30 | 0.000000e+00 | +0.000000e+00 | PASS |
| fluence_photons_per_m2 | 1.000000e+24 | 1.000000e+24 | 0.000000e+00 | +0.000000e+00 | PASS |
| steps | 10 | 10 | 0.000000e+00 | +0.000000e+00 | PASS |
| capture_fraction | 1 | 1 | 0.000000e+00 | +0.000000e+00 | PASS |
| polar | 0.914639699 | 0.914639662 | -3.663390e-08 | -4.005282e-08 | PASS |
| omega_pixel | 4.204127e-07 | 4.204125e-07 | -2.026682e-13 | -4.820695e-07 | PASS |
| cos_2theta | 0.91064779 | 0.910647743 | -4.729859e-08 | -5.193950e-08 | PASS |
| I_pixel_final | 2.881395e-07 | 2.459466e-07 | -4.219290e-08 | -1.464322e-01 | CRITICAL |

## First Divergence

**I_before_scaling** — Raw accumulated intensity before normalization
- C: `943654.809`
- PyTorch: `805473.787`
- Δ abs: `-138181.022`
- Δ rel: -1.464317e-01
- Status: **CRITICAL**