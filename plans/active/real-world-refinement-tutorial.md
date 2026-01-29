# Real-World Refinement Tutorial: CUSTOM Detector Geometry

## Overview

**Purpose**: Create an interactive Jupyter notebook demonstrating gradient-based parameter refinement using real crystallographic data (`A.mat`, `scaled.hkl`) with a complex CUSTOM detector geometry.

**Target Audience**: Crystallographers and developers who want to see refinement working on a realistic experimental configuration, not just simple test cases.

**Deliverable**: `notebooks/real_world_refinement_tutorial.ipynb`

**Estimated Implementation Time**: 2-3 hours

**Output Artifacts**:
- `real_world_refinement_result.png` - Static convergence visualization
- `real_world_refinement_animation.gif` - Animated GIF showing refinement progression

---

## Background: The C Command Being Replicated

This tutorial replicates the configuration from:

```bash
nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate \
  -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 \
  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 \
  -distance 231.274660 -lambda 0.976800 -pixel 0.172 \
  -detpixels_x 2463 -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 -Nb 47 -Nc 29 \
  -osc 0.1 -phi 0 -phisteps 10 \
  -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0
```

**Key characteristics:**
- Real HKL data: 64,333 reflections from `scaled.hkl`
- MOSFLM orientation matrix from `A.mat` (triclinic cell: 26.75 × 31.31 × 33.67 Å)
- CUSTOM detector convention with explicit basis vectors
- Pilatus-like detector: 2463 × 2527 pixels, 0.172 mm pixel size
- Asymmetric crystal: 36 × 47 × 29 unit cells
- Custom spindle axis: (-1, 0, 0)

---

## Parameters to Refine

Based on gradient flow testing, these parameters have verified working gradients:

| Parameter | Ground Truth | Initial (Perturbed) | Physical Meaning | Gradient Magnitude |
|-----------|--------------|---------------------|------------------|-------------------|
| `phi_start_deg` | 0.0° | 1.0° | Crystal rotation about spindle | ~5800 |
| `mosaic_spread_deg` | 0.2° | 0.5° | Crystal disorder/mosaicity | ~12900 |

**Rationale for selection:**
1. **phi_start_deg**: Most physically intuitive (orientation error), strong gradient, ~1s per iteration
2. **mosaic_spread_deg**: Affects spot shape/width, independent of geometry, requires `mosaic_seed=42`

**Not refined** (but gradient-capable):
- `cell_a/b/c`: Works without MOSFLM matrix, but changes orientation
- `misset_x/y/z`: Coupled with phi (both rotate crystal)

---

## Input Files (Already in Repository)

| File | Location | Contents |
|------|----------|----------|
| `A.mat` | `/home/ollie/Documents/nanoBragg/A.mat` | 3×3 MOSFLM reciprocal vectors (Å⁻¹) |
| `scaled.hkl` | `/home/ollie/Documents/nanoBragg/scaled.hkl` | 64,333 reflections (h k l F format) |

**Cell parameters derived from A.mat:**
- a = 26.75 Å, b = 31.31 Å, c = 33.67 Å
- α = 88.69°, β = 71.53°, γ = 68.14°

---

## Performance Characteristics (Verified)

| Operation | Time (CPU) | Memory |
|-----------|------------|--------|
| Forward pass (1 phi step) | ~1.1s | ~1.5 GB |
| Forward + backward | ~1.0s | ~2.0 GB |
| Forward (10 phi steps) | ~10s | ~1.5 GB |

**Recommendation**: Use single phi step (`phi_steps=1`, `osc_range_deg=0.0`) for tutorial speed. Mention oscillation as extension.

---

## Notebook Structure

### Cell 1: Environment Setup

```python
# Environment setup
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["NANOBRAGG_DISABLE_COMPILE"] = "1"

import torch
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
dtype = torch.float32  # float32 for speed; float64 for gradient verification

print(f"Device: {device}")
print(f"PyTorch version: {torch.__version__}")
```

**Notes:**
- `KMP_DUPLICATE_LIB_OK=TRUE`: Prevents MKL library conflicts
- `NANOBRAGG_DISABLE_COMPILE=1`: Avoids torch.compile issues
- `float32`: Sufficient for refinement; use `float64` only for gradcheck

---

### Cell 2: Imports

```python
from nanobrag_torch.config import (
    CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
)
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.io.mosflm import read_mosflm_matrix, reciprocal_to_real_cell
from nanobrag_torch.io.hkl import read_hkl_file
```

---

### Cell 3: Load Real Data (Markdown + Code)

