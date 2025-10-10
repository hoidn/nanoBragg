# Omega Subpixel Comparison: C vs PyTorch
**Date:** 2025-10-10T10:01:02Z  
**Detector:** 4096×4096, pixel=0.05mm, distance=500mm, λ=0.5Å  
**Oversample:** 2×2

## Executive Summary

**Finding:** C code uses **identical omega values for all subpixels** when `oversample_omega=False` (default). The last-value semantics observed in PyTorch (Attempt #23) is **not** present in the C implementation.

**Implication:** The 0.721 correlation collapse cannot be attributed to oversample last-value bias. The C code computes omega once per pixel and reuses it for all 4 subpixels, making edge vs. center differences irrelevant.

## C Omega Tap Data

### Edge Pixel (0,0)
```
subpixel=(0,0): 8.86109941671327e-09 sr
subpixel=(0,1): 8.86109941671327e-09 sr
subpixel=(1,0): 8.86109941671327e-09 sr
subpixel=(1,1): 8.86109941671327e-09 sr
```
- **Mean:** 8.8611e-09 sr
- **Last:** 8.8611e-09 sr
- **Last/Mean:** 1.0000 (perfect)
- **Relative Asymmetry:** 0.0000 (all identical)

### Center Pixel (2048,2048)
```
subpixel=(0,0): 9.99999983125e-09 sr
subpixel=(0,1): 9.99999983125e-09 sr
subpixel=(1,0): 9.99999983125e-09 sr
subpixel=(1,1): 9.99999983125e-09 sr
```
- **Mean:** 1.0000e-08 sr
- **Last:** 1.0000e-08 sr
- **Last/Mean:** 1.0000 (perfect)
- **Relative Asymmetry:** 0.0000 (all identical)

## PyTorch Omega Tap Data (Attempt #23)

### Edge Pixel (0,0)
- **Last/Mean:** 1.000028 (~0.003% bias)
- **Relative Asymmetry:** 5.7×10⁻⁵

### Center Pixel (2048,2048)
- **Last/Mean:** ≈1.0
- **Relative Asymmetry:** ≈0

## Analysis

### C Code Behavior
From `nanoBragg.c:2965-2971`:
```c
if(omega_pixel == 0.0 || oversample_omega)
{
    /* this is either the first time for this pixel, or we are oversampling omega */
    omega_pixel = pixel_size*pixel_size/airpath/airpath*close_distance/airpath;
    if(point_pixel) omega_pixel = 1.0/airpath/airpath;
}
```

When `oversample_omega=False` (default), the condition `omega_pixel == 0.0` is true **only on the first subpixel** (0,0). For subsequent subpixels (0,1), (1,0), (1,1), `omega_pixel` retains its value from the first iteration → **all 4 subpixels use the same omega**.

### PyTorch Deviation
PyTorch (Attempt #23) computed distinct omega values for each subpixel, introducing a small (~0.003%) last-value bias at the edge. However, this deviation is **backwards** — PyTorch was more precise than the C code, not less.

### Hypothesis Rejection
**Primary hypothesis:** Last-value omega weighting causes edge divergence → **REJECTED**.

The C code's oversample loop **does not** average omega values; it simply reuses the first subpixel's omega for all subsequent subpixels. This is semantically equivalent to "last-value" if you only consider the final multiplication, but it's actually "first-value" during accumulation.

## Conclusion

The Phase E omega hypothesis is **refuted**. Differences in omega handling explain at most ~0.003% of the intensity variation, far below the ~28% error needed to explain corr=0.721.

**Next Actions:**
1. Pivot to alternate hypotheses: F_cell default usage (Tap 4) or water background scaling (Tap 6).
2. Review normalization steps and scaling factor application order.
3. Consider full-frame ROI masking differences (PyTorch post-hoc mask vs C skip).

## References
- C tap: `reports/2026-01-vectorization-parity/phase_e0/20251010T100102Z/c_taps/tap_omega.txt`
- PyTorch tap: `reports/2026-01-vectorization-parity/phase_e0/20251010T095445Z/py_taps/omega_metrics.json`
- Plan Phase E table: `plans/active/vectorization-parity-regression.md`
