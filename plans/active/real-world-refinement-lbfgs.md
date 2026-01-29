# Real-World Refinement Tutorial: LBFGS Optimizer Variant

## Overview

**Purpose**: Create a second version of the real-world refinement notebook that uses the L-BFGS optimizer instead of Adam, demonstrating quasi-Newton optimization for crystallographic parameter refinement.

**Source**: `notebooks/real_world_refinement_tutorial.ipynb` (Adam version)

**Deliverable**: `notebooks/real_world_refinement_lbfgs.ipynb`

**Output Artifacts**:
- `real_world_refinement_lbfgs_result.png` - Static convergence visualization
- `real_world_refinement_lbfgs_animation.gif` - Animated GIF showing refinement progression

---

## Why L-BFGS?

L-BFGS (Limited-memory Broyden-Fletcher-Goldfarb-Shanno) is a quasi-Newton optimization method that approximates the Hessian matrix to take more informed steps. Compared to Adam:

| Aspect | Adam | L-BFGS |
|--------|------|--------|
| Step direction | Gradient + momentum | Quasi-Newton (curvature-aware) |
| Convergence | Linear | Superlinear (near optimum) |
| Iterations to converge | Many (30-100) | Few (5-20) |
| Cost per iteration | 1 forward + 1 backward | Multiple forward + backward (line search) |
| Hyperparameters | lr, betas, eps | lr, max_iter, history_size |
| Memory | O(params) | O(params × history_size) |
| Best for | Noisy gradients, large batches | Smooth loss landscapes, full-batch |

**For crystallographic refinement**, L-BFGS is often preferred because:
1. The loss landscape is smooth (deterministic simulation)
2. Full-batch gradients (no stochastic noise)
3. Fewer iterations = fewer expensive forward passes
4. Curvature information helps navigate narrow valleys

---

## Key Implementation Differences

### 1. Optimizer Setup

**Adam (original):**
```python
optimizer = torch.optim.Adam([phi_param], lr=0.003)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(...)
```

**L-BFGS (new):**
```python
optimizer = torch.optim.LBFGS(
    [phi_param],
    lr=1.0,              # L-BFGS typically uses lr=1.0
    max_iter=20,         # Max iterations per step() call
    history_size=10,     # Number of past gradients to store
    line_search_fn='strong_wolfe',  # Robust line search
)
```

### 2. Optimization Loop Structure

**Adam (original):**
```python
for iteration in range(N_ITERATIONS):
    optimizer.zero_grad()
    # ... build simulator ...
    predicted = simulator.run()
    loss = F.mse_loss(predicted, target)
    loss.backward()
    optimizer.step()
```

**L-BFGS (new):**
```python
def closure():
    optimizer.zero_grad()
    # ... build simulator ...
    predicted = simulator.run()
    loss = F.mse_loss(predicted, target)
    loss.backward()
    return loss

for iteration in range(N_ITERATIONS):
    loss = optimizer.step(closure)
```

### 3. Frame Capture for Animation

L-BFGS may call the closure multiple times per `step()` due to line search. We need to capture frames carefully:

```python
# Track closure calls vs optimizer steps
closure_calls = 0
frames = []

def closure():
    nonlocal closure_calls
    closure_calls += 1
    # ... compute loss ...

    # Only save frame on first closure call per step
    if closure_calls == 1:
        frames.append({...})

    return loss

for iteration in range(N_ITERATIONS):
    closure_calls = 0  # Reset for each step
    loss = optimizer.step(closure)
```

### 4. Convergence Criteria

L-BFGS has built-in convergence detection. We can also add early stopping:

```python
TOLERANCE = 1e-6
prev_loss = float('inf')

for iteration in range(N_ITERATIONS):
    loss = optimizer.step(closure)

    # Early stopping if converged
    if abs(prev_loss - loss.item()) < TOLERANCE:
        print(f"Converged at iteration {iteration}")
        break
    prev_loss = loss.item()
```

---

## Notebook Structure Changes

### Cells to Modify

