# Phase B Static Audit — dtype Neutrality Analysis

**Timestamp:** 2025-10-10T173558Z
**Task:** `[DTYPE-NEUTRAL-001]` Phase B (B1-B5)
**Goal:** Map all dtype-cache coupling points to define remediation scope

## Executive Summary

**Root Cause:** Detector geometry caching (`get_pixel_coords`) stores basis vectors and pix0_vector at initialization time with `self.dtype`. When `Detector.to(dtype=torch.float64)` is later called, it updates `self.dtype` and instance tensors but **does NOT update the cached copies**. Subsequent cache comparisons (`torch.allclose`) attempt to compare float32 cached tensors against float64 live tensors → `RuntimeError`.

**Primary Hotspot:** `src/nanobrag_torch/models/detector.py:757-780` (cache validation in `get_pixel_coords`)

**Secondary Hotspot:** `src/nanobrag_torch/simulator.py:569-604` (ROI/pixel coord caching)

**Scope:** 2 files, 5 cache variables, 8 `torch.allclose` comparison sites

---

## B1: Static Audit of Detector Caches

### Cache Variables Identified

From `src/nanobrag_torch/models/detector.py`:

1. **`_cached_basis_vectors`** (tuple of 3 tensors)
   - **Initialization:** Line 145-149 — clones `fdet_vec`, `sdet_vec`, `odet_vec` at construction time
   - **Storage dtype:** Inherits from `self.dtype` at `__init__` (line 49: default `torch.float32`)
   - **Usage:** Line 762-764 — `.to(self.device)` device coercion but **NO dtype coercion**
   - **Comparison:** Line 767-773 — `torch.allclose(self.fdet_vec, cached_f, atol=1e-15)`
   - **Problem:** After `Detector.to(dtype=torch.float64)`, `self.fdet_vec` is float64 but `cached_f` remains float32 (only moved to device, not converted to dtype)

2. **`_cached_pix0_vector`** (single tensor)
   - **Initialization:** Line 150 — clones `self.pix0_vector`
   - **Storage dtype:** Inherits from `self.dtype` at init
   - **Usage:** Line 777 — `.to(self.device)` (device only)
   - **Comparison:** Line 778-780 — `torch.allclose(self.pix0_vector, cached_pix0, atol=1e-15)`
   - **Problem:** Same dtype mismatch after `to(dtype=...)` call

3. **`_pixel_coords_cache`** (Optional[torch.Tensor])
   - **Initialization:** Line 143 — set to `None`
   - **Population:** Line 791 — assigned from `_compute_planar_pixel_coords()` or `_compute_curved_pixel_coords()`
   - **Invalidation:** Line 236 (in `to()` method), Line 241 (in `invalidate_cache()`)
   - **Note:** This cache **is invalidated** by `to()` method (line 236), so it's **not a problem**

### Cache Validation Logic

**Location:** `detector.py:755-802` (`get_pixel_coords` method)

**Flow:**
```python
# Line 762-764: Cached tensors moved to device (but NOT dtype!)
cached_f = self._cached_basis_vectors[0].to(self.device)  # ← PROBLEM: no dtype arg
cached_s = self._cached_basis_vectors[1].to(self.device)
cached_o = self._cached_basis_vectors[2].to(self.device)

# Line 767-773: Comparison with live tensors (now mismatched dtypes)
if not (
    torch.allclose(self.fdet_vec, cached_f, atol=1e-15)  # ← RuntimeError here
    and torch.allclose(self.sdet_vec, cached_s, atol=1e-15)
    and torch.allclose(self.odet_vec, cached_o, atol=1e-15)
):
    geometry_changed = True

# Line 777-780: pix0 comparison (same issue)
cached_pix0 = self._cached_pix0_vector.to(self.device)  # ← PROBLEM: no dtype
if not torch.allclose(self.pix0_vector, cached_pix0, atol=1e-15):  # ← RuntimeError
    geometry_changed = True
```

**Critical Gap:** Lines 762-764, 777 call `.to(self.device)` but should call `.to(device=self.device, dtype=self.dtype)` to maintain dtype parity.

---

## B2: Inventory of Tensor Factories

### Detector Basis Vector Creation

**Locations:**
- `__init__` lines 125-133 (default config path)
- `_calculate_basis_vectors` lines 464-576 (dynamic calculation)

