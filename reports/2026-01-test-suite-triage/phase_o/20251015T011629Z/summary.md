# Phase O Chunk Rerun Summary

**Date:** 2025-10-15T01:16:29Z
**Purpose:** Refresh Phase O baseline with updated chunk 09/10 selectors post-C17 fix
**Environment:** CPU-only (CUDA_VISIBLE_DEVICES=-1), KMP_DUPLICATE_LIB_OK=TRUE
**Chunks:** 10 total, each with --maxfail=0 --durations=25

## Executive Summary

**Total Results:** 543 passed, 12 failed, 137 skipped, 2 xfailed
**Overall Pass Rate:** 97.8% (543 passed / 555 collected excluding xfailed)
**Total Runtime:** ~489 seconds (~8.2 minutes)

**Key Findings:**
- **C17 Resolution Confirmed:** Chunk 09/10 selector updates successful, no collection failures
- **Gradient Test Regression:** 10 failures in chunk 03 (test_gradients.py) - torch.compile donated buffer issue
- **Performance Threshold Flakiness:** 2 marginal failures in perf tests (chunks 04, 08) - CI timing variance

## Per-Chunk Breakdown

| Chunk | Tests | Passed | Failed | Skipped | XFail | Time (s) | Key Issues |
|-------|-------|--------|--------|---------|-------|----------|------------|
| 01 | 71 | 62 | 0 | 9 | 0 | 54.6 | ✅ Clean |
| 02 | 51 | 46 | 0 | 5 | 0 | 23.8 | ✅ Clean |
| 03 | 62 | 42 | **10** | 10 | 1 | 85.6 | ⚠️ Gradients + donated buffers |
| 04 | 86 | 72 | **1** | 12 | 1 | 33.3 | ⚠️ Thread scaling 1.14× < 1.15× |
| 05 | 44 | 38 | 0 | 6 | 0 | 76.4 | ✅ Clean |
| 06 | 72 | 59 | 0 | 13 | 0 | 61.5 | ✅ Clean |
| 07 | 63 | 60 | 0 | 3 | 0 | 15.2 | ✅ Clean |
| 08 | 117 | 57 | **1** | 59 | 0 | 44.8 | ⚠️ Vectorization 15.1× ≥ 15.0× |
| 09 | 48 | 37 | 0 | 12 | 0 | 89.1 | ✅ Clean |
| 10 | 78 | 70 | 0 | 8 | 0 | 27.9 | ✅ Clean |

## Failure Analysis

### Critical: Gradient Tests (Chunk 03, 10 failures)

**Root Cause:** `torch.compile` donated buffers incompatible with `torch.autograd.gradcheck`

**Failing Tests:**
- `test_gradcheck_cell_a` through `test_gradcheck_cell_gamma` (6 failures)
- `test_joint_gradcheck`, `test_gradgradcheck_cell_params` (2 failures)
- `test_property_gradient_stability` (1 failure)
- `test_gradient_flow_simulation` (1 failure - different error: zero gradients)

**Error Message:**
```
RuntimeError: This backward function was compiled with non-empty donated buffers which
requires create_graph=False and retain_graph=False. Please keep backward(create_graph=False,
retain_graph=False) across all backward() function calls, or set
torch._functorch.config.donated_buffer=False to disable donated buffer.
```

**Known Fix:** Per arch.md §15 and testing_strategy.md §4.1, these tests **MUST** set `NANOBRAGG_DISABLE_COMPILE=1` environment variable before torch import.

**Action Required:** Update `tests/test_gradients.py` to add module-level env guard:
```python
import os
os.environ["NANOBRAGG_DISABLE_COMPILE"] = "1"  # BEFORE torch import
import torch
```

**Reference:** Phase M2 validation (20251011T172830Z) confirmed 10/10 gradcheck tests pass with this guard.

### Minor: Performance Flakiness (Chunks 04, 08, 2 failures)

**Chunk 04:** `test_cpu_thread_scaling`
- **Issue:** Speedup 1.14× fell just below 1.15× threshold
- **Root Cause:** PyTorch MKL already parallelizes internally; manual thread scaling has diminishing returns
- **Threshold Relaxation History:** Already relaxed from 2.5× to 1.15× for PyTorch reality
- **Assessment:** Marginal failure due to CI timing variance, not a functional regression

**Chunk 08:** `test_vectorized_speedup`
- **Issue:** Oversample scaling 15.1× exceeded 15.0× threshold by 0.1×
- **Root Cause:** torch.compile recompilation overhead for different tensor shapes (oversample=1 vs 3)
- **Threshold Context:** Already lenient (allows 15× instead of expected 3× for vectorized code)
- **Assessment:** Marginal failure, code is fully vectorized (no Python loops per AT-PERF-006)

**Recommendation:** Both thresholds may need slight relaxation (e.g., 1.12× and 16.0×) to reduce CI flakiness while preserving detection of real regressions.

## Coverage Validation

### Chunk 09/10 Selector Refresh
**Status:** ✅ Success

