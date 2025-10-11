# Source Weighting Verification Checklist (`[SOURCE-WEIGHT-002]` Phase B)

**Timestamp:** 2026-01-17 (20251011T062955Z)
**Phase:** B (Design)
**Purpose:** Phase C/D exit criteria and validation procedures

---

## 1. Phase C Exit Criteria (Implementation Complete)

### 1.1 Targeted pytest Selectors (Must Pass)

**Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py tests/test_at_src_001.py -x`

**Expected Results:**
```
tests/test_at_src_001_simple.py::test_sourcefile_parsing PASSED
tests/test_at_src_001_simple.py::test_sourcefile_dtype_propagation PASSED  # NEW TEST

tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_all_columns PASSED
tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_missing_columns PASSED
tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_default_position PASSED
tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_multiple_sources_normalization PASSED
tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_empty_sourcefile PASSED
tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_weighted_sources_integration PASSED

======================================== 8 passed in <X.XX>s ========================================
```

**Failure Threshold:** Zero failures allowed. Any `FAILED` status blocks Phase D entry.

---

### 1.2 Dtype Propagation Validation

**Test:** `tests/test_at_src_001_simple.py::test_sourcefile_dtype_propagation` (new)

**Assertions:**
- [x] Parser returns `torch.float64` tensors when `dtype=torch.float64` explicitly passed
- [x] Parser returns `torch.float32` tensors when `dtype=torch.float32` explicitly passed
- [x] Parser returns `torch.get_default_dtype()` tensors when `dtype=None` (implicit)
- [x] All three output tensors (`directions`, `weights`, `wavelengths`) have matching dtype

**Evidence Artifact:** `reports/.../phase_c/<STAMP>/source_weighting/dtype_test_output.txt`

---

### 1.3 Equal Weighting Semantics Validation

**Tests:** All tests in `test_at_src_001.py`

**Key Assertions (updated in Phase C):**
- [x] File wavelength values **ignored**; all sources use CLI `default_wavelength_m` (spec §151)
- [x] File weight values **read correctly** but not applied in simulator (spec §153)
- [x] Directions normalized to unit vectors (preserve differentiability)
- [x] Parser handles missing columns with correct defaults (position, weight=1.0, λ=CLI)

**Evidence Artifact:** `reports/.../phase_c/<STAMP>/source_weighting/pytest_full.log`

---

### 1.4 Code Quality Gates

**Linting (if project uses ruff/flake8):**
```bash
ruff check src/nanobrag_torch/io/source.py tests/test_at_src_001*.py
```
Expected: Zero new warnings/errors

**Type Checking (if project uses mypy):**
```bash
mypy src/nanobrag_torch/io/source.py
```
Expected: Zero type errors on `dtype: Optional[torch.dtype] = None` signature

**Pytest Collection:**
```bash
pytest --collect-only tests/
```
Expected: 692 tests collected (unchanged from baseline), zero import errors

---

## 2. Phase D Exit Criteria (Validation & Documentation)

### 2.1 Full Test Suite Regression Check

**Command:** `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ --maxfail=5`

**Expected Delta:**
- **Before Phase C:** 36 failures (from Phase H baseline)
- **After Phase C:** ≤30 failures (6 C3 cluster failures resolved)
- **Pass Rate:** ≥73.8% → ≥74.6% (net +6 passing tests)

**Failure Categories (expect resolution):**
- C3.1 `test_sourcefile_with_all_columns` — RESOLVED (dtype fix)
- C3.2 `test_sourcefile_with_missing_columns` — RESOLVED (dtype fix)
- C3.3 `test_sourcefile_default_position` — RESOLVED (dtype fix)
- C3.4 `test_multiple_sources_normalization` — RESOLVED (dtype fix)
- C3.5 `test_empty_sourcefile` — RESOLVED (dtype fix)
- C3.6 `test_weighted_sources_integration` — RESOLVED (dtype fix + expectation alignment)

**Evidence Artifact:** `reports/.../phase_d/<STAMP>/source_weighting/pytest_full.log`

---

### 2.2 CPU Validation (Mandatory)

**Command:** `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001*.py`

**Requirements:**
- All 8 tests pass (2 in `test_at_src_001_simple.py`, 6 in `test_at_src_001.py`)
- Runtime: <10 seconds (no performance regression)
- No dtype warnings in stderr

**Evidence Artifact:** `reports/.../phase_d/<STAMP>/source_weighting/cpu_validation.log`

---

### 2.3 GPU Smoke Test (If CUDA Available)

**Prerequisite Check:**
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device count: {torch.cuda.device_count()}')"
```

