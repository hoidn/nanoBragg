# Phase 0 Blueprint: Pure Function Refactoring

## Context
Phase 2 Attempt #1 revealed that `_compute_physics_for_position` is a bound method capturing `self`. Caching bound methods across instances is unsafe and causes silent correctness bugs. This blueprint defines the refactoring to make it a pure function.

## Current Signature (Bound Method)
```python
def _compute_physics_for_position(
    self,
    pixel_coords_angstroms,
    rot_a, rot_b, rot_c,
    rot_a_star, rot_b_star, rot_c_star,
    incident_beam_direction=None,
    wavelength=None,
    source_weights=None
):
```

## Self References Found

Extracted from simulator.py lines 169-384:

1. **`self.incident_beam_direction`** (line 202)
   - Type: `torch.Tensor`, shape (3,) or (n_sources, 3)
   - Already a parameter with default value fallback

2. **`self.wavelength`** (line 204)
   - Type: `torch.Tensor`, scalar or shape (n_sources,)
   - Already a parameter with default value fallback

3. **`self.beam_config.dmin`** (line 252)
   - Type: `float`
   - Used for dmin culling (resolution limit)

4. **`self.crystal.get_structure_factor(h0, k0, l0)`** (line 285)
   - Type: Method call returning `torch.Tensor`
   - Core crystal method for structure factor lookup

5. **`self.crystal.N_cells_a/b/c`** (lines 288-290)
   - Type: `int` or `torch.Tensor`
   - Number of unit cells in each direction

6. **`self.crystal.config.shape`** (line 291)
   - Type: `CrystalShape` enum
   - Crystal shape for lattice structure factor calculation

7. **`self.crystal.config.fudge`** (line 292)
   - Type: `float`
   - Fudge factor for lattice structure factor

## Proposed Pure Function Signature

### Option 1: Module-level Function (RECOMMENDED)
```python
def compute_physics_for_position(
    # Geometry inputs (already parameters)
    pixel_coords_angstroms: torch.Tensor,
    rot_a: torch.Tensor,
    rot_b: torch.Tensor,
    rot_c: torch.Tensor,
    rot_a_star: torch.Tensor,
    rot_b_star: torch.Tensor,
    rot_c_star: torch.Tensor,

    # Beam parameters (already parameters with defaults removed)
    incident_beam_direction: torch.Tensor,
    wavelength: torch.Tensor,
    source_weights: Optional[torch.Tensor] = None,

    # NEW: Beam configuration (dmin culling)
    dmin: float = 0.0,

    # NEW: Crystal structure factor function
    crystal_get_structure_factor: Callable[[torch.Tensor, torch.Tensor, torch.Tensor], torch.Tensor],

    # NEW: Crystal parameters for lattice factor
    N_cells_a: int,
    N_cells_b: int,
    N_cells_c: int,
    crystal_shape: CrystalShape,
    crystal_fudge: float,
) -> torch.Tensor:
    """
    Compute physics (Miller indices, structure factors, intensity) for given positions.

    This is a pure function with no self references, enabling safe cross-instance
    kernel caching for torch.compile optimization (PERF-PYTORCH-004 Phase 0).

    All required state is passed as explicit parameters. The function contains no
    bound method closures and can be safely compiled and cached across simulator
    instances.

    Args:
        pixel_coords_angstroms: Pixel/subpixel coordinates in Angstroms (S, F, 3) or (batch, 3)
        rot_a, rot_b, rot_c: Rotated real-space lattice vectors (N_phi, N_mos, 3)
        rot_a_star, rot_b_star, rot_c_star: Rotated reciprocal vectors (N_phi, N_mos, 3)
        incident_beam_direction: Incident beam direction
            - Single source: shape (3,)
            - Multiple sources: shape (n_sources, 3)
        wavelength: Wavelength in Angstroms
            - Single source: scalar
            - Multiple sources: shape (n_sources,) or (n_sources, 1, 1)
        source_weights: Optional per-source weights for multi-source accumulation.
            Shape: (n_sources,). If None, equal weighting is assumed.
        dmin: Minimum d-spacing for culling (0 = no culling)
        crystal_get_structure_factor: Function to look up structure factors for (h0, k0, l0)
        N_cells_a/b/c: Number of unit cells in each direction
        crystal_shape: Crystal shape enum for lattice structure factor calculation
        crystal_fudge: Fudge factor for lattice structure factor

    Returns:
        intensity: Computed intensity |F|^2 integrated over phi and mosaic
            - Single source: shape (S, F) or (batch,)
            - Multiple sources: weighted sum across sources, shape (S, F) or (batch,)
    """
```

### Option 2: @staticmethod (Alternative)
```python
class Simulator:
    @staticmethod
    def _compute_physics_for_position(
        # ... same signature as Option 1 ...
    ) -> torch.Tensor:
```

**Recommendation: Use Option 1 (module-level function)**
- Clearer that it's a pure function with no class dependencies
- Easier to test in isolation
- More explicit about the separation from instance state
- Can be imported and used independently

## Implementation Plan

### P0.1: Design (CURRENT)
- ✓ Document all self references
- ✓ Design pure function signature
- ✓ Choose module-level vs @staticmethod approach