**Markdown:**
```markdown
## 1. Load Real Crystallographic Data

We load:
- `A.mat`: MOSFLM-style orientation matrix (3×3 reciprocal vectors)
- `scaled.hkl`: Structure factors (64,333 reflections)

The orientation matrix encodes both the unit cell AND the crystal orientation.
```

**Code:**
```python
# Paths relative to repo root
REPO_ROOT = Path(".").resolve()
if not (REPO_ROOT / "A.mat").exists():
    REPO_ROOT = Path("..").resolve()  # If running from notebooks/

# Load MOSFLM matrix
WAVELENGTH_A = 0.976800  # ~12.7 keV
a_star, b_star, c_star = read_mosflm_matrix(
    str(REPO_ROOT / "A.mat"), WAVELENGTH_A
)
cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)

print(f"Unit cell from A.mat:")
print(f"  a={cell_params[0]:.2f} b={cell_params[1]:.2f} c={cell_params[2]:.2f} Å")
print(f"  α={cell_params[3]:.2f}° β={cell_params[4]:.2f}° γ={cell_params[5]:.2f}°")

# Load HKL reflections
hkl_grid, hkl_meta = read_hkl_file(str(REPO_ROOT / "scaled.hkl"), default_F=0.0)
n_reflections = (hkl_grid > 0).sum().item()

print(f"\nHKL data:")
print(f"  Grid shape: {hkl_grid.shape}")
print(f"  Non-zero reflections: {n_reflections:,}")
print(f"  h range: [{hkl_meta['h_min']}, {hkl_meta['h_max']}]")
print(f"  k range: [{hkl_meta['k_min']}, {hkl_meta['k_max']}]")
print(f"  l range: [{hkl_meta['l_min']}, {hkl_meta['l_max']}]")
```

**Expected output:**
```
Unit cell from A.mat:
  a=26.75 b=31.31 c=33.67 Å
  α=88.69° β=71.53° γ=68.14°

HKL data:
  Grid shape: torch.Size([49, 57, 62])
  Non-zero reflections: 64,333
  h range: [-24, 24]
  k range: [-28, 28]
  l range: [-31, 30]
```

---

### Cell 4: Configure CUSTOM Detector (Markdown + Code)

**Markdown:**
```markdown
## 2. Configure the Experiment

This configuration matches a real synchrotron experiment with:
- Pilatus-like detector (2463 × 2527 pixels)
- CUSTOM detector convention (explicit basis vectors)
- Off-axis beam position

The custom vectors define the physical detector geometry:
- `fdet_vector`: Fast axis direction (pixel columns)
- `sdet_vector`: Slow axis direction (pixel rows)
- `odet_vector`: Detector normal (pointing away from sample)
- `pix0_vector`: Position of pixel (0,0) corner in lab frame
- `beam_vector`: X-ray beam direction
```

**Code:**
```python
# === DETECTOR CONFIGURATION ===
# CUSTOM convention: all vectors specified explicitly
detector_config = DetectorConfig(
    distance_mm=231.274660,
    pixel_size_mm=0.172,
    fpixels=2463,  # Fast axis (columns)
    spixels=2527,  # Slow axis (rows)
    detector_convention=DetectorConvention.CUSTOM,
    # Beam center in mm (CUSTOM: no axis swap)
    beam_center_f=217.742295,
    beam_center_s=213.907080,
    # Custom basis vectors (slightly tilted detector)
    custom_fdet_vector=(0.999982, -0.005998, -0.000118),
    custom_sdet_vector=(-0.005998, -0.999970, -0.004913),
    custom_odet_vector=(-0.000088, 0.004914, -0.999988),
    custom_beam_vector=(0.00051387949, 0.0, -0.99999986),
    # Detector origin (pixel 0,0 corner) in meters
    pix0_override_m=(
        -216.336293 * 0.001,
        215.205512 * 0.001,
        -230.200866 * 0.001,
    ),
    oversample=1,
)

# === BEAM CONFIGURATION ===
beam_config = BeamConfig(
    wavelength_A=WAVELENGTH_A,
    flux=1e18,
    exposure=1.0,
    beamsize_mm=1.0,
)

print(f"Detector: {detector_config.fpixels} × {detector_config.spixels} pixels")
print(f"Pixel size: {detector_config.pixel_size_mm} mm")
print(f"Distance: {detector_config.distance_mm} mm")
print(f"Wavelength: {beam_config.wavelength_A} Å ({12398.42/beam_config.wavelength_A:.0f} eV)")
```

---

### Cell 5: Define Ground Truth and Perturbation (Markdown + Code)

**Markdown:**
```markdown
## 3. Define Ground Truth Parameters

We'll refine two parameters:
1. **phi_start_deg**: Crystal rotation about the spindle axis
2. **mosaic_spread_deg**: Crystal mosaicity (disorder)

The "experimental" data is generated with ground truth values.
Refinement starts from perturbed initial guesses.
```

