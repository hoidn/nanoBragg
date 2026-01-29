# DBEX-GRADIENT-001: Gradient Flow Restoration for DBEX Integration

## Context
- **Initiative**: DBEX-GRADIENT-001 — Restore gradient correctness for beam wavelength and detector distance parameters to unblock DBEX integration (DB-AT-010 acceptance test).
- **Source**: `inbox/nanobrag_torch_gradient_blockers_report.md` from DBEX maintainers (2025-12-08)
- **Priority**: Tier-0 external blocker — blocks DBEX gradient-safety conformance profile
- **Scope**: Two distinct gradient issues requiring separate fixes

---

## Verification Status (2025-12-07)

**Verification script**: `scripts/verify_dbex_gradient_bugs.py`

| Test | Result | Gradient Value |
|------|--------|----------------|
| Wavelength at init time | **FAIL** | None (graph detached) |
| Distance at init time | **PASS** | -0.412 |
| Distance post-creation override | **FAIL** | None (graph detached) |

**Verified Code Pattern Difference**:
```
Crystal uses:   torch.as_tensor(config.cell_a, ...)     → preserves requires_grad ✓
Simulator uses: torch.tensor(beam_config.wavelength_A, ...) → DETACHES! ✗
```

**Key Findings**:

1. **Wavelength Bug (CONFIRMED)**: The simulator uses `torch.tensor()` at line 571, which **always** detaches the graph—even when tensor is passed at init time.
   - Input: `wavelength requires_grad: True`
   - After init: `Simulator.wavelength requires_grad: False`
   - Same object: `False` (new tensor created)

2. **Distance at Init (WORKS)**: When tensor passed to `DetectorConfig.distance_mm` at creation time, gradients flow correctly.
   - `Detector.distance requires_grad: True`
   - Gradient computed: `-0.412`

3. **Distance Post-Override (FAILS)**: DBEX's pattern of overriding `config.distance_mm` after detector creation breaks gradients.
   - Before override: `detector.distance: 0.1 (float)`
   - After override: `detector.distance: 0.1 (float)` ← unchanged!
   - The detector caches `self.distance` at init; later config changes don't propagate.

**Reconciled Understanding**:

The DBEX-reported 21,556× Jacobian mismatch is likely a **secondary symptom** of the post-override pattern. When gradients don't flow through the intended path, gradcheck compares:
- Numerical gradient: perturbs the tensor, but detector uses frozen float → zero sensitivity
- Analytical gradient: some partial flow through other code paths → non-zero but wrong

This explains the magnitude mismatch: it's not a scaling bug, it's comparing apples to oranges because the override pattern completely breaks the intended gradient flow.

---

## Issue Summary

### Issue 1: Beam Wavelength Gradient Detachment
- **Symptom**: `torch.autograd.gradcheck` fails with disconnected autograd graph
- **Root Cause**: `simulator.py:571` uses `torch.tensor()` which detaches incoming tensors
- **Impact**: Wavelength cannot be a learnable parameter, even when tensor passed at init time
- **Verification**: CONFIRMED
- **Fix**: Replace `torch.tensor()` with `torch.as_tensor()` (same pattern as Crystal)

### Issue 2: Detector Distance Post-Creation Override
- **Symptom**: Gradients don't flow when `config.distance_mm` overridden after detector creation
- **Root Cause**: `detector.distance` cached at init time, not updated by later config changes
- **Impact**: DBEX override pattern breaks gradient flow
- **Verification**: CONFIRMED
- **Note**: Distance works correctly when tensor passed at init time (gradient = -0.412)
- **Fix Options**:
  1. Convert `detector.distance` to `@property` that reads from config (supports post-override)
  2. Document that tensors must be passed at init time (simpler, but requires DBEX change)

---

## Root Cause Analysis

### Issue 1: Wavelength Detachment — Detailed Analysis

**Location**: `src/nanobrag_torch/simulator.py:571`

```python
# CURRENT (BROKEN):
self.wavelength = torch.tensor(self.beam_config.wavelength_A, device=self.device, dtype=self.dtype)
```

**Problem**: When `beam_config.wavelength_A` is already a tensor (passed by DBEX for gradient testing), `torch.tensor()` creates a **new tensor** that is disconnected from the original computation graph. This severs gradient flow.

**Contrast with working pattern** (Crystal, `src/nanobrag_torch/models/crystal.py:69-86`):
```python
# WORKING:
self.cell_a = torch.as_tensor(self.config.cell_a, device=self.device, dtype=self.dtype)
```

`torch.as_tensor()` preserves `requires_grad=True` if the input is already a tensor.

**Additional affected parameters** (same pattern at simulator.py:579, 583):
- `fluence` (line 579)
- `kahn_factor` (line 583)

### Issue 2: Detector Distance Post-Creation Override — Detailed Analysis

**Verified Behavior** (from `scripts/verify_dbex_gradient_bugs.py`):

