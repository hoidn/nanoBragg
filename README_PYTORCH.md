# nanoBragg PyTorch - User Guide

This guide explains how to use the PyTorch implementation of nanoBragg for diffraction simulation, including parallel comparison with the C reference implementation.

## Table of Contents
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Common Examples](#common-examples)
- [Parallel C/PyTorch Comparison](#parallel-cpytorch-comparison)
- [Visualization Tools](#visualization-tools)
- [Test Suite](#test-suite)
- [Troubleshooting](#troubleshooting)
- [Performance](#performance)
- [Known Limitations](#known-limitations)
 - [Stage-A Parameterized Experiment](#stage-a-parameterized-experiment)

## PyTorch Runtime Guardrails

- Ensure all simulator changes remain **fully vectorized** (extend the broadcast dimensions instead of adding Python loops).
- Keep tensors on the caller’s **device/dtype**; preload configuration tensors onto the target device and avoid per-iteration `.to()` shims.
- Run CPU and CUDA smoke tests (see `docs/development/pytorch_runtime_checklist.md`) before declaring success.

Refer to [`docs/development/pytorch_runtime_checklist.md`](docs/development/pytorch_runtime_checklist.md) for the full checklist.

## Installation

### Prerequisites
- Python 3.11+
- PyTorch 2.0+
- NumPy, Matplotlib, SciPy

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd nanoBragg

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
nanoBragg -cell 100 100 100 90 90 90 \
          -default_F 100 \
          -lambda 1.0 \
          -distance 100 \
          -detpixels 256 \
          -floatfile output.bin

# With MOSFLM matrix
nanoBragg -mat orientation.mat \
          -hkl P1.hkl \
          -lambda 6.2 \
          -distance 100 \
          -detpixels 1024 \
          -floatfile output.bin
```

### Key Parameters

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
nanoBragg -hkl mystructure.hkl \
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

## Stage-A Parameterized Experiment

For gradient-based refinement of crystal, detector, and beam parameters (“Stage-A”
optimization), the PyTorch implementation provides a high-level `ExperimentModel`
API on top of the existing `Simulator`:

```python
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.models.experiment import ExperimentModel

crystal_cfg = CrystalConfig(cell_a=100.0, cell_b=100.0, cell_c=100.0)
detector_cfg = DetectorConfig(distance_mm=100.0, pixel_size_mm=0.1)
beam_cfg = BeamConfig(wavelength_A=1.0)

# Stage-A learnable mode
experiment = ExperimentModel(
    crystal_config=crystal_cfg,
    detector_config=detector_cfg,
    beam_config=beam_cfg,
    param_init="stage_a",
    device="cuda",
)

optimizer = torch.optim.Adam(experiment.parameters(), lr=1e-2)
target = ...  # target float image tensor

for _ in range(num_steps):
    optimizer.zero_grad()
    pred = experiment()
    loss = ((pred - target) ** 2).mean()
    loss.backward()
    optimizer.step()
```

To run with no learnable parameters (pure config-driven behavior) while using
the same wrapper, set `param_init="frozen"`; in that mode
`ExperimentModel.parameters()` is empty and the output matches the legacy
`Simulator` path for the same configs.

See `docs/architecture/parameterized_experiment.md` for the full specification
of Stage-A degrees of freedom and parameter mappings.

## Parallel C/PyTorch Comparison

### Using nb-compare Tool

The `nb-compare` tool runs both C and PyTorch implementations and compares outputs:

```bash
# Basic comparison
nb-compare -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100

# With custom output directory
nb-compare --outdir my_comparison -- -default_F 100 -cell 100 100 100 90 90 90 ...

# Specify C binary location
nb-compare --c-bin ./golden_suite_generator/nanoBragg -- [arguments...]

# With ROI for faster testing
nb-compare --roi 100 156 100 156 -- [arguments...]
```

The tool generates:
- `c_output.bin` - C implementation output
- `pytorch_output.bin` - PyTorch output
- `comparison.png` - Visual comparison
- `metrics.txt` - Correlation and RMSE metrics

### Manual Comparison

```bash
# Set the C binary path
export NB_C_BIN=./golden_suite_generator/nanoBragg

# Run C version
$NB_C_BIN -cell 100 100 100 90 90 90 -default_F 100 -lambda 1.0 \
          -distance 100 -detpixels 256 -floatfile c_output.bin

# Run PyTorch version
nanoBragg -cell 100 100 100 90 90 90 -default_F 100 -lambda 1.0 \
          -distance 100 -detpixels 256 -floatfile py_output.bin

# Compare using Python
python3 -c "
import numpy as np
import matplotlib.pyplot as plt

# Load images
c_img = np.fromfile('c_output.bin', dtype=np.float32).reshape(256, 256)
py_img = np.fromfile('py_output.bin', dtype=np.float32).reshape(256, 256)

# Compute correlation
corr = np.corrcoef(c_img.flatten(), py_img.flatten())[0,1]
print(f'Correlation: {corr:.4f}')

# Plot comparison
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
axes[0].imshow(c_img, cmap='viridis')
axes[0].set_title('C Output')
axes[1].imshow(py_img, cmap='viridis')
axes[1].set_title('PyTorch Output')
axes[2].imshow(py_img - c_img, cmap='RdBu_r')
axes[2].set_title('Difference')
plt.tight_layout()
plt.savefig('comparison.png')
print('Saved comparison.png')
"
```

## Visualization Tools

### Generate PNG from Binary Output

```python
#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import sys

# Load binary file
data = np.fromfile(sys.argv[1], dtype=np.float32)

# Determine size (assume square)
size = int(np.sqrt(len(data)))
image = data.reshape(size, size)

# Create visualization
plt.figure(figsize=(8, 8))
plt.imshow(image, cmap='viridis', origin='lower')
plt.colorbar(label='Intensity')
plt.title(f'Diffraction Pattern ({size}x{size})')
plt.savefig(sys.argv[1].replace('.bin', '.png'), dpi=150)
print(f"Saved {sys.argv[1].replace('.bin', '.png')}")
```

Save as `bin2png.py` and use:
```bash
python3 bin2png.py output.bin
```

### Batch Visualization Script

The repository includes comparison scripts in `scripts/comparison/`:

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

### Quick Comparison Function

Add to your `.bashrc` or `.zshrc`:

```bash
nb_compare() {
    local args="$@"
    local c_out="/tmp/c_output.bin"
    local py_out="/tmp/py_output.bin"

    # Run both implementations
    $NB_C_BIN $args -floatfile $c_out
    nanoBragg $args -floatfile $py_out

    # Generate comparison
    python3 -c "
import numpy as np
import matplotlib.pyplot as plt

# Load and reshape (detect size from file)
c_data = np.fromfile('$c_out', dtype=np.float32)
py_data = np.fromfile('$py_out', dtype=np.float32)
size = int(np.sqrt(len(c_data)))
c_img = c_data.reshape(size, size)
py_img = py_data.reshape(size, size)

# Calculate metrics
corr = np.corrcoef(c_img.flatten(), py_img.flatten())[0,1]
rmse = np.sqrt(np.mean((c_img - py_img)**2))

print(f'Correlation: {corr:.6f}')
print(f'RMSE: {rmse:.6f}')
print(f'Max diff: {np.abs(c_img - py_img).max():.6f}')

# Plot
fig, axes = plt.subplots(2, 3, figsize=(12, 8))
im = axes[0,0].imshow(c_img, cmap='viridis')
axes[0,0].set_title('C Reference')
plt.colorbar(im, ax=axes[0,0])

axes[0,1].imshow(py_img, cmap='viridis')
axes[0,1].set_title('PyTorch')

diff = axes[0,2].imshow(py_img - c_img, cmap='RdBu_r')
axes[0,2].set_title('Difference')
plt.colorbar(diff, ax=axes[0,2])

# Log scale
axes[1,0].imshow(np.log10(np.maximum(c_img, 1e-10)), cmap='viridis')
axes[1,0].set_title('C (log scale)')

axes[1,1].imshow(np.log10(np.maximum(py_img, 1e-10)), cmap='viridis')
axes[1,1].set_title('PyTorch (log scale)')

# Histogram
axes[1,2].hist(c_img.flatten(), bins=50, alpha=0.5, label='C')
axes[1,2].hist(py_img.flatten(), bins=50, alpha=0.5, label='PyTorch')
axes[1,2].set_yscale('log')
axes[1,2].legend()
axes[1,2].set_title('Intensity Distribution')

plt.suptitle(f'Comparison (correlation={corr:.4f})')
plt.tight_layout()
plt.savefig('/tmp/nb_comparison.png', dpi=150)
plt.show()
"
}

# Usage:
# nb_compare -cell 100 100 100 90 90 90 -default_F 100 -lambda 1.0 -distance 100 -detpixels 256
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

# Run with coverage
pytest tests/ --cov=nanobrag_torch --cov-report=html
```

### Running Visual Test Suite

```bash
# Run comprehensive visual comparisons
./scripts/comparison/run_parallel_visual.py

# This generates:
# - 20+ comparison plots
# - Correlation metrics for each test
# - Summary report with statistics
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

3. **Import Errors**
   ```bash
   # Ensure package is installed
   pip install -e .
   ```

4. **Memory Issues with Large Detectors**
   ```bash
   # Use ROI to limit computation
   nanoBragg ... -roi 400 600 400 600
   ```

5. **Triclinic Crystal Pattern Offsets**
   - See [Known Limitations](docs/user/known_limitations.md#triclinic-crystal-misset-limitation)
   - Use smaller misset angles (<45°) for triclinic crystals
   - Check correlation values and center region accuracy

## Performance

### CUDA Performance and torch.compile Warm-Up

**Critical for production workflows:** The PyTorch implementation uses `torch.compile` for GPU acceleration, which introduces a **cold-start compilation overhead (0.5-6 seconds)** on the first run. After warm-up, performance approaches C parity at production scales.

#### Performance Characteristics

| Detector Size | C Time | PyTorch (Cold) | PyTorch (Warm) | Gap (Cold) | Gap (Warm) |
|---------------|--------|----------------|----------------|------------|------------|
| 1024²         | 0.048s | 0.553s         | 0.134s         | 11.5×      | **2.8×**   |
| 4096²         | 0.539s | 0.799s         | 0.615s         | 1.48×      | **1.14×**  |

**Key Insight:** At production scale (4096²), PyTorch is only 14% slower than C after warm-up.

#### Production Workflow Recommendations

For production batch processing, **compile once and simulate many times**:

```python
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig

# Create simulator once (triggers torch.compile on first run)
simulator = Simulator(crystal_config, detector_config, beam_config, device='cuda')

# Warm-up: run once to trigger compilation
_ = simulator.run()  # 0.5-6s compilation overhead

# Production loop: subsequent runs are fast
for dataset in datasets:
    # Update parameters as needed
    simulator.crystal_config.phi_start_deg = dataset.phi_start
    # ... update other parameters ...

    # Run simulation (no recompilation, ~1.14× C speed at 4096²)
    result = simulator.run()
    save_result(result, dataset.output_path)
```

**Benefits:**
- Eliminates 0.5-6s overhead per simulation
- Achieves near-parity performance (1.14× slower at 4096²)
- Enables batch processing workflows

#### GPU Optimization

The implementation automatically uses GPU when available via PyTorch's CUDA backend:

- **CUDA Graph Capture:** Enabled automatically via `torch.compile`
- **Kernel Fusion:** Triton compiler fuses operations for efficiency
- **No manual tuning required:** Just run on a CUDA-enabled device

```bash
# GPU is used automatically if available
nanoBragg -device cuda -detpixels 4096 -floatfile output.bin ...

# Force CPU execution
nanoBragg -device cpu -detpixels 256 -floatfile output.bin ...
```

### Performance Best Practices

1. **For production**: Use warm-up pattern above to amortize compilation cost
2. **For testing**: Use small detectors (`-detpixels 256`) to minimize time
3. **For single runs**: Expect 1.5-12× slower than C depending on detector size
4. **For batch processing**: Achieve near-parity performance (~1.14× slower at 4096²)

### Quick Performance Tips

1. **Use ROI for testing**: `-roi xmin xmax ymin ymax` to limit computation
2. **Reduce oversampling**: Default `-oversample 1` is usually sufficient
3. **Limit mosaic domains**: Start with `-mosaic_domains 1` for quick tests
4. **Use smaller detectors**: `-detpixels 256` for rapid iteration
5. **GPU acceleration**: Automatically enabled when CUDA is available

### Detailed Performance Analysis

For complete performance benchmarks and optimization strategies, see:
- [`reports/benchmarks/PERF-PYTORCH-003_investigation_summary.md`](reports/benchmarks/PERF-PYTORCH-003_investigation_summary.md)
- [`docs/user/performance.md`](docs/user/performance.md)

## Known Limitations

The PyTorch implementation has some known limitations that users should be aware of:

- **Triclinic Misset Limitation**: Extreme misset angles (>45°) with triclinic crystals may cause pattern offsets and reduced correlation (~0.958 instead of 0.995+)
- **Memory constraints** with large detector arrays (>2048×2048 pixels)
- **GPU memory limits** for complex simulations

For complete details and workarounds, see the [Known Limitations Guide](docs/user/known_limitations.md).

## Further Documentation

- [Known Limitations Guide](docs/user/known_limitations.md) - Current limitations and workarounds
- [Architecture Documentation](docs/architecture/README.md)
- [C Parameter Dictionary](docs/architecture/c_parameter_dictionary.md)
- [Testing Strategy](docs/development/testing_strategy.md)
- [Debugging Guide](docs/debugging/debugging.md)
## PyTorch Runtime Guardrails

- Ensure all simulator changes remain **fully vectorized** (extend the broadcast dimensions instead of adding Python loops).
- Keep tensors on the caller’s **device/dtype**; preload config tensors onto the target device and avoid per-iteration `.to()` shims.
- Run CPU and CUDA smoke tests (see `docs/development/pytorch_runtime_checklist.md`) before declaring success.

Refer to `[docs/development/pytorch_runtime_checklist.md](docs/development/pytorch_runtime_checklist.md)` for the full checklist.
