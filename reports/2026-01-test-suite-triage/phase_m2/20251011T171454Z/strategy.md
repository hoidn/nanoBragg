# Phase M2 Strategy: Gradient Compile Guard Implementation

**Date:** 2025-10-11
**Phase:** M2 — Gradient Infrastructure Gate (Cluster C2)
**Scope:** Resolve donated-buffer `torch.compile` constraint blocking `gradcheck` tests
**Priority:** P1 (critical path blocker for Sprint 1 completion)

---

## Problem Statement

**Cluster C2 (Gradient Compile Guard)** blocks 10 gradient tests due to a PyTorch `torch.compile` limitation with donated buffers in `torch.autograd.gradcheck`. The current symptom is:

```
RuntimeError: Cannot call gradcheck on donated buffer
```

This occurs when the Simulator uses `torch.compile` in the forward pass and `gradcheck` attempts to compute numerical gradients via backward passes.

**Spec Reference:** `arch.md` §15 (Differentiability Guidelines), `docs/development/testing_strategy.md` §1.4 (PyTorch Device & Dtype Discipline)

---

## Root Cause Analysis

### Technical Background

`torch.compile` (Dynamo/Inductor) optimizes tensor operations by fusing kernels and reusing buffers. When a tensor's storage is "donated" (reused in-place to save memory), PyTorch marks it as ineligible for gradient computation.

`torch.autograd.gradcheck` performs numerical gradient validation by:
1. Evaluating `f(x)` at the current point
2. Perturbing `x` by small epsilon values
3. Evaluating `f(x + ε)` and `f(x - ε)`
4. Computing numerical derivative: `(f(x+ε) - f(x-ε)) / (2ε)`
5. Comparing against autograd-computed gradients

**Conflict:** When the forward pass uses compiled code with donated buffers, step 3's re-evaluation attempts to access donated storage, triggering the RuntimeError.

### Current Implementation

**File:** `src/nanobrag_torch/simulator.py`

The Simulator optionally enables `torch.compile` via the `NANOBRAGG_DISABLE_COMPILE` environment variable (checked at module import):

```python
# simulator.py (approximate lines 1-15)
import os
import torch

DISABLE_COMPILE = os.environ.get('NANOBRAGG_DISABLE_COMPILE', '0') == '1'

class Simulator:
    def __init__(self, ...):
        # ...
        if not DISABLE_COMPILE:
            self.forward = torch.compile(self.forward)
```

**Issue:** The current guard exists but may not be correctly wired into test execution or the Simulator's `__init__` flow.

---

## Proposed Solution

### Option A: Environment Variable Guard (Recommended)

**Rationale:** Minimal code changes; aligns with existing `NANOBRAGG_DISABLE_COMPILE` pattern; allows per-test control without modifying production code.

**Implementation Steps:**

1. **Verify Current Guard Logic** (`simulator.py`)
   - Confirm `DISABLE_COMPILE` flag is read at module level
   - Ensure `torch.compile` is skipped when flag is set
   - Add explicit log/comment noting compile guard purpose

2. **Update Test Harness** (`tests/test_gradients.py`)
   - Set `os.environ['NANOBRAGG_DISABLE_COMPILE'] = '1'` at module top (before torch import)
   - Document rationale in module docstring
   - Example:
     ```python
     # tests/test_gradients.py (lines 1-10)
     import os
     os.environ['NANOBRAGG_DISABLE_COMPILE'] = '1'  # Required for gradcheck compatibility

     import torch
     import pytest
     from nanobrag_torch.simulator import Simulator
     # ...
     ```

3. **Validate Cross-Device** (`testing_strategy.md` §1.4)
   - Run gradcheck tests on CPU: `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck"`
   - If CUDA available, repeat with `CUDA_VISIBLE_DEVICES=0` to ensure guard works on GPU
   - Expected result: 10/10 gradcheck tests pass

4. **Documentation Updates**
   - `arch.md` §15: Add subsection "Gradient Testing with torch.compile"
   - `docs/development/testing_strategy.md` §1.4: Note compile guard requirement for gradient tests
   - `docs/development/pytorch_runtime_checklist.md`: Add item "Disable compile for gradcheck tests"

### Option B: Contextual Decorator (Alternative)

**Rationale:** More granular control; allows per-method compile disabling without global env var.