```
Before override:
  detector_config.distance_mm: 100.0 (type: float)
  detector.distance: 0.1 (type: float)

After override:
  detector_config.distance_mm: 100.0 (type: Tensor)
  detector.distance: 0.1 (type: float)  <-- STILL FLOAT!
```

**Root Cause**: The Detector class computes `self.distance` during `__init__`:

```python
# detector.py:60 (runs at construction time)
self.distance = config.distance_mm / 1000.0  # Computed once, cached
```

The DBEX override pattern:
```python
detector = Detector(config=detector_config, ...)  # distance cached as float
detector_config.distance_mm = tensor_with_grad    # Config updated, but detector.distance unchanged
```

**Why Jacobian Mismatch was Reported**:

The 21,556× mismatch likely occurs because DBEX's gradient flow goes through:
1. The overridden `config.distance_mm` tensor → produces some gradient
2. But the actual physics uses `detector.distance` (frozen float) → produces different sensitivity

The mismatch is not a bug in the gradient computation itself, but a **semantic mismatch** between what the user expects to be differentiable and what actually participates in computation.

**Verification Evidence**: When tensor is passed at init time (not post-creation):
- `Detector.distance requires_grad: True`
- Gradcheck passes with 50% tolerance

**Note on Jacobian Magnitude**: The originally reported 21,556× mismatch could not be reproduced with our verification script. This may be because:
1. DBEX has additional transformations in their pipeline
2. The mismatch manifests only under specific conditions we didn't test
3. The override pattern completely severs gradient flow (which we confirmed), making comparison meaningless

---

## Fix Strategy

### Guiding Principles

1. **Follow the Crystal pattern**: Crystal parameters work correctly using `torch.as_tensor()`. Apply the same pattern to Beam and Detector.

2. **Property-based access for derived values**: Instead of caching derived values at init time, use `@property` methods that recompute from the authoritative source (config fields).

3. **Minimal changes**: Only modify code paths that affect gradient flow. Avoid refactoring unrelated code.

4. **Preserve API compatibility**: External callers should not need to change their code.

---

## Implementation Plan

### Phase A: Beam Parameter Gradient Restoration

**Goal**: Fix wavelength, fluence, and kahn_factor gradient detachment in simulator.py

**Exit Criteria**:
- `torch.autograd.gradcheck` passes for wavelength parameter
- Existing beam-related tests continue to pass

| ID | Task | State | Details |
|----|------|-------|---------|
| A1 | Add `as_tensor_preserving_grad` helper | [ ] | Create utility function in `src/nanobrag_torch/utils/tensor_utils.py` that uses `torch.as_tensor()` for tensors and `torch.tensor()` for scalars. Pattern: `x.to(device, dtype)` if tensor, else `torch.tensor(x, device, dtype)` |
| A2 | Update BeamConfig type hints | [ ] | Change `wavelength_A`, `fluence`, `polarization_factor` from `float` to `Union[float, torch.Tensor]` in `src/nanobrag_torch/config.py` |
| A3 | Fix wavelength initialization | [ ] | Replace `torch.tensor()` with helper at `simulator.py:571` |
| A4 | Fix fluence initialization | [ ] | Replace `torch.tensor()` with helper at `simulator.py:579` |
| A5 | Fix kahn_factor initialization | [ ] | Replace `torch.tensor()` with helper at `simulator.py:583` |
| A6 | Add wavelength gradcheck test | [ ] | Create `tests/test_gradients.py::test_gradcheck_wavelength` following existing cell parameter pattern |
| A7 | Add fluence gradcheck test | [ ] | Create `tests/test_gradients.py::test_gradcheck_fluence` |
| A8 | Verify existing tests pass | [ ] | Run full gradient test suite with `NANOBRAGG_DISABLE_COMPILE=1` |

### Phase B: Detector Distance Gradient Restoration

**Goal**: Fix distance_mm Jacobian mismatch by ensuring consistent gradient flow

**Exit Criteria**:
- `torch.autograd.gradcheck` passes for distance_mm parameter
- Numerical and analytical Jacobians agree within 5% tolerance

**Decision**: Use property-based access (Option 1) to support DBEX's post-creation override pattern without requiring them to change their code.