**Code:**
```python
# === GROUND TRUTH ===
TRUE_PHI = 0.0           # degrees
TRUE_MOSAIC = 0.2        # degrees (subtle broadening)

# === INITIAL GUESS (PERTURBED) ===
INIT_PHI = 1.0           # 1° error in orientation
INIT_MOSAIC = 0.5        # Overestimate of mosaicity

# === FIXED PARAMETERS ===
FIXED_CRYSTAL_PARAMS = dict(
    cell_a=cell_params[0],
    cell_b=cell_params[1],
    cell_c=cell_params[2],
    cell_alpha=cell_params[3],
    cell_beta=cell_params[4],
    cell_gamma=cell_params[5],
    N_cells=(36, 47, 29),
    osc_range_deg=0.0,      # Single frame (no oscillation)
    phi_steps=1,
    spindle_axis=(-1, 0, 0),
    # MOSFLM orientation from A.mat
    mosflm_a_star=a_star,
    mosflm_b_star=b_star,
    mosflm_c_star=c_star,
    # Mosaic seed for deterministic gradients (CRITICAL!)
    mosaic_seed=42,
    mosaic_domains=5,
)

print("Ground Truth:")
print(f"  phi_start_deg = {TRUE_PHI}°")
print(f"  mosaic_spread_deg = {TRUE_MOSAIC}°")
print(f"\nInitial Guess:")
print(f"  phi_start_deg = {INIT_PHI}° (error: {abs(INIT_PHI - TRUE_PHI)}°)")
print(f"  mosaic_spread_deg = {INIT_MOSAIC}° (error: {abs(INIT_MOSAIC - TRUE_MOSAIC)}°)")
```

**CRITICAL**: `mosaic_seed=42` ensures deterministic mosaic domain sampling. Without this, gradients are meaningless because each forward pass samples different random rotations.

---

### Cell 6: Generate Target Pattern (Markdown + Code)

**Markdown:**
```markdown
## 4. Generate "Experimental" Target

We generate a synthetic diffraction pattern using ground truth parameters.
This serves as the optimization target.
```

**Code:**
```python
def create_simulator(phi_deg, mosaic_deg, hkl_grid, hkl_meta):
    """Create simulator with given parameters."""
    crystal_config = CrystalConfig(
        **FIXED_CRYSTAL_PARAMS,
        phi_start_deg=phi_deg,
        mosaic_spread_deg=mosaic_deg,
    )

    crystal = Crystal(crystal_config, beam_config=beam_config,
                      device=device, dtype=dtype)
    crystal.hkl_data = hkl_grid.to(device=device, dtype=dtype)
    crystal.hkl_metadata = hkl_meta

    detector = Detector(detector_config, device=device, dtype=dtype)

    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        beam_config=beam_config,
        device=device,
        dtype=dtype,
    )
    return simulator, crystal

# Generate target with ground truth parameters
print("Generating target pattern (ground truth)...")
sim_target, _ = create_simulator(TRUE_PHI, TRUE_MOSAIC, hkl_grid, hkl_meta)

with torch.no_grad():
    target = sim_target.run()

print(f"Target shape: {target.shape}")
print(f"Target sum: {target.sum().item():.2e}")
print(f"Target max: {target.max().item():.2e}")
print(f"Non-zero pixels: {(target > 0).sum().item():,} / {target.numel():,}")
```

---

### Cell 7: Visualize Target (Markdown + Code)

**Markdown:**
```markdown
## 5. Visualize the Target Pattern

Real diffraction patterns have huge dynamic range, so we use log scale.
```

**Code:**
```python
def plot_diffraction(image, title="", ax=None, vmax_percentile=99.9):
    """Plot diffraction pattern with log scale."""
    if isinstance(image, torch.Tensor):
        img = image.detach().cpu().numpy()
    else:
        img = image

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))

    # Log scale with floor to avoid log(0)
    img_log = np.log10(img + 1e-10)
    vmax = np.percentile(img_log[img > 0], vmax_percentile) if (img > 0).any() else 0
    vmin = vmax - 4  # 4 orders of magnitude

    im = ax.imshow(img_log, origin='lower', cmap='viridis',
                   vmin=vmin, vmax=vmax, aspect='auto')
    ax.set_title(title)
    ax.set_xlabel('Fast axis (pixels)')
    ax.set_ylabel('Slow axis (pixels)')
    plt.colorbar(im, ax=ax, label='log10(intensity)')
    return ax

fig, ax = plt.subplots(figsize=(10, 10))
plot_diffraction(target, f"Target (phi={TRUE_PHI}°, mosaic={TRUE_MOSAIC}°)", ax=ax)
plt.tight_layout()
plt.show()
```

