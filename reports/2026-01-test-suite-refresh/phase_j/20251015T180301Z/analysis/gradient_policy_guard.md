# Gradient Policy Guard Fixture (Phase J — Task J2)

## Purpose & Scope

**Objective:** Implement a pytest module-scoped fixture for `tests/test_gradients.py` that enforces the `NANOBRAGG_DISABLE_COMPILE=1` environment variable requirement. This fixture will prevent C2-cluster donated-buffer errors (observed in Phase G/M2) by ensuring gradient tests only run when torch.compile is disabled.

**Scope:**
- Environment variable validation (`NANOBRAGG_DISABLE_COMPILE`)
- Clear skip messages with remediation commands
- Module-specific application (only affects `test_gradients.py`)
- No performance impact on non-gradient tests

**Out of Scope:**
- Gradient correctness validation (covered by `torch.autograd.gradcheck`)
- Timeout policy enforcement (covered by `@pytest.mark.timeout(905)`)
- Device/dtype neutrality checks (covered by existing test parametrization)

## Environment Checks & Enforcement

### Required Environment Variable

**Name:** `NANOBRAGG_DISABLE_COMPILE`
**Expected Value:** `"1"` (string literal)
**Purpose:** Disables torch.compile in simulator to prevent donated buffer interference with torch.autograd.gradcheck

**Rationale:** (from Phase M2 validation, 2025-10-11T172830Z)
- torch.compile creates donated buffers that break gradient computation during numerical gradient checks
- torch.autograd.gradcheck requires clean tensor memory management
- Disabling compile is required for all 10 gradcheck tests to pass (validated in Phase M2)

**Canonical Reference:**
- `docs/development/testing_strategy.md` S4.1 (Gradient Checks execution requirements)
- `arch.md` S15 (Differentiability Guidelines, gradient test guard requirement)
- `reports/2026-01-test-suite-refresh/phase_m2/20251011T172830Z/summary.md` (Phase M2 validation results)

### Fixture Design

**Scope:** `module` (applies to entire `test_gradients.py` module)
**Autouse:** `True` (automatically applies to all tests in module)

**Implementation:**
```python
@pytest.fixture(scope="module", autouse=True)
def gradient_policy_guard():
    """
    Enforce NANOBRAGG_DISABLE_COMPILE=1 environment variable for gradient tests.

    Gradient tests require compile guard to prevent torch.compile donated buffer
    interference with torch.autograd.gradcheck. This fixture skips the entire
    test_gradients.py module if the required environment variable is not set.

    Required Environment:
    - NANOBRAGG_DISABLE_COMPILE=1 (must be set before pytest execution)

    Canonical Command:
        env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \\
          NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py

    References:
    - docs/development/testing_strategy.md S4.1 (gradient test requirements)
    - arch.md S15 (gradient correctness and test guard policy)
    - reports/2026-01-test-suite-refresh/phase_m2/20251011T172830Z/summary.md
    - plans/active/test-suite-triage-phase-h.md (Phase J Task J2)
    """
    import os

    if os.environ.get('NANOBRAGG_DISABLE_COMPILE') != '1':
        pytest.skip(
            "Gradient tests require NANOBRAGG_DISABLE_COMPILE=1 environment variable.\n\n"
            "This guard prevents torch.compile donated buffer interference with "
            "torch.autograd.gradcheck.\n\n"
            "To run gradient tests, use:\n"
            "  env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \\\n"
            "    NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py\n\n"
            "For details, see:\n"
            "  - docs/development/testing_strategy.md S4.1\n"
            "  - arch.md S15 (Differentiability Guidelines)\n"
            "  - reports/2026-01-test-suite-refresh/phase_m2/20251011T172830Z/"
        )
```

### Alternative Design: Class-Scoped Fixture

If gradient tests are organized into test classes, a class-scoped fixture may be more appropriate:

```python
# At module level in test_gradients.py
@pytest.fixture(scope="class", autouse=True)
def gradient_policy_guard():
    """
    Class-scoped gradient policy guard.

    Use this variant if gradient tests are organized into classes.
    Applies to all test classes in test_gradients.py.
    """
    import os

    if os.environ.get('NANOBRAGG_DISABLE_COMPILE') != '1':
        pytest.skip(
            "Gradient tests require NANOBRAGG_DISABLE_COMPILE=1. "
            "Run with: env NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_gradients.py"
        )
```

**Recommendation:** Use module-scoped fixture (first variant) since it applies uniformly to all gradient tests regardless of organization structure.

## Skip/Xfail Handling

### Skip Behavior

**Trigger:** `NANOBRAGG_DISABLE_COMPILE` is not set or has value other than `"1"`

**Action:** Skip entire `test_gradients.py` module using `pytest.skip()`

