# MOSAIC-GRADIENT-001: Fix Gradient Computation for Mosaic Spread Parameter

## Context
- **Initiative**: MOSAIC-GRADIENT-001 — Fix gradient correctness for `mosaic_spread_deg > 0`
- **Source**: `inbox/mosaic_gradient_bug_2025_12_08.md` from DBEX maintainers
- **Priority**: HIGH — blocks DB-AT-010 acceptance suite
- **Scope**: Single function fix with documentation updates

---

## Verification Status (2025-12-08)

**Bug Confirmed** via direct reproduction:

| `mosaic_spread_deg` | Analytical | Numerical | Ratio | Status |
|---------------------|------------|-----------|-------|--------|
| `0.0` | -3.771e+03 | -3.771e+03 | **1.00x** | PASS |
| `0.001` | -3.771e+03 | 3.230e+03 | **-0.86x** | FAIL |
| `0.003` | -3.772e+03 | 6.596e+04 | **-17.49x** | FAIL |

**Existing test status**: `test_suite.py::test_gradcheck_mosaic_spread` is **SKIPPED** due to stale API (expects 3-tuple, gets 2-tuple return from `get_rotated_real_vectors`).

---

## Root Cause Analysis

### Location
`src/nanobrag_torch/models/crystal.py:1336-1344` in `_generate_mosaic_rotations()`:

```python
# CURRENT (BROKEN):
random_axes = torch.randn(config.mosaic_domains, 3, device=self.device, dtype=self.dtype)
axes_normalized = random_axes / torch.norm(random_axes, dim=1, keepdim=True)

random_angles = (
    torch.randn(config.mosaic_domains, device=self.device, dtype=self.dtype)
    * mosaic_spread_rad
)
```

### Problem
`torch.randn()` without a seeded generator produces **different random values on each forward pass**:

1. Forward pass computes `loss` with random rotations R₁
2. `gradcheck` calls `loss(param + eps)` with **new** random rotations R₂
3. `gradcheck` calls `loss(param - eps)` with **new** random rotations R₃
4. Analytical gradient is computed through R₁

The numerical gradient `(loss(R₂) - loss(R₃)) / (2*eps)` measures sensitivity to **different** rotation matrices, not to the parameter `mosaic_spread_deg`. This causes arbitrary ratio mismatches.

### Spec Compliance
The spec (spec-a-core.md:367) already mandates deterministic seeding:
> "Mosaic seed: default -12345678; controlled by -mosaic_seed."

The implementation was **non-compliant** — `config.mosaic_seed` exists but is unused.

---

## Fix Strategy

### Approach: Deterministic Seeding + Reparameterization

Use `torch.Generator` seeded from `config.mosaic_seed`, combined with the reparameterization trick to preserve gradient flow through `mosaic_spread_deg`:

```python
def _generate_mosaic_rotations(self, config: "CrystalConfig") -> torch.Tensor:
    # Create deterministic generator
    gen = torch.Generator(device=self.device)
    seed = config.mosaic_seed if config.mosaic_seed is not None else -12345678
    # Handle negative seeds (Python int to unsigned)
    gen.manual_seed(seed & 0x7FFFFFFF)

    # Base randomness (frozen, no gradient needed)
    base_axes = torch.randn(
        config.mosaic_domains, 3, device=self.device, dtype=self.dtype, generator=gen
    )
    base_angles = torch.randn(
        config.mosaic_domains, device=self.device, dtype=self.dtype, generator=gen
    )

    # Normalize axes
    axes_normalized = base_axes / torch.norm(base_axes, dim=1, keepdim=True)

    # Differentiable scaling (gradient flows through mosaic_spread_rad)
    mosaic_spread_rad = torch.deg2rad(config.mosaic_spread_deg)  # ← may be tensor
    actual_angles = base_angles * mosaic_spread_rad  # ← gradient path preserved

    # ... rest unchanged (Rodrigues' formula)
```

