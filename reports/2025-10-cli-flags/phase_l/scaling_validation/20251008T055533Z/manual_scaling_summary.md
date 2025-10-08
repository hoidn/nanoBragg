# Scaling Chain Comparison: C vs PyTorch

Evidence run (manual harness) — 20251008T055533Z pixel (685,1039) c-parity mode

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

**I_before_scaling** — Raw accumulated intensity before normalization
- C: `943654.809`
- PyTorch: `941686.236`
- Δ abs: `-1968.57326`
- Δ rel: -2.086116e-03
- Status: **DIVERGENT**