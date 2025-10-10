# Dtype Neutrality Documentation Updates

**Initiative:** `[DTYPE-NEUTRAL-001]`
**Phase:** C (Documentation Planning)
**Date:** 2025-10-10T174636Z

---

## Overview

This document specifies all documentation updates required to accompany the dtype neutrality fix in `Detector.get_pixel_coords()`. Updates must be applied in Phase E (Validation & Documentation Closeout) after successful code validation.

---

## Required Updates

### 1. Detector Architecture Documentation

**File:** `docs/architecture/detector.md`

**Section:** §7 Performance Optimizations → §7.2 Cache Invalidation

**Current Content (lines 83-88):**

```markdown
### 7.2 Cache Invalidation
The cache is invalidated when:
- Basis vectors change (detected via tensor comparison)
- `pix0_vector` changes
- Device or dtype changes
```

**Proposed Update:**

Add new subsection after line 88:

```markdown
### 7.3 Dtype Neutrality

**Critical Implementation Detail:** Cache retrieval in `get_pixel_coords()` must coerce cached tensors to the current `self.dtype` before comparison to support dynamic dtype switching.

**Mechanism:**
```python
# CORRECT: Coerce device AND dtype
cached_f = self._cached_basis_vectors[0].to(device=self.device, dtype=self.dtype)

# INCORRECT: Only device coercion (causes dtype mismatch crashes)
cached_f = self._cached_basis_vectors[0].to(self.device)  # ❌ Missing dtype
```

**Rationale:**
When `detector.to(dtype=torch.float64)` is called, live geometry tensors (`self.fdet_vec`, etc.) are converted to float64, but cached tensors remain in their original dtype. The `torch.allclose` comparison between float32 cached tensors and float64 live tensors raises `RuntimeError: Float did not match Double`. Coercing cached tensors to `self.dtype` during retrieval ensures type consistency.

**Testing:**
- Validated by `tests/test_at_parallel_013.py` (deterministic mode, float64 precision)
- Validated by `tests/test_at_parallel_024.py` (mosaic rotation with dtype switching)

**Performance Impact:** Negligible — coercion only occurs during cache validation (not on cache hits).
```

**Justification:**
- Captures the subtle dtype handling requirement for future maintainers
- Links to concrete test cases for validation
- Explains both the "what" and the "why"

---

### 2. PyTorch Runtime Checklist

**File:** `docs/development/pytorch_runtime_checklist.md`

**Section:** §2 Device & Dtype Neutrality

**Current Content (lines 12-16):**

```markdown
2. **Device & Dtype Neutrality**
   - **Default dtype is float32** for performance and memory efficiency. Precision-critical operations (gradient checks, metric duality) explicitly override to float64 where required.
   - Materialize configuration tensors (beam, detector, crystal) on the execution device before the main loop.
   - Avoid per-iteration `.to()`, `.cpu()`, `.cuda()`, or tensor factories (`torch.tensor(...)`) inside compiled regions; cache constants once.
   - Run CPU **and** CUDA smoke commands (`pytest -v -m gpu_smoke`) when a GPU is available.
```

**Proposed Update:**

Add new bullet point after line 16:

```markdown
   - **Cache dtype neutrality:** When retrieving cached tensors for comparison, use `.to(device=..., dtype=...)` to match both device AND dtype of live tensors. Example from `Detector.get_pixel_coords()`:
     ```python
     # Retrieve cached basis vector with dtype coercion
     cached_f = self._cached_basis_vectors[0].to(device=self.device, dtype=self.dtype)
     # Now safe to compare with live geometry tensor
     torch.allclose(self.fdet_vec, cached_f, atol=1e-15)  # ✅ Both same dtype
     ```
     Omitting `dtype=` causes `RuntimeError` when dtype switches occur (e.g., `detector.to(dtype=torch.float64)`).
```