**Key insight**: The reparameterization factors `base_angles * mosaic_spread_rad` separates:
- `base_angles`: Frozen random values (same every forward pass with same seed)
- `mosaic_spread_rad`: Potentially differentiable parameter (gradient flows through)

### Why Not Full C-Parity?

The C code uses a different algorithm (`mosaic_rotation_umat` with spherical cap sampling via CLCG). Full C-parity would require:
1. Porting `mosaic_rotation_umat` to differentiable PyTorch ops
2. Matching the exact CLCG sequence

**Decision**: Fix gradient bug first (this plan). C-parity for mosaic rotation algorithm is a separate, lower-priority task since the current Gaussian-based sampling is physically reasonable.

---

## Implementation Plan

### Phase A: Core Fix

**Goal**: Fix `_generate_mosaic_rotations()` to use deterministic seeding

**Exit Criteria**:
- `torch.autograd.gradcheck` passes for `mosaic_spread_deg` parameter
- Same seed produces identical rotation matrices across calls
- Different seeds produce different (but consistent) rotation matrices

| ID | Task | State | Details |
|----|------|-------|---------|
| A1 | Update `_generate_mosaic_rotations` | [ ] | Add `torch.Generator` seeded from `config.mosaic_seed`; use reparameterization pattern |
| A2 | Handle negative seed values | [ ] | C default is -12345678; use `seed & 0x7FFFFFFF` for unsigned conversion |
| A3 | Verify seed consistency | [ ] | Add unit test: same seed → same rotations; different seed → different rotations |
| A4 | Add gradcheck for mosaic_spread_deg | [ ] | Create test with non-zero mosaic that passes gradcheck |

### Phase B: Test Restoration

**Goal**: Fix stale tests and add comprehensive gradient coverage

**Exit Criteria**:
- `test_gradcheck_mosaic_spread` passes (not skipped)
- New gradcheck test covers full simulator path with mosaic

| ID | Task | State | Details |
|----|------|-------|---------|
| B1 | Fix `test_gradcheck_mosaic_spread` API | [ ] | Update to use 2-tuple return signature from `get_rotated_real_vectors` |
| B2 | Add simulator-level mosaic gradcheck | [ ] | Test gradient through full `Simulator.run()` with `mosaic_spread_deg > 0` |
| B3 | Add seed determinism test | [ ] | Verify same mosaic_seed produces identical images |
| B4 | Verify existing tests pass | [ ] | Run full test suite with `NANOBRAGG_DISABLE_COMPILE=1` |

### Phase C: Documentation

**Goal**: Update architecture docs to prevent recurrence

**Exit Criteria**:
- New CLAUDE.md rule on stochastic operations
- pytorch_design.md updated with stochastic op guidance
- Crystal component contract created

| ID | Task | State | Details |
|----|------|-------|---------|
| C1 | Add CLAUDE.md Rule 18 | [ ] | "Stochastic Operations Must Use Seeded Generators" |
| C2 | Update pytorch_design.md §1.2 | [ ] | Add subsection "1.2.1 Stochastic Operations" |
| C3 | Create crystal.md contract | [ ] | New file `docs/architecture/crystal.md` per Rule 14 |
| C4 | Update fix_plan.md | [ ] | Mark MOSAIC-GRADIENT-001 as resolved |

---

## Technical Specifications

### A1: Updated `_generate_mosaic_rotations` Implementation