**Pytest Output Example:**
```
tests/test_gradients.py::test_cell_a_gradient SKIPPED
tests/test_gradients.py::test_detector_distance_gradient SKIPPED
...
==================== 15 skipped in 0.05s ====================

SKIPPED [15] tests/test_gradients.py:12: Gradient tests require NANOBRAGG_DISABLE_COMPILE=1 environment variable.

This guard prevents torch.compile donated buffer interference with torch.autograd.gradcheck.

To run gradient tests, use:
  env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
    NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py

For details, see:
  - docs/development/testing_strategy.md S4.1
  - arch.md S15 (Differentiability Guidelines)
  - reports/2026-01-test-suite-refresh/phase_m2/20251011T172830Z/
```

### Xfail Consideration

**Question:** Should we use `pytest.xfail()` instead of `pytest.skip()`?

**Analysis:**
- **pytest.skip():** Test is not executed, appears in "skipped" section of output
  - ✅ Clear intent: environment prerequisites not met
  - ✅ Consistent with common pytest patterns for environment checks
  - ✅ Does not count as "failure" in CI metrics

- **pytest.xfail():** Test is marked as "expected to fail" and may or may not run
  - ❌ Less clear intent: xfail typically indicates known bugs, not environment setup
  - ❌ Confusing for users: gradient tests are not broken, just require specific environment
  - ❌ May still execute test (depending on xfail mode), wasting time

**Recommendation:** Use `pytest.skip()` for clearer semantics.

### Alternative: pytest.fail() with Actionable Error

**Consideration:** Should we use `pytest.fail()` instead of `pytest.skip()` to make missing environment a hard error?

**Analysis:**
- **Advantage:** Forces users to explicitly set environment (prevents accidental skip)
- **Disadvantage:** Breaks full-suite runs when users don't intend to run gradient tests

**Recommendation:** Use `pytest.skip()` for developer flexibility. CI can enforce `NANOBRAGG_DISABLE_COMPILE=1` explicitly in gradient-specific jobs.

## Implementation Location

**File:** `tests/test_gradients.py`

**Placement:** Add fixture definition at module level, after imports, before first test

**Example File Structure:**
```python
"""
Gradient correctness tests for nanoBragg PyTorch implementation.

These tests verify that automatic differentiation works correctly for all
differentiable parameters. All tests require NANOBRAGG_DISABLE_COMPILE=1.
"""

import os
# Set NANOBRAGG_DISABLE_COMPILE before torch import (required for test file)
os.environ['NANOBRAGG_DISABLE_COMPILE'] = os.environ.get('NANOBRAGG_DISABLE_COMPILE', '0')

import pytest
import torch
import numpy as np

from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator


# Phase J Task J2: Gradient policy guard fixture
@pytest.fixture(scope="module", autouse=True)
def gradient_policy_guard():
    """
    Enforce NANOBRAGG_DISABLE_COMPILE=1 for gradient tests.

    See: reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/gradient_policy_guard.md
    """
    if os.environ.get('NANOBRAGG_DISABLE_COMPILE') != '1':
        pytest.skip(
            "Gradient tests require NANOBRAGG_DISABLE_COMPILE=1 environment variable.\n\n"
            "Run with: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE "
            "NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py\n\n"
            "See: docs/development/testing_strategy.md S4.1"
        )


# Existing tests follow...
class TestCellParameterGradients:
    """Test gradients for crystal cell parameters."""
    ...
```

**Key Points:**
1. Fixture defined after imports, before first test class
2. Module-level `os.environ` setting at top (existing pattern in test_gradients.py)
3. Clear docstring referencing design document
4. Skip message includes complete reproduction command

## Integration with Existing Guards

### Module-Level Environment Setup

**Current Pattern in test_gradients.py:**
```python
import os
os.environ['NANOBRAGG_DISABLE_COMPILE'] = '1'  # Set before torch import
```

**Issue:** This sets the variable unconditionally, masking cases where users forget to set it externally

**Recommendation:** Change to conditional set that preserves external value:
```python
import os
# Preserve external NANOBRAGG_DISABLE_COMPILE if set, otherwise default to '0'
os.environ['NANOBRAGG_DISABLE_COMPILE'] = os.environ.get('NANOBRAGG_DISABLE_COMPILE', '0')
```

**Effect:**
- If user sets `NANOBRAGG_DISABLE_COMPILE=1` externally → preserved → fixture passes
- If user doesn't set variable → defaults to '0' → fixture skips tests with clear message
- Existing test behavior unchanged when environment is set correctly

### Interaction with @pytest.mark.timeout(905)

**Current Pattern:**
```python
@pytest.mark.timeout(905)
@pytest.mark.slow_gradient
def test_property_gradient_stability():
    ...
```

**Interaction:**
- Timeout marker is independent of policy guard
- If policy guard skips module, timeout is never evaluated (no overhead)
- If policy guard passes, timeout applies normally

**No conflicts expected.**

### Interaction with Device Parametrization

**Current Pattern:**
```python
@pytest.mark.parametrize("device", ["cpu", "cuda"])
def test_detector_distance_gradient(device):
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    ...
```

**Interaction:**
- Policy guard runs first (module scope, autouse=True)
- If guard skips, device parametrization never executes
- If guard passes, device parametrization proceeds normally

**No conflicts expected.**

