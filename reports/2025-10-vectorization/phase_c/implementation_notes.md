# Phase C1 Implementation Notes: Batched Neighborhood Gather

**Date:** 2025-10-07
**Git SHA:** (to be recorded in fix_plan)
**Initiative:** VECTOR-TRICUBIC-001 (PERF-PYTORCH-004 backlog)
**Plan Reference:** `plans/active/vectorization.md` Phase C (tasks C1–C3)
**Design Reference:** `reports/2025-10-vectorization/phase_b/design_notes.md`

---

## Executive Summary

Successfully implemented batched neighborhood gather (Phase C1) in `Crystal._tricubic_interpolation`. The implementation constructs `(B, 4, 4, 4)` structure factor neighborhoods for batched Miller index queries using advanced PyTorch indexing, eliminating the need for Python loops over query points.

**Key Deliverable:** Infrastructure for vectorized tricubic interpolation is complete. Phase D (polynomial evaluation vectorization) can now consume the batched neighborhoods.

---

## Implementation Changes

### File Modified: `src/nanobrag_torch/models/crystal.py`

**Lines:** 355–429 (replaced scalar-only gather with batched implementation)

**Key Changes:**

1. **Batch Flattening:** All input Miller indices `(h, k, l)` with arbitrary shapes are flattened to `(B,)` where `B = total number of query points`.

2. **Coordinate Grid Construction:** For each query point, build `(B, 4)` coordinate grids representing the 4×4×4 neighborhood:
   ```python
   offsets = torch.arange(-1, 3, device=self.device, dtype=torch.long)  # [-1, 0, 1, 2]
   h_grid_coords = h_flr_flat.unsqueeze(-1) + offsets  # (B, 4)
   ```

3. **Advanced Indexing for Neighborhoods:** Use broadcasting to gather `(B, 4, 4, 4)` subcubes:
   ```python
   sub_Fhkl = self.hkl_data[
       h_array_grid[:, :, None, None],  # (B, 4, 1, 1)
       k_array_grid[:, None, :, None],  # (B, 1, 4, 1)
       l_array_grid[:, None, None, :]   # (B, 1, 1, 4)
   ]
   ```

4. **Path Routing:**
   - **B=1 (scalar):** Use existing `polin3` helper (squeeze batch dim)
   - **B>1 (batched):** Fall back to nearest-neighbor until Phase D vectorizes `polin3`

5. **Out-of-Bounds Handling:** Preserved existing OOB detection; warning emission occurs before flattening.

---

## Test Coverage

### New Test File: `tests/test_tricubic_vectorized.py`

**Test Suite:** `TestTricubicGather` with 4 test cases

#### test_vectorized_matches_scalar
- **Purpose:** Validate batched gather produces correct neighborhoods
- **Coverage:** Scalar (B=1), batch (B=3), grid (S=2, F=3), edge OOB cases
- **Result:** ✅ PASSED (2.17s)

#### test_neighborhood_gathering_internals
- **Purpose:** White-box test validating internal shapes and coordinate arrays
- **Coverage:** Flattening logic, coordinate grid construction, sample values
- **Result:** ✅ PASSED

#### test_device_neutrality[cpu]
- **Purpose:** Verify CPU execution with correct device propagation
- **Result:** ✅ PASSED

#### test_device_neutrality[cuda]
- **Purpose:** Verify CUDA execution with correct device propagation
- **Result:** ✅ PASSED (fixed device comparison: `.device.type` vs `.device`)

### Regression Tests

**File:** `tests/test_at_str_002.py` (existing tricubic interpolation tests)

- `test_tricubic_interpolation_enabled` ✅ PASSED
- `test_tricubic_out_of_bounds_fallback` ✅ PASSED
- `test_auto_enable_interpolation` ✅ PASSED

**Combined Core Suite:** 38/38 tests passed (crystal geometry, detector geometry, vectorized gather)

---

## Design Alignment

### Conformance with design_notes.md

| Design Requirement | Implementation Status | Notes |
|--------------------|----------------------|-------|
| **Section 2.2:** `(B, 4, 4, 4)` output shape | ✅ Complete | Advanced indexing produces correct shape |
| **Section 2.3:** `(B, 4)` coordinate arrays | ✅ Complete | `h_indices`, `k_indices`, `l_indices` for Phase D |
| **Section 2.6:** Broadcasting pattern | ✅ Complete | Followed exact indexing pattern from design |
| **Section 4.1:** Differentiability | ✅ Preserved | No `.item()` calls; tensors stay on graph |
| **Section 4.2:** Device neutrality | ✅ Verified | CPU + CUDA tests pass |
| **Section 5.1:** OOB fallback | ✅ Preserved | Single warning emission, default_F fallback |

