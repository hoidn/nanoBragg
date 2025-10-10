# Dtype Neutrality Validation Test Suite

**Initiative:** `[DTYPE-NEUTRAL-001]`
**Phase:** C (Test Specification)
**Date:** 2025-10-10T174636Z

---

## Overview

This document specifies the authoritative test commands for validating the dtype neutrality fix in `Detector.get_pixel_coords()`. All commands must be executed in the documented order with artifacts captured for each phase.

---

## Prerequisites

### Environment Setup

```bash
# Required environment variable (MKL conflict avoidance)
export KMP_DUPLICATE_LIB_OK=TRUE

# Verify editable install
pip show nanobrag-torch | grep "Editable project location" || echo "WARNING: Not installed in editable mode"

# Verify CUDA availability (optional, for GPU smoke tests)
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Baseline Collection

**Before applying fix:**

```bash
# Capture environment snapshot
pytest --collect-only -q > phase_d_baseline_collect.log 2>&1

# Capture baseline failure signatures
pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py \
  --maxfail=2 --tb=short > phase_d_baseline_failures.log 2>&1
```

**Expected baseline:** Both tests crash with `RuntimeError: Float did not match Double` in `detector.py:767`.

---

## Primary Validation (Dtype Crash Elimination)

### Test Suite

**Objective:** Verify dtype mismatch crashes are eliminated.

**Tests:**
- `test_at_parallel_013.py` — Deterministic mode with float64 precision
- `test_at_parallel_024.py` — Mosaic rotation with dtype switching

### Command

```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_013.py \
  tests/test_at_parallel_024.py \
  --maxfail=0 \
  --durations=10 \
  --tb=short \
  | tee phase_d_primary_validation.log
```

### Expected Post-Fix Outcomes

**Success Indicators:**

✅ **No dtype crashes:**
- No `RuntimeError: Float did not match Double` errors
- No `RuntimeError: expected scalar type Float but found Double` errors
- Tests progress past detector geometry initialization

⚠️ **Seed-related failures MAY occur** (expected, separate issue):
- Tests may fail with seed mismatch messages
- Tests may fail with numerical assertion errors
- This is EXPECTED and documented in `plans/active/determinism.md`

**Failure Indicators (reopen fix plan if observed):**

❌ **Dtype crashes persist:**
- Same `Float did not match Double` errors → fix incomplete or reverted
- New dtype-related errors → edge case discovered

❌ **New crashes unrelated to dtype:**
- Document failure signature and halt validation
- Potential side effect of fix

### Artifact Capture

```bash
# On completion, save artifacts
mkdir -p reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_d/primary/
cp phase_d_primary_validation.log reports/.../phase_d/primary/pytest.log

# Extract key metrics
grep -E "(PASSED|FAILED|ERROR|RuntimeError)" phase_d_primary_validation.log \
  > reports/.../phase_d/primary/summary.txt
```

---

## Secondary Validation (Regression Prevention)

### Test Suite

**Objective:** Ensure no behavioral changes for default float32 usage.

**Tests:** `test_detector_geometry.py` — Comprehensive detector geometry validation

### Command

```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_detector_geometry.py \
  --durations=10 \
  --tb=short \
  | tee phase_d_regression_check.log
```

### Expected Outcomes

✅ **All tests pass:**
- Same pass/fail status as before fix
- No new warnings or errors
- No performance degradation (check durations)

**Baseline Comparison:**

```bash
# Compare test durations (before vs after fix)
grep "slowest durations" phase_d_baseline_collect.log > before_durations.txt
grep "slowest durations" phase_d_regression_check.log > after_durations.txt
diff before_durations.txt after_durations.txt || echo "Performance change detected"
```

**Performance Tolerance:** ±5% duration variance acceptable.

### Artifact Capture

```bash
mkdir -p reports/.../phase_d/secondary/
cp phase_d_regression_check.log reports/.../phase_d/secondary/pytest.log
cp {before,after}_durations.txt reports/.../phase_d/secondary/
```

---

## Tertiary Validation (Device Coverage)

### Test Suite

**Objective:** Verify dtype coercion works on both CPU and CUDA.

### CPU Validation (Always Required)

```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_013.py \
  -k "cpu" \
  --tb=short \
  | tee phase_d_cpu_smoke.log
```

**Expected:** Dtype crashes eliminated on CPU path.

### CUDA Validation (If Available)

```bash
# Skip if CUDA unavailable
if python -c "import torch; exit(0 if torch.cuda.is_available() else 1)"; then
  KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
    tests/test_at_parallel_013.py \
    -k "gpu" \
    --tb=short \
    | tee phase_d_cuda_smoke.log
else
  echo "CUDA not available, skipping GPU smoke test" | tee phase_d_cuda_smoke.log