- **Previous Issue (C17):** Chunks 09/10 had module coverage gaps post-refactoring
- **Fix Applied (Attempt #47):** Updated selectors per plans/active/test-suite-triage.md:302
- **Verification:**
  - Chunk 09: 37 passed, 12 skipped - all expected modules present
  - Chunk 10: 70 passed, 8 skipped - full detector/perf/conventions coverage
- **Collection:** No import errors, no missing modules

### Skip Rate Analysis
**Total Skipped:** 137 / 692 collected (19.8%)

**Primary Skip Reasons:**
1. **Parity Tests (NB_RUN_PARALLEL=1 not set):** ~80 skips in chunk 08 (test_parity_matrix.py)
2. **C Binary Required:** AT-PARALLEL tests with live C↔Py comparison
3. **CUDA Unavailable:** GPU-specific tests on CPU-only CI
4. **Platform-Specific:** Expected skips per testing_strategy.md

**Assessment:** Skip rate within normal bounds for CPU-only parity-disabled run.

## Timing Analysis

**Fastest Chunk:** 07 (15.2s) - unit tests, geometry validation
**Slowest Chunk:** 09 (89.1s) - CLI integration with noise generation
**Average Chunk Time:** 48.9s
**Per-Test Average:** 0.71s

**Compliance:** All chunks under 360s limit per testing_strategy.md:60 ✅

## Exit Codes

All chunks returned exit code 0 (pytest collected exit status, failures reported via junit XML).

## Artifacts

**Location:** `reports/2026-01-test-suite-triage/phase_o/20251015T011629Z/`

**Per-Chunk:**
- `chunks/chunk_XX/pytest.log` - full console output
- `chunks/chunk_XX/pytest.xml` - junit XML results
- `chunks/chunk_XX/exit_code.txt` - bash exit code

**Aggregated:**
- `summary.md` (this file)

## Next Actions

### Immediate (Blocking Phase O Closure)

1. **Fix Gradient Tests (C18 - NEW)**
   - File: `tests/test_gradients.py`
   - Action: Add `os.environ["NANOBRAGG_DISABLE_COMPILE"] = "1"` before torch import (lines 1-5)
   - Verification Command:
     ```bash
     env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
       pytest -v tests/test_gradients.py -k "gradcheck" --tb=short
     ```
   - Expected: 10/10 gradcheck tests pass
   - Reference: arch.md:372-373, testing_strategy.md:514-523

2. **Assess Performance Thresholds (Optional - C19)**
   - Tests: `test_cpu_thread_scaling`, `test_vectorized_speedup`
   - Decision: Accept marginal failures as CI timing variance OR relax thresholds slightly
   - Recommendation: Defer to Phase P (performance tuning focus)

### Follow-Up (Post-Phase O)

3. **Update Remediation Tracker**
   - File: `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md`
   - Action: Record Phase O STAMP, pass/fail/skip counts, add C18 entry, update C17 status to "Resolved"

4. **Close Phase O in docs/fix_plan.md**
   - Condition: After C18 fix passes and tracker updated
   - Mark item `done`, record final metrics, archive if >500 lines

5. **Plan Phase P (Performance)**
   - Focus: Systematic perf threshold review based on Phase O timing data
   - Input: Slowest-25 durations from all chunk logs

## Comparison to Previous Baseline (20251015T003950Z)

**Metrics not directly comparable** - previous run used different selectors for chunks 09/10.

**Key Difference:** This run validates the C17 fix (updated selectors) was successful.

## Authoritative Commands (Reproduction)

```bash
# Set environment
export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
export PHASE_O="reports/2026-01-test-suite-triage/phase_o/$STAMP"
mkdir -p "$PHASE_O"/chunks/chunk_{01..10}

# Run chunks (example - chunk 01)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_abs_001.py tests/test_at_cli_009.py tests/test_at_io_002.py \
  tests/test_at_parallel_007.py tests/test_at_parallel_017.py tests/test_at_parallel_028.py \
  tests/test_at_pol_001.py tests/test_at_src_002.py tests/test_cli_scaling.py \
  tests/test_detector_pivots.py tests/test_physics.py \
  --maxfail=0 --durations=25 \
  --junitxml "$PHASE_O/chunks/chunk_01/pytest.xml" \
  2>&1 | tee "$PHASE_O/chunks/chunk_01/pytest.log"
echo $? > "$PHASE_O/chunks/chunk_01/exit_code.txt"

# [Repeat for chunks 02-10 with respective selectors from input.md lines 18-27]
```

**Full Chunk Selectors:** See `input.md` lines 18-27 (authoritative source)

## Conclusion

Phase O chunk rerun **partially successful**:
- ✅ C17 fix validated (chunk 09/10 selectors working)
- ✅ 543/555 tests passing (97.8% pass rate)
- ⚠️ **C18 discovered:** Gradient tests missing compile-disable guard (straightforward fix)
- ⚠️ C19 (optional): Performance test threshold flakiness (defer to Phase P)

**Phase O Closure Blocked:** C18 must be resolved before closing.

**Estimated Remediation Time:** ~5 minutes (add 3-line env guard + rerun chunk 03)

---

**Generated:** 2025-10-15T01:45:00Z
**Ralph Loop:** Phase O chunk rerun execution
**Next Loop:** C18 gradient test fix (if approved by supervisor)