### Outstanding Work (Phase D Prerequisites)

- **Polynomial Vectorization:** `polint`, `polin2`, `polin3` helpers still expect scalar inputs
- **Batched Path Activation:** Currently falls back to nearest-neighbor for B>1
- **Performance Benchmarking:** Phase E will measure speedup gains

---

## Numerical Validation

### Shape Assertions

All tests verify correct tensor shapes:
- Scalar input `(1,)` → gather `(1, 4, 4, 4)` → output `(1,)`
- Batch input `(3,)` → gather `(3, 4, 4, 4)` → output `(3,)`
- Grid input `(2, 3)` → flatten `(6,)` → gather `(6, 4, 4, 4)` → reshape output `(2, 3)`

### Coordinate Validation

White-box test confirmed:
- For `h=1.5` (floor=1), coordinate grid is `[0, 1, 2, 3]` (= floor + offsets)
- Flattening preserves query points: `(1, 2)` → `(B=2,)`

### Device Propagation

- Input tensors on `device="cuda"` → neighborhoods gathered on CUDA → output on CUDA
- No silent CPU↔CUDA transfers detected

---

## Performance Characteristics

### Memory Footprint (Phase C1 Infrastructure)

| Detector Size | B (pixels) | sub_Fhkl Shape | Memory (float32) |
|---------------|-----------|----------------|------------------|
| 512×512       | 262,144   | (262144, 4, 4, 4) | ~67 MB |
| 1024×1024     | 1,048,576 | (1048576, 4, 4, 4) | ~268 MB |
| 2048×2048     | 4,194,304 | (4194304, 4, 4, 4) | ~1.07 GB |

**Observation:** Memory scales linearly with detector size. No OOM issues detected during testing.

### Execution Time (Baseline for Phase E)

**Current Status:** Phase C1 gathers neighborhoods but falls back to nearest-neighbor for B>1.
- Scalar path (B=1): Uses existing `polin3` → interpolation works
- Batched path (B>1): Falls back to `_nearest_neighbor_lookup` → no speedup yet

**Phase E Goal:** After Phase D vectorizes polynomial evaluation, measure speedup vs. current fallback.

---

## Code Quality Checklist

- [x] **No Python loops over batch dimension:** All operations use tensor broadcasting
- [x] **Device-neutral:** Offsets and grids inherit device from input tensors
- [x] **Differentiability preserved:** No `.item()` or `.detach()` calls on grad tensors
- [x] **Backward compatible:** Scalar path (B=1) unchanged; existing tests pass
- [x] **Clear comments:** Implementation cites design_notes.md sections
- [x] **Shape assertions in tests:** Validates expected tensor shapes
- [x] **OOB handling:** Preserved existing warning/fallback logic

---

## Known Limitations

1. **Batched Path Uses Fallback:**
   - Phase C1 builds neighborhoods correctly but doesn't use them yet
   - Falls back to nearest-neighbor for B>1 pending Phase D
   - Warning message updated to reflect partial implementation

2. **No Mini-Batching:**
   - Phase C1 processes all B points at once
   - May hit memory limits for very large detectors (>2048²)
   - Phase E will implement chunking if needed

3. **Phase D Dependency:**
   - Cannot activate batched interpolation path until `polin3` is vectorized
   - Current implementation validates gather infrastructure only

---

## Next Steps (Phase D)

### D1: Vectorize `polint` (1D interpolation)
- Accept `(B, 4)` coordinate arrays and `(B, 4)` values
- Return `(B,)` interpolated results
- Maintain numerical parity with C-code Lagrange formula

### D2: Vectorize `polin2`/`polin3` (2D/3D interpolation)
- Stack vectorized `polint` results using `torch.stack`
- Accept `(B, 4, 4)` and `(B, 4, 4, 4)` neighborhoods
- Test against scalar results for equivalence

### D3: Audit Differentiability
- Run `torch.autograd.gradcheck` on vectorized helpers
- Verify gradients flow through batched interpolation path
- Ensure no graph breaks for torch.compile

---

## Artifacts & References

### Implementation Artifacts
- **Modified:** `src/nanobrag_torch/models/crystal.py` lines 355–429
- **Created:** `tests/test_tricubic_vectorized.py` (4 test cases)
- **This Document:** `reports/2025-10-vectorization/phase_c/implementation_notes.md`

