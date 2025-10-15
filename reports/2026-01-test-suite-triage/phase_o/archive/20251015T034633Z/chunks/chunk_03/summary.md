# Phase O5 Chunk 03 Split-Run Summary

**STAMP:** 20251015T034633Z
**Date:** 2025-10-15 03:46 UTC
**Task:** TEST-SUITE-TRIAGE-001 Next Action 9 — Phase O5 split-run baseline

## Executive Summary

⚠️ **PARTIAL SUCCESS** — Part 1 completed successfully (23 passed, 5 skipped, 8.19s). Part 2 encountered timeout at 600s (10min limit) after completing ~73% of tests (19/26 visible before interruption). XML aggregation incomplete due to missing part2.xml.

## Results

### Part 1 (First 5 Test Files)
- **Duration:** 8.19s
- **Tests:** 28 total
- **Results:** 23 passed, 0 failed, 5 skipped
- **Exit Code:** 0
- **Status:** ✅ COMPLETE

**Test Files:**
- `tests/test_at_cli_001.py` (6 tests, all passed)
- `tests/test_at_flu_001.py` (8 tests, all passed)
- `tests/test_at_io_004.py` (7 tests, all passed)
- `tests/test_at_parallel_020.py` (4 tests, all skipped - NB_RUN_PARALLEL not set)
- `tests/test_at_perf_001.py` (3 tests, 2 passed, 1 skipped)

**Slowest Tests (Part 1):**
1. `test_vectorization_scaling`: 2.16s
2. CLI help tests: ~1.00s each (6 tests)

### Part 2 (Last 5 Test Files)
- **Duration:** 600s (timeout)
- **Tests:** 26 selected (from 34 collected, 8 deselected by `-k "not gradcheck"`)
- **Results (Partial):** 19 visible tests before timeout:
  - 17 passed
  - 1 failed (`test_gradient_flow_simulation`)
  - 1 xfailed (`test_explicit_defaults_equal_implicit`)
  - 5 skipped
- **Exit Code:** 124 (timeout)
- **Status:** ⚠️ INCOMPLETE (timeout at ~73% completion)

**Test Files (Visible Before Timeout):**
- `tests/test_at_pre_002.py` (6 tests, all passed)
- `tests/test_at_sta_001.py` (5 tests, all passed)
- `tests/test_configuration_consistency.py` (6 tests, 1 xfailed, 5 skipped)
- `tests/test_gradients.py` (partially complete, 3 visible: 1 failed, 2 passed)
- `tests/test_show_config.py` (status unknown, not visible in log)

**Known Failure:**
- `test_gradient_flow_simulation` FAILED (assertion-based, NOT a C2 gradcheck issue)

## Timeout Analysis

**Root Cause:** Part 2 includes `test_gradients.py` which contains multiple slow gradient property tests. The 600s timeout was insufficient despite the `-k "not gradcheck"` filter (which only excludes gradcheck tests, not all gradient tests).

**Evidence:**
- Part 2 log shows test execution stopped mid-run at line 29 (`test_property_gradient_stability` being executed)
- No pytest.xml generated (pytest interrupted before completion)
- test_gradients.py property tests can be slow even without gradcheck (metric duality, volume consistency, gradient stability)

## Aggregation Status

❌ **INCOMPLETE** — Cannot aggregate XML results because `pytest_part2.xml` was not generated (timeout interrupt).

**Partial Manual Count (Part 1 + Visible Part 2):**
- Passed: 23 + 17 = 40
- Failed: 0 + 1 = 1
- Skipped: 5 + 5 = 10
- XFailed: 0 + 1 = 1

**Estimated Total (if Part 2 had completed):**
- Expected total tests: ~54 (28 from part1 + 26 from part2)
- Visible completion: ~47/54 (87%)

## Findings

### C2 Cluster Status (Gradcheck Tests)
✅ **VALIDATION DEFERRED** — The `-k "not gradcheck"` filter successfully excluded all 8 core gradcheck tests from this run. These tests are expected to pass with `NANOBRAGG_DISABLE_COMPILE=1` guard per Phase M2 Attempt #70 validation.

### C18 Performance Cluster
⚠️ **ONE FAILURE OBSERVED** — `test_gradient_flow_simulation` FAILED in part 2. This is an assertion-based gradient flow test, NOT a gradcheck test. Requires investigation.

## Recommendations

### Option A: Split Into Thirds (Recommended)
Split chunk 03 into 3 parts instead of 2:
- Part 1: `test_at_cli_001.py`, `test_at_flu_001.py` (~8s)
- Part 2: `test_at_io_004.py`, `test_at_parallel_020.py`, `test_at_perf_001.py` (~5s)
- Part 3: `test_at_pre_002.py`, `test_at_sta_001.py`, `test_configuration_consistency.py`, `test_gradients.py`, `test_show_config.py` (~600s with margin)

**Rationale:** test_gradients.py property tests dominate runtime. Isolating them in part 3 with full 600s budget provides margin.

### Option B: Raise Timeout
Request harness timeout increase to 900s (15min) for part 2 runs containing gradient property tests.

### Option C: Further Filter Part 2
Add additional `-k` filters to exclude slow property tests: `-k "not gradcheck and not property"`. Re-run part 2 with tighter filter.

## Environment

- **Python:** 3.13.5
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6 (disabled via `CUDA_VISIBLE_DEVICES=-1`)
- **Platform:** linux 6.14.0-29-generic
- **Required Env:**
  - `CUDA_VISIBLE_DEVICES=-1` (CPU-only)
  - `KMP_DUPLICATE_LIB_OK=TRUE` (MKL conflicts)
  - `NANOBRAGG_DISABLE_COMPILE=1` (gradcheck guard)

## Artifacts

- `reports/2026-01-test-suite-triage/phase_o/20251015T034633Z/chunks/chunk_03/`
  - `pytest_part1.log` (complete, 65 lines)
  - `pytest_part1.xml` (complete, 28 tests)
  - `pytest_part2.log` (truncated at line 29, ~73% complete)
  - `part1_exit_code.txt` (0 = success)
  - `part2_exit_code.txt` (124 = timeout)
  - ❌ `pytest_part2.xml` (missing - not generated due to timeout)

## Next Actions

1. **Escalate to supervisor:** Document timeout issue in input.md response
2. **Choose mitigation:** Select Option A (thirds), Option B (raise timeout), or Option C (tighter filter)
3. **Retry:** Re-execute part 2 (or revised parts) with chosen mitigation
4. **Aggregate:** Once both parts complete, run aggregation script and update remediation_tracker.md

## References

- **Plan:** plans/active/test-suite-triage.md Phase O5a-O5e
- **Prior Attempts:** docs/fix_plan.md Attempt #71 (similar timeout), Attempt #70 (C2 validation)
- **Blocked Attempt:** reports/2026-01-test-suite-triage/phase_o/blocked_attempt_73.md
- **input.md:** Line 8 (Do Now command), Lines 54-64 (Pitfalls guidance)