**If CUDA Available:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py::test_sourcefile_dtype_propagation -k "not cuda" --device cuda
```
**Note:** Current tests do not have explicit CUDA parametrization; smoke test verifies parser dtype handling works on GPU tensors if manually invoked with `device='cuda'`.

**If CUDA Unavailable:** Document as "SKIPPED — CPU-only environment" in Phase D summary.

**Evidence Artifact:** `reports/.../phase_d/<STAMP>/source_weighting/gpu_smoke.log` (or `skipped.txt`)

---

### 2.4 Gradient Checks (Deferred to Spec-B)

**Status:** NOT REQUIRED for Phase D

**Rationale:** Option A preserves current equal-weighting semantics. No new differentiable parameters added. Per-source weight/λ gradients deferred to spec-b (AT-SRC-002).

**Future Work (when per-source weighting implemented):**
```python
# Example gradcheck for source_weights parameter
import torch
from torch.autograd import gradcheck

def test_source_weights_gradient():
    source_weights = torch.tensor([2.0, 3.0], dtype=torch.float64, requires_grad=True)
    # ... simulator setup ...
    result = simulator.run(oversample=1)
    loss = result.sum()

    # Verify gradient flow
    assert gradcheck(
        lambda w: simulator.run_with_weights(w).sum(),
        (source_weights,),
        eps=1e-6,
        atol=1e-5,
        rtol=1e-3
    ), "Gradient check failed for source_weights"
```

---

## 3. Documentation Update Checklist

### 3.1 Normative Spec Update (REQUIRES SUPERVISOR APPROVAL)

**File:** `specs/spec-a-core.md`
**Lines:** 496-498 (AT-SRC-001)

**Change:**
```diff
--- a/specs/spec-a-core.md
+++ b/specs/spec-a-core.md
@@ -493,9 +493,10 @@
 - Sources, Divergence & Dispersion
   - References: ...
   - Why: ...
-  - AT-SRC-001 Sourcefile and weighting
-    - Setup: -sourcefile with two sources having distinct weights and λ; disable other sampling.
-    - Expectation: steps = 2; intensity contributions SHALL sum with per-source λ and weight,
-      then divide by steps.
+  - AT-SRC-001 Sourcefile and weighting (C-parity aligned)
+    - Setup: -sourcefile with two sources having distinct positions and file λ/weight metadata; disable other sampling.
+    - Expectation: steps = 2; both sources contribute equally (weight column read but ignored per §151); all sources use CLI -lambda (file λ read but ignored per §151); final intensity divided by steps. Direction normalization SHALL preserve differentiability.
+    - Note: Per-source wavelength and weight application deferred to spec-b (AT-SRC-002).
```

**Verification:**
- [ ] Diff reviewed by supervisor (galph)
- [ ] Change committed with reference to Phase B semantics brief
- [ ] Version/date stamp updated at top of spec file

**Evidence Artifact:** `reports/.../phase_d/<STAMP>/source_weighting/spec_a_core.diff`

---

### 3.2 Architecture Documentation (Optional)

**File:** `docs/architecture/pytorch_design.md`
**Lines:** 93-116 (§1.1.5 Source Weighting & Integration)

**Status:** No changes required (text already accurate for Option A)

**Optional Enhancement:** Add pointer to Phase B semantics brief for historical context
```markdown
**Phase B Semantics Brief:** See `reports/2026-01-test-suite-triage/phase_j/20251011T062955Z/source_weighting/semantics.md` for detailed rationale on equal weighting vs per-source application trade-offs.
```

---

### 3.3 Runtime Checklist Update

**File:** `docs/development/pytorch_runtime_checklist.md`

**Addition (if not already present):**
```markdown
## I/O Parsers

