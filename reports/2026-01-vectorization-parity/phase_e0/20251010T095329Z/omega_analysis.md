# Omega Asymmetry Analysis

- Timestamp (UTC): `20251010T095329Z`
- Oversample factor: `2`
- Detector pixels: 4096 × 4096, pixel size 0.05 mm, distance 500 mm
- Beam wavelength: 0.5 Å (unpolarized)

## Edge Pixel (0, 0)

### Subpixel Solid Angles (steradians)
| Subpixel | ω (sr) |
| --- | ---: |
| 0 | 8.860596932944e-09 |
| 1 | 8.860848168892e-09 |
| 2 | 8.860848168892e-09 |
| 3 | 8.861099416713e-09 |

### Summary Statistics
- Mean ω: `8.860848171860e-09`
- Min ω: `8.860596932944e-09`
- Max ω: `8.861099416713e-09`
- Last ω (flatten index -1): `8.861099416713e-09`
- Relative asymmetry (max-min)/mean: `0.000057`
- Last / mean ratio: `1.000028`

## Center Pixel (2048, 2048)

### Subpixel Solid Angles (steradians)
| Subpixel | ω (sr) |
| --- | ---: |
| 0 | 9.999999531250e-09 |
| 1 | 9.999999681250e-09 |
| 2 | 9.999999681250e-09 |
| 3 | 9.999999831250e-09 |

### Summary Statistics
- Mean ω: `9.999999681250e-09`
- Min ω: `9.999999531250e-09`
- Max ω: `9.999999831250e-09`
- Last ω (flatten index -1): `9.999999831250e-09`
- Relative asymmetry (max-min)/mean: `0.000000`
- Last / mean ratio: `1.000000`

### Interpretation
- Edge pixel: last subpixel ω is 0.00% relative to mean (positive → overweighted).
- Center pixel: last subpixel ω deviates 0.000% from mean (nearly symmetric).
- If PyTorch multiplies by the last subpixel ω (current behavior), edge pixels inherit this bias directly, explaining degraded full-frame correlation.