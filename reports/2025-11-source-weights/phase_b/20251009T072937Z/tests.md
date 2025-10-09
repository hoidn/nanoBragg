# Regression Coverage Plan — Weighted Source Normalization

**Generated:** 2025-10-09T07:29:37Z
**Context:** Phase B3 of source-weight-normalization initiative
**Prereqs:** normalization_flow.md (B1) and strategy.md (B2) completed

---

## Test Strategy Overview

**Objective:** Verify that the normalization fix (`source_norm = sum(source_weights)`) produces correct behavior across:
1. **Parity:** PyTorch matches C reference for weighted-source cases
2. **Backward Compatibility:** Existing tests (uniform weights, single source) remain passing
3. **Edge Cases:** Validation prevents pathological configurations
4. **Device Neutrality:** CPU and CUDA produce consistent results (within tolerance)

---

## Test Case Definitions

### TC-A: Non-Uniform Source Weights (PRIMARY VALIDATION)

**Purpose:** Validate fix for 327.9× discrepancy (Phase A evidence).

**Configuration:**
- **Sources:** Two sources with weights [1.0, 0.2]
- **Source File:** `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt` (reuse Phase A fixture)
- **Cell:** 100 100 100 90 90 90 (simple cubic)
- **Wavelength:** 6.2 Å
- **Distance:** 100 mm
- **Detector:** 128×128 pixels (fast test), pixel 0.1 mm
- **Default F:** 100

**Canonical Command (C reference):**
```bash
"$NB_C_BIN" -source reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt \
  -cell 100 100 100 90 90 90 \
  -default_F 100 \
  -N 5 \
  -lambda 6.2 \
  -distance 100 \
  -detpixels 128 \
  -floatfile /tmp/tc_a_c.bin
```

**Canonical Command (PyTorch):**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch \
  -source reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt \
  -cell 100 100 100 90 90 90 \
  -default_F 100 \
  -N 5 \
  -lambda 6.2 \
  -distance 100 \
  -detpixels 128 \
  -floatfile /tmp/tc_a_py.bin
```

**Pytest Selector:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_001.py::TestATSRC001::test_weighted_source_parity -v
```
(Test file to be created in Phase C)

**Expected Metrics:**
- **CPU:** Correlation ≥ 0.9999, sum_ratio ∈ [0.999, 1.001]
- **CUDA:** Correlation ≥ 0.999, sum_ratio ∈ [0.99, 1.01]

**Failure Mode (Before Fix):**
- Sum ratio ≈ 1.67× (PyTorch divides by 2, C divides by 1.2)

---

### TC-B: Uniform Source Weights (BACKWARD COMPATIBILITY)

**Purpose:** Verify no regression for existing multi-source behavior.

**Configuration:**
- **Sources:** Three sources with weights [1.0, 1.0, 1.0]
- **Cell:** 100 100 100 90 90 90
- **Wavelength:** 6.2 Å
- **Distance:** 100 mm
- **Detector:** 128×128 pixels
- **Default F:** 100

**Canonical Command (PyTorch only, compare against pre-fix baseline):**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch \
  -source fixtures/three_sources_uniform.txt \
  -cell 100 100 100 90 90 90 \
  -default_F 100 \
  -N 5 \
  -lambda 6.2 \
  -distance 100 \
  -detpixels 128 \
  -floatfile /tmp/tc_b_py.bin
```

**Pytest Selector:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_001.py::TestATSRC001::test_uniform_weights_backward_compat -v
```

**Expected Metrics:**
- Output identical to current implementation (before fix)
- Correlation = 1.0, max |Δ| ≈ 0 (within float32 epsilon)

**Rationale:** `sum([1,1,1]) = 3 = n_sources`, so behavior is mathematically equivalent.

---

### TC-C: Single Source (DEFAULT BEHAVIOR)

**Purpose:** Verify no impact on single-source simulations (most common use case).

**Configuration:**
- **Sources:** None (default beam configuration)
- **Cell:** 100 100 100 90 90 90
- **Wavelength:** 6.2 Å
- **Distance:** 100 mm
- **Detector:** 128×128 pixels
- **Default F:** 100