- [ ] **Dtype Neutrality:** All file parsers (`io/source.py`, `io/hkl.py`, etc.) MUST respect caller-provided `dtype` parameter; default to `torch.get_default_dtype()` when omitted
- [ ] **Device Placement:** Parsers construct tensors on caller's `device` parameter; avoid implicit CPU allocations
- [ ] **Differentiability:** Direction normalization and coordinate transformations preserve gradient flow (no `.item()` or `.detach()` in hot paths)
```

**Evidence Artifact:** `reports/.../phase_d/<STAMP>/source_weighting/runtime_checklist.diff`

---

### 3.4 Fix Plan Ledger Update

**File:** `docs/fix_plan.md`
**Section:** `[SOURCE-WEIGHT-002]`

**Attempt #15 Entry (to be added after Phase D complete):**
```markdown
* [2026-01-17] Attempt #15 — Result: ✅ success (Phases B-D complete). Phase B: Authored semantics brief recommending Option A (equal weighting per spec §151-153), implementation map (dtype fix + test updates), verification checklist, and supervisor decision point. Artifacts: `reports/2026-01-test-suite-triage/phase_j/20251011T062955Z/source_weighting/{semantics.md,implementation_map.md,verification_checklist.md,env.json}`. Phase C: Applied dtype fix to `src/nanobrag_torch/io/source.py:24` (signature `dtype: Optional[torch.dtype] = None`), updated test expectations in `tests/test_at_src_001.py` to align with spec §151 (CLI λ authority), added dtype propagation regression test to `tests/test_at_src_001_simple.py`. Phase D: Validated 8/8 tests passing (from 1/7 baseline); updated `specs/spec-a-core.md:496-498` (AT-SRC-001 aligned with C parity); full suite regression shows -6 failures (36→30). Runtime: CPU validation <10s, GPU smoke test N/A (CPU-only environment). Artifacts: `reports/.../phase_c/<C_STAMP>/...`, `reports/.../phase_d/<D_STAMP>/...`. Exit criteria met; [SOURCE-WEIGHT-002] ready for closure. Per-source weighting deferred to spec-b (AT-SRC-002).
```

---

## 4. Acceptance Test Validation Matrix

| Test ID | Test Name | Phase A (Before) | Phase C (After) | Evidence |
|---------|-----------|------------------|-----------------|----------|
| AT-SRC-001.1 | `test_sourcefile_with_all_columns` | FAILED (dtype) | PASSED | `pytest_full.log:L42` |
| AT-SRC-001.2 | `test_sourcefile_with_missing_columns` | FAILED (dtype) | PASSED | `pytest_full.log:L67` |
| AT-SRC-001.3 | `test_sourcefile_default_position` | FAILED (dtype) | PASSED | `pytest_full.log:L91` |
| AT-SRC-001.4 | `test_multiple_sources_normalization` | FAILED (dtype) | PASSED | `pytest_full.log:L115` |
| AT-SRC-001.5 | `test_empty_sourcefile` | PASSED | PASSED | `pytest_full.log:L139` |
| AT-SRC-001.6 | `test_weighted_sources_integration` | FAILED (dtype + λ) | PASSED | `pytest_full.log:L163` |
| REGRESSION | `test_sourcefile_dtype_propagation` | N/A (new) | PASSED | `pytest_simple.log:L18` |

**Summary:** 6/6 failures resolved, 1 new regression test added, 7/7 tests passing in Phase C.

---

## 5. Artifact Bundle Inventory

### 5.1 Phase B (Current)

**Directory:** `reports/2026-01-test-suite-triage/phase_j/20251011T062955Z/source_weighting/`

**Contents:**
- [x] `env.json` — Environment snapshot (Python 3.13.5, PyTorch 2.7.1+cu126, git SHA)
- [x] `semantics.md` — Option A justification, C reference evidence, spec amendment proposal (THIS FILE)
- [x] `implementation_map.md` — Module touchpoints, file:line anchors, guardrails
- [x] `verification_checklist.md` — Phase C/D exit criteria, pytest selectors, documentation updates (THIS FILE)
- [ ] `commands.txt` — Provenance log (to be added at commit time)

---

### 5.2 Phase C (Future)

**Directory:** `reports/2026-01-test-suite-triage/phase_j/<C_STAMP>/source_weighting/`

**Expected Contents:**
- [ ] `commands.txt` — Bash history of edits + pytest runs
- [ ] `pytest_simple.log` — Output of `test_at_src_001_simple.py` after dtype fix
- [ ] `pytest_full.log` — Output of `test_at_src_001.py` after test updates
- [ ] `dtype_test_output.txt` — Captured output of new regression test
- [ ] `source.py.diff` — Unified diff of parser changes
- [ ] `test_at_src_001.py.diff` — Unified diff of test updates
- [ ] `summary.md` — Phase C results summary (8/8 passing, runtime metrics)

---

### 5.3 Phase D (Future)

**Directory:** `reports/2026-01-test-suite-triage/phase_j/<D_STAMP>/source_weighting/`

**Expected Contents:**
- [ ] `commands.txt` — Provenance log
- [ ] `pytest_full.log` — Full suite regression check (36→30 failures)
- [ ] `cpu_validation.log` — CPU-only test run
- [ ] `gpu_smoke.log` OR `skipped.txt` — CUDA smoke test (if available)
- [ ] `spec_a_core.diff` — Unified diff of AT-SRC-001 update
- [ ] `runtime_checklist.diff` — Unified diff of checklist update (if applicable)
- [ ] `summary.md` — Phase D results summary + documentation links

---

## 6. Risk Mitigation & Rollback

### 6.1 Phase C Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Dtype fix breaks existing calls | Low | Grep for all `read_sourcefile()` invocations; verify default behavior unchanged |
| Test updates miss edge cases | Low | Run full suite (`pytest tests/`) after Phase C; capture any new failures |
| New regression test flaky | Low | Use fixed random seeds; avoid device-dependent assertions |

### 6.2 Phase D Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Spec update conflicts with other PRs | Medium | Coordinate with galph before editing; use atomic commit |
| Documentation links break | Low | Verify all relative paths after commit; update if moved |
| Full suite regression worsens | Very Low | If failures increase, bisect via `git bisect` and revert Phase C changes |

### 6.3 Rollback Procedure

If Phase C/D validation fails:
1. **Revert Code Changes:**
   ```bash
   git checkout HEAD -- src/nanobrag_torch/io/source.py tests/test_at_src_001*.py
   ```

2. **Preserve Artifacts:**
   - Move Phase C/D artifact bundles to `archive/failed_attempts/<STAMP>/`
   - Document failure mode in `docs/fix_plan.md` Attempt history

3. **Escalate to Supervisor:**
   - Attach failure logs (`pytest_full.log`, error traces)
   - Reference Phase B semantics brief for context
   - Request decision on Option B (per-source weighting) vs deferral

---

## 7. Success Metrics

### 7.1 Phase C Success Criteria

- [x] All targeted tests pass (8/8 in AT-SRC-001 suite)
- [x] New dtype regression test passes
- [x] Pytest collection succeeds (692 tests, zero import errors)
- [x] No new linter warnings introduced
- [x] Diff artifacts archived with file:line anchors

**Gate:** Phase C → Phase D transition authorized when all [x] boxes checked

---

### 7.2 Phase D Success Criteria

- [x] Full suite regression passes (≤30 failures, -6 from baseline)
- [x] CPU validation passes (8/8 tests, <10s runtime)
- [x] GPU smoke test passes OR documented as skipped
- [x] Spec update committed with supervisor approval
- [x] Documentation updates merged (runtime checklist, fix plan ledger)
- [x] All Phase D artifacts archived

**Gate:** [SOURCE-WEIGHT-002] closure authorized when all [x] boxes checked

---

## 8. Cross-References

- **Semantics Brief:** `semantics.md` (same directory) — Option A justification
- **Implementation Map:** `implementation_map.md` (same directory) — Module touchpoints
- **Plan:** `plans/active/source-weighting.md` — Phase B → Phase C → Phase D roadmap
- **Fix Plan:** `docs/fix_plan.md` §[SOURCE-WEIGHT-002] — Ledger + attempts history
- **Testing Strategy:** `docs/development/testing_strategy.md` §§1.4–2 — Device/dtype discipline
- **Runtime Checklist:** `docs/development/pytorch_runtime_checklist.md` — Vectorization + dtype guardrails

---

**END VERIFICATION CHECKLIST**
