# Phase B Summary — dtype Neutrality Static Audit

**Initiative:** `[DTYPE-NEUTRAL-001]`
**Phase:** B (Static Audit)
**Date:** 2025-10-10T173558Z
**Status:** ✅ COMPLETE

---

## Objectives Met

All Phase B tasks (B1-B5) completed per `plans/active/dtype-neutral.md`:

- ✅ **B1:** Static audit of detector caches
- ✅ **B2:** Inventory tensor factories
- ✅ **B3:** Cross-component survey
- ✅ **B4:** Draft tap list
- ✅ **B5:** Update fix_plan attempt log (this summary feeds into it)

---

## Key Findings

### 1. Root Cause Isolated

**Problem:** `Detector.get_pixel_coords()` cache validation compares tensors with mismatched dtypes after `Detector.to(dtype=...)` is called.

**Mechanism:**
1. Detector initialized with `dtype=torch.float32` (default)
2. Caches created: `_cached_basis_vectors`, `_cached_pix0_vector` (both float32)
3. Test calls `detector.to(dtype=torch.float64)`
4. `to()` method updates `self.dtype`, `self.fdet_vec`, etc. to float64
5. BUT cache variables (`_cached_basis_vectors`, `_cached_pix0_vector`) remain float32
6. Next `get_pixel_coords()` call retrieves caches via `.to(self.device)` (NO dtype coercion)
7. `torch.allclose` comparison attempts float32 ↔ float64 → **RuntimeError**

### 2. Precise Fix Location

**File:** `src/nanobrag_torch/models/detector.py`

**Lines to modify:**
- Line 762: `cached_f = self._cached_basis_vectors[0].to(self.device)` → add `dtype=self.dtype`
- Line 763: `cached_s = self._cached_basis_vectors[1].to(self.device)` → add `dtype=self.dtype`
- Line 764: `cached_o = self._cached_basis_vectors[2].to(self.device)` → add `dtype=self.dtype`
- Line 777: `cached_pix0 = self._cached_pix0_vector.to(self.device)` → add `dtype=self.dtype`

**Total changes:** 4 lines, trivial diff

### 3. Scope Boundaries

**Affected:**
- Detector geometry caching (1 component, 2 cache variables)

**Not affected:**
- Simulator caching (already dtype-safe, line 569 explicitly coerces)
- Crystal component (no caching)
- Beam component (no caching)
- Tensor factories (all dtype-aware)

**Blast radius:** Minimal — fix is surgical

---

## Evidence Artifacts

All artifacts stored under: `reports/2026-01-test-suite-triage/phase_d/20251010T173558Z/dtype-neutral/phase_b/`

| File | Purpose |
|------|---------|
| `commands.txt` | Timestamp and artifact root reference |
| `detector_cached_vars.txt` | Grep results for `_cached` in detector.py |
| `detector_allclose_calls.txt` | Grep results for `torch.allclose` in detector.py |
| `all_cached_vars.txt` | Project-wide cache variable inventory |
| `analysis.md` | Comprehensive B1-B3 audit findings |
| `tap_points.md` | Optional instrumentation plan (B4) |
| `summary.md` | This document |

---

## Recommended Remediation (Phase C Preview)

### Code Change

**File:** `src/nanobrag_torch/models/detector.py`

**Diff:**
```diff
--- a/src/nanobrag_torch/models/detector.py
+++ b/src/nanobrag_torch/models/detector.py
@@ -759,9 +759,9 @@ class Detector:
         ):
             # Check if basis vectors have changed
             # Move cached vectors to current device for comparison
-            cached_f = self._cached_basis_vectors[0].to(self.device)
-            cached_s = self._cached_basis_vectors[1].to(self.device)
-            cached_o = self._cached_basis_vectors[2].to(self.device)
+            cached_f = self._cached_basis_vectors[0].to(device=self.device, dtype=self.dtype)
+            cached_s = self._cached_basis_vectors[1].to(device=self.device, dtype=self.dtype)
+            cached_o = self._cached_basis_vectors[2].to(device=self.device, dtype=self.dtype)

             if not (
                 torch.allclose(self.fdet_vec, cached_f, atol=1e-15)
@@ -774,7 +774,7 @@ class Detector:
             ):
                 geometry_changed = True
             # Check if pix0_vector has changed
-            cached_pix0 = self._cached_pix0_vector.to(self.device)
+            cached_pix0 = self._cached_pix0_vector.to(device=self.device, dtype=self.dtype)
             if not torch.allclose(
                 self.pix0_vector, cached_pix0, atol=1e-15
             ):
```

**Rationale:** Ensure cache retrieval coerces to current `self.dtype` to match live geometry tensors.

### Validation Strategy

**Primary validation:** Re-run determinism tests that currently crash with dtype mismatch.

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py --maxfail=0
```

**Expected outcome (post-fix):**
- No `RuntimeError: Float did not match Double`
- Tests may still fail for **seed-related reasons** (that's expected and a separate issue)
- Goal: Reach seed-dependent code paths, not crash in geometry setup

**Secondary validation:** Verify no regressions in existing passing tests.

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_geometry.py
```

**Expected:** All tests pass (no change in behavior for default float32 usage).

### Documentation Updates

1. **`docs/architecture/detector.md`** lines 73-88 (cache section)
   - Add note: "Cache comparisons in `get_pixel_coords` coerce cached tensors to current `self.dtype` before `torch.allclose` to support dynamic dtype switching."

2. **`docs/development/pytorch_runtime_checklist.md`** §2
   - Add example: "When caching tensors, retrieve with `.to(device=self.device, dtype=self.dtype)` to maintain dtype neutrality."

---

## Dependencies & Blockers

### Unblocks

- `[DETERMINISM-001]` Phase A rerun — determinism tests currently blocked by this dtype issue; fix allows them to proceed and reveal actual seed-related failures (if any)

### No blockers

Phase C (Remediation Blueprint) can proceed immediately. No external dependencies.

---

## Next Actions

**For supervisor (galph):**
1. Review Phase B artifacts and approve Phase C entry
2. Update `input.md` to delegate Phase C tasks to ralph

**For engineer (ralph):**
1. Await Phase C authorization from supervisor
2. Author `remediation_plan.md` per Phase C tasks (C1-C4) in `plans/active/dtype-neutral.md`
3. Implement 4-line fix in Phase D
4. Run validation suite and capture artifacts in Phase E

---

## Confidence Assessment

**Fix complexity:** Trivial (4-line diff)
**Risk:** Minimal (isolated to cache retrieval, no API changes)
**Test coverage:** Excellent (existing failures serve as perfect regression tests)
**Estimated effort:** 1 ralph loop (implementation + validation)

**Recommendation:** Proceed to Phase C immediately.
