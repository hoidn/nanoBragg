# Migration Guide: From Hard-coded to Dynamic Geometry

This guide helps users transition from the previous hard-coded cubic unit cells to the new general triclinic cell parameter support in nanoBragg PyTorch.

## Overview of Changes

The nanoBragg PyTorch implementation now supports:
- **General triclinic unit cells** with all six parameters (a, b, c, α, β, γ)
- **Differentiable cell parameters** for gradient-based optimization
- **Dynamic geometry calculations** that update automatically when parameters change

## Migration Steps

### 1. Updating Existing Cubic Simulations

#### Before (Hard-coded cubic):
```python
# Old approach with hard-coded 100 Å cubic cell
crystal = Crystal(device=device, dtype=dtype)
# Cell parameters were fixed at a=b=c=100 Å, α=β=γ=90°
```

#### After (Configurable parameters):
```python
from nanobrag_torch.config import CrystalConfig

# Explicit cubic configuration
config = CrystalConfig(
    cell_a=100.0,
    cell_b=100.0,
    cell_c=100.0,
    cell_alpha=90.0,
    cell_beta=90.0,
    cell_gamma=90.0
)
crystal = Crystal(config=config, device=device, dtype=dtype)
```

### 2. Enabling Gradient Flow for Parameters

To make cell parameters differentiable for optimization:

```python
import torch

# Create differentiable parameters
cell_a = torch.tensor(100.0, requires_grad=True)
cell_b = torch.tensor(100.0, requires_grad=True)
cell_c = torch.tensor(100.0, requires_grad=True)
cell_alpha = torch.tensor(90.0, requires_grad=True)
cell_beta = torch.tensor(90.0, requires_grad=True)
cell_gamma = torch.tensor(90.0, requires_grad=True)

# Pass tensors directly to config
config = CrystalConfig(
    cell_a=cell_a,
    cell_b=cell_b,
    cell_c=cell_c,
    cell_alpha=cell_alpha,
    cell_beta=cell_beta,
    cell_gamma=cell_gamma
)

crystal = Crystal(config=config, device=device, dtype=dtype)
```

### 3. Common Patterns

#### Creating a Hexagonal Cell
```python
config = CrystalConfig(
    cell_a=100.0,
    cell_b=100.0,
    cell_c=150.0,
    cell_alpha=90.0,
    cell_beta=90.0,
    cell_gamma=120.0  # Hexagonal γ angle
)
```

#### Creating a Triclinic Cell
```python
config = CrystalConfig(
    cell_a=85.0,
    cell_b=95.0,
    cell_c=105.0,
    cell_alpha=75.0,
    cell_beta=80.0,
    cell_gamma=85.0
)
```

#### Optimizing Cell Parameters
```python
# Set up differentiable parameters
params = torch.tensor([100.0, 100.0, 100.0, 90.0, 90.0, 90.0], 
                     requires_grad=True)

# Optimization loop
optimizer = torch.optim.Adam([params], lr=0.01)

for iteration in range(100):
    optimizer.zero_grad()
    
    # Unpack parameters
    config = CrystalConfig(
        cell_a=params[0],
        cell_b=params[1],
        cell_c=params[2],
        cell_alpha=params[3],
        cell_beta=params[4],
        cell_gamma=params[5]
    )
    
    # Create crystal and run simulation
    crystal = Crystal(config=config)
    # ... run simulation and compute loss ...
    
    loss.backward()
    optimizer.step()
```

## Performance Considerations

### 1. Caching Behavior

The new implementation uses property-based caching for geometry calculations:
- Geometry is recalculated only when cell parameters change
- Multiple accesses to `crystal.a_star`, etc. reuse cached values
- Cache is automatically cleared when parameters are updated

### 2. Memory Usage

- Triclinic calculations require slightly more memory than cubic
- Gradient storage adds overhead when `requires_grad=True`
- Consider using `torch.no_grad()` context for inference-only runs

### 3. Computational Cost

- Triclinic geometry calculations are more complex than cubic
- Overhead is minimal for forward passes
- Backward passes (gradients) add ~2x computation time

## Backward Compatibility

### Default Behavior
If no configuration is provided, the Crystal class defaults to the original cubic cell:
```python
crystal = Crystal()  # Defaults to 100 Å cubic cell
```

### Test Suite Compatibility
All existing tests continue to work with the new implementation. The golden test data for `simple_cubic` remains valid.

## Common Issues and Solutions

### Issue 1: Gradients Not Flowing
**Symptom**: `param.grad is None` after backward()
**Solution**: Ensure parameters have `requires_grad=True` and are tensors, not Python floats

### Issue 2: Type Mismatch Errors
**Symptom**: "Expected Tensor but got float" errors
**Solution**: Wrap scalar values in `torch.tensor()` when mixing with tensor parameters

### Issue 3: Device Mismatch
**Symptom**: "Expected all tensors to be on the same device" errors
**Solution**: Ensure all parameters are on the same device:
```python
device = torch.device('cuda')
cell_a = torch.tensor(100.0, device=device, requires_grad=True)
```

## Advanced Usage

### Constraining Parameters
```python
# Apply constraints during optimization
with torch.no_grad():
    # Keep lengths positive
    params[:3] = torch.clamp(params[:3], min=1.0)
    # Keep angles between 20° and 160°
    params[3:] = torch.clamp(params[3:], min=20.0, max=160.0)
```

### Batch Processing
```python
# Process multiple crystals with different parameters
batch_size = 10
cell_params = torch.randn(batch_size, 6) * 10 + 100  # Random variations

crystals = []
for i in range(batch_size):
    config = CrystalConfig(
        cell_a=cell_params[i, 0],
        cell_b=cell_params[i, 1],
        # ... etc
    )
    crystals.append(Crystal(config=config))
```

## Further Reading

- [Cell Parameter Refinement Tutorial](tutorials/cell_parameter_refinement.ipynb)
- [PyTorch Architecture Design](../architecture/pytorch_design.md)
- [Testing Strategy](../development/testing_strategy.md)