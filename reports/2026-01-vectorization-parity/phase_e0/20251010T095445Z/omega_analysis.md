# Omega Asymmetry Analysis

- Timestamp (UTC): `20251010T095445Z`
- Oversample factor: `2`
- Detector pixels: 4096 × 4096, pixel size 0.05 mm, distance 500 mm
- Beam wavelength: 0.5 Å (unpolarized)

## Edge Pixel (0, 0)

### Subpixel Solid Angles (steradians)
| Subpixel | ω (sr) |
| --- | ---: |
| 0 | 8.861099416713e-09 |
| 1 | 8.861350615094e-09 |
| 2 | 8.861350615094e-09 |
| 3 | 8.861601825343e-09 |

### Summary Statistics
- Mean ω: `8.861350618061e-09`
- Min ω: `8.861099416713e-09`
- Max ω: `8.861601825343e-09`
- Last ω (flatten index -1): `8.861601825343e-09`
- Relative asymmetry (max-min)/mean: `0.000057`
- Last / mean ratio: `1.000028`

## Center Pixel (2048, 2048)

### Subpixel Solid Angles (steradians)
| Subpixel | ω (sr) |
| --- | ---: |
| 0 | 9.999999831250e-09 |
| 1 | 9.999999906250e-09 |
| 2 | 9.999999906250e-09 |
| 3 | 9.999999981250e-09 |

### Summary Statistics
- Mean ω: `9.999999906250e-09`
- Min ω: `9.999999831250e-09`
- Max ω: `9.999999981250e-09`
- Last ω (flatten index -1): `9.999999981250e-09`
- Relative asymmetry (max-min)/mean: `0.000000`
- Last / mean ratio: `1.000000`

### Interpretation
- Last-value bias = `last_over_mean - 1.0`; values above zero indicate overweighting.
- Edge last-value bias: `0.000028` (~0.003% of mean).
- Center last-value bias: `0.000000` (~0.000% of mean).
- PyTorch multiplies accumulated intensity by the last ω when `oversample_omega=False`; these metrics measure the magnitude of that weighting.