| Cell | Change |
|------|--------|
| Title (intro) | Update to mention L-BFGS |
| Cell 7 (setup-refine) | Replace Adam with LBFGS, explain closure pattern |
| Cell 8 (run-refine) | Restructure loop to use closure |
| Cell 9 (results) | Update iteration count expectations |
| Cell 10 (viz) | Same structure, different filename |
| Cell 11 (animation) | Update output filename |
| Summary | Discuss L-BFGS characteristics |

### Cells Unchanged

- Environment setup
- Imports
- Data loading
- Detector configuration
- Parameter definition
- Target generation
- Visualization helpers
- Gradient verification

---

## Expected Performance Comparison

Based on the problem characteristics (smooth loss, single parameter, deterministic):

| Metric | Adam (100 iter) | L-BFGS (~10-15 iter) |
|--------|-----------------|----------------------|
| Total forward passes | 100 | ~30-50 (line search) |
| Final phi error | ~0.05° | ~0.01° (tighter) |
| Loss reduction | ~2.6x | ~10x+ |
| Wall time | ~90s | ~30-50s |

---

## Cell-by-Cell Specification

### Cell 1: Title (Markdown) - MODIFIED

```markdown
# Real-World Refinement Tutorial: L-BFGS Optimizer

This notebook demonstrates gradient-based parameter refinement using the **L-BFGS optimizer**,
a quasi-Newton method that uses curvature information for faster convergence.

**Comparison with Adam version:**
- L-BFGS: Fewer iterations, uses Hessian approximation, best for smooth loss landscapes
- Adam: More iterations, momentum-based, robust to noisy gradients

**What you'll learn:**
1. Loading real crystallographic data (MOSFLM matrices, HKL files)
2. Configuring a CUSTOM detector convention with explicit basis vectors
3. Using L-BFGS optimization with closure functions
4. Comparing convergence characteristics with first-order methods
```

### Cells 2-6: UNCHANGED

(Environment setup, imports, data loading, detector config, parameter definition, target generation)

### Cell 7: Setup Refinement - MODIFIED

```python
# Create learnable parameter (phi only)
phi_param = torch.tensor(INIT_PHI, device=device, dtype=dtype, requires_grad=True)

# L-BFGS optimizer
# - lr=1.0 is standard (line search finds actual step size)
# - history_size=10 stores 10 past gradients for Hessian approximation
# - strong_wolfe line search ensures sufficient decrease and curvature conditions
optimizer = torch.optim.LBFGS(
    [phi_param],
    lr=1.0,
    max_iter=20,           # Max line search iterations per step
    history_size=10,       # Memory for Hessian approximation
    tolerance_grad=1e-7,   # Gradient tolerance for convergence
    tolerance_change=1e-9, # Parameter change tolerance
    line_search_fn='strong_wolfe',
)

# History tracking
history = {
    'iteration': [],
    'loss': [],
    'phi': [],
    'closure_calls': [],  # Track line search evaluations
}

# Frame storage for GIF animation
frames = []

print("Refinement setup:")
print(f"  Parameter: phi_param")
print(f"  Optimizer: L-BFGS(lr=1.0, history_size=10)")
print(f"  Line search: strong_wolfe")
print(f"  Note: L-BFGS typically converges in 5-15 iterations")
```

### Cell 8: Run Refinement - MODIFIED (Major Change)

