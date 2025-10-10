# C Tap 5 Intensity Pre-Normalization Metrics

**Timestamp:** 20251010T112334Z
**Purpose:** Capture C-side Tap 5 (intensity pre-normalization) for comparison with PyTorch Attempt #29

## Pixel (0, 0) - Edge

```
TRACE_C_TAP5: pixel 0 0
TRACE_C_TAP5: I_before_scaling 141520.166457388
TRACE_C_TAP5: steps 4
TRACE_C_TAP5: omega_pixel 8.86109941671327e-09
TRACE_C_TAP5: capture_fraction 1
TRACE_C_TAP5: polar 0.961276939690433
TRACE_C_TAP5: I_pixel_final 0.000301366151806705
```

### Summary
- **I_before_scaling:** 1.415202e+05 (accumulated intensity before normalization)
- **steps:** 4 (oversample² = 2²)
- **omega_pixel:** 8.861099e-09 sr (solid angle)
- **capture_fraction:** 1.0 (no absorption)
- **polar:** 0.961277 (polarization factor)
- **I_pixel_final:** 3.013662e-04 (after r_e²·fluence/steps scaling and last-value multipliers)

## Pixel (2048, 2048) - Center

```
TRACE_C_TAP5: pixel 2048 2048
TRACE_C_TAP5: I_before_scaling 0
TRACE_C_TAP5: steps 4
TRACE_C_TAP5: omega_pixel 9.99999983125e-09
TRACE_C_TAP5: capture_fraction 1
TRACE_C_TAP5: polar 0.999999994375
TRACE_C_TAP5: I_pixel_final 0
```

### Summary
- **I_before_scaling:** 0.0 (no Bragg contribution, F_cell=0 for all subpixels)
- **steps:** 4 (oversample² = 2²)
- **omega_pixel:** 1.000000e-08 sr (solid angle, slightly higher than edge due to on-axis position)
- **capture_fraction:** 1.0 (no absorption)
- **polar:** 1.000000 (near-unity polarization at beam center)
- **I_pixel_final:** 0.0 (no intensity)

## Key Observations

1. **Edge vs Center Omega Ratio:** ω_center / ω_edge = 1.000000e-08 / 8.861099e-09 ≈ 1.129, matching PyTorch Attempt #29 (~1.13× ratio).

2. **Edge vs Center Polar Ratio:** polar_center / polar_edge = 1.000000 / 0.961277 ≈ 1.040, also matching PyTorch (~1.04× ratio).

3. **Steps Consistency:** Both pixels report `steps=4`, confirming oversample=2 produces 4 subpixel samples.

4. **Center Pixel Zero Intensity:** The center pixel (2048,2048) has `I_before_scaling=0` because all subpixels yield `F_cell=0` (HKL grid has no Bragg peaks near the direct beam for this configuration). This is expected behavior.

5. **Last-Value Semantics:** The C code applies `omega_pixel`, `polar`, and `capture_fraction` as last-value multipliers (line 3374-3376 in nanoBragg.c) when `oversample_thick/polar/omega` flags are NOT set (default behavior).

## Next Steps

Compare these C metrics with PyTorch Tap 5 metrics from Attempt #29:
- Edge pixel: I_before_scaling=3.54e4 (PyTorch) vs 1.415e5 (C) → ~4× discrepancy
- Center pixel: Both implementations report zero intensity (consistent)
- Omega/polar ratios: Both implementations show ~1.13×/1.04× centre/edge ratios (consistent)

**Hypothesis:** The ~4× intensity discrepancy at the edge pixel suggests a systematic scaling factor difference in the accumulated intensity term `I`, likely related to F_cell², F_latt², or the number of contributions per subpixel. This requires detailed comparison of per-subpixel F_cell and F_latt values in the next investigation phase.

