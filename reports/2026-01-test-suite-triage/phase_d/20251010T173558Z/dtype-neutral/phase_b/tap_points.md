# Instrumentation Tap Points for dtype Neutrality Validation

**Phase:** B4 (optional debugging instrumentation)
**Purpose:** Confirm dtype transitions after fix implementation

## Recommended Taps

### Tap 1: Cached Basis Vector Dtype Check
**Location:** `src/nanobrag_torch/models/detector.py:762`
**Variables:**
```python
cached_f = self._cached_basis_vectors[0].to(device=self.device, dtype=self.dtype)
# INSTRUMENTATION:
assert cached_f.dtype == self.fdet_vec.dtype, \
    f"Dtype mismatch: cached_f={cached_f.dtype}, fdet_vec={self.fdet_vec.dtype}"
```
**Rationale:** Verifies cache retrieval correctly coerces to current dtype before comparison.

### Tap 2: pix0_vector Dtype Check
**Location:** `src/nanobrag_torch/models/detector.py:777`
**Variables:**
```python
cached_pix0 = self._cached_pix0_vector.to(device=self.device, dtype=self.dtype)
# INSTRUMENTATION:
assert cached_pix0.dtype == self.pix0_vector.dtype, \
    f"Dtype mismatch: cached_pix0={cached_pix0.dtype}, pix0_vector={self.pix0_vector.dtype}"
```

**Rationale:** Verifies pix0 cache dtype parity.

### Tap 3: Cache Update Dtype Preservation
**Location:** `src/nanobrag_torch/models/detector.py:794`
**Variables:**
```python
self._cached_basis_vectors = (
    self.fdet_vec.clone(),
    self.sdet_vec.clone(),
    self.odet_vec.clone(),
)
# INSTRUMENTATION:
assert self._cached_basis_vectors[0].dtype == self.dtype, \
    f"Cache stored wrong dtype: cached={self._cached_basis_vectors[0].dtype}, expected={self.dtype}"
```

**Rationale:** Ensures new cache snapshots inherit current `self.dtype`.

### Tap 4: to() Method dtype Propagation
**Location:** `src/nanobrag_torch/models/detector.py:236` (after `self.dtype = dtype` line)
**Variables:**
```python
if dtype is not None:
    self.dtype = dtype
# INSTRUMENTATION:
print(f"[DETECTOR] to() called: new dtype={self.dtype}, device={self.device}")
```

**Rationale:** Confirms `to()` method correctly updates instance dtype attribute.

---

## Alternative: Pytest Assertions (Recommended)

Instead of inline instrumentation, leverage existing test assertions:

**Test:** `tests/test_at_parallel_013.py::test_pytorch_determinism_same_seed`

**Validation:**
1. Create Detector with `dtype=torch.float64`
2. Call `detector.get_pixel_coords()` (should not crash)
3. Assert pixel coords have `dtype=torch.float64`

**Example:**
```python
def test_detector_dtype_switch():
    config = DetectorConfig()
    detector = Detector(config, dtype=torch.float32)
    coords_f32 = detector.get_pixel_coords()
    assert coords_f32.dtype == torch.float32

    # Switch dtype
    detector.to(dtype=torch.float64)
    coords_f64 = detector.get_pixel_coords()
    assert coords_f64.dtype == torch.float64  # Should pass after fix

    # Verify no crash from cache comparison
    coords_f64_again = detector.get_pixel_coords()
    assert torch.allclose(coords_f64, coords_f64_again, atol=1e-12)
```

**Recommendation:** Use pytest assertions rather than inline logging. Inline taps are only needed if post-fix debugging reveals additional subtle dtype drift.

---

## Notes

- **Taps T1-T3 are optional** and should only be added if determinism tests still fail after Phase D implementation.
- **Primary validation:** Re-running `pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py` and confirming RuntimeError no longer occurs.
- **Success criterion:** Tests may still fail for seed-related reasons, but should NOT crash with dtype mismatch errors.