---

### Cell 8: Compare Initial vs Target (Markdown + Code)

**Markdown:**
```markdown
## 6. Compare Initial Guess to Target

The perturbed parameters produce a visibly different pattern.
The goal of refinement is to recover the target.
```

**Code:**
```python
# Generate pattern with initial (wrong) parameters
print("Generating initial pattern (perturbed)...")
sim_init, _ = create_simulator(INIT_PHI, INIT_MOSAIC, hkl_grid, hkl_meta)

with torch.no_grad():
    initial_pattern = sim_init.run()

# Compute initial loss
initial_loss = torch.nn.functional.mse_loss(initial_pattern, target).item()

print(f"Initial MSE loss: {initial_loss:.4e}")

# Visualize comparison
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

plot_diffraction(target, f"Target\nphi={TRUE_PHI}°, mosaic={TRUE_MOSAIC}°", ax=axes[0])
plot_diffraction(initial_pattern, f"Initial Guess\nphi={INIT_PHI}°, mosaic={INIT_MOSAIC}°", ax=axes[1])

# Difference (linear scale for visibility)
diff = (initial_pattern - target).cpu().numpy()
vmax = np.percentile(np.abs(diff), 99)
im = axes[2].imshow(diff, origin='lower', cmap='RdBu_r',
                    vmin=-vmax, vmax=vmax, aspect='auto')
axes[2].set_title(f"Difference\nMSE = {initial_loss:.2e}")
axes[2].set_xlabel('Fast axis (pixels)')
axes[2].set_ylabel('Slow axis (pixels)')
plt.colorbar(im, ax=axes[2], label='Intensity difference')

plt.tight_layout()
plt.show()
```

---

### Cell 9: Setup Refinement (Markdown + Code)

**Markdown:**
```markdown
## 7. Set Up Gradient-Based Refinement

We create learnable parameters and an optimizer.
The key insight: parameters passed to `CrystalConfig` can be PyTorch tensors with `requires_grad=True`.
```

**Code:**
```python
# Create learnable parameters
phi_param = torch.tensor(INIT_PHI, device=device, dtype=dtype, requires_grad=True)
mosaic_param = torch.tensor(INIT_MOSAIC, device=device, dtype=dtype, requires_grad=True)

# Optimizer
optimizer = torch.optim.Adam([phi_param, mosaic_param], lr=0.05)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=5, verbose=True
)

# History tracking
history = {
    'iteration': [],
    'loss': [],
    'phi': [],
    'mosaic': [],
}

# Frame storage for GIF animation
frames = []
FRAME_INTERVAL = 3  # Save frame every N iterations

print("Refinement setup:")
print(f"  Parameters: phi_param, mosaic_param")
print(f"  Optimizer: Adam(lr=0.05)")
print(f"  Scheduler: ReduceLROnPlateau(patience=5)")
```

---

### Cell 10: Refinement Loop (Markdown + Code)

**Markdown:**
```markdown
## 8. Run Refinement

Each iteration:
1. Build crystal config with current (differentiable) parameters
2. Run forward simulation
3. Compute MSE loss against target
4. Backpropagate gradients
5. Update parameters

Expected runtime: ~30-60 seconds for 30 iterations.
```

**Code:**
```python
N_ITERATIONS = 30
detector = Detector(detector_config, device=device, dtype=dtype)

print(f"Starting refinement: {N_ITERATIONS} iterations")
print(f"{'Iter':>4} | {'Loss':>10} | {'phi (°)':>10} | {'mosaic (°)':>10} | {'LR':>8}")
print("-" * 55)

for iteration in range(N_ITERATIONS):
    optimizer.zero_grad()

    # Build config with current parameters (differentiable!)
    crystal_config = CrystalConfig(
        **FIXED_CRYSTAL_PARAMS,
        phi_start_deg=phi_param,
        mosaic_spread_deg=mosaic_param,
    )

    # Forward simulation
    crystal = Crystal(crystal_config, beam_config=beam_config,
                      device=device, dtype=dtype)
    crystal.hkl_data = hkl_grid.to(device=device, dtype=dtype)
    crystal.hkl_metadata = hkl_meta

    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        beam_config=beam_config,
        device=device,
        dtype=dtype,
    )
    predicted = simulator.run()

    # Loss
    loss = torch.nn.functional.mse_loss(predicted, target)

    # Backward
    loss.backward()

    # Update
    optimizer.step()
    scheduler.step(loss)

    # Physical constraints
    with torch.no_grad():
        mosaic_param.clamp_(min=0.01, max=2.0)

    # Record history
    history['iteration'].append(iteration)
    history['loss'].append(loss.item())
    history['phi'].append(phi_param.item())
    history['mosaic'].append(mosaic_param.item())

    # Progress
    if iteration % 5 == 0 or iteration == N_ITERATIONS - 1:
        lr = optimizer.param_groups[0]['lr']
        print(f"{iteration:4d} | {loss.item():10.2e} | {phi_param.item():10.4f} | {mosaic_param.item():10.4f} | {lr:8.5f}")

    # Save frame for GIF animation
    if iteration % FRAME_INTERVAL == 0 or iteration == N_ITERATIONS - 1:
        frames.append({
            'iteration': iteration,
            'loss': loss.item(),
            'phi': phi_param.item(),
            'mosaic': mosaic_param.item(),
            'predicted': predicted.detach().cpu().clone(),
        })

print("-" * 55)
print(f"Refinement complete! Saved {len(frames)} frames for animation.")
```

