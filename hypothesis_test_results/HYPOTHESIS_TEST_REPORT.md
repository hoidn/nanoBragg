# Hypothesis Testing Report

**Generated**: 2025-09-09T22:34:55.890214
**Total Tests**: 30

## Summary

| Hypothesis | Tests | Mean Correlation | Mean Error (mm) | Std Error (mm) |
|------------|-------|-----------------|-----------------|----------------|
| H1: Different Rotation Centers | 9 | 0.0000 | 0.00 | 0.00 |
| H2: Beam Position Interpretation | 7 | 0.0000 | 0.00 | 0.00 |
| H4: Missing Coordinate Transformat | 3 | 0.0000 | 0.00 | 0.00 |
| H5: Detector Thickness/Parallax | 4 | 0.0000 | 0.00 | 0.00 |
| H6: Integer vs Fractional Pixel | 7 | 0.0000 | 0.00 | 0.00 |

## Detailed Results

### Hypothesis 1: Different Rotation Centers

**Number of tests**: 9
**Mean correlation**: 0.0000
**Mean error**: 0.00mm

| Test | Correlation | Error (mm) | Error Vector (mm) |
|------|-------------|------------|-------------------|
| distance_50mm | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| distance_100mm | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| distance_200mm | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| distance_400mm | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| rot_0_0_0 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| rot_5_0_0 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| rot_0_5_0 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| rot_0_0_5 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| rot_10_10_10 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |

### Hypothesis 2: Beam Position Interpretation

**Number of tests**: 7
**Mean correlation**: 0.0000
**Mean error**: 0.00mm

| Test | Correlation | Error (mm) | Error Vector (mm) |
|------|-------------|------------|-------------------|
| beam_0_0 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| beam_25.6_25.6 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| beam_51.2_51.2 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| beam_76.8_76.8 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| pixel_size_0.05mm | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| pixel_size_0.1mm | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| pixel_size_0.2mm | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |

### Hypothesis 4: Missing Coordinate Transformation

**Number of tests**: 3
**Mean correlation**: 0.0000
**Mean error**: 0.00mm

| Test | Correlation | Error (mm) | Error Vector (mm) |
|------|-------------|------------|-------------------|
| identity | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| pivot_BEAM | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| pivot_SAMPLE | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |

### Hypothesis 5: Detector Thickness/Parallax

**Number of tests**: 4
**Mean correlation**: 0.0000
**Mean error**: 0.00mm

| Test | Correlation | Error (mm) | Error Vector (mm) |
|------|-------------|------------|-------------------|
| incident_angle_0 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| incident_angle_15 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| incident_angle_30 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| incident_angle_45 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |

### Hypothesis 6: Integer vs Fractional Pixel

**Number of tests**: 7
**Mean correlation**: 0.0000
**Mean error**: 0.00mm

| Test | Correlation | Error (mm) | Error Vector (mm) |
|------|-------------|------------|-------------------|
| detector_size_512 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| detector_size_1024 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| detector_size_2048 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| beam_fraction_51.0 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| beam_fraction_51.2 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| beam_fraction_51.5 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |
| beam_fraction_51.7 | 0.0000 | 0.00 | [0.0, 0.0, 0.0] |

## Conclusions

Based on the test results:

- **Most likely hypothesis**: H1 - Different Rotation Centers
- **Error difference from 28mm**: 28.00mm
