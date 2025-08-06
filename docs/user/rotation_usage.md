# Rotation and Mosaicity Usage Guide

This document explains how to use the rotation and mosaicity capabilities implemented in the nanoBragg PyTorch port.

## Overview

The PyTorch implementation provides full support for:
- **Crystal rotation** via phi angle stepping (oscillation data collection)
- **Mosaicity simulation** via mosaic domain generation
- **Differentiable parameters** for gradient-based optimization

All rotation features are implemented in the `CrystalConfig` class and processed by the `Simulator`.

## Basic Usage

### Simple Rotation

```python
import torch
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig

# Set up basic components
device = torch.device("cpu")
dtype = torch.float64

crystal = Crystal(device=device, dtype=dtype)
detector = Detector(device=device, dtype=dtype)

# Configure rotation - single phi angle
config = CrystalConfig(
    phi_start_deg=30.0,      # Starting phi angle
    phi_steps=1,             # Single orientation
    osc_range_deg=0.0,       # No oscillation
    mosaic_spread_deg=0.0,   # No mosaicity
    mosaic_domains=1         # Single domain
)

simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)
image = simulator.run()
```

### Phi Oscillation (Data Collection)

```python
# Simulate oscillation data collection
config = CrystalConfig(
    phi_start_deg=0.0,       # Starting angle
    phi_steps=36,            # Number of phi steps  
    osc_range_deg=10.0,      # Total oscillation range
    mosaic_spread_deg=0.1,   # Small mosaicity
    mosaic_domains=10        # Moderate domain count
)

simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)
image = simulator.run()  # Summed intensity over all phi steps
```

### Mosaicity Simulation

```python
# Simulate crystal imperfection
config = CrystalConfig(
    phi_start_deg=0.0,
    phi_steps=1,
    osc_range_deg=0.0,
    mosaic_spread_deg=2.0,   # 2-degree mosaic spread
    mosaic_domains=50        # Many domains for smooth broadening
)

simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)
image = simulator.run()
```

## Configuration Parameters

### Rotation Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `phi_start_deg` | float | Starting phi angle in degrees | 0.0 |
| `phi_steps` | int | Number of phi angle steps | 1 |
| `osc_range_deg` | float | Total oscillation range in degrees | 0.0 |

**Phi stepping:** When `phi_steps > 1`, the crystal is rotated through `osc_range_deg` in equal steps, and intensities are summed.

### Mosaicity Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `mosaic_spread_deg` | float | RMS mosaic spread in degrees | 0.0 |
| `mosaic_domains` | int | Number of mosaic domains | 1 |

**Mosaic domains:** Each domain represents a slightly misoriented crystallite. Orientations are sampled from a Gaussian distribution with the specified spread.

## Advanced Usage

### Differentiable Parameters

Both rotation and mosaicity parameters support automatic differentiation:

```python
import torch.autograd

# Create differentiable parameters
phi_param = torch.tensor(10.0, requires_grad=True, dtype=torch.float64)
mosaic_param = torch.tensor(1.5, requires_grad=True, dtype=torch.float64)

# Use in configuration (note: .item() needed for config)
config = CrystalConfig(
    phi_start_deg=phi_param.item(),
    mosaic_spread_deg=mosaic_param.item(),
    phi_steps=1,
    mosaic_domains=20
)

simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)
image = simulator.run()

# Compute loss and gradients
loss = torch.sum(image)  # Example loss function
loss.backward()

print(f"Phi gradient: {phi_param.grad}")
print(f"Mosaic gradient: {mosaic_param.grad}")
```

### Parameter Optimization

```python
import torch.optim

# Optimization example
phi_param = torch.tensor(0.0, requires_grad=True, dtype=torch.float64)
mosaic_param = torch.tensor(0.5, requires_grad=True, dtype=torch.float64)

optimizer = torch.optim.Adam([phi_param, mosaic_param], lr=0.1)

target_image = torch.randn(detector.spixels, detector.fpixels)  # Example target

for epoch in range(10):
    optimizer.zero_grad()
    
    config = CrystalConfig(
        phi_start_deg=phi_param.item(),
        mosaic_spread_deg=mosaic_param.item(),
        phi_steps=1,
        mosaic_domains=10
    )
    
    simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)
    predicted_image = simulator.run()
    
    loss = torch.nn.functional.mse_loss(predicted_image, target_image)
    loss.backward()
    optimizer.step()
    
    print(f"Epoch {epoch}: loss={loss:.4f}, phi={phi_param:.2f}°, mosaic={mosaic_param:.2f}°")
```

