# nanoBragg PyTorch guide

This guide explains how to use the PyTorch implementation of nanoBragg for diffraction simulation, including parallel comparison with the C reference implementation.

## Table of Contents
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Common Examples](#common-examples)
- [Test Suite](#test-suite)

## Installation

### Setup
```bash
# Install in editable mode (recommended)
pip install -e .

# Set environment variable to prevent MKL conflicts
export KMP_DUPLICATE_LIB_OK=TRUE
```

## Basic Usage

The PyTorch implementation provides a command-line interface compatible with the original C version.

### Command Line Interface

After installation, the `nanoBragg` command is available:

```bash
nanoBragg [options]
```

Or run directly without installation:
```bash
python3 -m nanobrag_torch [options]
```

### Required Parameters

You must provide either:
- **Crystal from MOSFLM matrix**: `-mat <file>` (with `-lambda` for wavelength)
- **Crystal from cell parameters**: `-cell a b c alpha beta gamma` (in Å and degrees)

Plus either:
- **Structure factors from HKL file**: `-hkl <file>`
- **Uniform structure factors**: `-default_F <value>`

### Essential Parameters

```bash
# Minimal example with cell parameters
python3 -m nanobrag_torch -cell 100 100 100 90 90 90 \
          -default_F 100 \
          -lambda 1.0 \
          -distance 100 \
          -detpixels 256 \
          -floatfile output.bin

```

### CLI Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-lambda <Å>` | X-ray wavelength | Required |
| `-distance <mm>` | Detector distance | 100 |
| `-detpixels <N>` | Detector size (NxN) | 1024 |
| `-pixel <mm>` | Pixel size | 0.1 |
| `-N <cells>` | Crystal size (NxNxN unit cells) | 1 |
| `-mosaic <deg>` | Mosaic spread | 0 |
| `-misset x y z` | Crystal misorientation (degrees) | 0 0 0 |

### Output Options

```bash
# Float image (32-bit raw binary)
-floatfile output.bin

# SMV format (integer with header)
-intfile output.img

# SMV with Poisson noise
-noisefile noisy.img

# 8-bit PNG preview
-pgmfile preview.pgm

# Region of Interest (pixels)
-roi xmin xmax ymin ymax
```

## Common Examples

### 1. Simple Cubic Crystal
```bash
nanoBragg -cell 100 100 100 90 90 90 \
          -default_F 100 \
          -lambda 6.2 \
          -N 5 \
          -distance 100 \
          -detpixels 1024 \
          -floatfile cubic.bin
```

### 2. Triclinic Crystal with Misset
```bash
nanoBragg -cell 70 80 90 85 95 105 \
          -default_F 100 \
          -lambda 1.5 \
          -N 1 \
          -misset 5 3 2 \
          -distance 150 \
          -detpixels 256 \
          -floatfile triclinic.bin
```

### 3. With HKL Structure Factors
```bash
nanoBragg -hkl ./tests/test_data/hkl_files/minimal.hkl \
          -cell 100 100 100 90 90 90 \
          -lambda 1.0 \
          -distance 100 \
          -detpixels 512 \
          -intfile diffraction.img
```

### 4. Detector Rotations
```bash
nanoBragg -cell 100 100 100 90 90 90 \
          -default_F 100 \
          -lambda 1.0 \
          -distance 100 \
          -detector_rotx 5 \
          -detector_roty 3 \
          -detector_rotz 2 \
          -floatfile rotated.bin
```

### 5. Different Detector Conventions
```bash
# MOSFLM convention (default)
nanoBragg -mosflm -cell 100 100 100 90 90 90 ...

# XDS convention
nanoBragg -xds -cell 100 100 100 90 90 90 ...
```


### Batch Visualization Script

The repository includes comparison scripts in `scripts/comparison/`. These requires building C nanoBragg first. All comparisons pass with high (>.99) correlation coefficients, but there are small discrepancies in some conditions still. 

```bash
# Run visual comparison tests
./scripts/comparison/run_parallel_visual.py

# Generates parallel_test_visuals/ directory with:
# - Side-by-side C vs PyTorch comparisons
# - Difference maps
# - Log-scale views
# - Intensity histograms
# - Correlation metrics
```

## Test Suite

### Running Tests

```bash
# Set environment
export KMP_DUPLICATE_LIB_OK=TRUE
export NB_RUN_PARALLEL=1  # Enable C comparison tests

# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_at_parallel_*.py -v  # Parallel validation tests
pytest tests/test_at_geo_*.py -v       # Geometry tests
pytest tests/test_gradients.py -v      # Gradient flow tests
```


### Key Test Categories

- **AT-PARALLEL-001 to 027**: C/PyTorch equivalence tests
- **AT-GEO**: Detector geometry validation
- **AT-STR**: Structure factor and crystal tests
- **AT-IO**: File I/O validation
- **Gradient tests**: Differentiability validation

## Troubleshooting

### Common Issues

1. **MKL Library Conflict**
   ```bash
   export KMP_DUPLICATE_LIB_OK=TRUE
   ```

2. **C Binary Not Found**
   ```bash
   export NB_C_BIN=./golden_suite_generator/nanoBragg
   # Or rebuild:
   make -C golden_suite_generator
   ```