**Justification:**
- Provides actionable guidance with concrete code example
- Positioned in the most relevant checklist section (Device & Dtype Neutrality)
- Warns about common mistake (omitting `dtype=`)

---

### 3. Testing Strategy Documentation

**File:** `docs/development/testing_strategy.md`

**Section:** §1.4 PyTorch Device & Dtype Discipline

**Current Content (lines 18-27):**

```markdown
### 1.4 PyTorch Device & Dtype Discipline

- **Device-neutral code:** Every PyTorch path MUST operate correctly on both CPU and CUDA tensors and across supported dtypes. Do not hard-code `.cpu()`/`.cuda()` calls, create CPU-only constants, or assume float64 execution when the caller may supply float32/half tensors.
- **Authoritative smoke runs:** When a change touches tensor math, run the authoritative reproduction command once on CPU and once on CUDA (when available). Capture both logs/metrics and attach them to the fix plan. Treat any `torch.compile` or Dynamo warning about mixed devices as blocking.
- **Targeted tests:** Prefer parametrised tests that iterate over `device in {"cpu", "cuda"}` (guarded by `torch.cuda.is_available()`). At minimum, ensure a `gpu_smoke` marker or equivalent pytest node exercises the new logic on CUDA before declaring success.
- **Helper utilities:** Encapsulate device/dtype harmonisation in small helpers (e.g., `tensor.to(other_tensor)` or `type_as`). Centralise these helpers in reusable modules to keep the rule enforceable across future PyTorch projects.
- **CI gate:** If CI offers GPU runners, add a fast smoke job that runs the `gpu_smoke` marker (or agreed command) so regressions like CPU↔GPU tensor mixing fail quickly.
- **Vectorization check:** Confirm `_compute_physics_for_position` and related helpers remain batched across sources/phi/mosaic/oversample; extend broadcast dimensions instead of adding Python loops.
- **Runtime checklist:** Consult `docs/development/pytorch_runtime_checklist.md` during development and cite it in fix-plan notes for PyTorch changes.
```

**Proposed Update:**

Add new bullet point after "Helper utilities" (after line 24):

```markdown
- **Cache dtype consistency:** When implementing cached computations, ensure cache retrieval coerces to current `dtype` to support dynamic dtype switching. Use `.to(device=self.device, dtype=self.dtype)` instead of `.to(self.device)` alone. See `Detector.get_pixel_coords()` (lines 762-777) for reference implementation.
```

**Justification:**
- Reinforces dtype discipline at the strategic testing level
- Cross-references concrete implementation for developers
- Positioned alongside related device/dtype guidance

---

### 4. Fix Plan Update

**File:** `docs/fix_plan.md`

**Section:** `[DTYPE-NEUTRAL-001]` entry → Attempts History

**Add Attempt #3 Entry:**

```markdown
**Attempt #3 (Phase C: Remediation Blueprint) — 2025-10-10T174636Z**
- **Outcome:** ✅ Phase C complete — Blueprint artifacts authored
- **Artifacts:**
  - `reports/2026-01-test-suite-triage/phase_d/20251010T174636Z/dtype-neutral/phase_c/remediation_plan.md`
  - `reports/2026-01-test-suite-triage/phase_d/20251010T174636Z/dtype-neutral/phase_c/tests.md`
  - `reports/2026-01-test-suite-triage/phase_d/20251010T174636Z/dtype-neutral/phase_c/docs_updates.md`
- **Deliverables:**
  - 4-line fix specification with diff
  - Comprehensive validation strategy (primary/secondary/tertiary)
  - Documentation update plan (3 files, 4 touchpoints)
  - Risk assessment and rollback guidance
- **Next:** Phase D implementation execution delegated to ralph
- **Unblocks:** `[DETERMINISM-001]` once dtype neutrality validated
```