### Test Results
- **Targeted:** 1/1 passed (`test_vectorized_matches_scalar`)
- **Full Suite:** 4/4 passed (`test_tricubic_vectorized.py`)
- **Regression:** 3/3 passed (`test_at_str_002.py`)
- **Core Suite:** 38/38 passed (crystal + detector + vectorized tests)

### Plan References
- **Plan:** `plans/active/vectorization.md` Phase C tasks C1–C3
- **Design:** `reports/2025-10-vectorization/phase_b/design_notes.md` Section 2, Section 4
- **Fix Plan:** `docs/fix_plan.md` VECTOR-TRICUBIC-001 (to be updated)

---

## Observations & Lessons Learned

### Successful Patterns

1. **Design-First Approach:**
   - Phase B design memo provided clear tensor shape contracts
   - Implementation followed broadcasting patterns exactly
   - No trial-and-error indexing mistakes

2. **Test-Driven Development:**
   - Wrote tests before activating batched path
   - White-box tests caught coordinate grid bugs early
   - Device neutrality tests prevented CPU/CUDA drift

3. **Incremental Delivery:**
   - Phase C1 delivers gather infrastructure only
   - Preserves existing scalar path (no regressions)
   - Clear handoff to Phase D (polynomial work)

### Challenges Encountered

1. **Device Comparison Issue:**
   - Initial test compared `torch.device("cuda")` vs `torch.device("cuda:0")`
   - Fixed by comparing `.device.type` strings instead
   - Documented in test comments for future reference

2. **Test Selector Mismatch:**
   - `input.md` referenced `TestTricubicInterpolation::test_tricubic_interpolation_enabled`
   - Actual test path is `test_at_str_002.py::test_tricubic_interpolation_enabled` (function, not class method)
   - Ran all AT-STR-002 tests instead to ensure coverage

### Validation Insights

- **Gather Logic Correct:** Neighborhoods match expected HKL data patterns
- **Shape Handling Robust:** Works for scalar, 1D batch, 2D grid inputs
- **OOB Detection Active:** Warning triggers for edge cases as expected
- **No Memory Issues:** 1024² detector (268 MB) well within GPU/CPU limits

---

## Document Metadata

- **Author:** Ralph (nanoBragg PyTorch development loop)
- **Status:** COMPLETE (Phase C1 delivered)
- **Next Phase:** Phase D (polynomial vectorization)
- **Artifact Path:** `reports/2025-10-vectorization/phase_c/implementation_notes.md`

---

## Phase C3 Updates: Shape Assertions & Device-Aware Caching

**Date:** 2025-10-07 (continued)
**Git SHA:** (to be recorded in fix_plan)
**Plan Reference:** `plans/active/vectorization.md` Phase C task C3

### C3 Implementation Summary

Hardened the batched gather implementation with explicit shape assertions and device consistency checks to prevent silent regressions during Phase D polynomial vectorization work.

### Changes Made

**File Modified:** `src/nanobrag_torch/models/crystal.py` lines 412–464

#### 1. Shape Assertions (C3.1) ✅

Added assertions after neighborhood gathering to verify correct tensor shapes:

```python
# Phase C3: Shape assertions to prevent silent regressions
# Verify neighborhood tensor has correct shape for polynomial evaluation
assert sub_Fhkl.shape == (B, 4, 4, 4), \
    f"Neighborhood shape mismatch: expected ({B}, 4, 4, 4), got {sub_Fhkl.shape}"

# Verify coordinate arrays have correct shape
assert h_indices.shape == (B, 4), f"h_indices shape mismatch: expected ({B}, 4), got {h_indices.shape}"
assert k_indices.shape == (B, 4), f"k_indices shape mismatch: expected ({B}, 4), got {k_indices.shape}"
assert l_indices.shape == (B, 4), f"l_indices shape mismatch: expected ({B}, 4), got {l_indices.shape}"
```

**Code References:**
- `crystal.py:414-420` — Neighborhood and coordinate shape assertions

Added output shape assertions for both interpolation paths:

```python
# Scalar path (B=1):
assert F_cell.numel() == 1, \
    f"Scalar interpolation output must have 1 element, got {F_cell.numel()} (shape {F_cell.shape})"
assert result.shape == original_shape, \
    f"Output shape mismatch: expected {original_shape}, got {result.shape}"

# Batched path (B>1, fallback):
assert result.shape == original_shape, \
    f"Fallback output shape mismatch: expected {original_shape}, got {result.shape}"
```

