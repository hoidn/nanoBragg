# Refinement Demo: Gradient-Based Parameter Recovery

## Overview

**Purpose**: Demonstrate differentiable diffraction simulation by recovering crystal parameters from synthetic "experimental" data using gradient-based optimization.

**Target Audience**: Crystallography PI familiar with mosaicity and orientation refinement.

**Time Budget**: 2 hours (hackathon format)

**Deliverable**: Working Python script that:
1. Generates synthetic diffraction data with known parameters
2. Initializes refinement with wrong parameters
3. Recovers ground truth via gradient descent
4. Outputs convergence metrics

---

## Parameters to Refine

| Parameter | Ground Truth | Initial Guess | Physical Meaning |
|-----------|--------------|---------------|------------------|
| `mosaic_spread_deg` | 0.8° | 0.2° | Crystal disorder (domain spread) |
| `misset_x` | 5.0° | 0.0° | Orientation rotation about X |
| `misset_y` | 3.0° | 0.0° | Orientation rotation about Y |
| `misset_z` | -2.0° | 0.0° | Orientation rotation about Z |

**Rationale**: Joint mosaic + orientation refinement demonstrates:
- Gradients through stochastic rotation sampling (mosaic)
- Gradients through SO(3) rotation matrices (misset)
- Practical relevance to crystallographic data processing

---

## Existing Components

### Imports

```python
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
```

### Component Roles

| Component | Source | Role |
|-----------|--------|------|
| `CrystalConfig` | `src/nanobrag_torch/config.py:97` | Holds cell, mosaic, misset parameters |
| `Crystal` | `src/nanobrag_torch/models/crystal.py` | Computes lattice vectors, applies rotations |
| `DetectorConfig` | `src/nanobrag_torch/config.py:168` | Detector geometry (pixels, distance) |
| `Detector` | `src/nanobrag_torch/models/detector.py` | Pixel coordinate generation |
| `BeamConfig` | `src/nanobrag_torch/config.py:496` | Wavelength, fluence |
| `Simulator` | `src/nanobrag_torch/simulator.py` | Forward diffraction calculation |

---

## Reference Tests

These tests demonstrate the exact patterns needed:

### 1. Optimization Loop Pattern
**File**: `tests/test_gradients.py:667-776`
**Class**: `TestOptimizationRecovery.test_optimization_recovers_cell`

Shows:
- Creating target crystal with known parameters
- Initializing parameters with `requires_grad=True`
- Adam optimizer setup
- Loss computation and backward pass
- History tracking

### 2. Simulator with Mosaic Spread
**File**: `tests/test_gradients.py:1290-1331`
**Class**: `TestMosaicGradients.test_mosaic_spread_gradcheck_simulator`

Shows:
- `CrystalConfig` with `mosaic_spread_deg` as tensor
- `mosaic_seed=42` for reproducibility (CRITICAL)
- Full simulator forward pass
- Gradient flow verification

### 3. Misset Gradient Flow
**File**: `tests/test_crystal_geometry.py:759-799`
**Function**: `test_misset_gradient_flow`

Shows:
- Creating misset angles as tensors with `requires_grad=True`
- Passing tuple of tensors to `misset_deg`
- Verifying gradients exist after backward

---

## Implementation Plan

### Phase 1: Environment Setup (5 min)

```python
#!/usr/bin/env python3
"""
Refinement Demo: Mosaic Spread + Orientation Recovery

Demonstrates gradient-based parameter recovery using nanoBragg PyTorch.
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["NANOBRAGG_DISABLE_COMPILE"] = "1"

import torch
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

device = torch.device("cpu")
dtype = torch.float64
torch.manual_seed(42)
```

**Notes**:
- `KMP_DUPLICATE_LIB_OK=TRUE`: Prevents MKL library conflicts
- `NANOBRAGG_DISABLE_COMPILE=1`: Avoids torch.compile issues with gradcheck
- `torch.float64`: Required for gradient numerical stability

