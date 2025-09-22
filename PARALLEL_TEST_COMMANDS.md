# AT-PARALLEL Test CLI Commands

This document lists all the command-line parameters used in the AT-PARALLEL test suite for comparing C and PyTorch implementations.

## AT-PARALLEL-001: Beam Center Scaling
Tests that beam center scales correctly with detector size.
```bash
# Base command (vary -detpixels)
-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 3 -distance 100 -detpixels [64|128|256|512|1024]
```

## AT-PARALLEL-002: Pixel Size Independence
Tests invariance to pixel size changes.
```bash
# Base command (vary -pixel)
-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 256 -distance 100 -pixel [0.05|0.1|0.2|0.4]
```

## AT-PARALLEL-003: Detector Offset Preservation
Tests detector offset handling.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100 -Xbeam 30 -Ybeam 40
```

## AT-PARALLEL-004: MOSFLM 0.5 Pixel Offset
Tests MOSFLM vs XDS convention differences.
```bash
# MOSFLM convention
-mosflm -default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100

# XDS convention
-xds -default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100
```

## AT-PARALLEL-005: Beam Center Parameter Mapping
Tests beam center parameter handling.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100 -Xbeam 25.6 -Ybeam 25.6
```

## AT-PARALLEL-006: Single Reflection Position
Tests single reflection positioning at different distances.
```bash
# Base command (vary -distance)
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance [50|100|200]
```

## AT-PARALLEL-007: Peak Position with Rotations
Tests peak positions with detector rotations.
```bash
# Base command with rotations
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100 -mosflm \
  -detector_rotx [0|5|10] -detector_roty [0|3|5] -detector_rotz [0|2|3]
```

## AT-PARALLEL-008: Multi-Peak Pattern Registration
Tests multiple peak patterns.
```bash
-default_F 100 -cell 70 80 90 75 85 95 -lambda 1.0 -N 5 -detpixels 512 -distance 100 -misset 10 5 3
```

## AT-PARALLEL-009: Intensity Normalization
Tests intensity scaling.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -distance 100 -detpixels 256 -fluence 1e24
```

## AT-PARALLEL-010: Solid Angle Corrections
Tests solid angle and obliquity corrections.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -distance 100 -detpixels 256 -point_pixel
```

## AT-PARALLEL-011: Polarization Factor Verification
Tests polarization corrections.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -distance 100 -detpixels 256 -polar 0.99
```

## AT-PARALLEL-012: Reference Pattern - Simple Cubic
Tests standard reference patterns.
```bash
# Simple cubic
-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 1024 -distance 100

# Triclinic
-default_F 100 -cell 70 80 90 75 85 95 -lambda 1.0 -N 5 -detpixels 512 -distance 100 -misset 10 5 3
```

## AT-PARALLEL-013: Cross-Platform Consistency
Tests consistency across platforms.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100
```

## AT-PARALLEL-014: Noise Robustness Test
Tests noise generation consistency.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100 \
  -noisefile noise.img -seed 42
```

## AT-PARALLEL-015: Mixed Unit Input Handling
Tests unit conversion handling.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -energy 12398.42 -N 5 -detpixels 256 -distance 100
```

## AT-PARALLEL-016: Extreme Scale Testing
Tests extreme parameter values.
```bash
# Very small crystal
-default_F 100 -cell 10 10 10 90 90 90 -lambda 0.1 -N 1 -detpixels 512 -distance 50

# Very large crystal
-default_F 100 -cell 1000 1000 1000 90 90 90 -lambda 10.0 -N 100 -detpixels 512 -distance 1000
```

## AT-PARALLEL-017: Grazing Incidence Geometry
Tests extreme detector geometries.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100 \
  -detector_rotx 85 -detector_roty 5 -twotheta 85
