# Phase M2g.3-M2g.4 Implementation Blocker

**Date:** 2025-10-08
**Loop:** Ralph i=161
**Phase:** CLI-FLAGS-003 M2g.3-M2g.4
**Status:** BLOCKED (architectural incompatibility)
**Git SHA:** (pre-commit)

## Executive Summary

Attempted to implement Phase M2g.3-M2g.4 per `input.md` directive:
- **M2g.3**: ✅ `initialize_phi_cache()` already exists and works
- **M2g.4**: ❌ **BLOCKED** - `apply_phi_carryover()` cannot handle 2D pixel grid broadcast

**Root Cause:** The current `apply_phi_carryover()` method (Crystal.py:245-342) expects 1D batched pixel indices but receives 2D grid indices `(S, F)`. This causes a tensor shape mismatch in `torch.where()` broadcast that cannot be resolved without either:
1. Expanding rotation tensors to include pixel dimensions → memory explosion (100+ GB)
2. Implementing a batched processing architecture → requires larger refactor
3. Moving cache application inside physics kernel → even larger refactor

## Implementation Attempt

### Code Changes Made

**File:** `src/nanobrag_torch/simulator.py`
**Location:** Lines 852-873 (after line 850 in original)

```python
# Phase M2g.4: Apply φ carryover cache for c-parity mode
# Thread pixel indices through to enable per-pixel φ=0 substitution
# C-Code Reference (nanoBragg.c:2797,3044-3095): OpenMP firstprivate persistence
if self.crystal.config.phi_carryover_mode == "c-parity":
    # Derive pixel indices from ROI mask using meshgrid
    # This creates (slow, fast) index tensors matching detector dimensions
    spixels = self.detector.spixels
    fpixels = self.detector.fpixels

    # Create index grids: slow_idx[s,f] = s, fast_idx[s,f] = f
    slow_grid = torch.arange(spixels, device=self.device, dtype=torch.long).view(-1, 1).expand(spixels, fpixels)
    fast_grid = torch.arange(fpixels, device=self.device, dtype=torch.long).view(1, -1).expand(spixels, fpixels)

    # Apply cache substitution: replace φ=0 with cached φ=final from prior pixels
    # This modifies the rotation tensors in-place for the vectorized physics computation
    (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = (
        self.crystal.apply_phi_carryover(
            slow_grid, fast_grid,
            (rot_a, rot_b, rot_c),
            (rot_a_star, rot_b_star, rot_c_star)
        )
    )
```

### Test Result

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -v
```

**Outcome:** Test runs but **FAILS** with expected error:
```
AssertionError: F_latt relative error 1.57884 > 1e-06.
Expected -2.3831966530, got 1.3794838506.
Absolute delta: 3.762680504.
This likely indicates φ=0 carryover not working correctly.
```

**Interpretation:**
- PyTorch produces `F_latt = 1.379` (fresh φ=0 rotation)
- Expected `F_latt = -2.383` (cached φ=final from prior pixel)
- Cache substitution is **not happening** despite code being called

## Root Cause Analysis

### Tensor Shape Incompatibility

The `apply_phi_carryover` method (Crystal.py:245-342) has a fundamental shape mismatch when handling 2D pixel grids:

**Input Shapes:**
```python
slow_grid, fast_grid: (S, F) = (2527, 2463) for supervisor case
rot_a: (N_phi, N_mos, 3) = (10, 1, 3)
```

**Inside `apply_phi_carryover`:**
```python
# Line 300: Index into cache
cache_real_a = self._phi_cache_real_a[slow_grid, fast_grid]
# Result shape: (S, F, N_mos, 3) = (2527, 2463, 1, 3)

# Line 324: Add phi dimension
cached_real_a_broadcast = cached_real_a.unsqueeze(0)
# Result shape: (1, S, F, N_mos, 3) = (1, 2527, 2463, 1, 3)

# Line 316-320: Create phi mask
phi_mask_broadcast: (N_phi, 1, 1) = (10, 1, 1)