**Implementation:**
```python
# utils/compile_guards.py (new file)
import functools
import torch

def disable_compile(fn):
    """Decorator to skip torch.compile for gradient-sensitive functions."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with torch._dynamo.config.disable():
            return fn(*args, **kwargs)
    return wrapper

# tests/test_gradients.py
from utils.compile_guards import disable_compile

@disable_compile
def test_cell_parameter_gradients():
    simulator = Simulator(...)
    # gradcheck logic
```

**Trade-offs:**
- **Pros:** No environment variable management; explicit per-test control
- **Cons:** Requires new utility module; more invasive than Option A; less discoverable

**Recommendation:** Defer Option B unless Option A proves insufficient.

---

## Expected Pytest Selectors

### Primary Target (C2 Cluster)
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck"
```

**Expected Outcome:** 10 passed (all `gradcheck`-related tests)

### Secondary Validation (Full Gradient Suite)
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py
```

**Expected Outcome:** All gradient tests pass (including integration tests beyond `gradcheck`)

### Cross-Device Smoke (if CUDA available)
```bash
env CUDA_VISIBLE_DEVICES=0 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck"
```

**Expected Outcome:** Same 10 passed on GPU

---

## Documentation Touch Points

### 1. Architecture (`arch.md`)

**Section:** §15 Differentiability Guidelines

**Addition:**
```markdown
### Gradient Testing with torch.compile

**Constraint:** `torch.compile` uses donated buffers for memory optimization, which prevents `torch.autograd.gradcheck` from re-evaluating the forward pass during numerical gradient computation.

**Solution:** Disable compilation for gradient tests via `NANOBRAGG_DISABLE_COMPILE=1` environment variable. This guard is automatically applied in `tests/test_gradients.py` to ensure `gradcheck` compatibility.

**Usage:**
- **Production:** Compilation enabled by default for performance
- **Testing (gradients):** Compilation disabled via env flag
- **Testing (other):** Compilation enabled unless specifically problematic

**Reference:** `docs/development/testing_strategy.md` §1.4 (PyTorch Device & Dtype Discipline)
```

### 2. Testing Strategy (`docs/development/testing_strategy.md`)

**Section:** §1.4 PyTorch Device & Dtype Discipline

**Addition (new subsection):**
```markdown
#### Compile Guard for Gradient Tests

**Requirement:** Gradient validation tests using `torch.autograd.gradcheck` MUST disable `torch.compile` to avoid donated-buffer conflicts.

**Implementation:**
- Set `os.environ['NANOBRAGG_DISABLE_COMPILE'] = '1'` at top of `tests/test_gradients.py` (before torch import)
- Simulator checks this flag and skips `torch.compile(self.forward)` when set
- All other tests run with compilation enabled (default behavior)

**Validation Pattern:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck"
```

**Rationale:** `torch.compile` optimizes performance via buffer reuse, but donated buffers prevent `gradcheck`'s repeated forward-pass evaluations. Disabling compilation for gradient tests preserves differentiability validation without compromising production performance.
```

### 3. PyTorch Runtime Checklist (`docs/development/pytorch_runtime_checklist.md`)

**Addition (new item):**
```markdown
## Gradient Testing