---

### Cell 11: Results Summary (Markdown + Code)

**Markdown:**
```markdown
## 9. Results Summary
```

**Code:**
```python
print("\n" + "=" * 60)
print("REFINEMENT RESULTS")
print("=" * 60)

print(f"\n{'Parameter':<20} | {'True':>10} | {'Initial':>10} | {'Refined':>10} | {'Error':>10}")
print("-" * 70)
print(f"{'phi_start_deg':<20} | {TRUE_PHI:>10.3f} | {INIT_PHI:>10.3f} | {phi_param.item():>10.3f} | {abs(phi_param.item() - TRUE_PHI):>10.3f}")
print(f"{'mosaic_spread_deg':<20} | {TRUE_MOSAIC:>10.3f} | {INIT_MOSAIC:>10.3f} | {mosaic_param.item():>10.3f} | {abs(mosaic_param.item() - TRUE_MOSAIC):>10.3f}")

print(f"\nConvergence:")
print(f"  Initial loss: {history['loss'][0]:.4e}")
print(f"  Final loss:   {history['loss'][-1]:.4e}")
print(f"  Reduction:    {history['loss'][0] / history['loss'][-1]:.1f}x")

# Success criteria
phi_error = abs(phi_param.item() - TRUE_PHI)
mosaic_error = abs(mosaic_param.item() - TRUE_MOSAIC)
loss_reduction = history['loss'][0] / history['loss'][-1]

print(f"\nSuccess Criteria:")
print(f"  [{'PASS' if phi_error < 0.1 else 'FAIL'}] phi error < 0.1° (actual: {phi_error:.3f}°)")
print(f"  [{'PASS' if mosaic_error < 0.1 else 'FAIL'}] mosaic error < 0.1° (actual: {mosaic_error:.3f}°)")
print(f"  [{'PASS' if loss_reduction > 10 else 'FAIL'}] loss reduction > 10x (actual: {loss_reduction:.1f}x)")
```

---

### Cell 12: Convergence Visualization (Markdown + Code)

**Markdown:**
```markdown
## 10. Visualize Convergence
```

**Code:**
```python
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Loss curve
axes[0, 0].semilogy(history['loss'], 'b-', linewidth=2)
axes[0, 0].set_xlabel('Iteration')
axes[0, 0].set_ylabel('MSE Loss')
axes[0, 0].set_title('Loss Convergence')
axes[0, 0].grid(True, alpha=0.3)

# Phi convergence
axes[0, 1].plot(history['phi'], 'g-', linewidth=2, label='Refined')
axes[0, 1].axhline(TRUE_PHI, color='r', linestyle='--', linewidth=2, label=f'True ({TRUE_PHI}°)')
axes[0, 1].axhline(INIT_PHI, color='gray', linestyle=':', linewidth=1, label=f'Initial ({INIT_PHI}°)')
axes[0, 1].set_xlabel('Iteration')
axes[0, 1].set_ylabel('phi_start_deg (°)')
axes[0, 1].set_title('Phi Convergence')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Mosaic convergence
axes[1, 0].plot(history['mosaic'], 'purple', linewidth=2, label='Refined')
axes[1, 0].axhline(TRUE_MOSAIC, color='r', linestyle='--', linewidth=2, label=f'True ({TRUE_MOSAIC}°)')
axes[1, 0].axhline(INIT_MOSAIC, color='gray', linestyle=':', linewidth=1, label=f'Initial ({INIT_MOSAIC}°)')
axes[1, 0].set_xlabel('Iteration')
axes[1, 0].set_ylabel('mosaic_spread_deg (°)')
axes[1, 0].set_title('Mosaic Convergence')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Final comparison
with torch.no_grad():
    sim_final, _ = create_simulator(phi_param.item(), mosaic_param.item(), hkl_grid, hkl_meta)
    final_pattern = sim_final.run()

diff_final = (final_pattern - target).cpu().numpy()
vmax = np.percentile(np.abs(diff_final), 99)
im = axes[1, 1].imshow(diff_final, origin='lower', cmap='RdBu_r',
                       vmin=-vmax, vmax=vmax, aspect='auto')
axes[1, 1].set_title(f'Final Residual\nMSE = {history["loss"][-1]:.2e}')
axes[1, 1].set_xlabel('Fast axis (pixels)')
axes[1, 1].set_ylabel('Slow axis (pixels)')
plt.colorbar(im, ax=axes[1, 1], label='Intensity difference')

plt.tight_layout()
plt.savefig('real_world_refinement_result.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\nFigure saved to: real_world_refinement_result.png")
```

