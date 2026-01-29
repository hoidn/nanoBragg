# VI Benchmark Summary

**Date:** 2026-01-29T080653Z
**Command:** `KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 python scripts/benchmark_vi_mosaic.py --iterations 150 --outdir demo_outputs`
**Branch:** feature/spec-based-2

## Configuration

| Parameter | Value |
|-----------|-------|
| Iterations | 150 |
| Device | cpu |
| Init spread (deg) | 0.5 |
| True spread (deg) | 2.0 |
| Cell edge (A) | 100.0 |
| Wavelength (A) | 1.0 |
| Distance (mm) | 100.0 |
| Pixel size (mm) | 0.1 |
| Detector (fpixels x spixels) | 64 x 64 |

## Results

| Model | Final Loss | Final Spread (deg) | Mean Iter Time (s) |
|-------|-----------|--------------------|--------------------|
| MC baseline | 1.303e-04 | 1.460 | 0.0082 |
| Analytic | 3.780e-03 | 2.873 | 0.0049 |
| VI (K=4) | 729.95 | 0.152 | 0.0181 |

## Observations

- **MC baseline** converges to lowest loss (1.3e-04) and spread ~1.46 deg (vs true 2.0 deg).
- **Analytic** converges slower with higher final loss (3.8e-03) and overshoots spread to ~2.87 deg.
- **VI (K=4)** loss is on a different scale (Poisson ELBO ~729) and spread converges to ~0.15 deg, significantly underestimating the true 2.0 deg. VI per-iteration time is ~2.2x MC baseline.

## Artifacts

- `benchmark_vi_mosaic.log` - full stdout/stderr
- `vi_vs_mc_loss.png` - loss curve comparison plot
- `vi_vs_mc_summary.json` - raw numeric data