---

### Phase 2: Define Ground Truth (10 min)

```python
# === GROUND TRUTH PARAMETERS ===
TRUE_MOSAIC_SPREAD = 0.8  # degrees
TRUE_MISSET = (5.0, 3.0, -2.0)  # degrees (Rx, Ry, Rz)

# Fixed parameters (not refined)
FIXED_PARAMS = dict(
    cell_a=100.0,
    cell_b=100.0,
    cell_c=100.0,
    cell_alpha=90.0,
    cell_beta=90.0,
    cell_gamma=90.0,
    N_cells=(5, 5, 5),
    default_F=100.0,
    mosaic_domains=5,
    mosaic_seed=42,  # CRITICAL: deterministic sampling
)

# Detector configuration
DETECTOR_CONFIG = DetectorConfig(
    fpixels=64,        # Fast axis pixels (increase for visual demo)
    spixels=64,        # Slow axis pixels
    pixel_size_mm=0.1,
    distance_mm=100.0,
)

# Beam configuration
BEAM_CONFIG = BeamConfig(
    wavelength_A=1.0,
    fluence=1e28,
)
```

**Critical**: `mosaic_seed=42` ensures deterministic random rotations. Without this, each forward pass samples different rotations and gradients are meaningless.

---

### Phase 3: Generate Synthetic "Experimental" Data (15 min)

```python
def generate_experimental_data():
    """Generate synthetic diffraction pattern with ground truth parameters."""

    true_config = CrystalConfig(
        **FIXED_PARAMS,
        mosaic_spread_deg=TRUE_MOSAIC_SPREAD,
        misset_deg=TRUE_MISSET,
    )

    crystal = Crystal(config=true_config, device=device, dtype=dtype)
    detector = Detector(config=DETECTOR_CONFIG, device=device, dtype=dtype)
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        crystal_config=true_config,
        beam_config=BEAM_CONFIG,
        device=device,
        dtype=dtype,
    )

    # Run forward simulation and detach from graph
    experimental_image = simulator.run().detach()

    print(f"Generated experimental data: {experimental_image.shape}")
    print(f"  Image sum: {experimental_image.sum().item():.2e}")
    print(f"  Image max: {experimental_image.max().item():.2e}")
    print(f"  True mosaic_spread: {TRUE_MOSAIC_SPREAD}°")
    print(f"  True misset: {TRUE_MISSET}")

    return experimental_image

experimental_image = generate_experimental_data()
```

---

### Phase 4: Initialize Refinement Parameters (10 min)

```python
# === INITIAL GUESS (WRONG) ===
init_mosaic = torch.tensor(0.2, dtype=dtype, requires_grad=True)
init_misset_x = torch.tensor(0.0, dtype=dtype, requires_grad=True)
init_misset_y = torch.tensor(0.0, dtype=dtype, requires_grad=True)
init_misset_z = torch.tensor(0.0, dtype=dtype, requires_grad=True)

# Bundle for optimizer
params = [init_mosaic, init_misset_x, init_misset_y, init_misset_z]

# Adam optimizer with moderate learning rate
optimizer = torch.optim.Adam(params, lr=0.05)

# History tracking
history = {
    "iteration": [],
    "loss": [],
    "mosaic_spread": [],
    "misset_x": [],
    "misset_y": [],
    "misset_z": [],
}

print(f"\nInitial parameters:")
print(f"  mosaic_spread: {init_mosaic.item():.3f}° (true: {TRUE_MOSAIC_SPREAD}°)")
print(f"  misset: ({init_misset_x.item():.2f}, {init_misset_y.item():.2f}, {init_misset_z.item():.2f})° (true: {TRUE_MISSET})")
```

---

### Phase 5: Optimization Loop (30 min)