**Canonical Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch \
  -cell 100 100 100 90 90 90 \
  -default_F 100 \
  -N 5 \
  -lambda 6.2 \
  -distance 100 \
  -detpixels 128 \
  -floatfile /tmp/tc_c_py.bin
```

**Pytest Selector:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_001.py::TestATSRC001::test_single_source_unaffected -v
```

**Expected Metrics:**
- Output identical to current implementation
- Correlation = 1.0, max |Δ| ≈ 0

**Rationale:** `source_weights = None` → falls back to `n_sources = 1` (no code path change).

---

### TC-D: Edge Case Validation (BEAMCONFIG INIT)

**Purpose:** Verify that pathological weight configurations are rejected at initialization.

**Test Cases:**

#### TC-D1: Zero-Sum Weights
```python
def test_zero_sum_weights_rejected():
    with pytest.raises(ValueError, match="source_weights must sum to a positive value"):
        BeamConfig(
            wavelength_A=6.2,
            source_directions=torch.tensor([[1, 0, 0], [-1, 0, 0]]),
            source_weights=torch.tensor([0.5, -0.5])  # Sum = 0
        )
```

#### TC-D2: All-Zero Weights
```python
def test_all_zero_weights_rejected():
    with pytest.raises(ValueError, match="source_weights must sum to a positive value"):
        BeamConfig(
            wavelength_A=6.2,
            source_directions=torch.tensor([[1, 0, 0], [0, 1, 0]]),
            source_weights=torch.tensor([0.0, 0.0])  # Sum = 0
        )
```

#### TC-D3: Negative Weights
```python
def test_negative_weights_rejected():
    with pytest.raises(ValueError, match="source_weights must be non-negative"):
        BeamConfig(
            wavelength_A=6.2,
            source_directions=torch.tensor([[1, 0, 0], [0, 1, 0]]),
            source_weights=torch.tensor([1.0, -0.2])  # Contains negative
        )
```

**Pytest Selector:**
```bash
pytest tests/test_config.py::TestBeamConfigValidation -v
```

**Location:** Validation logic to be added in `src/nanobrag_torch/config.py:BeamConfig.__post_init__`.

---

### TC-E: Device Neutrality (CPU vs CUDA)

**Purpose:** Verify CPU and CUDA produce consistent results for weighted sources.

**Configuration:** Same as TC-A (non-uniform weights [1.0, 0.2])

**Pytest Selector:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_001.py::TestATSRC001::test_weighted_source_parity[cpu] -v
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_001.py::TestATSRC001::test_weighted_source_parity[cuda] -v
```

**Expected Metrics:**
- CPU vs CUDA correlation ≥ 0.9999
- Max |Δ| ≤ 1e-4 (allow for minor device-specific numerical differences)

**Rationale:** Ensures AT-PERF-DEVICE-001 compliance (device-neutral implementation).

---

## Test Implementation Plan

### Phase C3: Add Tests (Implementation Phase)

**File:** `tests/test_at_src_001.py` (new file)
**Structure:**
```python
import pytest
import torch
import numpy as np
from pathlib import Path

class TestATSRC001:
    """AT-SRC-001: Weighted Source Normalization"""

    @pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available"))])
    def test_weighted_source_parity(self, device):
        """TC-A: Non-uniform weights [1.0, 0.2] match C reference"""
        # Run C reference
        # Run PyTorch
        # Load both outputs
        # Compute correlation, sum_ratio, max |Δ|
        # Assert thresholds met
        pass

    def test_uniform_weights_backward_compat(self):
        """TC-B: Uniform weights [1.0, 1.0, 1.0] unchanged"""
        # Run with fix applied
        # Load baseline (pre-fix output)
        # Assert identical
        pass

    def test_single_source_unaffected(self):
        """TC-C: Single source (no source file) unchanged"""
        # Run with fix applied
        # Load baseline
        # Assert identical
        pass
```

**File:** `tests/test_config.py` (extend existing)
**Add:**
```python
class TestBeamConfigValidation:
    """Validation of BeamConfig edge cases"""

    def test_zero_sum_weights_rejected(self):
        """TC-D1: Zero-sum weights raise ValueError"""
        # As defined above
        pass

    def test_all_zero_weights_rejected(self):
        """TC-D2: All-zero weights raise ValueError"""
        pass

    def test_negative_weights_rejected(self):
        """TC-D3: Negative weights raise ValueError"""
        pass