fi
```

**Expected (if CUDA available):** Dtype crashes eliminated on CUDA path.

### Artifact Capture

```bash
mkdir -p reports/.../phase_d/tertiary/
cp phase_d_{cpu,cuda}_smoke.log reports/.../phase_d/tertiary/
```

---

## Full Test Suite Run (Optional, Comprehensive)

### Command

```bash
# Run entire test suite to check for unexpected regressions
KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  --maxfail=10 \
  --durations=20 \
  --tb=line \
  | tee phase_d_full_suite.log
```

**When to run:**
- Before final commit (recommended)
- If time permits (comprehensive validation)
- Not required for initial fix validation

### Expected Outcomes

✅ **No new failures:**
- Same pass/fail distribution as before fix
- No dtype-related crashes in any test

⚠️ **Acceptable changes:**
- Determinism tests may now fail differently (seed issues exposed)
- Document any new failure signatures in `phase_e/validation.md`

---

## Validation Metrics

### Metrics to Capture

For each test run, record:

1. **Pass/Fail Counts:**
   ```bash
   grep -E "passed|failed|error" <log_file> | tail -1
   ```

2. **Dtype Error Counts:**
   ```bash
   grep -c "Float did not match Double" <log_file>
   ```

3. **Test Durations:**
   ```bash
   grep "slowest durations" <log_file>
   ```

4. **New Warnings:**
   ```bash
   grep -E "WARNING|DeprecationWarning" <log_file> | sort -u
   ```

### Success Thresholds

| Metric | Baseline (Before Fix) | Target (After Fix) | Status |
|--------|----------------------|-------------------|--------|
| Dtype crashes in AT-013/024 | 2 | 0 | Gate |
| Detector geometry pass rate | 100% | 100% | Gate |
| Performance regression | N/A | <5% slowdown | Nice-to-have |
| New warnings | 0 | 0 | Gate |

---

## Test Execution Checklist

**Pre-fix validation:**

- [ ] Baseline environment snapshot captured
- [ ] Baseline failure logs captured
- [ ] Dtype crash confirmed in both AT-013 and AT-024

**Post-fix validation sequence:**

- [ ] Primary validation executed (AT-013/024)
- [ ] Dtype crashes eliminated (verified in logs)
- [ ] Secondary validation executed (detector geometry)
- [ ] No regressions detected
- [ ] Tertiary validation executed (CPU, CUDA if available)
- [ ] Device coverage confirmed
- [ ] Metrics captured for all validation phases
- [ ] Artifacts saved under `reports/.../phase_d/`

**Documentation:**

- [ ] All logs committed to git
- [ ] Metrics summarized in `phase_e/validation.md`
- [ ] `docs/fix_plan.md` updated with Attempt #3 entry

---

## Troubleshooting

### If Primary Validation Fails

**Symptom:** Dtype crashes still occur after fix.

**Debug Steps:**

1. Verify fix was applied correctly:
   ```bash
   git diff src/nanobrag_torch/models/detector.py | grep "dtype=self.dtype"
   ```
   Expected: 4 occurrences

2. Check for missed cache paths:
   ```bash
   grep -n "\.to(self\.device)" src/nanobrag_torch/models/detector.py | grep -v "dtype="
   ```
   Expected: No results (all `.to(self.device)` should include `dtype=`)

3. Rerun with increased verbosity:
   ```bash
   pytest -vv -s tests/test_at_parallel_013.py --tb=long 2>&1 | tee debug.log
   ```

4. Document findings in `phase_d/troubleshooting.md`

### If Secondary Validation Fails

**Symptom:** Detector geometry tests fail or show regressions.

**Debug Steps:**

1. Isolate failing test:
   ```bash
   pytest -vv tests/test_detector_geometry.py::<failing_test> --tb=long
   ```

2. Compare outputs before/after fix:
   ```bash
   git stash  # Temporarily revert fix
   pytest tests/test_detector_geometry.py::<failing_test> > before.log 2>&1
   git stash pop
   pytest tests/test_detector_geometry.py::<failing_test> > after.log 2>&1
   diff before.log after.log
   ```

3. Check for unintended dtype conversions:
   - Review detector tensor dtypes in failing test
   - Verify cache regeneration logic

4. Document in `phase_d/troubleshooting.md` and halt further changes

---

## References

**Authoritative Sources:**

- Test strategy: `docs/development/testing_strategy.md` §1.4 (Device & Dtype Discipline)
- Runtime checklist: `docs/development/pytorch_runtime_checklist.md` §2
- Detector architecture: `docs/architecture/detector.md` §§7-8 (Caching)
- Phase B analysis: `reports/2026-01-test-suite-triage/phase_d/20251010T173558Z/dtype-neutral/phase_b/summary.md`

**Test Files:**

- Primary: `tests/test_at_parallel_013.py` (deterministic mode)
- Primary: `tests/test_at_parallel_024.py` (mosaic rotation)
- Secondary: `tests/test_detector_geometry.py` (regression check)

**Artifact Storage:**

- Root: `reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_d/`
- Subdirectories: `primary/`, `secondary/`, `tertiary/`, `troubleshooting/` (if needed)

---

**End of Test Specification**