### P0.2: Refactor to Module-Level Function
1. Move function definition outside Simulator class (after imports, before class definition)
2. Update signature with all explicit parameters
3. Remove `self.` prefix from all references:
   - Remove `self.` from `incident_beam_direction` and `wavelength` fallbacks
   - Replace `self.beam_config.dmin` with `dmin` parameter
   - Replace `self.crystal.get_structure_factor(h0, k0, l0)` with `crystal_get_structure_factor(h0, k0, l0)`
   - Replace `self.crystal.N_cells_a/b/c` with `N_cells_a/b/c` parameters
   - Replace `self.crystal.config.shape` with `crystal_shape` parameter
   - Replace `self.crystal.config.fudge` with `crystal_fudge` parameter

### P0.3: Update All Call Sites
Find all invocations of `self._compute_physics_for_position(...)` and update to pass explicit parameters.

**Known call sites to update:**
1. `Simulator.run()` method - main simulation loop (likely multiple calls)
2. Any test code that calls `_compute_physics_for_position` directly

**Updated call pattern:**
```python
# OLD (bound method)
intensity = self._compute_physics_for_position(
    pixel_coords,
    rot_a, rot_b, rot_c,
    rot_a_star, rot_b_star, rot_c_star,
    incident_beam_direction=beam_dir,
    wavelength=wl,
    source_weights=weights
)

# NEW (pure function)
intensity = compute_physics_for_position(
    pixel_coords,
    rot_a, rot_b, rot_c,
    rot_a_star, rot_b_star, rot_c_star,
    incident_beam_direction=beam_dir,
    wavelength=wl,
    source_weights=weights,
    dmin=self.beam_config.dmin,
    crystal_get_structure_factor=self.crystal.get_structure_factor,
    N_cells_a=self.crystal.N_cells_a,
    N_cells_b=self.crystal.N_cells_b,
    N_cells_c=self.crystal.N_cells_c,
    crystal_shape=self.crystal.config.shape,
    crystal_fudge=self.crystal.config.fudge,
)
```

### P0.4: Validation
- Run full core test suite: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_suite.py tests/test_units.py tests/test_at_geo*.py -v`
- Run AT-PARALLEL tests: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_*.py -v`
- Ensure gradient tests pass (differentiability maintained)

**Expected results:**
- Core suite: 98 passed, 7 skipped, 1 xfailed
- AT-PARALLEL: 78 passed, 48 skipped
- No regressions

### P0.5: Documentation
Add inline comments explaining the refactoring:

```python
def compute_physics_for_position(
    # ... parameters ...
):
    """
    ... existing docstring ...

    REFACTORING NOTE (PERF-PYTORCH-004 Phase 0):
    This function was refactored from a bound method to a pure function to enable
    safe cross-instance kernel caching with torch.compile. Caching bound methods
    is unsafe because they capture `self`, which can lead to silent correctness
    bugs when the cached kernel is reused across different simulator instances
    with different state.

    All required state is now passed as explicit parameters, ensuring that:
    1. The function has no hidden dependencies on instance state
    2. torch.compile can safely cache compiled kernels across instances
    3. The function's behavior is fully determined by its inputs
    4. Testing and debugging are simplified (pure function properties)
    """
```

## Gradient Flow Verification

The refactoring must preserve gradient flow through all differentiable parameters:

**Differentiable inputs:**
- `pixel_coords_angstroms` - geometry (detector parameters)
- `rot_a/b/c`, `rot_a_star/b_star/c_star` - crystal orientation
- `incident_beam_direction` - beam geometry
- `wavelength` - beam energy

**Non-differentiable (config) inputs:**
- `dmin` - threshold (float constant)
- `N_cells_a/b/c` - integers
- `crystal_shape` - enum
- `crystal_fudge` - float constant

**Critical:** The `crystal_get_structure_factor` callable must preserve gradients if the structure factors are differentiable. Currently `Crystal.get_structure_factor()` is NOT differentiable (uses integer indexing), so no gradient issue here.

## Testing Strategy

1. **Unit test:** Verify the pure function produces identical output to the original bound method
2. **Integration test:** Verify full simulation pipeline produces identical results
3. **Gradient test:** Verify gradients flow correctly for differentiable parameters
4. **Cross-instance test:** Verify compiled kernel can be safely reused (Phase 2 prerequisite)

## Future Work (Phase 2+)

Once this refactoring is complete:
- Phase 2 can implement safe kernel caching using the pure function
- Phase 3 can pursue fullgraph=True compilation
- Phase 4 can explore custom kernel fusion

## Risk Assessment

**Low risk refactoring:**
- Function signature changes are mechanical
- All state is explicitly passed (no hidden dependencies)
- Test suite will catch any behavioral changes
- Gradient flow is preserved (no new non-differentiable operations)

**Potential issues:**
- Performance impact of passing additional parameters (likely negligible)
- Need to update any code that mocks or patches this method
- torch.compile may need warm-up recompile (one-time cost)

## Exit Criteria

- ✓ `compute_physics_for_position` is a module-level pure function
- ✓ No `self` references remain in the function body
- ✓ All call sites updated with explicit parameters
- ✓ Core test suite passes: 98/7/1
- ✓ AT-PARALLEL tests pass: 78/48
- ✓ Gradient tests remain green
- ✓ Inline documentation explains refactoring rationale