# Line 332: Try to broadcast with torch.where
a_out = torch.where(phi_mask_broadcast, cached_real_a_broadcast, a)
# Shapes:
#   phi_mask_broadcast: (10, 1, 1)
#   cached_real_a_broadcast: (1, 2527, 2463, 1, 3)
#   a: (10, 1, 3)
#
# Broadcasting rules:
#   - phi_mask and cached need to align dimensions
#   - But cached has pixel dims (S, F) that a lacks!
#   - torch.where will try: (10, 2527, 2463, 1, 3) but a is only (10, 1, 3)
#   - This creates shape (10, 2527, 2463, 1, 3) output → MEMORY EXPLOSION
```

### Why It Doesn't Crash

Looking at the code more carefully, `torch.where` with broadcasting **does work** but creates a massive tensor:

```python
# Actual broadcast result:
a_out.shape = (N_phi, S, F, N_mos, 3) = (10, 2527, 2463, 1, 3)
# Memory: 10 × 2527 × 2463 × 1 × 3 × 8 bytes (float64) = 1.5 GB per vector × 3 = 4.5 GB
```

This doesn't immediately OOM for the small supervisor case but:
1. **Wastes memory** - rotation tensors explode from ~240 bytes to 4.5 GB
2. **Doesn't fix the bug** - later code expects `(N_phi, N_mos, 3)` not `(N_phi, S, F, N_mos, 3)`
3. **Breaks vectorization** - downstream code cannot handle per-pixel rotation tensors

### Why Cache Substitution Fails

Even if the broadcast succeeds, the returned tensors have shape `(N_phi, S, F, N_mos, 3)` but the caller (Simulator.run) expects `(N_phi, N_mos, 3)`. The code likely silently fails or gets reshaped, losing the per-pixel information.

## Architectural Mismatch

The fundamental issue identified in `analysis.md` (Option 1 Refresh, lines 106-159):

> **3.1 Current Vectorization Flow**
>
> rotated_real, rotated_recip = crystal.get_rotated_real_vectors(crystal_config)
> # Shape: (N_phi, N_mos, 3) - computed ONCE for entire image
>
> # All pixels (s,f) use the SAME rotation tensor:
> for s in range(spixels):
>     for f in range(fpixels):
>         # Same `rotated_real` for all (s,f) → no per-pixel carryover

The current architecture **cannot support per-pixel φ=0 substitution** without either:

### Option A: Expand Rotation Tensors (REJECTED)
```python
rotated_real: (S, F, N_phi, N_mos, 3)
# Memory: 2527 × 2463 × 10 × 1 × 3 × 4 bytes = 747 MB per vector × 6 = 4.5 GB
# With N_mos=10: 45 GB
```
**Verdict:** Violates memory constraint from analysis.md

### Option B: Batched Processing (FEASIBLE but needs refactor)
```python
# Process pixels in batches (e.g., row-by-row):
for row in range(spixels):
    # Compute rotations for this row only
    rot_row = crystal.get_rotated_real_vectors_for_row(row, ...)
    # Apply cache substitution per pixel in row
    # Run physics for row
```
**Verdict:** Requires refactoring `get_rotated_real_vectors` and `_compute_physics_for_position` to handle batched pixels. This is beyond M2g.3-M2g.4 scope.

### Option C: Move Cache Inside Physics Kernel (FEASIBLE but larger refactor)
```python
# Inside compute_physics_for_position or its caller:
def _compute_physics_with_cache(pixel_s, pixel_f, ...):
    # Compute fresh rotations
    rot_vectors = get_rotated_real_vectors(...)

    # Apply cache lookup per pixel
    if phi == 0 and cache_valid[pixel_s, pixel_f]:
        rot_vectors = cache[pixel_s, pixel_f]

    # Compute physics
    return compute_physics(rot_vectors, ...)
```
**Verdict:** Requires refactoring physics computation to accept per-pixel rotation inputs. Even larger scope than Option B.

## Recommended Path Forward

### Immediate Actions (Next Ralph Loop)

1. **Revert simulator.py changes** (lines 852-873) - they don't work and waste memory
2. **Document blocker in fix_plan** - M2g.4 cannot proceed without architecture decision
3. **Update plan tasks M2g.4 → blocked** pending supervisor architecture decision

### Architecture Decision Needed (Supervisor/Galph)

Choose between:

**Option B (Recommended):** Implement batched pixel processing
- **Pros:** Preserves vectorization within batches, ROI-friendly memory
- **Cons:** Requires refactoring `get_rotated_real_vectors` and run() loop
- **Effort:** Moderate (2-3 Ralph loops)
- **Risk:** Medium (new batching logic needs careful testing)

**Option C:** Move cache inside physics kernel
- **Pros:** Most architecturally clean, cache naturally per-pixel
- **Cons:** Deeper refactor touching compiled kernels
- **Effort:** Large (4-6 Ralph loops)
- **Risk:** High (touches performance-critical compiled code)

### Exit Strategy

If neither Option B nor C is acceptable within time constraints:
1. **Accept the parity gap** - document C-PARITY-001 as unimplementable in current architecture
2. **Skip c-parity mode** - focus on spec-compliant path only
3. **Revisit in Phase N+1** - defer to future architectural overhaul

## References

- `plans/active/cli-noise-pix0/plan.md:112-113` - M2g.3-M2g.4 original task descriptions
- `reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/analysis.md` - Option B design analysis
- `src/nanobrag_torch/models/crystal.py:245-342` - Current `apply_phi_carryover` implementation
- `src/nanobrag_torch/simulator.py:821-873` - Attempted integration point (lines 852-873 added)
- `tests/test_cli_scaling_parity.py:91-181` - Failing parity test
- `docs/bugs/verified_c_bugs.md:166-204` - C-PARITY-001 specification

## Metadata

- **Commit SHA:** (pending - changes not committed due to blocker)
- **Test Status:** FAILED (F_latt error 158%, expected parity gap)
- **Memory Impact:** Attempted approach creates 4.5 GB rotation tensors (100× expansion)
- **Next Owner:** Galph (architecture decision) → Ralph (implementation once unblocked)