```python
def _generate_mosaic_rotations(self, config: "CrystalConfig") -> torch.Tensor:
    """
    Generate random rotation matrices for mosaic domains.

    Uses deterministic seeding from config.mosaic_seed for reproducibility
    and gradient correctness. The reparameterization trick preserves
    gradient flow through mosaic_spread_deg.

    Args:
        config: CrystalConfig containing mosaic parameters.

    Returns:
        torch.Tensor: Rotation matrices with shape (N_mos, 3, 3).

    C-Code Behavior Reference:
        The C code (nanoBragg.c lines 3820-3868) uses mosaic_rotation_umat()
        with deterministic CLCG seeding. While this implementation uses
        Gaussian sampling instead of spherical cap sampling, it maintains
        the key property of deterministic, reproducible rotations.
    """
    from ..utils.geometry import rotate_axis

    # Create deterministic generator from mosaic_seed
    # Spec (spec-a-core.md:367): default seed is -12345678
    gen = torch.Generator(device=self.device)
    seed = config.mosaic_seed if config.mosaic_seed is not None else -12345678
    # Convert to valid unsigned seed (handle negative C-style seeds)
    gen.manual_seed(seed & 0x7FFFFFFF)

    # Generate frozen base randomness (same every call with same seed)
    # These do NOT carry gradients - they are the "noise" in reparameterization
    base_axes = torch.randn(
        config.mosaic_domains, 3, device=self.device, dtype=self.dtype, generator=gen
    )
    base_angle_scales = torch.randn(
        config.mosaic_domains, device=self.device, dtype=self.dtype, generator=gen
    )

    # Normalize axes
    axes_normalized = base_axes / torch.norm(base_axes, dim=1, keepdim=True)

    # Convert mosaic spread to radians (preserves gradient if input is tensor)
    if isinstance(config.mosaic_spread_deg, torch.Tensor):
        mosaic_spread_rad = torch.deg2rad(config.mosaic_spread_deg)
    else:
        mosaic_spread_rad = torch.deg2rad(
            torch.tensor(config.mosaic_spread_deg, device=self.device, dtype=self.dtype)
        )

    # Reparameterization: actual_angles = base_noise * scale_parameter
    # Gradient flows through mosaic_spread_rad, not through base_angle_scales
    random_angles = base_angle_scales * mosaic_spread_rad

    # Create rotation matrices using Rodrigues' formula
    identity = base_axes.new_zeros(3, 3)
    identity[0, 0] = 1.0
    identity[1, 1] = 1.0
    identity[2, 2] = 1.0
    identity_vecs = identity.unsqueeze(0).repeat(config.mosaic_domains, 1, 1)

    # Apply rotations to each column of identity matrix
    rotated_vecs = torch.zeros_like(identity_vecs)
    for i in range(3):
        rotated_vecs[:, :, i] = rotate_axis(
            identity_vecs[:, :, i], axes_normalized, random_angles
        )

    return rotated_vecs
```

### B2: Simulator-Level Mosaic Gradcheck Test

```python
def test_gradcheck_mosaic_spread_simulator(self):
    """Test gradients for mosaic_spread_deg through full simulator."""
    import os
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    device = torch.device("cpu")
    dtype = torch.float64

    def mosaic_loss_fn(mosaic_spread_deg):
        from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
        from nanobrag_torch.models import Crystal, Detector
        from nanobrag_torch.simulator import Simulator

        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(3, 3, 3),
            default_F=100.0,
            mosaic_spread_deg=mosaic_spread_deg,
            mosaic_domains=3,
            mosaic_seed=42,  # Fixed seed for reproducibility
        )
        detector_config = DetectorConfig(
            fpixels=16, spixels=16, pixel_size_mm=0.1, distance_mm=100.0
        )
        beam_config = BeamConfig(wavelength_A=1.0, fluence=1e12)

        crystal = Crystal(config=crystal_config, beam_config=beam_config,
                         device=device, dtype=dtype)
        detector = Detector(config=detector_config, device=device, dtype=dtype)
        simulator = Simulator(crystal=crystal, detector=detector,
                            beam_config=beam_config, device=device, dtype=dtype)

        return simulator.run().sum()

    mosaic_test = torch.tensor(0.5, dtype=dtype, requires_grad=True)

    gradcheck_result = torch.autograd.gradcheck(
        mosaic_loss_fn,
        mosaic_test,
        eps=1e-4,
        atol=1e-3,
        rtol=1e-2,
    )
    assert gradcheck_result, "Mosaic spread gradcheck failed"
```