```python
N_ITERATIONS = 100

# Pre-create detector (doesn't change during refinement)
detector = Detector(config=DETECTOR_CONFIG, device=device, dtype=dtype)

print(f"\n{'='*60}")
print(f"Starting refinement: {N_ITERATIONS} iterations")
print(f"{'='*60}")

for iteration in range(N_ITERATIONS):
    optimizer.zero_grad()

    # Build config with current (differentiable) parameters
    current_config = CrystalConfig(
        **FIXED_PARAMS,
        mosaic_spread_deg=init_mosaic,
        misset_deg=(init_misset_x, init_misset_y, init_misset_z),
    )

    # Forward simulation
    crystal = Crystal(config=current_config, device=device, dtype=dtype)
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        crystal_config=current_config,
        beam_config=BEAM_CONFIG,
        device=device,
        dtype=dtype,
    )
    predicted_image = simulator.run()

    # MSE loss against experimental data
    loss = torch.nn.functional.mse_loss(predicted_image, experimental_image)

    # Backward pass
    loss.backward()

    # Optimizer step
    optimizer.step()

    # Enforce physical constraints
    with torch.no_grad():
        init_mosaic.clamp_(min=0.01, max=5.0)  # Mosaic spread must be positive

    # Record history
    history["iteration"].append(iteration)
    history["loss"].append(loss.item())
    history["mosaic_spread"].append(init_mosaic.item())
    history["misset_x"].append(init_misset_x.item())
    history["misset_y"].append(init_misset_y.item())
    history["misset_z"].append(init_misset_z.item())

    # Progress reporting
    if iteration % 10 == 0 or iteration == N_ITERATIONS - 1:
        print(f"Iter {iteration:3d}: loss={loss.item():.4e}, "
              f"mosaic={init_mosaic.item():.3f}°, "
              f"misset=({init_misset_x.item():+.2f}, {init_misset_y.item():+.2f}, {init_misset_z.item():+.2f})°")
```

---

### Phase 6: Results Summary (10 min)

```python
print(f"\n{'='*60}")
print("REFINEMENT RESULTS")
print(f"{'='*60}")

print(f"\n{'Parameter':<18} | {'True':>8} | {'Initial':>8} | {'Refined':>8} | {'Error':>8}")
print("-" * 60)
print(f"{'mosaic_spread (°)':<18} | {TRUE_MOSAIC_SPREAD:>8.3f} | {'0.200':>8} | {init_mosaic.item():>8.3f} | {abs(init_mosaic.item() - TRUE_MOSAIC_SPREAD):>8.3f}")
print(f"{'misset_x (°)':<18} | {TRUE_MISSET[0]:>8.2f} | {'0.00':>8} | {init_misset_x.item():>8.2f} | {abs(init_misset_x.item() - TRUE_MISSET[0]):>8.2f}")
print(f"{'misset_y (°)':<18} | {TRUE_MISSET[1]:>8.2f} | {'0.00':>8} | {init_misset_y.item():>8.2f} | {abs(init_misset_y.item() - TRUE_MISSET[1]):>8.2f}")
print(f"{'misset_z (°)':<18} | {TRUE_MISSET[2]:>8.2f} | {'0.00':>8} | {init_misset_z.item():>8.2f} | {abs(init_misset_z.item() - TRUE_MISSET[2]):>8.2f}")

print(f"\nConvergence:")
print(f"  Initial loss: {history['loss'][0]:.4e}")
print(f"  Final loss:   {history['loss'][-1]:.4e}")
print(f"  Reduction:    {history['loss'][0] / history['loss'][-1]:.1f}x")

# Export history for plotting (optional)
# import json
# with open("refinement_history.json", "w") as f:
#     json.dump(history, f, indent=2)
```

---

## Fallback: Single-Parameter Demo

If joint refinement encounters issues, simplify to mosaic-spread-only:

