# Phase C1 C Trace Artifacts

**Date:** 2025-10-10T04:48:47Z  
**Git SHA:** 6d841a84  
**Configuration:** 4096² MOSFLM, λ=0.5Å, distance=500mm, pixel=0.05mm

## Captured Traces

All three pixel traces completed successfully:

1. **pixel_2048_2048.log** — ROI center, on-peak baseline (72 TRACE_C lines)
2. **pixel_1792_2048.log** — ROI boundary, first row outside ROI (72 TRACE_C lines)
3. **pixel_4095_2048.log** — Far edge, probe inflation hypothesis (72 TRACE_C lines)

## Trace Contents

Each log contains:
- Detector geometry trace (pix0_vector, basis vectors after rotations)
- Pixel-specific physics (I_before_scaling, r_e_sqr, fluence, steps, capture_fraction, polar, omega_pixel)
- Final scaled intensity

## Usage for Phase C2

These C traces serve as ground truth for Phase C2 PyTorch trace comparison. The PyTorch traces must match these values to ≥12 significant digits for alignment validation.

## Commands

See `../commands.txt` for exact reproduction commands.
See `../env.json` for complete environment metadata.
