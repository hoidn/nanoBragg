# Dtype Neutrality Remediation Plan

**Initiative:** `[DTYPE-NEUTRAL-001]`
**Phase:** C (Remediation Blueprint)
**Date:** 2025-10-10T174636Z
**Owner:** ralph (implementation executor)
**Reviewer:** galph (supervisor)

---

## Executive Summary

**Problem:** `Detector.get_pixel_coords()` crashes with `RuntimeError: Float did not match Double` when detector dtype is switched after cache creation, blocking determinism test execution.

**Root Cause:** Cache retrieval coerces device but not dtype, causing `torch.allclose` comparisons between float32 cached tensors and float64 live geometry tensors.

**Fix:** Add `dtype=self.dtype` parameter to 4 cache retrieval `.to()` calls in `detector.py`.

**Risk:** Minimal — surgical change isolated to cache handling, no API modifications.

**Effort:** 1 ralph loop (4-line code change + validation).

---

## Scope & Affected Components

### In Scope

**Component:** `Detector` (geometry caching subsystem)
**File:** `src/nanobrag_torch/models/detector.py`
**Lines:** 762-764, 777
**Change Type:** Bug fix (missing dtype coercion in cache retrieval)

### Out of Scope

- Simulator caching (already dtype-safe, line 569)
- Crystal component (no caching)
- Beam component (no caching)
- Tensor factory functions (already dtype-aware)

### Blast Radius

**Minimal:**
- Only affects detector geometry cache validation logic
- No public API changes
- No behavioral changes for default float32 usage
- Pure internal consistency fix

---

## Technical Details

### Current Behavior (Buggy)

**Failure Path:**
1. Detector initialized with `dtype=torch.float32` (default)
2. First `get_pixel_coords()` call creates caches (float32):
   - `_cached_basis_vectors = [fdet, sdet, odet]` (all float32)
   - `_cached_pix0_vector = pix0` (float32)
3. Test calls `detector.to(dtype=torch.float64)`
4. `to()` updates `self.dtype` and all live geometry tensors to float64
5. **BUT:** Cache variables remain float32 (not touched by `to()`)
6. Next `get_pixel_coords()` call retrieves caches:
   ```python
   cached_f = self._cached_basis_vectors[0].to(self.device)  # Still float32!
   ```
7. Comparison fails:
   ```python
   torch.allclose(self.fdet_vec, cached_f, atol=1e-15)  # float64 vs float32 → RuntimeError
   ```

### Fixed Behavior

**After 4-line change:**
1. Cache retrieval coerces both device AND dtype:
   ```python
   cached_f = self._cached_basis_vectors[0].to(device=self.device, dtype=self.dtype)
   ```
2. Comparison succeeds: both tensors are float64
3. Cache detected as stale (values may differ after dtype conversion)
4. Cache regenerated with current dtype
5. Subsequent calls use consistent dtype throughout

---

## Implementation Diff

**File:** `src/nanobrag_torch/models/detector.py`

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

**Lines Changed:** 4
**Characters Changed:** ~80 (adding `dtype=self.dtype` 4 times)

---

## Validation Strategy

### Primary Validation

**Objective:** Verify dtype mismatch crashes are eliminated.

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py --maxfail=0 --durations=10
```

**Expected Outcome (Post-Fix):**
- ✅ No `RuntimeError: Float did not match Double` crashes
- ⚠️ Tests may still fail due to **seed-related issues** (separate problem)
- ✅ Goal: Reach deterministic mode code paths without crashing in geometry setup
- ✅ Validates dtype coercion works for both tests

**Failure Modes to Watch:**
- If tests still crash with dtype errors → fix incomplete (missed a cache path)
- If tests pass unexpectedly → seed issues may have been coincidentally resolved
- If tests fail with different errors → expected, document new failure signatures

### Secondary Validation (Regression Check)

**Objective:** Ensure no behavioral changes for default float32 usage.

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_geometry.py
```

**Expected Outcome:**
- ✅ All tests pass (same as before fix)
- ✅ No performance degradation
- ✅ No new warnings or errors

### Tertiary Validation (Device Coverage)

**Objective:** Verify fix works on both CPU and CUDA (if available).

**Commands:**
```bash
# CPU validation (always run)
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py -k "cpu"

# CUDA validation (if torch.cuda.is_available())
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py -k "gpu" || echo "CUDA not available, skipping GPU smoke test"
```