### C1: New CLAUDE.md Rule

```markdown
18. **Stochastic Operations Must Use Seeded Generators:** Any use of `torch.rand`,
    `torch.randn`, or similar stochastic functions in code that may be differentiated
    **MUST** use a `torch.Generator` with deterministic seeding.
    -   **Action:** Create generator with `gen = torch.Generator(device=device)`,
        seed it from the appropriate config parameter (e.g., `config.mosaic_seed`),
        and pass `generator=gen` to stochastic ops.
    -   **Forbidden:** `torch.randn(...)` without `generator=` argument in any
        code path that may be differentiated.
    -   **Rationale:** Unseeded RNG produces different values per forward call,
        breaking `torch.autograd.gradcheck` which compares analytical gradients
        (from one forward pass) against numerical gradients (from multiple forwards
        with perturbed inputs). Without deterministic seeding, numerical gradients
        measure sensitivity to random noise, not to the intended parameter.
    -   **Reparameterization Pattern:** For parameters that scale stochastic values
        (e.g., `mosaic_spread_deg`), use: `actual_value = frozen_base_noise * scale_param`.
        The frozen noise has no gradient; the scale parameter carries gradients.
    -   **Verification:** Any function using stochastic operations must have a
        passing `torch.autograd.gradcheck` test with non-zero stochastic parameters.
```

### C2: pytorch_design.md Addition

```markdown
### 1.2.1 Stochastic Operations in Differentiable Paths

Stochastic tensor operations (e.g., mosaic rotation sampling) require special
handling for gradient correctness:

**Problem**: `torch.autograd.gradcheck` evaluates the function multiple times
with perturbed inputs. If the function uses unseeded randomness, each evaluation
sees different random values, making numerical gradient estimation meaningless.

**Solution**: Deterministic seeding + reparameterization

1. **Freeze the randomness**: Create a `torch.Generator` seeded from config
   (e.g., `config.mosaic_seed`). Pass this generator to all stochastic ops.

2. **Reparameterize for gradients**: Factor stochastic values as:
   ```python
   actual_value = frozen_base_noise * differentiable_scale
   ```
   where `frozen_base_noise` is sampled with the seeded generator (no gradient),
   and `differentiable_scale` is the parameter that should receive gradients.

3. **Test both properties**:
   - **Gradient correctness**: `gradcheck` passes with non-zero stochastic params
   - **Seed reproducibility**: Same seed produces identical results

**Example**: Mosaic rotation generation
```python
gen = torch.Generator(device=device)
gen.manual_seed(config.mosaic_seed & 0x7FFFFFFF)

base_angles = torch.randn(n_domains, generator=gen)  # frozen
actual_angles = base_angles * mosaic_spread_rad       # gradient flows here
```

**Evidence**: `tests/test_gradients.py::test_gradcheck_mosaic_spread_simulator`
```

### C3: Crystal Component Contract (docs/architecture/crystal.md)

```markdown
# Crystal Component Contract

## Overview

The `Crystal` class (`src/nanobrag_torch/models/crystal.py`) represents the
crystallographic sample, including unit cell geometry, orientation, and
mosaicity. It computes lattice vectors and applies rotations for diffraction
simulation.

## Responsibilities

1. **Unit Cell Geometry**: Compute real-space (a, b, c) and reciprocal-space
   (a*, b*, c*) lattice vectors from cell parameters
2. **Static Orientation**: Apply misset rotation to establish crystal reference frame
3. **Dynamic Rotations**: Apply phi (spindle) and mosaic domain rotations
4. **Gradient Flow**: Preserve differentiability for cell parameters, misset angles,
   and mosaic spread

## Key Interfaces

### `get_rotated_real_vectors(config: CrystalConfig)`

Returns rotated lattice vectors for all phi steps and mosaic domains.

**Returns**: `Tuple[Tuple[a, b, c], Tuple[a*, b*, c*]]`
- Real-space vectors: `(N_phi, N_mos, 3)` tensors
- Reciprocal-space vectors: `(N_phi, N_mos, 3)` tensors

### `_generate_mosaic_rotations(config: CrystalConfig)`

Generates random rotation matrices for mosaic domain sampling.

**Critical Invariants**:
1. **Deterministic**: Uses `config.mosaic_seed` for reproducibility
2. **Differentiable**: Gradients flow through `mosaic_spread_deg` via reparameterization
3. **Default seed**: -12345678 per spec-a-core.md:367

## Stochastic Operations

The mosaic rotation generation uses the **reparameterization trick**:

```python
# Frozen base noise (seeded, no gradient)
gen = torch.Generator(device).manual_seed(seed)
base_angles = torch.randn(n_domains, generator=gen)