## Physical Interpretation

### Phi Rotation

- **Spindle rotation:** Crystal rotates around the spindle axis (typically Z-axis)
- **Reciprocal space sampling:** Different phi angles sample different regions of reciprocal space
- **Data collection:** Oscillation methods collect diffraction data over a phi range

### Mosaicity

- **Crystal imperfection:** Real crystals have slight orientation variations
- **Spot broadening:** Mosaic spread causes Bragg spots to become broader and more diffuse
- **Realistic simulation:** Essential for matching experimental diffraction patterns

## Performance Considerations

### Memory Usage

- **Mosaic domains:** Memory scales with `mosaic_domains × detector_pixels`
- **Phi steps:** Memory scales with `phi_steps × detector_pixels`
- **Recommendation:** Use moderate values (10-50 domains, 1-100 steps) for testing

### Computational Cost

- **Vectorization:** All rotation calculations are vectorized for efficiency
- **GPU support:** Full GPU acceleration when using `device="cuda"`
- **Batching:** Consider processing multiple phi steps in parallel

### Optimization Tips

```python
# For fast prototyping
config = CrystalConfig(
    mosaic_domains=5,     # Fewer domains
    phi_steps=1           # Single orientation
)

# For production simulation
config = CrystalConfig(
    mosaic_domains=100,   # Many domains for smooth spots
    phi_steps=360         # Fine phi sampling
)
```

## Common Use Cases

### 1. Static Diffraction Pattern

```python
config = CrystalConfig(phi_start_deg=0.0, phi_steps=1, mosaic_spread_deg=0.1, mosaic_domains=20)
```

### 2. Oscillation Data Collection

```python
config = CrystalConfig(phi_start_deg=0.0, phi_steps=72, osc_range_deg=180.0, mosaic_spread_deg=0.5, mosaic_domains=30)
```

### 3. Parameter Refinement

```python
# Start with experimental estimates, optimize using gradients
config = CrystalConfig(phi_start_deg=measured_phi, mosaic_spread_deg=estimated_mosaic, ...)
```

### 4. Method Development

```python
# Test rotation algorithms with known parameters
config = CrystalConfig(phi_start_deg=45.0, mosaic_spread_deg=1.0, ...)
```

## Demo Script

A comprehensive demonstration is available:

```bash
python scripts/demo_rotation.py
```

This generates:
- Baseline images (no rotation)
- Phi rotation series 
- Mosaicity effect comparison
- Summary report

## Validation and Testing

The rotation implementation includes comprehensive validation:

1. **Golden test reproduction:** `test_simple_cubic_mosaic_reproduction`
2. **Gradient correctness:** `test_gradcheck_phi_rotation`, `test_gradcheck_mosaic_spread`
3. **Numerical stability:** `test_gradient_numerical_stability`

Run tests with:
```bash
python -m pytest tests/test_suite.py::TestTier1TranslationCorrectness::test_simple_cubic_mosaic_reproduction -v
python -m pytest tests/test_suite.py::TestTier2GradientCorrectness::test_gradcheck_phi_rotation -v
```

## Troubleshooting

### Common Issues

1. **Memory errors:** Reduce `mosaic_domains` or `phi_steps`
2. **Gradient errors:** Check that parameters have `requires_grad=True`
3. **NaN values:** Verify reasonable parameter ranges (phi: -180°-180°, mosaic: 0°-10°)

### Environment Setup

Always set the environment variable for PyTorch compatibility:

```python
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
```

### Debugging

Use the debug pixel trace capability for detailed investigation:

```bash
python scripts/debug_pixel_trace.py --mosaic_spread 1.0 --phi 30.0
```

## Future Enhancements

Planned features for future releases:
- Multi-axis rotation (omega, kappa)
- Anisotropic mosaicity
- Time-resolved rotation
- Beam divergence integration

## References

- C implementation: `nanoBragg.c` (original reference)
- Architecture design: `docs/architecture/pytorch_design.md`
- Testing strategy: `docs/development/testing_strategy.md`
- Implementation plan: `plans/rotation/implementation_rotation.md`