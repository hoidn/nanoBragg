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
- Factoring out implicit state: The reference implementation hides configuration in globals and scratch structs. We turned those into explicit tensor inputs.

  Example 1: Parameters like `fluence`, `r_e_sqr`, `Na`, `Nb`, `Nc`, and crystal vectors are declared in `main()` and used deep inside the loops without being passed as arguments. This creates hidden dependencies.
```c
// In nanoBragg.c main()
double fluence = 1e12;
double Na=5, Nb=5, Nc=5;

// ... deep inside loops ...
// F_latt uses Na, Nb, Nc implicitly
F_latt = sincg(M_PI*h, Na) * ...

// Intensity scaling uses fluence implicitly
test = r_e_sqr * fluence * I / steps;
```

**PyTorch Equivalent (Explicit State Passing)**
All parameters are explicitly passed to the core physics function. This makes the data flow clear and allows `torch.compile` to safely cache the function, as its behavior is self-contained.
```python
# In simulator.py
def compute_physics_for_position(
    ...,
    Na, Nb, Nc,  # Explicitly passed
    ...
):
    F_latt = sincg(torch.pi * h, Na) * ...
    return (F_cell * F_latt) ** 2

# In Simulator.run()
physics_intensity = self._compute_physics_for_position(
    ...,
    Na=self.crystal.N_cells_a, ...
)
final_intensity = physics_intensity * self.r_e_sqr * self.fluence
```

Example 2:

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

  The `floatimage` array is a shared state buffer that is modified iteratively. The `I += ...` pattern inside the loops breaks the chain of operations needed for backpropagation.
```c
// In nanoBragg.c
float *floatimage = calloc(...);

// ... deep inside 7 nested loops ...
for(mos_tic=0; mos_tic<mosaic_domains; ++mos_tic) {
    // ... calculate F_cell, F_latt ...
    I += F_cell*F_cell*F_latt*F_latt;
}
// ...
floatimage[imgidx] += I / steps * ...;
```

**PyTorch Equivalent (Declarative & Vectorized)**
The entire calculation is a single expression. `intensity` is computed for all points at once. The loops are replaced by tensor dimensions, and the accumulation is a final, differentiable `torch.sum()` operation.
```python
# In simulator.py
# Dims: S=source, P=pixel, Φ=phi, M=mosaic

# Compute F_cell, F_latt for all points
# Shape: (S, P, Φ, M)
F_total = F_cell * F_latt

# Compute intensity for all points
intensity_contributions = F_total ** 2

# Sum over orientation & source dimensions
# This is the differentiable equivalent of the C loops
total_intensity = torch.sum(
    intensity_contributions * source_weights,
    dim=(0, -1, -2)
)
```

### Setting up automatic differentiation 

#### 1. Making a Parameter Differentiable

To make a parameter differentiable, define it as a `torch.Tensor` with `requires_grad=True` and pass it into the appropriate configuration object.

**Example: Getting the Gradient for a Detector Rotation**
```python
import torch
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.config import CrystalConfig, DetectorConfig

# 1. Define parameter as a tensor with requires_grad=True
rotx_deg = torch.tensor([5.0], dtype=torch.float64, requires_grad=True)

# 2. Pass it to the configuration
detector_config = DetectorConfig(detector_rotx_deg=rotx_deg)
sim = Simulator(Crystal(CrystalConfig()), Detector(detector_config))

# 3. Run simulation and compute a scalar loss
intensity_image = sim.run()
loss = torch.sum(intensity_image)

# 4. Backpropagate to compute the gradient
loss.backward()

print(f"Gradient w.r.t. detector_rotx_deg: {rotx_deg.grad.item()}")
```

#### 2. Testing Gradients with `gradcheck`

`torch.autograd.gradcheck` is the standard tool for verifying your gradients. It compares the analytical gradient from autograd with a numerical approximation. A successful check confirms your computation is differentiable.

`gradcheck` is sensitive to numerical precision and should always be run using `torch.float64`.

You must wrap your simulation in a function that takes only the differentiable tensor as input and returns a scalar loss.

**Example: Verifying the Gradient for `detector_rotx_deg`**
```python
from torch.autograd import gradcheck

# Define the parameter to test (must be float64)
rotx_deg_init = torch.tensor([5.0], dtype=torch.float64, requires_grad=True)

# 1. Wrap the simulation in a function for gradcheck
def simulation_func(rotx_tensor):
    sim = Simulator(
        Crystal(CrystalConfig()),
        Detector(DetectorConfig(detector_rotx_deg=rotx_tensor)),
        dtype=torch.float64  # Ensure simulator runs in double precision
    )
    return torch.sum(sim.run())

# 2. Run gradcheck
try:
    test_passed = gradcheck(simulation_func, (rotx_deg_init,), atol=1e-4)
    print(f"Gradient check passed: {test_passed}")
except Exception as e:
    print(f"Gradient check failed: {e}")
```

### Debugging gradient propagation 

The problems typically fall into one of these classes:

- Numerical instability (e.g. sing singular points)
- Non-differntiable expressions (e.g. nearest neigbor assignment, clamping, rounding)
- Conditionals (if / else statements must be converted to binary mask selection)
- Non-differentiable tensor ops (e.g. .item(), .abs(), arange, etc.)

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