| ID | Task | State | Details |
|----|------|-------|---------|
| B1 | Analyze all `self.distance` usages | [ ] | Grep detector.py for all uses of `self.distance` to understand full scope |
| B2 | ~~Update DetectorConfig type hints~~ | [x] | Already `Union[float, torch.Tensor]` in config.py:178 |
| B3 | Convert distance to property | [ ] | Replace `self.distance = ...` assignment with `@property def distance(self)` that computes from `self.config.distance_mm / 1000.0` using `torch.as_tensor()` |
| B4 | Convert close_distance to property | [ ] | Same pattern for `close_distance` (depends on `distance`) |
| B5 | Convert pixel_size to property | [ ] | Same pattern for consistency (or verify it's not on gradient path) |
| B6 | Update simulator distance access | [ ] | Ensure `simulator.py:847` uses consistent path (detector property, not config directly) |
| B7 | Add distance_mm gradcheck test | [ ] | Create `tests/test_gradients.py::test_gradcheck_detector_distance` |
| B8 | Add post-override gradcheck test | [ ] | Test DBEX pattern: create detector with float, override config with tensor, verify gradient flows |
| B9 | Verify existing detector tests pass | [ ] | Run detector geometry and rotation gradient tests |

### Phase C: Integration Verification

**Goal**: Confirm DBEX harness passes with fixes applied

**Exit Criteria**:
- DBEX DB-AT-010 test suite passes (if reproducible locally)
- All existing nanobrag_torch tests pass

| ID | Task | State | Details |
|----|------|-------|---------|
| C1 | Run full nanobrag_torch test suite | [ ] | `env NANOBRAGG_DISABLE_COMPILE=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v` |
| C2 | Create DBEX-style integration test | [ ] | Replicate DBEX override pattern in local test to verify fix |
| C3 | Document fix in architecture docs | [ ] | Update `docs/architecture/README.md` gradient rules if needed |
| C4 | Update fix_plan.md | [ ] | Mark DBEX-GRADIENT-001 as resolved |

---

## Technical Specifications

### A1: Helper Function Design

```python
# src/nanobrag_torch/utils/tensor_utils.py

def as_tensor_preserving_grad(
    x: Union[float, int, torch.Tensor],
    device: torch.device,
    dtype: torch.dtype
) -> torch.Tensor:
    """
    Convert scalar or tensor to tensor while preserving gradient graph.

    Unlike torch.tensor(), this function preserves requires_grad=True
    when the input is already a tensor, maintaining gradient flow.

    Args:
        x: Scalar value or tensor to convert
        device: Target device
        dtype: Target dtype

    Returns:
        Tensor on specified device/dtype with gradient graph preserved
    """
    if isinstance(x, torch.Tensor):
        return x.to(device=device, dtype=dtype)
    return torch.tensor(x, device=device, dtype=dtype)
```

### B3: Property-Based Distance Design

```python
# src/nanobrag_torch/models/detector.py

class Detector:
    def __init__(self, config: DetectorConfig, ...):
        # Remove: self.distance = config.distance_mm / 1000.0
        # Store reference to config for dynamic access
        self._config = config
        ...

    @property
    def distance(self) -> torch.Tensor:
        """Detector distance in meters, computed from config.distance_mm."""
        distance_mm = self._config.distance_mm
        if isinstance(distance_mm, torch.Tensor):
            return distance_mm / 1000.0
        return torch.tensor(distance_mm / 1000.0, device=self.device, dtype=self.dtype)

    @property
    def close_distance(self) -> torch.Tensor:
        """Close distance in meters for obliquity calculations."""
        if self._config.close_distance_mm is not None:
            close_mm = self._config.close_distance_mm
            if isinstance(close_mm, torch.Tensor):
                return close_mm / 1000.0
            return torch.tensor(close_mm / 1000.0, device=self.device, dtype=self.dtype)
        return self.distance
```

---

## Verification Commands

```bash
# Phase A verification
env NANOBRAGG_DISABLE_COMPILE=1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_gradients.py -k "wavelength or fluence"

# Phase B verification
env NANOBRAGG_DISABLE_COMPILE=1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_gradients.py -k "detector_distance"

# Full regression check
env NANOBRAGG_DISABLE_COMPILE=1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_gradients.py tests/test_detector_geometry.py
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Property access slower than cached value | Medium | Low | Benchmark; cache invalidation pattern if needed |
| Breaking existing non-gradient code | Low | High | Comprehensive test run before/after |
| Incomplete distance usage audit | Medium | High | Thorough grep + manual review |
| Type hint changes break downstream | Low | Medium | Union types maintain backward compat |

---

## Dependencies

- `docs/development/testing_strategy.md` §4.1 — Tier-2 gradient test requirements
- `docs/architecture/detector.md` — Detector unit conventions
- `tests/test_gradients.py` — Existing gradcheck infrastructure
- `src/nanobrag_torch/models/crystal.py` — Reference implementation for working pattern

---

## Success Metrics

1. **Wavelength gradcheck**: `torch.autograd.gradcheck` passes with `rtol=0.05`
2. **Fluence gradcheck**: `torch.autograd.gradcheck` passes with `rtol=0.05`
3. **Distance gradcheck**: `torch.autograd.gradcheck` passes with `rtol=0.05`
4. **Jacobian ratio**: Numerical/analytical within 1.05x (not 21,556x)
5. **Regression**: All existing tests pass (552+ tests)
6. **DBEX unblock**: DB-AT-010 gradient suite passes (external verification)
