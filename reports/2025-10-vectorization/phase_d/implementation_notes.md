# Phase D3 Implementation Notes: Polynomial Regression Tests

**Date:** 2025-10-07
**Git SHA:** (to be recorded after commit)
**Initiative:** VECTOR-TRICUBIC-001 (PERF-PYTORCH-004 backlog)
**Plan Reference:** `plans/active/vectorization.md` Phase D task D3
**Worksheet Reference:** `reports/2025-10-vectorization/phase_d/polynomial_validation.md`

---

## Executive Summary

Phase D3 successfully delivered **11 regression tests** for vectorized polynomial interpolation helpers (`polint_vectorized`, `polin2_vectorized`, `polin3_vectorized`). All tests are marked `xfail(strict=True)` and correctly fail with `ImportError` since Phase D2 implementation has not yet landed. Tests validate:

- Scalar vs batched equivalence
- Gradient flow (`torch.autograd.gradcheck`)
- Device parametrisation (CPU + CUDA)
- Dtype neutrality (float32 + float64)
- Batch shape preservation

**Key Deliverable:** Test infrastructure ready for Phase D2 implementation to make tests green.

---

## 1. Test Suite Design

### 1.1 Test Class Structure

**File:** `tests/test_tricubic_vectorized.py`
**New Class:** `TestTricubicPoly` (added after existing `TestTricubicGather`)

**Test Count:** 11 tests collected
- Scalar equivalence: 3 tests (polint, polin2, polin3)
- Gradient flow: 3 tests (polint, polin2, polin3)
- Shape preservation: 1 test (polin3 batch handling)
- Dtype parametrisation: 2 tests (float32, float64)
- Device parametrisation: 2 tests (CPU, CUDA)

### 1.2 Fixture Design

**Fixture:** `poly_fixture_data`

Provides deterministic test data per worksheet Table 2.1:

**1D polint data (B=3):**
- `xa`: (3, 4) — coordinate arrays with linear spacing
- `ya`: (3, 4) — values with known patterns (powers of 2, cubic, linear)
- `x`: (3,) — query points [1.5, 0.5, 2.5]

**2D polin2 data (B=2):**
- `x1a_2d, x2a_2d`: (2, 4) — 2D grid coordinates
- `ya_2d`: (2, 4, 4) — grid values with pattern `ya[i,j] = i + j` (batch 0), `i*j` (batch 1)
- `x1_2d, x2_2d`: (2,) — query points [1.5, 0.5] and [1.5, 1.5]

**3D polin3 data (B=2):**
- `x1a_3d, x2a_3d, x3a_3d`: (2, 4) — 3D grid coordinates
- `ya_3d`: (2, 4, 4, 4) — cubic grid with pattern `ya[i,j,k] = i + j + k` (batch 0), scaled by 10 (batch 1)
- `x1_3d, x2_3d, x3_3d`: (2,) — query points

**Design Rationale:**
- Uses `torch.float64` for numerical precision in gradient checks
- Small integer-based values minimize rounding noise
- Deterministic patterns enable manual verification if needed
- Multiple batch sizes (B=1,2,3,10) exercise edge cases

---

## 2. Assertion Strategy

### 2.1 Core Validations

All tests verify:
1. **Shape correctness:** Output shape matches batch dimension `(B,)`
2. **No NaNs/Infs:** Numerical stability checks
3. **Scalar equivalence:** Batched output matches loop over scalar helpers (where applicable)
4. **Gradient flow:** `torch.autograd.gradcheck` with tolerances `eps=1e-6, atol=1e-4`
5. **Device/dtype preservation:** Output matches input device and dtype

### 2.2 Expected Failure Signatures

All tests currently fail with:
```
ImportError: cannot import name 'polint_vectorized' from 'nanobrag_torch.utils.physics'
```

This is correct behavior per `@pytest.mark.xfail(strict=True)` — tests will transition from XFAIL → PASS when Phase D2 implementation lands.

**Strict Mode:** If implementation accidentally passes before code is committed, pytest will **fail the test** (preventing premature claims of completion).

---

## 3. Device Coverage

### 3.1 CPU Tests