---

### Cell 13: Generate Refinement Animation GIF (Markdown + Code)

**Markdown:**
```markdown
## 11. Generate Refinement Animation

Create an animated GIF showing how the predicted diffraction pattern evolves
during refinement, converging toward the experimental target.
```

**Code:**
```python
from matplotlib.animation import FuncAnimation, PillowWriter

def create_refinement_gif(
    frames: list,
    target_image: torch.Tensor,
    history: dict,
    output_path: str = "real_world_refinement_animation.gif",
    fps: int = 6,
) -> None:
    """
    Create animated GIF showing refinement progression.

    The animation shows three panels:
    1. Target (experimental) pattern - static
    2. Predicted pattern - evolves during refinement
    3. Residual (Target - Predicted) - shrinks as refinement converges

    Args:
        frames: List of dicts with 'iteration', 'loss', 'phi', 'mosaic', 'predicted'
        target_image: The target diffraction pattern
        history: Dict with loss/parameter history for annotation
        output_path: Output GIF file path
        fps: Frames per second (lower = slower animation)
    """
    if not frames:
        print("WARNING: No frames to animate")
        return

    target_np = target_image.cpu().numpy()

    # Compute consistent color scales across all frames
    all_intensities = [target_np] + [f["predicted"].numpy() for f in frames]

    # Use log scale for diffraction patterns
    def safe_log(arr):
        return np.log10(arr + 1e-10)

    log_target = safe_log(target_np)
    log_max = max(safe_log(arr).max() for arr in all_intensities)
    log_min = log_max - 4  # 4 orders of magnitude

    # Compute difference scale
    all_diffs = [target_np - f["predicted"].numpy() for f in frames]
    diff_max = max(max(abs(d.min()), abs(d.max())) for d in all_diffs)

    # Create figure with 3 panels
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    fig.suptitle("Real-World Refinement: CUSTOM Detector Geometry", fontsize=14, fontweight="bold")

    # Panel 1: Target (static)
    im_target = axes[0].imshow(
        log_target, cmap="viridis", origin="lower",
        vmin=log_min, vmax=log_max, aspect='auto'
    )
    axes[0].set_title(f"Target\n(phi={TRUE_PHI}°, mosaic={TRUE_MOSAIC}°)")
    axes[0].set_xlabel("Fast axis (pixels)")
    axes[0].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im_target, ax=axes[0], fraction=0.046, label="log10(intensity)")

    # Panel 2: Predicted (animated)
    first_pred = safe_log(frames[0]["predicted"].numpy())
    im_pred = axes[1].imshow(
        first_pred, cmap="viridis", origin="lower",
        vmin=log_min, vmax=log_max, aspect='auto'
    )
    title_pred = axes[1].set_title("Predicted (Iter 0)")
    axes[1].set_xlabel("Fast axis (pixels)")
    plt.colorbar(im_pred, ax=axes[1], fraction=0.046, label="log10(intensity)")

    # Panel 3: Residual (animated)
    first_diff = target_np - frames[0]["predicted"].numpy()
    im_diff = axes[2].imshow(
        first_diff, cmap="RdBu_r", origin="lower",
        vmin=-diff_max, vmax=diff_max, aspect='auto'
    )
    title_diff = axes[2].set_title("Residual (Target - Predicted)")
    axes[2].set_xlabel("Fast axis (pixels)")
    plt.colorbar(im_diff, ax=axes[2], fraction=0.046, label="Intensity difference")

    # Parameter annotation box
    param_text = fig.text(
        0.02, 0.02, "", fontsize=10, family="monospace",
        verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.9)
    )

    def update(frame_idx):
        """Update function for animation."""
        frame = frames[frame_idx]
        pred_np = frame["predicted"].numpy()
        diff_np = target_np - pred_np

        # Update predicted image
        im_pred.set_data(safe_log(pred_np))
        axes[1].set_title(f"Predicted (Iter {frame['iteration']})")

        # Update residual image
        im_diff.set_data(diff_np)

        # Update parameter text
        text = (
            f"Iteration: {frame['iteration']}\n"
            f"Loss: {frame['loss']:.3e}\n"
            f"───────────────────\n"
            f"phi:    {frame['phi']:+.4f}° (true: {TRUE_PHI}°)\n"
            f"mosaic: {frame['mosaic']:.4f}° (true: {TRUE_MOSAIC}°)\n"
            f"───────────────────\n"
            f"phi error:    {abs(frame['phi'] - TRUE_PHI):.4f}°\n"
            f"mosaic error: {abs(frame['mosaic'] - TRUE_MOSAIC):.4f}°"
        )
        param_text.set_text(text)

        return [im_pred, im_diff, param_text]

    plt.tight_layout(rect=[0, 0.12, 1, 0.95])

    # Create animation
    anim = FuncAnimation(
        fig, update,
        frames=len(frames),
        interval=1000 // fps,
        blit=False
    )

    # Save as GIF
    print(f"Creating GIF with {len(frames)} frames at {fps} fps...")
    writer = PillowWriter(fps=fps)
    anim.save(output_path, writer=writer)
    print(f"Animation saved to: {output_path}")

    plt.close()

# Generate the GIF
GIF_OUTPUT_PATH = "real_world_refinement_animation.gif"
create_refinement_gif(
    frames=frames,
    target_image=target,
    history=history,
    output_path=GIF_OUTPUT_PATH,
    fps=6,  # Slower for large detector (easier to see details)
)

# Display info about the generated GIF
import os
if os.path.exists(GIF_OUTPUT_PATH):
    size_mb = os.path.getsize(GIF_OUTPUT_PATH) / (1024 * 1024)
    print(f"\nGIF file size: {size_mb:.1f} MB")
    print(f"To view: open {GIF_OUTPUT_PATH}")
```