## Testing the Fixture

**Validation Commands:** (per Phase J Task J3)

### Test 1: Positive Case (Environment Set)

**Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_gradients.py --collect-only -q
```

**Expected Output:**
```
tests/test_gradients.py::TestCellParameterGradients::test_cell_a_gradient
tests/test_gradients.py::TestCellParameterGradients::test_cell_gamma_gradient
...
==================== 15 tests collected ====================
```

**Expected Result:** ✅ All tests collected, no skips

### Test 2: Negative Case (Environment Not Set)

**Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_gradients.py --collect-only -q
```

**Expected Output:**
```
tests/test_gradients.py::TestCellParameterGradients::test_cell_a_gradient SKIPPED
tests/test_gradients.py::TestCellParameterGradients::test_cell_gamma_gradient SKIPPED
...
==================== 15 skipped in 0.05s ====================
```

**Expected Result:** ✅ All tests skipped with clear message

### Test 3: Negative Case (Wrong Value)

**Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=0 \
  pytest -v tests/test_gradients.py --collect-only -q
```

**Expected Output:**
```
==================== 15 skipped in 0.05s ====================

SKIPPED [15] tests/test_gradients.py:12: Gradient tests require NANOBRAGG_DISABLE_COMPILE=1 environment variable.
```

**Expected Result:** ✅ All tests skipped (value != "1")

### Test 4: Full Execution (Validate Gradcheck Passes)

**Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_gradients.py -k "gradcheck" --tb=short
```

**Expected Output:**
```
tests/test_gradients.py::test_cell_a_gradient PASSED
tests/test_gradients.py::test_detector_distance_gradient PASSED
...
==================== 10 passed in 45s ====================
```

**Expected Result:** ✅ All gradcheck tests pass (validates compile guard is working)

**Artifact Capture:**
- Save pytest output to `reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/validation/gradient_guard_test_*.log`
- Record skip counts and messages

## Failure Remediation

### Failure Scenario 1: Tests Skipped Unexpectedly

**Symptom:** User expects gradient tests to run but sees:
```
==================== 15 skipped in 0.05s ====================
```

**Diagnosis:**
```bash
echo $NANOBRAGG_DISABLE_COMPILE
# Output: (empty) or "0"
```

**Remediation:**
```bash
# Set environment variable explicitly
export NANOBRAGG_DISABLE_COMPILE=1

# Or use inline env for single command
env NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py
```

### Failure Scenario 2: Donated Buffer Errors Recur

**Symptom:** Gradient tests run but fail with:
```
RuntimeError: Cannot access data pointer of Tensor that doesn't hold data
```

**Diagnosis:**
```bash
# Check if compile guard was bypassed
pytest -v tests/test_gradients.py 2>&1 | grep -i "compile"
```

**Remediation:**
1. Verify `NANOBRAGG_DISABLE_COMPILE=1` is set before pytest execution
2. Verify simulator respects flag (check `src/nanobrag_torch/simulator.py`)
3. Verify no conflicting environment variables (e.g., `TORCHDYNAMO_DISABLE=0`)

### Failure Scenario 3: Fixture Code Error

**Symptom:** pytest fails during collection with:
```
ERROR tests/test_gradients.py - AttributeError: module 'pytest' has no attribute 'skip'
```

**Diagnosis:** pytest not imported or incorrect version

**Remediation:**
```bash
# Verify pytest version (requires >=6.0)
pytest --version

# Reinstall if needed
pip install --upgrade pytest
```

## Open Questions

1. **CI Enforcement Strategy:** Should CI jobs fail hard if gradient tests are skipped? (Prevents accidental skips in automated runs)

2. **Fixture Scope Optimization:** Could we use `session` scope instead of `module` if gradient tests are expanded to multiple files? (Would need to check multiple test files)

3. **Environment Variable Naming:** Is `NANOBRAGG_DISABLE_COMPILE` sufficiently descriptive? Alternative: `NANOBRAGG_GRADCHECK_MODE=1`? (Current name aligns with existing simulator flag)

4. **Logging Integration:** Should fixture log when tests are skipped to `reports/` for audit trail? (May be overkill for simple environment check)

5. **Phase I Timeout Interaction:** Phase I established 905s timeout for `test_property_gradient_stability`. Should this fixture verify timeout marker is present? (Out of scope for policy guard, handled by pytest-timeout plugin)

## References

- **Testing Strategy:** `docs/development/testing_strategy.md` S4.1 (Gradient Checks execution requirements)
- **Architecture:** `arch.md` S15 (Differentiability Guidelines, gradient test execution requirement)
- **Phase M2 Validation:** `reports/2026-01-test-suite-refresh/phase_m2/20251011T172830Z/summary.md` (10/10 gradcheck tests passing)
- **Phase I Timeout Study:** `reports/2026-01-test-suite-refresh/phase_i/20251015T173309Z/analysis/timeout_decision.md` (905s ceiling rationale)
- **Plan Context:** `plans/active/test-suite-triage-phase-h.md` (Phase J Task J2)