# Differentiable scaling (gradient flows through mosaic_spread_rad)
actual_angles = base_angles * mosaic_spread_rad
```

This ensures:
- Same seed → same rotations (reproducibility)
- `torch.autograd.gradcheck` passes (gradient correctness)

## Units

| Parameter | Input Unit | Internal Unit |
|-----------|------------|---------------|
| cell_a/b/c | Angstroms | Angstroms |
| cell_alpha/beta/gamma | Degrees | Radians (converted) |
| mosaic_spread_deg | Degrees | Radians (converted) |
| misset_deg | Degrees | Radians (converted) |

## Configuration Parameters

See `CrystalConfig` in `src/nanobrag_torch/config.py` for full parameter list.

Key mosaic parameters:
- `mosaic_spread_deg`: Isotropic mosaic spread (default: 0.0)
- `mosaic_domains`: Number of mosaic domains (default: 1)
- `mosaic_seed`: RNG seed for domain rotations (default: -12345678)

## Gradient-Critical Notes

1. **All cell parameters** (`cell_a`, `cell_b`, etc.) support gradients when passed as tensors
2. **mosaic_spread_deg** supports gradients via reparameterization
3. **mosaic_seed** does NOT affect gradients (it only controls which frozen noise is used)

## C-Code Reference

Primary C-code sections for this component:
- Cell vector construction: nanoBragg.c lines 1800-1950
- Mosaic rotation: nanoBragg.c lines 3820-3868 (`mosaic_rotation_umat`)
- Phi rotation loop: nanoBragg.c lines 3044-3095

## Testing

- Gradient tests: `tests/test_gradients.py`
- Unit cell tests: `tests/test_suite.py::TestCrystalGeometry`
- Mosaic tests: `tests/test_suite.py::TestTier2GradientCorrectness::test_gradcheck_mosaic_spread`
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Seed handling differs from C code | Medium | Low | Behavior is still deterministic; C-parity for exact algorithm is separate task |
| Performance regression from Generator creation | Low | Low | Generator creation is ~1μs; negligible vs simulation time |
| Breaking existing tests that depend on random mosaic | Low | Medium | Search for tests using non-zero mosaic; update seeds if needed |

---

## Acceptance Criteria

1. **Gradient correctness**: `torch.autograd.gradcheck` passes for `mosaic_spread_deg=0.5` through full simulator
2. **Determinism**: Two runs with same `mosaic_seed` produce identical images (bitwise)
3. **Variability**: Two runs with different `mosaic_seed` produce different images
4. **Spec compliance**: Default seed is -12345678 per spec-a-core.md:367
5. **Documentation**: CLAUDE.md Rule 18 and pytorch_design.md §1.2.1 added
6. **Test restoration**: `test_gradcheck_mosaic_spread` passes (not skipped)

---

## Dependencies

- **Blocked by**: None
- **Blocks**: DBEX DB-AT-010 acceptance suite
- **Related**: DBEX-GRADIENT-001 (separate wavelength/distance issues)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-08 | Initial plan created from bug report analysis |