```python
# Simplified: only mosaic spread, no misset
TRUE_MISSET = (0.0, 0.0, 0.0)  # Identity orientation
init_mosaic = torch.tensor(0.2, dtype=dtype, requires_grad=True)
params = [init_mosaic]

# In optimization loop:
current_config = CrystalConfig(
    **FIXED_PARAMS,
    mosaic_spread_deg=init_mosaic,
    misset_deg=(0.0, 0.0, 0.0),  # Fixed at identity
)
```

This single-parameter case is guaranteed to work per `test_mosaic_spread_gradcheck_simulator`.

---

## Troubleshooting

### Issue: Loss doesn't decrease
- Check `mosaic_seed` is set (deterministic sampling required)
- Verify `requires_grad=True` on all refined parameters
- Try reducing learning rate to `0.01`

### Issue: Parameters explode
- Add clamping: `init_mosaic.clamp_(min=0.01, max=5.0)`
- Reduce learning rate
- Check loss scale (consider normalizing)

### Issue: CUDA errors
- Set `device = torch.device("cpu")` for debugging
- Ensure `NANOBRAGG_DISABLE_COMPILE=1` is set

### Issue: Gradient is None
- Verify parameter tensor has `requires_grad=True`
- Check that `.detach()` isn't called on intermediate tensors
- Ensure `experimental_image` was detached before loop

---

## Time Budget Summary

| Phase | Time | Checkpoint |
|-------|------|------------|
| 1. Environment setup | 5 min | Imports work |
| 2. Define ground truth | 10 min | Constants defined |
| 3. Generate experimental data | 15 min | `experimental_image` tensor |
| 4. Initialize parameters | 10 min | `params` list, optimizer |
| 5. Optimization loop | 30 min | Loss decreasing |
| 6. Results summary | 10 min | Convergence verified |
| Buffer for debugging | 40 min | Issues resolved |
| **Total** | **2 hours** | |

---

## Success Criteria

1. **Loss decreases** by at least 10x from initial to final
2. **Mosaic spread** recovers within ±0.1° of ground truth
3. **Misset angles** recover within ±1° of ground truth
4. **No NaN/Inf** in loss or parameters

---

## Extension: Visualization (Post-Hackathon)

For the actual PI demo, add:

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# Row 1: Images
axes[0, 0].imshow(experimental_image.numpy(), cmap='viridis', origin='lower')
axes[0, 0].set_title('Experimental (Ground Truth)')

axes[0, 1].imshow(initial_image.numpy(), cmap='viridis', origin='lower')
axes[0, 1].set_title('Initial Guess')

axes[0, 2].imshow(predicted_image.detach().numpy(), cmap='viridis', origin='lower')
axes[0, 2].set_title('Refined')

# Row 2: Convergence curves
axes[1, 0].semilogy(history['loss'])
axes[1, 0].set_xlabel('Iteration')
axes[1, 0].set_ylabel('MSE Loss')
axes[1, 0].set_title('Loss Convergence')

axes[1, 1].plot(history['mosaic_spread'], label='Refined')
axes[1, 1].axhline(TRUE_MOSAIC_SPREAD, color='r', linestyle='--', label='Truth')
axes[1, 1].set_xlabel('Iteration')
axes[1, 1].set_ylabel('Mosaic Spread (°)')
axes[1, 1].legend()

axes[1, 2].plot(history['misset_x'], label='misset_x')
axes[1, 2].plot(history['misset_y'], label='misset_y')
axes[1, 2].plot(history['misset_z'], label='misset_z')
axes[1, 2].axhline(TRUE_MISSET[0], color='C0', linestyle='--', alpha=0.5)
axes[1, 2].axhline(TRUE_MISSET[1], color='C1', linestyle='--', alpha=0.5)
axes[1, 2].axhline(TRUE_MISSET[2], color='C2', linestyle='--', alpha=0.5)
axes[1, 2].set_xlabel('Iteration')
axes[1, 2].set_ylabel('Misset Angles (°)')
axes[1, 2].legend()

plt.tight_layout()
plt.savefig('refinement_demo.png', dpi=150)
plt.show()
```
