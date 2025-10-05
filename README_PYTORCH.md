# nanoBragg PyTorch guide

This guide explains how to use the PyTorch implementation of nanoBragg for diffraction simulation, including parallel comparison with the C reference implementation.

## What This Is About

The PyTorch port of nanoBragg is a drop-in simulator that is also differentiable. Adaptations include:

- Vectorizing the legacy control flow: The C code walks sub-pixels, mosaic blocks, and sources with nested loops and early exits. We rebuilt those pieces as batched tensor ops so autograd sees a continuous graph.

  Example: nested loops → batched tensor ops

  ```c
  // C (nanoBragg.c core loops)
  for (spixel=0; spixel<spixels; ++spixel) {
    for (fpixel=0; fpixel<fpixels; ++fpixel) {
      imgidx = spixel*fpixels + fpixel;
      for (thick_tic=0; thick_tic<detector_thicksteps; ++thick_tic) {
        for (subS=0; subS<oversample; ++subS) {
          for (subF=0; subF<oversample; ++subF) {
            /* pixel_pos, diffracted, omega_pixel, capture_fraction */
            for (source=0; source<sources; ++source) {
              /* incident, lambda, scattering, stol, polar */
              for (phi_tic=0; phi_tic<phisteps; ++phi_tic) {
                /* rotate a0,b0,c0 by spindle phi → ap,bp,cp */
                for (mos_tic=0; mos_tic<mosaic_domains; ++mos_tic) {
                  /* apply mosaic rotation, compute h,k,l and h0,k0,l0 */
                  /* F_latt via sincg/sinc3/gauss/tophat; accumulate */
                }
              }
            }
          }
        }
      }
    }
  }
  ```

  ```python
  # PyTorch (vectorized, no Python loops; dims broadcast and reduce)
  # pixel_coords: (Sp, Fp, 3)
  # sources: (S, 3), wavelengths: (S,)
  # mosaic rotations: (M, 3, 3)
  diffracted = pixel_coords / pixel_coords.norm(dim=-1, keepdim=True)
  incident = sources.view(S, 1, 1, 3).expand(-1, Sp, Fp, -1)
  scat = (diffracted.unsqueeze(0) - incident) / wavelengths.view(S, 1, 1, 1)
  # rotate lattice vectors per mosaic domain and dot for h,k,l
  rot_a = (mosaic_umats @ a_vec).view(M, 3)
  h = (scat.unsqueeze(-2) @ rot_a.view(1,1,1,M,3,1)).squeeze(-1)
  # ... similar for k,l, then F_cell, F_latt ...
  intensity = ((F_cell * F_latt) ** 2 * weights.view(S,1,1,1)).sum(dim=0).sum(dim=-1)
  ```
- Killing implicit state: The reference implementation hides configuration in globals and scratch structs. We turned those into explicit tensor inputs.

  Example: beam direction (global → explicit)

  ```c
  // C (implicit global used across functions)
  double beam_vector[4] = {0,1,0,0};
  if (strstr(argv[i], "-beam_vector") && argc > i+3) {
      beam_vector[1] = atof(argv[i+1]);
      beam_vector[2] = atof(argv[i+2]);
      beam_vector[3] = atof(argv[i+3]);
  }
  ...
  ratio = dot_product(beam_vector, vector); // used implicitly downstream
  ```

  ```python
  # PyTorch (explicit config, explicit tensors)
  # __main__.py
  parser.add_argument('-beam_vector', nargs=3, type=float)
  if args.beam_vector:
      config['beam_vector'] = tuple(args.beam_vector)

  # detector/simulator: construct a tensor and pass explicitly
  if 'beam_vector' in config:
      beam_vec = torch.tensor(config['beam_vector'], device=device, dtype=dtype)
  else:
      beam_vec = default_beam_vector(convention)
  intensity = compute_physics_for_position(..., incident_beam_direction=beam_vec, ...)
  ```
- Example: stabilizing the shape factors.  One of many numerical landmines. Functions like sincg, sinc3, and polarization all contained removable singularities that autograd interpreted as "divide by zero." For sincg, we substituted in the L'Hôpital limits so the limit values are emitted directly:

  ```python
  eps = 1e-10
  u_over_pi = u / torch.pi
  nearest_int = torch.round(u_over_pi)
  is_near_int_pi = torch.abs(u_over_pi - nearest_int) < eps / torch.pi

  # lim u→nπ sin(Nu)/sin(u) = N * (-1)^{n(N-1)} (covers n = 0 as well)
  sign = torch.where(((nearest_int * (N - 1)).abs() % 2) >= 0.5,
                     -torch.ones_like(u), torch.ones_like(u))
  near_int_val = N * sign

  # fallback: sin(Nu)/sin(u); the eps guard is cheap insurance against tiny denominators
  ratio = torch.sin(N * u) / torch.where(torch.abs(torch.sin(u)) < eps,
                                         torch.ones_like(u) * eps,
                                         torch.sin(u))

  result = torch.where(is_near_int_pi, near_int_val, ratio)
  ```

Other adaptations: removing non‑differentiable ops

  Example: Nearest‑neighbor assignment → Tricubic interpolation
  ```python
  # Before (nearest neighbor lookup; non-differentiable w.r.t. h,k,l)
  h0 = torch.round(h).long(); k0 = torch.round(k).long(); l0 = torch.round(l).long()
  F_cell = Fhkl[h0 - h_min, k0 - k_min, l0 - l_min]

  # After (tricubic interpolation when enabled; differentiable a.e.)
  if interpolate:
      F_cell = polin3(h_indices, k_indices, l_indices, sub_Fhkl, h, k, l)
  else:
      F_cell = nearest_neighbor(h, k, l)
  ```

If you touch the physics helpers or geometry pipeline, rerun the C/PyTorch trace comparisons and gradient tests to catch any regressions.

## Table of Contents
- [What This Is About](#what-this-is-about)
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

These are the basic parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-lambda <Å>` | X-ray wavelength | Required |
| `-distance <mm>` | Detector distance | 100 |
| `-detpixels <N>` | Detector size (NxN) | 1024 |
| `-pixel <mm>` | Pixel size | 0.1 |
| `-N <cells>` | Crystal size (NxNxN unit cells) | 1 |
| `-mosaic <deg>` | Mosaic spread | 0 |
| `-misset x y z` | Crystal misorientation (degrees) | 0 0 0 |

See the C reference (README.md) for a more exhaustive listing and detailed descriptions.

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

### Benchmarks 
`python scripts/benchmarks/benchmark_detailed.py`

### Batch Visualization Script

The repository includes comparison scripts in `scripts/comparison/`. These requires building C nanoBragg first. All comparisons now pass with high (typically > .9999) correlation coefficients.

```bash
# Run visual comparison tests
./scripts/comparison/run_parallel_visual.py

# Runs 20 comparison tests and generates parallel_test_visuals/ directory with:
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
