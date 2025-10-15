# Chunk 03 Summary - Phase O5 Four-Way Shard Execution

**STAMP:** 20251015T043128Z
**Date:** 2025-10-14 (UTC)
**Purpose:** Capture chunk 03 with isolated gradient tests and proper `NANOBRAGG_DISABLE_COMPILE=1` guard to establish baseline timing data.

## Execution Strategy

Per `plans/active/test-suite-triage.md:304-312`, chunk 03 was split into four shards to isolate the slow gradient tests and gather precise timing data:

- **Part 1:** Quick CLI/parallel modules
- **Part 2:** Perf/pre/config sweep
- **Part 3a:** Fast gradient properties
- **Part 3b:** Slow gradient workloads (with extended 1200s timeout)

## Results Summary

### Aggregated Counts
- **Total Tests:** 53
- **Passed:** 42
- **Failed:** 1
- **Errors:** 0
- **Skipped:** 10

### Part-by-Part Breakdown

#### Part 1: Quick CLI/Parallel Modules
**Runtime:** 6.14s
**Command:**
```bash
timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part1.txt \
  -k "not gradcheck" --maxfail=0 --durations=25 \
  --junitxml ...pytest_part1.xml
```
**Results:** 21 passed, 5 skipped
**Slowest Tests:** All CLI help tests ~1s each

#### Part 2: Perf/Pre/Config Sweep
**Runtime:** 17.51s
**Command:**
```bash
timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part2.txt \
  -k "not gradcheck" --maxfail=0 --durations=25 \
  --junitxml ...pytest_part2.xml
```
**Results:** 18 passed, 4 skipped, 1 xfailed
**Slowest Tests:**
- `test_vectorization_scaling`: 2.60s
- `test_explicit_pivot_override`: 2.01s
- `test_distance_vs_close_distance_pivot_defaults`: 2.00s

#### Part 3a: Fast Gradient Properties
**Runtime:** 0.96s
**Command:**
```bash
timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part3a.txt \
  --maxfail=0 --durations=25 \
  --junitxml ...pytest_part3a.xml
```
**Results:** 2 passed
**Tests:**
- `test_property_metric_duality`: 0.07s
- `test_property_volume_consistency`: 0.04s

#### Part 3b: Slow Gradient Workloads
**Runtime:** 848.12s (14m 8s)
**Command:**
```bash
timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part3b.txt \
  --maxfail=0 --durations=25 \
  --junitxml ...pytest_part3b.xml
```
**Results:** 1 passed, 1 failed
**Tests:**
- `test_property_gradient_stability`: 845.68s ⚠️ **SLOW**
- `test_gradient_flow_simulation`: 1.59s **FAILED**

## Gradient Timing Analysis

### Critical Finding: test_property_gradient_stability
**Runtime:** 845.68s (~14.1 minutes)
**Status:** PASSED
**Issue:** Exceeds acceptable threshold (<900s per test, but very close to limit)
**Impact:** Blocks fast iteration on gradient tests; contributes to chunk 03 timeout risk

### test_gradient_flow_simulation
**Runtime:** 1.59s
**Status:** FAILED
**Error:** `AssertionError: At least one gradient should be non-zero`
**Details:** All cell parameter gradients (a,b,c,α,β,γ) returned zero magnitudes (<1e-10)
**Cluster:** C19 (gradient flow regression)

## Exit Criteria Assessment

✅ **Phase O5a-O5f:** All four shards executed successfully with proper guard
✅ **Timing data captured:** Per-test durations recorded via `--durations=25`
⚠️ **C18 performance:** `test_property_gradient_stability` timing validates slow-test classification
❌ **C19 gradient flow:** Failure confirms existing known issue

## Recommendations

1. **C18 Performance Tolerance Review:** Use the 845.68s timing as baseline for Sprint 1.5 tolerance discussion
2. **C19 Gradient Flow:** Requires dedicated debugging session (likely differentiability pipeline break)
3. **Selector Correction:** Fixed class names in part3a/part3b selectors (`TestPropertyBasedGradients`, `TestAdvancedGradients`)
4. **Future Reruns:** Four-shard workflow is validated; reuse for any chunk 03 baseline refreshes

## Artifacts

All logs and XML files stored under:
```
reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/chunks/chunk_03/
├── pytest_part1.{log,xml}
├── pytest_part2.{log,xml}
├── pytest_part3a.{log,xml}
└── pytest_part3b.{log,xml}
```

Gradcheck guard evidence copied from Attempt #69:
```
reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/gradients/
├── summary.md
└── exit_code.txt
```