**Pattern:** All use `torch.tensor(..., device=self.device, dtype=self.dtype)` — **CORRECT**

### Pixel Grid Generation

**Location:** `_compute_planar_pixel_coords` lines 865-886

```python
s_indices = torch.arange(self.spixels, device=self.device, dtype=self.dtype) + 0.5
f_indices = torch.arange(self.fpixels, device=self.device, dtype=self.dtype) + 0.5
s_grid, f_grid = torch.meshgrid(s_indices, f_indices, indexing="ij")
```

**Status:** **CORRECT** — uses `self.dtype` consistently

### Beam Direction & Constants

**Location:** `beam_vector` property lines 213-237

```python
return torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)
```

**Status:** **CORRECT** — dtype-aware

### Summary

All tensor **factories** are dtype-neutral. Problem is isolated to **cache retrieval** logic that omits dtype coercion.

---

## B3: Cross-Component Survey

### Simulator Caches

From `src/nanobrag_torch/simulator.py`:

1. **`_cached_pixel_coords_meters`** (line 569)
   - Populated via `self.detector.get_pixel_coords().to(device=self.device, dtype=self.dtype)`
   - **Safe:** Explicitly coerces to `self.dtype`

2. **`_cached_roi_mask`** (lines 573-604)
   - Created via `torch.ones(..., device=self.device, dtype=self.dtype)`
   - **Safe:** dtype-aware creation

### Crystal Caches

Quick scan (no `_cached_` prefix found in `crystal.py`):
```bash
$ rg -n "_cached_" src/nanobrag_torch/models/crystal.py
# (no results)
```

**Status:** Crystal does NOT use explicit caching with potential dtype drift.

### Beam Model

No caching identified in `beam.py` (stateless property calculations).

**Conclusion:** Detector is the **only** component with dtype-unsafe cache handling.

---

## B4: Proposed Instrumentation Taps

For post-fix validation, add lightweight logging at these points:

| Tap | Location | Variable | Purpose |
|-----|----------|----------|---------|
| T1 | `detector.py:762` | `cached_f.dtype`, `self.fdet_vec.dtype` | Verify dtype match before comparison |
| T2 | `detector.py:777` | `cached_pix0.dtype`, `self.pix0_vector.dtype` | Verify dtype match before comparison |
| T3 | `detector.py:794` | `self._cached_basis_vectors[0].dtype` | Confirm cache update preserves `self.dtype` |
| T4 | `detector.py:236` | `self.dtype` | Log dtype after `to()` call to verify change propagates |

**Implementation Note:** These taps are optional and only needed if debugging persists after fix. Normal pytest assertions should suffice.

---

## B5: Artifact Summary & fix_plan Update

### Artifacts Generated

- `commands.txt` — timestamp and artifact root
- `detector_cached_vars.txt` — detector cache grep results
- `detector_allclose_calls.txt` — torch.allclose usage sites
- `all_cached_vars.txt` — project-wide cache inventory
- `analysis.md` — this document

### Key Findings

1. **Scope:** 1 component (Detector), 2 cache variables (`_cached_basis_vectors`, `_cached_pix0_vector`)
2. **Root cause:** Cache retrieval at lines 762-764, 777 omits `dtype` argument in `.to()` call
3. **Fix strategy:** Add `dtype=self.dtype` to 4 `.to()` calls (lines 762, 763, 764, 777)
4. **Regression coverage:** Determinism tests (AT-PARALLEL-013, AT-PARALLEL-024) will validate fix
5. **No additional tests required:** Existing test failures are perfect regression coverage

### Next Phase

**Phase C (Remediation Blueprint):**
- Draft code change: 4-line diff in `detector.py`
- Test strategy: Re-run `pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py`
- Success criterion: Tests reach seed-related logic (may still fail for seed reasons, but NOT dtype mismatches)
- Documentation: Update `docs/architecture/detector.md` line 73-88 (cache section) to note dtype handling

---

## References

- Phase A artifacts: `reports/2026-01-test-suite-triage/phase_d/20251010T172810Z/dtype-neutral/phase_a/`
- Detector architecture spec: `docs/architecture/detector.md` §§7-8
- PyTorch runtime checklist: `docs/development/pytorch_runtime_checklist.md` §2
- Testing strategy: `docs/development/testing_strategy.md` §1.4