**Notes:**
- Uses log scale for diffraction patterns (4 orders of magnitude range)
- Shows parameter values and errors in real-time annotation
- `fps=6` is slower than the simple demo (fps=8) because the larger images need more viewing time
- Frame interval of 3 means ~10 frames for 30 iterations

---

### Cell 14: Gradient Verification (Markdown + Code)

**Markdown:**
```markdown
## 12. Gradient Verification (Optional)

Verify that analytical gradients match numerical (finite difference) gradients.
This confirms the differentiable implementation is correct.
```

**Code:**
```python
def compute_loss_for_phi(phi_val):
    """Compute loss for a given phi value (for finite difference)."""
    sim, _ = create_simulator(float(phi_val), TRUE_MOSAIC, hkl_grid, hkl_meta)
    with torch.no_grad():
        pred = sim.run()
    return torch.nn.functional.mse_loss(pred, target).item()

# Test point
test_phi = 0.5
eps = 0.001

# Numerical gradient (central difference)
loss_plus = compute_loss_for_phi(test_phi + eps)
loss_minus = compute_loss_for_phi(test_phi - eps)
numerical_grad = (loss_plus - loss_minus) / (2 * eps)

# Analytical gradient
phi_test = torch.tensor(test_phi, device=device, dtype=dtype, requires_grad=True)
crystal_config = CrystalConfig(**FIXED_CRYSTAL_PARAMS, phi_start_deg=phi_test, mosaic_spread_deg=TRUE_MOSAIC)
crystal = Crystal(crystal_config, beam_config=beam_config, device=device, dtype=dtype)
crystal.hkl_data = hkl_grid.to(device=device, dtype=dtype)
crystal.hkl_metadata = hkl_meta
sim = Simulator(crystal=crystal, detector=detector, beam_config=beam_config, device=device, dtype=dtype)
pred = sim.run()
loss = torch.nn.functional.mse_loss(pred, target)
loss.backward()
analytical_grad = phi_test.grad.item()

print("Gradient Verification (phi_start_deg)")
print("=" * 45)
print(f"Test point: phi = {test_phi}°")
print(f"Numerical gradient:  {numerical_grad:.6f}")
print(f"Analytical gradient: {analytical_grad:.6f}")
rel_error = abs(analytical_grad - numerical_grad) / (abs(numerical_grad) + 1e-10)
print(f"Relative error:      {rel_error:.2e}")
print(f"Status: {'PASS' if rel_error < 0.05 else 'FAIL'} (threshold: 5%)")
```

---

### Cell 15: Summary (Markdown)