```python
N_ITERATIONS = 30  # L-BFGS needs fewer iterations
detector = Detector(detector_config, device=device, dtype=dtype)

# Convergence settings
TOLERANCE = 1e-8
prev_loss = float('inf')

print(f"Starting L-BFGS refinement: max {N_ITERATIONS} iterations")
print(f"{'Iter':>4} | {'Loss':>12} | {'phi (deg)':>12} | {'Closures':>10}")
print("-" * 50)

# Storage for closure to access
current_predicted = None
closure_count = 0

def closure():
    """
    Closure function required by L-BFGS.

    L-BFGS may call this multiple times per step() for line search.
    We must re-compute the full forward and backward pass each time.
    """
    global current_predicted, closure_count
    closure_count += 1

    optimizer.zero_grad()

    # Build config with current parameter (differentiable!)
    crystal_config = CrystalConfig(
        **FIXED_CRYSTAL_PARAMS,
        phi_start_deg=phi_param,
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

    # Store for frame capture (only on first call per step)
    current_predicted = predicted.detach().cpu().clone()

    # Loss
    loss = torch.nn.functional.mse_loss(predicted, target)

    # Backward
    loss.backward()

    return loss

# Main optimization loop
for iteration in range(N_ITERATIONS):
    closure_count = 0

    # L-BFGS step (may call closure multiple times)
    loss = optimizer.step(closure)

    # Record history
    history['iteration'].append(iteration)
    history['loss'].append(loss.item())
    history['phi'].append(phi_param.item())
    history['closure_calls'].append(closure_count)

    # Save frame for animation
    frames.append({
        'iteration': iteration,
        'loss': loss.item(),
        'phi': phi_param.item(),
        'predicted': current_predicted,
    })

    # Progress output
    print(f"{iteration:4d} | {loss.item():12.4e} | {phi_param.item():12.6f} | {closure_count:10d}")

    # Early stopping check
    if abs(prev_loss - loss.item()) < TOLERANCE:
        print(f"\nConverged! Loss change < {TOLERANCE}")
        break

    # Check if gradient is essentially zero (converged)
    if phi_param.grad is not None and abs(phi_param.grad.item()) < 1e-6:
        print(f"\nConverged! Gradient magnitude < 1e-6")
        break

    prev_loss = loss.item()

print("-" * 50)
total_closures = sum(history['closure_calls'])
print(f"Refinement complete!")
print(f"  Iterations: {len(history['iteration'])}")
print(f"  Total closure calls: {total_closures}")
print(f"  Avg closures per step: {total_closures / len(history['iteration']):.1f}")
```

### Cell 9: Results Summary - MODIFIED

```python
print("\n" + "=" * 65)
print("L-BFGS REFINEMENT RESULTS")
print("=" * 65)

print(f"\n{'Parameter':<20} | {'True':>10} | {'Initial':>10} | {'Refined':>10} | {'Error':>10}")
print("-" * 75)
print(f"{'phi_start_deg':<20} | {TRUE_PHI:>10.4f} | {INIT_PHI:>10.4f} | {phi_param.item():>10.4f} | {abs(phi_param.item() - TRUE_PHI):>10.4f}")

print(f"\nConvergence:")
print(f"  Initial loss:     {history['loss'][0]:.6e}")
print(f"  Final loss:       {history['loss'][-1]:.6e}")
print(f"  Loss reduction:   {history['loss'][0] / history['loss'][-1]:.1f}x")
print(f"  Iterations:       {len(history['iteration'])}")
print(f"  Total closures:   {sum(history['closure_calls'])}")

# Success criteria (tighter for L-BFGS)
phi_error = abs(phi_param.item() - TRUE_PHI)
loss_reduction = history['loss'][0] / history['loss'][-1]

print(f"\nSuccess Criteria:")
print(f"  [{'PASS' if phi_error < 0.05 else 'FAIL'}] phi error < 0.05 deg (actual: {phi_error:.4f} deg)")
print(f"  [{'PASS' if loss_reduction > 2.0 else 'FAIL'}] loss reduction > 2x (actual: {loss_reduction:.1f}x)")
print(f"  [{'PASS' if len(history['iteration']) < 20 else 'INFO'}] converged in < 20 iterations (actual: {len(history['iteration'])})")
```

### Cell 10: Visualization - MODIFIED (filenames)

Same code structure, but change:
- Output filename: `real_world_refinement_lbfgs_result.png`
- Add subplot showing closure calls per iteration

```python
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Loss curve
axes[0, 0].semilogy(history['loss'], 'b-o', linewidth=2, markersize=4)
axes[0, 0].set_xlabel('Iteration')
axes[0, 0].set_ylabel('MSE Loss')
axes[0, 0].set_title('Loss Convergence (L-BFGS)')
axes[0, 0].grid(True, alpha=0.3)

# Phi convergence
axes[0, 1].plot(history['phi'], 'g-o', linewidth=2, markersize=4, label='Refined')
axes[0, 1].axhline(TRUE_PHI, color='r', linestyle='--', linewidth=2, label=f'True ({TRUE_PHI} deg)')
axes[0, 1].axhline(INIT_PHI, color='gray', linestyle=':', linewidth=1, label=f'Initial ({INIT_PHI} deg)')
axes[0, 1].set_xlabel('Iteration')
axes[0, 1].set_ylabel('phi_start_deg')
axes[0, 1].set_title('Phi Convergence')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Closure calls per iteration (NEW - shows line search behavior)
axes[1, 0].bar(history['iteration'], history['closure_calls'], color='orange', alpha=0.7)
axes[1, 0].set_xlabel('Iteration')
axes[1, 0].set_ylabel('Closure Calls')
axes[1, 0].set_title('Line Search Evaluations per Step')
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Final residual
with torch.no_grad():
    sim_final, _ = create_simulator(phi_param.item(), hkl_grid, hkl_meta)
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
plt.savefig('real_world_refinement_lbfgs_result.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\nFigure saved to: real_world_refinement_lbfgs_result.png")
```