```

## AT-PARALLEL-018: Crystal Boundary Conditions
Tests edge cases in crystal geometry.
```bash
# Near-singular angles
-default_F 100 -cell 100 100 100 89.999 90.001 89.999 -lambda 1.0 -N 5 -detpixels 256 -distance 100
```

## AT-PARALLEL-019: (Not implemented - number skipped)

## AT-PARALLEL-020: Comprehensive Integration Test
Tests complete feature integration.
```bash
-default_F 100 -cell 70 80 90 85 95 105 -lambda 1.5 -N 8 -detpixels 512 -distance 150 \
  -misset 10 5 3 -mosaic 0.5 -mosaic_domains 10 -phi 0 -osc 5 -phisteps 5 \
  -fluence 1e24 -polar 0.99 -detector_rotx 5 -detector_roty 3 -detector_rotz 2
```

## AT-PARALLEL-021: Crystal Phi Rotation Equivalence
Tests phi rotation.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100 \
  -phi 0 -osc 5 -phisteps [1|10]
```

## AT-PARALLEL-022: Combined Detector+Crystal Rotation
Tests combined rotations.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100 \
  -phi 10 -osc 5 -phisteps 5 -detector_rotx 10 -detector_roty 5 -detector_rotz 3
```

## AT-PARALLEL-023: Misset Angles Equivalence
Tests misset angle handling.
```bash
# Various misset configurations
-default_F 100 -cell [100 100 100 90 90 90 | 70 80 90 85 95 105] -lambda 1.0 -N 5 \
  -detpixels 256 -distance 100 -misset [0 0 0 | 10 5 3 | 45 30 15 | -30 -45 -60 | 90 45 30]
```

## AT-PARALLEL-024: Random Misset Reproducibility
Tests random misset with seed.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100 \
  -misset -1 -1 -1 -mosaic_seed 42
```

## AT-PARALLEL-025: Maximum Intensity Position Alignment
Tests intensity maxima positions.
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100 \
  -Xbeam [25.6 | 30.0] -Ybeam [25.6 | 35.0]
```

## AT-PARALLEL-026: Absolute Peak Position for Triclinic Crystal
Tests triclinic crystal peak positions.
```bash
# Triclinic
-default_F 100 -cell 70 80 90 85 95 105 -lambda 1.5 -N 1 -detpixels 256 -distance 150 -misset 5 3 2

# Cubic comparison
-default_F 100 -cell 80 80 80 90 90 90 -lambda 1.5 -N 1 -detpixels 256 -distance 150 -misset 5 3 2
```

## AT-PARALLEL-027: Non-Uniform Structure Factor Pattern
Tests with HKL file input.
```bash
-hkl test_pattern.hkl -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100
```

---

## Common Parameter Patterns

### Crystal Definition
- `-cell a b c alpha beta gamma` - Unit cell parameters (Å and degrees)
- `-N n` - Crystal size (n×n×n unit cells)
- `-misset dx dy dz` - Misset angles (degrees)
- `-mosaic spread` - Mosaic spread (degrees)
- `-mosaic_domains n` - Number of mosaic domains

### Beam Parameters
- `-lambda wavelength` - X-ray wavelength (Å)
- `-energy eV` - Alternative to lambda (eV)
- `-fluence photons/m²` - Total integrated intensity
- `-polar factor` - Polarization factor (0-1)

### Detector Parameters
- `-detpixels n` - Detector size (n×n pixels)
- `-pixel size` - Pixel size (mm)
- `-distance d` - Detector distance (mm)
- `-Xbeam x` - Beam center X (mm)
- `-Ybeam y` - Beam center Y (mm)
- `-detector_rotx/y/z angle` - Detector rotations (degrees)
- `-twotheta angle` - Two-theta angle (degrees)

### Conventions
- `-mosflm` - Use MOSFLM convention
- `-xds` - Use XDS convention

### Output
- `-floatfile file.bin` - Output binary float image
- `-intfile file.img` - Output SMV format
- `-noisefile file.img` - Output with Poisson noise
- `-seed n` - Random seed for reproducibility

### Structure Factors
- `-default_F value` - Uniform structure factor
- `-hkl file.hkl` - Read structure factors from file