**Expected Outcome:**
- ✅ Both device paths handle dtype coercion correctly
- ✅ No mixed-device tensor errors

---

## Risk Assessment

### Low Risk Factors

1. **Surgical change:** Only 4 lines modified, no architectural changes
2. **Well-tested path:** Cache logic already heavily exercised by existing tests
3. **Type-safe operation:** `.to()` is PyTorch's blessed method for dtype conversion
4. **Backward compatible:** No API changes, fully transparent to callers

### Potential Issues

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Performance regression from extra dtype conversions | Low | Low | Cache hits avoid conversion; measure with benchmarks |
| Edge case with non-contiguous tensors | Very Low | Medium | `.to()` handles this automatically |
| Undetected cache staleness | Very Low | High | Existing `torch.allclose` logic unchanged, just dtype-aware now |

### Rollback Plan

**If fix causes regressions:**

1. **Immediate:** Revert 4-line change via git:
   ```bash
   git revert <commit-hash>
   git push
   ```

2. **Document:** Add entry to `docs/fix_plan.md` noting rollback and failure mode

3. **Alternative approach:** If revert needed, investigate:
   - Explicit dtype tracking in cache keys
   - Separate caches per dtype
   - Cache invalidation on `to()` call

**Recovery time:** <5 minutes (single commit revert)

---

## Success Criteria

### Must Have (Gate for Phase D → E)

- ✅ AT-PARALLEL-013 and AT-PARALLEL-024 no longer crash with dtype errors
- ✅ Existing detector geometry tests continue passing
- ✅ No new warnings or errors introduced

### Should Have

- ✅ CPU + CUDA smoke tests pass (when CUDA available)
- ✅ Performance within 5% of baseline (measure with `test_detector_geometry.py`)

### Nice to Have

- ✅ Determinism tests reveal actual seed-related failures (if any exist)
- ✅ Documentation updates merged alongside code fix

---

## Dependencies & Sequencing

### Unblocks

- `[DETERMINISM-001]` Phase A rerun — currently blocked by dtype crashes; fix allows investigation of actual seed behavior

### No External Dependencies

- Pure internal fix
- No upstream changes required
- No new library dependencies

### Implementation Sequence

1. **Phase D (This fix):** Apply 4-line change
2. **Phase E (Validation):** Run full test suite + capture artifacts
3. **Unblock:** `[DETERMINISM-001]` can proceed once dtype neutrality confirmed

---

## Artifact References

**Evidence Chain:**

- **Phase A:** `reports/2026-01-test-suite-triage/phase_d/20251010T172810Z/dtype-neutral/phase_a/summary.md`
  - Reproduction logs, minimal repro script, stack traces

- **Phase B:** `reports/2026-01-test-suite-triage/phase_d/20251010T173558Z/dtype-neutral/phase_b/summary.md`
  - Static audit, precise fix location, scope analysis

- **Phase C (this doc):** `reports/2026-01-test-suite-triage/phase_d/20251010T174636Z/dtype-neutral/phase_c/remediation_plan.md`
  - Blueprint for implementation

- **Phase D artifacts (pending):** `reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_d/`
  - Implementation commit hash, test logs

- **Phase E artifacts (pending):** `reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_e/`
  - Validation report, metrics, doc updates

---

## Reviewer Sign-Off

**Supervisor Review Required Before Phase D:**

- [ ] Diff reviewed and approved
- [ ] Validation strategy adequate
- [ ] Risk assessment acceptable
- [ ] Rollback plan understood
- [ ] Documentation updates planned (see `docs_updates.md`)

**Approved by:** _______________ (galph)
**Date:** _______________

---

## Implementation Notes

**For ralph (engineer):**

1. Read this plan end-to-end before coding
2. Apply diff exactly as shown (no variations)
3. Run validation commands in order (primary → secondary → tertiary)
4. Capture all logs under `phase_d/<STAMP>/`
5. Update `docs/fix_plan.md` with Attempt #3 entry citing this plan
6. If any validation fails, STOP and document failure mode before proceeding

**Do not:**
- Modify any other detector code
- Change cache invalidation logic
- Add performance optimizations in same commit
- Skip validation steps

---

**End of Remediation Plan**