**Command:**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v
```

**Result:** 11 xfailed in 2.28s
**Artifact:** `reports/2025-10-vectorization/phase_d/pytest_cpu.log`

**Test Breakdown:**
- `test_polint_matches_scalar_batched` — XFAIL (ImportError)
- `test_polint_gradient_flow` — XFAIL (ImportError)
- `test_polin2_matches_scalar_batched` — XFAIL (ImportError)
- `test_polin2_gradient_flow` — XFAIL (ImportError)
- `test_polin3_matches_scalar_batched` — XFAIL (ImportError)
- `test_polin3_gradient_flow` — XFAIL (ImportError)
- `test_polin3_batch_shape_preserved` — XFAIL (ImportError)
- `test_polynomials_support_float64[dtype0]` (float32) — XFAIL (ImportError)
- `test_polynomials_support_float64[dtype1]` (float64) — XFAIL (ImportError)
- `test_polynomials_device_neutral[cpu]` — XFAIL (ImportError)
- `test_polynomials_device_neutral[cuda]` — XFAIL (ImportError, skipped if CUDA unavailable)

### 3.2 CUDA Tests

**Status:** CUDA parametrised tests included but not separately executed
**Skip Condition:** `pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available()))`

**Expected Behavior:**
- If CUDA available: test runs and XFAILs (ImportError)
- If CUDA unavailable: test is **skipped** (not XFAIL)

**Artifact:** CUDA-specific log deferred to Phase D4 when implementation ready

---

## 4. Follow-on Steps (Phase D2)

### 4.1 Implementation Checklist

**File:** `src/nanobrag_torch/utils/physics.py`

**New Functions to Add:**
1. `polint_vectorized(xa, ya, x) -> torch.Tensor`
   - C-code reference docstring (nanoBragg.c lines 4150-4158)
   - Batched Lagrange polynomial evaluation
   - Shape: (B, 4), (B, 4), (B,) → (B,)

2. `polin2_vectorized(x1a, x2a, ya, x1, x2) -> torch.Tensor`
   - C-code reference docstring (nanoBragg.c lines 4162-4171)
   - 2D interpolation via 4× polint
   - Shape: (B, 4), (B, 4), (B, 4, 4), (B,), (B,) → (B,)

3. `polin3_vectorized(x1a, x2a, x3a, ya, x1, x2, x3) -> torch.Tensor`
   - C-code reference docstring (nanoBragg.c lines 4174-4187)
   - 3D tricubic interpolation via 4× polin2
   - Shape: (B, 4), (B, 4), (B, 4), (B, 4, 4, 4), (B,), (B,), (B,) → (B,)

**Critical Requirements (from worksheet):**
- Preserve `requires_grad` (no `.item()`, `.detach()`, `.numpy()`)
- Device-neutral (infer device from inputs, no hard-coded `.cpu()`/`.cuda()`)
- Dtype-neutral (preserve input dtype)
- NaN handling (clamp denominators: `denom.clamp_min(1e-10)`)
- C-code reference docstrings per CLAUDE Rule #11

### 4.2 Expected Test Outcome After D2

**Before D2:** 11 xfailed
**After D2:** 11 passed (if implementation correct)

**Transition Path:**
1. Add vectorized helpers to `utils/physics.py`
2. Run `pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v`
3. If ImportError persists → implementation not exported correctly
4. If tests FAIL → implementation has bugs (shape/gradient/device issues)
5. If tests PASS → Phase D3 validation complete, proceed to D4

**Regression Guard:**
- Existing `TestTricubicGather` tests (5 tests) must still pass
- Full test suite must not introduce new failures

---

## 5. Test Names Summary

All tests reference `polynomial_validation.md` sections for traceability:

| Test Name | Purpose | Worksheet Ref |
|-----------|---------|---------------|
| `test_polint_matches_scalar_batched` | 1D Lagrange equivalence | Section 3.1 |
| `test_polint_gradient_flow` | 1D gradcheck | Section 4.2 |
| `test_polin2_matches_scalar_batched` | 2D interpolation equivalence | Section 3.2 |
| `test_polin2_gradient_flow` | 2D gradcheck | Section 4.2 |
| `test_polin3_matches_scalar_batched` | 3D tricubic equivalence | Section 3.3 |
| `test_polin3_gradient_flow` | 3D gradcheck | Section 4.2 |
| `test_polin3_batch_shape_preserved` | Batch dimension handling | Section 2.2 |
| `test_polynomials_support_float64[dtype0/dtype1]` | Dtype neutrality | Section 5.2 |
| `test_polynomials_device_neutral[cpu/cuda]` | Device neutrality | Section 5.1 |

---

## 6. Artifacts

**Stored in:** `reports/2025-10-vectorization/phase_d/`

- `collect.log` — pytest collection output (11 tests collected)
- `pytest_cpu.log` — CPU test run showing 11 xfailed
- `pytest_cuda.log` — (deferred to D4, CUDA run after implementation)
- `implementation_notes.md` — This document

**Git Changes:**
- `tests/test_tricubic_vectorized.py` — Added `TestTricubicPoly` class (11 tests)
- `reports/2025-10-vectorization/phase_d/collect.log` — Evidence
- `reports/2025-10-vectorization/phase_d/pytest_cpu.log` — Evidence
- `reports/2025-10-vectorization/phase_d/implementation_notes.md` — Documentation

---

## 7. Environment Metadata

**Python Version:** 3.13.7
**PyTorch Version:** (inferred from pytest output, to be confirmed with `torch.__version__`)
**CUDA Available:** (to be confirmed with `torch.cuda.is_available()`)
**Platform:** linux (Linux 6.14.0-29-generic)
**Working Directory:** /home/ollie/Documents/tmp/nanoBragg
**Test Framework:** pytest-8.4.2

**Environment Variables:**
- `KMP_DUPLICATE_LIB_OK=TRUE` — Required for all PyTorch tests (prevents MKL conflicts)

---

## 8. Next Actions

**For Phase D2 (Implementation):**
1. Implement `polint_vectorized`, `polin2_vectorized`, `polin3_vectorized` in `utils/physics.py`
2. Add C-code reference docstrings per CLAUDE Rule #11
3. Run tests: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v`
4. Debug any failures (likely shape mismatches or gradient breaks)
5. Run CUDA tests if available
6. Update `implementation_notes.md` (Phase D2 section)

**For Phase D4 (Integration):**
1. Run full regression suite: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py tests/test_at_str_002.py -v`
2. Capture CPU + CUDA logs
3. Update `polynomial_validation.md` with timing deltas (if applicable)
4. Mark plan Phase D as complete

**For fix_plan.md:**
- Update Attempts History with metrics from this loop:
  - Tests authored: 11
  - Collection time: 2.32s
  - Execution time: 2.28s (all xfailed as expected)
  - Artifacts: collect.log, pytest_cpu.log, implementation_notes.md
  - Next Actions: Proceed to Phase D2 (implement vectorized helpers)

---

**End of Phase D3 Implementation Notes**