**Justification:**
- Maintains continuity in the Attempts History chain (follows Attempts #1-#2)
- Documents Phase C completion for supervisor review
- Clearly signals transition to Phase D (implementation)

---

## Documentation Update Sequence

**Recommended Order (Phase E):**

1. **Apply code fix** (4-line change in `detector.py`)
2. **Run validation suite** (primary, secondary, tertiary per `tests.md`)
3. **Update documentation files** in this order:
   - `docs/architecture/detector.md` (§7.3 addition)
   - `docs/development/pytorch_runtime_checklist.md` (§2 bullet addition)
   - `docs/development/testing_strategy.md` (§1.4 bullet addition)
   - `docs/fix_plan.md` (Attempt #3 entry)
4. **Commit all changes atomically:**
   ```bash
   git add \
     src/nanobrag_torch/models/detector.py \
     docs/architecture/detector.md \
     docs/development/pytorch_runtime_checklist.md \
     docs/development/testing_strategy.md \
     docs/fix_plan.md \
     reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/
   git commit -m "[DTYPE-NEUTRAL-001] Phase D+E: Fix cache dtype neutrality, validate, update docs"
   git push
   ```

---

## Cross-Reference Integrity

### Files That Reference Detector Caching

**Checked for consistency (no updates required):**

- `arch.md` §2a ADR-04 (Pixel Coordinate Caching) — High-level ADR, no implementation details
- `specs/spec-a-core.md` — No detector cache specifications (out of scope)
- `CLAUDE.md` Core Implementation Rules §16 (Device & Dtype Neutrality) — Already points to checklist
- `docs/index.md` — Navigation index, no content changes

**Updated (this plan):**

- `docs/architecture/detector.md` §7.3 (new subsection)
- `docs/development/pytorch_runtime_checklist.md` §2 (new bullet)
- `docs/development/testing_strategy.md` §1.4 (new bullet)
- `docs/fix_plan.md` Attempt #3 (new entry)

---

## Validation Checklist for Doc Updates

**Before committing documentation:**

- [ ] All file paths verified (files exist)
- [ ] Line number references accurate (checked against current versions)
- [ ] Code examples tested (copy-paste from actual implementation)
- [ ] Cross-references working (no broken links)
- [ ] Markdown formatting valid (linters pass)
- [ ] No typos or grammatical errors
- [ ] Consistent terminology across all docs
- [ ] Phase E validation report cites updated docs

---

## Future Enhancements (Out of Scope for This Fix)

**Potential follow-up improvements:**

1. **Explicit dtype tracking in cache keys:**
   - Store dtype alongside cached tensors
   - Invalidate cache when dtype changes
   - Avoid coercion overhead on every validation

2. **Separate caches per dtype:**
   - Maintain float32 and float64 caches independently
   - Switch between them on `to()` calls
   - Trade memory for performance

3. **Cache statistics logging:**
   - Track cache hit/miss rates
   - Monitor dtype conversion frequency
   - Identify optimization opportunities

**Note:** These are not required for current fix — document them in `docs/architecture/detector.md` §12 Future Enhancements if needed.

---

## References

**Evidence Chain:**

- Phase A: `reports/2026-01-test-suite-triage/phase_d/20251010T172810Z/dtype-neutral/phase_a/summary.md`
- Phase B: `reports/2026-01-test-suite-triage/phase_d/20251010T173558Z/dtype-neutral/phase_b/summary.md`
- Phase C: This document + `remediation_plan.md` + `tests.md`

**Authoritative Sources:**

- Detector spec: `docs/architecture/detector.md`
- Runtime checklist: `docs/development/pytorch_runtime_checklist.md`
- Testing strategy: `docs/development/testing_strategy.md`
- ADR: `arch.md` §2a ADR-04

**Test Coverage:**

- `tests/test_at_parallel_013.py` (deterministic mode)
- `tests/test_at_parallel_024.py` (mosaic rotation)
- `tests/test_detector_geometry.py` (regression check)

---

**End of Documentation Update Plan**