- [ ] Gradient tests disable `torch.compile` via `NANOBRAGG_DISABLE_COMPILE=1`
- [ ] Test module sets environment variable before torch import
- [ ] Cross-device validation performed (CPU + CUDA if available)
- [ ] `gradcheck` tests pass with `dtype=torch.float64` precision
```

---

## Implementation Plan

### Phase M2a: Draft Guardrail Strategy ✅ COMPLETE
**Status:** This document fulfills Phase M2a deliverable

**Artifacts:**
- Strategy document: `reports/2026-01-test-suite-triage/phase_m2/20251011T171454Z/strategy.md` (this file)

---

### Phase M2b: Implement/Diff Guard

**Owner:** Ralph (or designated gradient specialist)

**Steps:**
1. Read `src/nanobrag_torch/simulator.py` lines 1-20 to verify current `DISABLE_COMPILE` logic
2. If guard is missing or incomplete, add:
   ```python
   # simulator.py (after imports, before Simulator class)
   DISABLE_COMPILE = os.environ.get('NANOBRAGG_DISABLE_COMPILE', '0') == '1'

   class Simulator:
       def __init__(self, ...):
           # ... existing init code ...
           if not DISABLE_COMPILE:
               self.forward = torch.compile(self.forward, mode='reduce-overhead')
   ```
3. Update `tests/test_gradients.py` module header:
   ```python
   import os
   os.environ['NANOBRAGG_DISABLE_COMPILE'] = '1'  # gradcheck requires uncompiled forward pass

   import torch
   # ... rest of imports
   ```
4. Run targeted selector:
   ```bash
   env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck" --tb=short
   ```
5. Capture before/after logs under `phase_m2/20251011T<STAMP>/gradient_guard/`

**Exit Criteria:**
- ✅ 10/10 `gradcheck` tests pass
- ✅ No "donated buffer" RuntimeError
- ✅ Logs confirm compilation skipped during gradcheck

---

### Phase M2c: Cross-Device Sanity (If CUDA Available)

**Conditional:** Only execute if `torch.cuda.is_available() == True`

**Command:**
```bash
env CUDA_VISIBLE_DEVICES=0 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck" --tb=short
```

**Expected Result:** 10/10 passed (same as CPU)

**Artifacts:** `phase_m2/20251011T<STAMP>/gradients_gpu/pytest.log`

---

### Phase M2d: Documentation + Ledger Sync

**Files to Update:**
1. `arch.md` §15 (add Gradient Testing subsection per template above)
2. `docs/development/testing_strategy.md` §1.4 (add Compile Guard subsection)
3. `docs/development/pytorch_runtime_checklist.md` (add Gradient Testing checklist item)
4. `docs/fix_plan.md` [TEST-SUITE-TRIAGE-001] Attempts (add Phase M2 attempt entry)
5. `remediation_tracker.md` Cluster C2 (mark ✅ RESOLVED with artifact paths)

**Summary Artifact:** `phase_m2/20251011T<STAMP>/summary.md`

**Contents:**
- Pass counts: Expected +10 (all `gradcheck` tests)
- Code changes: List files modified (simulator.py, test_gradients.py)
- Documentation updates: List sections modified in arch/testing_strategy/checklist
- Commands log: Reproduction commands for future verification
- Environment snapshot: Python/PyTorch/CUDA versions

---

## Success Metrics

### Quantitative
- **Failure Reduction:** 11 failures → 1 failure (C6 MOSFLM offset remains)
- **Pass Rate Improvement:** +10 passing tests in gradient suite
- **Sprint 1 Progress:** C2 closure advances Sprint 1 to 92% complete (33/36 failures resolved)

### Qualitative
- ✅ Gradient tests run without manual intervention
- ✅ Compile guard documented for future gradient test additions
- ✅ Cross-device validation confirms CPU/GPU parity
- ✅ Architecture documentation updated with compile constraint rationale

---

## Risks & Mitigations

### Risk 1: Performance Regression in Gradient Tests
**Likelihood:** Low
**Impact:** Negligible (gradient tests are validation-focused, not performance-critical)
**Mitigation:** Document that production code retains compilation; only tests disable it

### Risk 2: Incomplete Guard Coverage
**Likelihood:** Low
**Impact:** Medium (some gradcheck tests might still fail)
**Mitigation:** Validate full gradient suite (`pytest -v tests/test_gradients.py`), not just `gradcheck` subset

### Risk 3: CUDA-Specific Donated Buffer Behavior
**Likelihood:** Low
**Impact:** Medium (GPU gradcheck might still fail)
**Mitigation:** Phase M2c explicitly tests CUDA path; if issues persist, document CUDA-specific guard

---

## Delegation Checklist

When handing off Phase M2b implementation to Ralph (or specialist):

- [ ] Strategy document reviewed (`phase_m2/20251011T171454Z/strategy.md`)
- [ ] Expected selectors confirmed (lines 100-125 above)
- [ ] Documentation touch points identified (arch.md, testing_strategy.md, checklist)
- [ ] Artifact expectations clear (before/after logs, summary.md, commands.txt)
- [ ] Exit criteria understood (10/10 gradcheck tests pass)
- [ ] Cross-device validation scoped (conditional on CUDA availability)
- [ ] Ledger sync requirements listed (fix_plan.md, remediation_tracker.md)

---

## Cross-References

- **Phase M1f Summary:** `reports/2026-01-test-suite-triage/phase_m1/20251011T171454Z/summary.md`
- **Remediation Tracker:** `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` (lines 62-78, Cluster C2)
- **Testing Strategy:** `docs/development/testing_strategy.md` §§1.4, 4.1-4.2 (gradient testing methodology)
- **Architecture:** `arch.md` §15 (Differentiability Guidelines)
- **Fix Plan Ledger:** `docs/fix_plan.md` [TEST-SUITE-TRIAGE-001]

---

**Phase M2a Status:** ✅ Strategy brief complete; ready for Phase M2b implementation delegation.
