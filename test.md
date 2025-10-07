### From Procedural State to a Differentiable Computation Graph

A core goal of the PyTorch port was to make the simulation fully differentiable. This required a significant architectural shift from the original C code's procedural, stateful design to a more functional, declarative model that PyTorch's autograd engine can understand. This section highlights the key refactoring principles.

#### 1. From Stateful Loops to Vectorized Tensor Operations

The C implementation is built on deeply nested `for` loops that iterate over every pixel, source, and orientation, accumulating intensity one step at a time into a shared memory buffer. This stateful, sequential process is inherently non-differentiable.

The PyTorch version replaces this with vectorized tensor operations. Instead of looping, we define the entire computation as a single mathematical expression over large tensors, where dimensions for pixels, sources, and orientations are processed in parallel.

**C Implementation (Procedural Accumulation)**
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

#### 2. From Conditional Branches to Differentiable Masking

The C code uses `if` statements and `continue` to skip calculations for performance (e.g., for masked pixels or out-of-range reflections). These hard branches create "holes" in the computation graph.

We replace them with **differentiable masking**. The calculation is performed for all elements, and the result is multiplied by a binary tensor of zeros and ones. This zeros out unwanted contributions while keeping the computation graph intact.

**C Implementation (Conditional `continue`)**
If a reflection is outside the resolution limit, the `continue` statement skips the rest of the loop for that pixel. This is non-differentiable.
```c
// In nanoBragg.c
if(dmin > 0.0 && stol > 0.0) {
    if(dmin > 0.5/stol) {
        continue; // Non-differentiable jump
    }
}
// ... rest of calculation ...
```

**PyTorch Equivalent (Differentiable Masking)**
A boolean `dmin_mask` is computed. The intensity is multiplied by this mask, which effectively zeros out the contribution of culled reflections without breaking the graph.
```python
# In simulator.py
dmin_mask = None
if dmin > 0:
    stol = 0.5 * torch.norm(scattering_vector, dim=-1)
    dmin_mask = stol > (0.5 / dmin)

intensity = (F_cell * F_latt) ** 2

if dmin_mask is not None:
    # Apply mask instead of skipping
    intensity = intensity * (~dmin_mask).to(intensity.dtype)
```

#### 3. From Implicit State to Pure Functions

The C implementation relies on hundreds of local variables and a few globals that represent the simulation's state. Functions often implicitly depend on this shared state.

The PyTorch version refactors this into a functional style. Configuration is stored in explicit `dataclasses`, and the core physics calculation is a **pure function** (`compute_physics_for_position`) that receives all necessary data as arguments. Its output depends only on its inputs, creating a self-contained and traceable computation graph.

**C Implementation (Implicit, Shared State)**
Parameters like `fluence`, `r_e_sqr`, `Na`, `Nb`, `Nc`, and crystal vectors are declared in `main()` and used deep inside the loops without being passed as arguments. This creates hidden dependencies.
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

This functional refactoring is the key that unlocks the full power of PyTorch, enabling not only GPU acceleration but also the automatic differentiation necessary for advanced, gradient-based scientific modeling.