**Code References:**
- `crystal.py:440-447` — Scalar path output assertions
- `crystal.py:461-462` — Batched fallback output assertion

**Note:** Changed scalar assertion from `F_cell.shape == torch.Size([])` to `F_cell.numel() == 1` because `polin3` may return either scalar `[]` or `[1]` shape depending on tensor operations.

#### 2. Device-Aware Caching Audit (C3.2) ✅

**Finding:** No explicit caching exists in `_tricubic_interpolation`.

**Device/Dtype Consistency Checks Added:**

```python
# Phase C3: Device/dtype consistency check
# Ensure all tensors are on the same device as the input query tensors
assert sub_Fhkl.device == h.device, \
    f"Device mismatch: sub_Fhkl on {sub_Fhkl.device}, input on {h.device}"
assert h_indices.device == h.device, \
    f"Device mismatch: h_indices on {h_indices.device}, input on {h.device}"
```

**Code References:**
- `crystal.py:422-427` — Device consistency assertions

**Device Handling Strategy:**
- `offsets` tensor: Created with explicit `device=self.device` parameter (line 373)
- `h_grid_coords`, `k_grid_coords`, `l_grid_coords`: Inherit device from `h_flr_flat` (CPU/CUDA propagates naturally)
- `sub_Fhkl`: Uses `device=self.device` when no HKL data loaded (line 384)
- `sub_Fhkl` (HKL path): Inherits device from `self.hkl_data` via advanced indexing (line 401-405)
- `h_indices`, `k_indices`, `l_indices`: Use `.to(dtype=self.dtype)` which preserves device (lines 386-388, 408-410)

**Verification:** Device checks enforce that all tensors stay on the input device throughout gather and interpolation.

#### 3. Targeted pytest Evidence (C3.3) ✅

**Command 1: Gather Tests**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -k "gather" -v
```

**Result:** 5/5 passed
- `test_vectorized_matches_scalar` ✅
- `test_neighborhood_gathering_internals` ✅
- `test_oob_warning_single_fire` ✅ (Phase C2 validation)
- `test_device_neutrality[cpu]` ✅
- `test_device_neutrality[cuda]` ✅

**Artifact:** `reports/2025-10-vectorization/phase_c/test_tricubic_vectorized.log`

**Command 2: Acceptance Test AT-STR-002**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py::test_tricubic_interpolation_enabled -v
```

**Result:** 1/1 passed

**Artifact:** `reports/2025-10-vectorization/phase_c/test_at_str_002_phi.log`

### Phase C3 Deliverables

- [x] **C3.1** — Shape assertions for neighborhoods `(B, 4, 4, 4)` and outputs
- [x] **C3.2** — Device-aware caching audit (no caching present; device checks added)
- [x] **C3.3** — Targeted pytest logs captured and stored

### Impact & Safety

**Regression Prevention:**
- Shape assertions catch any breaking changes to gather logic during Phase D refactoring
- Device checks prevent CPU↔CUDA mixed-device bugs
- Output assertions ensure reshape logic preserves input shapes

**Testing Coverage:**
- 6/6 targeted tests pass (5 gather + 1 acceptance)
- CPU and CUDA execution paths both validated
- OOB warning behavior verified (Phase C2)

**No Performance Impact:**
- Assertions compile away in optimized builds (typical Python behavior)
- No additional tensor operations introduced

### Known Limitations

**No Mini-Batching (from Phase C1):**
- All B points processed at once
- May hit memory limits for very large detectors (>2048²)
- Phase E will implement chunking if needed

**Batched Path Still Falls Back (from Phase C1):**
- Phase C3 hardens infrastructure but doesn't activate batched interpolation
- Phase D will vectorize `polin3`/`polin2`/`polint` to unlock batched path

### Next Steps: Phase D Prerequisites Met

**Phase D1 Ready:** Vectorize `polint`
- Input shapes: `(B, 4)` coordinate arrays, `(B, 4)` values
- Output shape: `(B,)` interpolated results
- Assertion coverage: `(B, 4)` inputs validated by C3 checks

**Phase D2 Ready:** Vectorize `polin2`/`polin3`
- Input shapes: `(B, 4, 4)` and `(B, 4, 4, 4)` neighborhoods
- Assertion coverage: `(B, 4, 4, 4)` neighborhood validated by C3 checks
- Device handling: All tensors guaranteed on same device

**Phase D3 Ready:** Audit differentiability
- Assertions use `.shape`, `.numel()`, `.device` (no `.item()` calls)
- No gradient-breaking operations introduced

---

**End of Implementation Notes**