### Cell 11: Animation - MODIFIED (filename only)

Same animation code, but:
- Output: `real_world_refinement_lbfgs_animation.gif`
- Update title to mention L-BFGS

### Cell 12: Gradient Verification - UNCHANGED

### Cell 13: Summary - MODIFIED

```markdown
## Summary

This tutorial demonstrated L-BFGS optimization for crystallographic parameter refinement.

### L-BFGS vs Adam Comparison

| Aspect | Adam (other notebook) | L-BFGS (this notebook) |
|--------|----------------------|------------------------|
| Iterations | ~100 | ~10-15 |
| Closure calls | 100 | ~30-50 |
| Final phi error | ~0.05° | ~0.01° |
| Loss reduction | ~2.6x | ~10x+ |
| Best for | Noisy gradients | Smooth landscapes |

### Key L-BFGS Implementation Details

- **Closure function**: L-BFGS requires a closure that computes loss and calls backward()
- **Line search**: `strong_wolfe` ensures robust step size selection
- **history_size=10**: Stores 10 past gradients for Hessian approximation
- **lr=1.0**: Standard for L-BFGS (line search determines actual step)

### When to Use L-BFGS

**Use L-BFGS when:**
- Loss landscape is smooth (deterministic simulation)
- Full-batch gradients (no minibatching)
- Need tight convergence
- Few parameters to optimize

**Use Adam when:**
- Gradients are noisy (stochastic sampling)
- Many parameters (neural networks)
- Coarse convergence is acceptable
- Memory is constrained

### Output Files

- `real_world_refinement_lbfgs_result.png` - Static convergence visualization
- `real_world_refinement_lbfgs_animation.gif` - Animated GIF of refinement progression
```

---

## Implementation Checklist

- [ ] Create notebook file `notebooks/real_world_refinement_lbfgs.ipynb`
- [ ] Update title cell to mention L-BFGS
- [ ] Modify cell 7 (setup) with L-BFGS optimizer
- [ ] Restructure cell 8 with closure pattern
- [ ] Update cell 9 results with tighter criteria
- [ ] Add closure calls subplot to cell 10
- [ ] Update output filenames throughout
- [ ] Update summary cell with comparison
- [ ] Run notebook end-to-end
- [ ] Verify convergence in fewer iterations than Adam
- [ ] Verify output artifacts are generated

---

## Troubleshooting

### Issue: L-BFGS doesn't converge
- Check `lr` is 1.0 (not smaller like Adam)
- Ensure `line_search_fn='strong_wolfe'` is set
- Increase `max_iter` for line search

### Issue: "LBFGS can only optimize Tensors"
- Ensure phi_param is a tensor, not a Python float
- Check `requires_grad=True`

### Issue: Closure called too many times
- This is normal - line search evaluates multiple step sizes
- Typical: 2-5 closure calls per step
- If >20, check if gradient is very small (near convergence)

### Issue: Gradient is None after step
- L-BFGS clears gradients internally
- Access gradient inside closure if needed

### Issue: Loss increases
- L-BFGS with strong_wolfe should never increase loss
- If it does, check for NaN in gradients
- Try reducing `tolerance_change`

---

## Success Criteria

1. **Converges in fewer iterations** than Adam (<20 vs 100)
2. **Tighter final error** (<0.05° vs ~0.05°)
3. **Higher loss reduction** (>5x vs ~2.6x)
4. **Gradient verification passes** (same as Adam)
5. **Output artifacts generated** correctly