```

---

## Tolerances and Thresholds

**CPU:**
- Correlation: ≥ 0.9999
- Sum ratio: [0.999, 1.001]
- Max |Δ|: ≤ 1e-5

**CUDA:**
- Correlation: ≥ 0.999
- Sum ratio: [0.99, 1.01]
- Max |Δ|: ≤ 1e-4

**Rationale:**
- CPU uses higher precision for reference comparisons
- CUDA allows slightly looser tolerance for device-specific rounding (float32 accumulation differences)

---

## Fixtures and Artifacts

**Phase A Reuse:**
- `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt` (weights [1.0, 0.2])

**New Fixtures (Phase C):**
- `tests/fixtures/three_sources_uniform.txt` (weights [1.0, 1.0, 1.0])
  ```
  X Y Z lambda weight
  1.0 0.0 0.0 6.2 1.0
  0.0 1.0 0.0 6.2 1.0
  0.0 0.0 1.0 6.2 1.0
  ```

**Baseline Outputs (Pre-Fix):**
- `tests/baselines/tc_b_uniform_baseline.bin` (TC-B comparison)
- `tests/baselines/tc_c_single_baseline.bin` (TC-C comparison)

**Artifact Storage (Post-Fix):**
- `reports/2025-11-source-weights/phase_d/tests/` (pytest logs, metrics JSON)

---

## CI Integration

**Pytest Markers:**
- `@pytest.mark.source_weights` — All weighted-source tests
- `@pytest.mark.cuda` — CUDA-specific tests (skipped if unavailable)
- `@pytest.mark.parity` — C↔PyTorch parity checks (requires `NB_RUN_PARALLEL=1`)

**CI Gate Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest -v -m "source_weights" tests/test_at_src_001.py tests/test_config.py::TestBeamConfigValidation
```

**Expected CI Behavior:**
- All tests pass on CPU (Linux/macOS/Windows)
- CUDA tests pass on GPU runners (if available)
- Parity tests require `NB_C_BIN` env var (skip if not set)

---

## Rollback Criteria

**If any of the following fail, revert the fix and investigate:**
1. TC-B (backward compatibility) fails: existing tests regress
2. TC-C (single source) fails: default behavior broken
3. TC-D (validation) not implemented: edge cases unguarded
4. TC-E (device neutrality) fails on CUDA: device-specific bug introduced

**Rollback Command:**
```bash
git revert HEAD  # Revert normalization fix commit
pytest -v  # Verify pre-fix tests still pass
```

---

## Performance Impact

**Expected:** Negligible. The fix changes:
- One scalar sum operation: `source_weights.sum().item()` (O(n_sources), typically n_sources < 100)
- No impact on hot path (physics kernel unchanged)

**Verification:** Run `scripts/benchmarks/benchmark_detailed.py` before and after fix, compare CPU/GPU throughput.

---

## Documentation Updates (Phase D3)

**Files to Update:**
1. `docs/architecture/pytorch_design.md` §8 (Physics Model & Scaling)
   - Add subsection: "Weighted Source Normalization"
   - Document `source_norm = sum(source_weights)` formula

2. `docs/development/testing_strategy.md` §2.5 (Parallel Validation Matrix)
   - Add AT-SRC-001 entry with TC-A command and thresholds

3. `README_PYTORCH.md` (CLI Usage Guide)
   - Document `-source` file format (X Y Z λ weight columns)
   - Explain weight semantics (relative fluence contributions)

4. `plans/active/source-weight-normalization.md`
   - Mark Phase B tasks [D] (done)
   - Update Phase C/D with implementation status

---

## Summary

**Total Test Coverage:**
- **5 test cases** (TC-A through TC-E)
- **3 pytest selectors** (`test_at_src_001.py`, `test_config.py`, parametrized devices)
- **2 fixture files** (reuse Phase A + new uniform weights)
- **2 tolerance tiers** (CPU strict, CUDA relaxed)

**Exit Criteria for Phase C (Implementation):**
- All 5 test cases pass on CPU
- TC-E passes on CUDA (if available)
- No existing tests regress
- Artifacts captured under `reports/.../phase_d/tests/`

**Next Step:** Phase C implementation (modify simulator.py:868, add tests, run validation).