```markdown
## 13. Summary

This tutorial demonstrated:

1. **Loading real crystallographic data** - MOSFLM orientation matrix (`A.mat`) and HKL reflections (`scaled.hkl`)

2. **CUSTOM detector convention** - Explicit specification of detector basis vectors for complex geometries

3. **Differentiable parameters** - `phi_start_deg` and `mosaic_spread_deg` as learnable PyTorch tensors

4. **Gradient-based refinement** - Adam optimizer minimizing MSE loss against synthetic "experimental" data

5. **Animated visualization** - GIF showing refinement progression with evolving predicted pattern and residuals

6. **Gradient verification** - Confirming analytical gradients match numerical finite differences

### Key Implementation Details

- **mosaic_seed=42**: Essential for deterministic gradients through stochastic mosaic sampling
- **MOSFLM vectors**: Encode both unit cell AND crystal orientation
- **CUSTOM convention**: Bypasses axis-swap logic, uses vectors directly
- **float32**: Sufficient for refinement; use float64 for gradcheck

### Extensions

- Add oscillation (`phi_steps=10`, `osc_range_deg=0.1`) for more realistic integration
- Refine additional parameters (misset angles, cell parameters)
- Use pixel batching for larger detectors (`simulator.run(pixel_batch_size=256)`)
- Apply to real experimental data with known ground truth
```

---

## Files to Create

| File | Description |
|------|-------------|
| `notebooks/real_world_refinement_tutorial.ipynb` | Main tutorial notebook |

## Output Files Generated by Notebook

| File | Description |
|------|-------------|
| `real_world_refinement_result.png` | Static 2×2 convergence visualization |
| `real_world_refinement_animation.gif` | Animated GIF of refinement progression |

---

## Implementation Checklist

- [ ] Create notebook file with all 15 cells
- [ ] Verify A.mat and scaled.hkl paths work from notebooks/ directory
- [ ] Run notebook end-to-end and capture outputs
- [ ] Verify success criteria pass (phi error < 0.1°, mosaic error < 0.1°, loss reduction > 10x)
- [ ] Verify static figure is saved (`real_world_refinement_result.png`)
- [ ] Verify GIF is generated (`real_world_refinement_animation.gif`)
- [ ] Check GIF file size is reasonable (<50 MB)
- [ ] Update notebooks/README.md if it exists

---

## Troubleshooting

### Issue: FileNotFoundError for A.mat or scaled.hkl
- Check REPO_ROOT detection logic
- Verify files exist at repo root: `ls -la A.mat scaled.hkl`

### Issue: 0% HKL hit rate
- Ensure `hkl_metadata` is set on crystal: `crystal.hkl_metadata = hkl_meta`
- Without metadata, HKL lookup uses wrong index offsets

### Issue: Zero gradient
- Verify `requires_grad=True` on parameter tensors
- Check `mosaic_seed` is set for mosaic parameters
- Ensure target was created with `torch.no_grad()` or `.detach()`

### Issue: Loss doesn't decrease
- Try reducing learning rate to 0.01
- Verify ground truth values are physically reasonable
- Check that initial perturbation isn't too large

### Issue: CUDA out of memory
- Use CPU: `device = torch.device("cpu")`
- Use pixel batching: `simulator.run(pixel_batch_size=128)`

### Issue: GIF file is too large (>100 MB)
- Increase `FRAME_INTERVAL` to save fewer frames (e.g., 5 instead of 3)
- Reduce `fps` to compress animation duration
- Consider using a smaller ROI for demonstration

### Issue: GIF creation fails with "No module named 'PIL'"
- Install Pillow: `pip install Pillow`
- matplotlib's PillowWriter requires Pillow for GIF export

### Issue: GIF shows no visible change in residuals
- Verify ground truth and initial perturbation are different enough
- Check that frames are being saved (print `len(frames)` after loop)
- Ensure `predicted.detach().cpu().clone()` is called (not just reference)

---

## Success Criteria

1. **Loss decreases** by at least 10x from initial to final
2. **phi_start_deg** recovers within ±0.1° of ground truth
3. **mosaic_spread_deg** recovers within ±0.1° of ground truth
4. **Gradient verification** passes (relative error < 5%)
5. **Runtime** < 2 minutes for full notebook (excluding GIF generation)
6. **GIF generated** successfully with visible convergence of residuals
7. **GIF file size** < 50 MB (reasonable for sharing)

---

## References

- Existing tutorial: `notebooks/refinement_tutorial.ipynb` (simpler, default detector)
- Refinement demo scripts: `scripts/refinement_demo*.py`
- HKL I/O: `src/nanobrag_torch/io/hkl.py`
- MOSFLM I/O: `src/nanobrag_torch/io/mosflm.py`
- Detector config: `docs/architecture/detector.md`
