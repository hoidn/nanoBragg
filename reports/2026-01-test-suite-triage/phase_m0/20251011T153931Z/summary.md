# Phase M0 Full Suite Baseline Summary

**Date:** 2025-10-11
**Initiative:** TEST-SUITE-TRIAGE-001
**Phase:** M0 - Directive Compliance Baseline
**Timestamp:** 20251011T153931Z

## Executive Summary

Complete test suite execution across 10 chunks with 687 tests collected.

### Overall Results

| Metric | Value |
|--------|-------|
| **Total Tests Collected** | 687 |
| **Total Executed** | 616 (chunks 01-10) |
| **Passed** | 504 (81.8%) |
| **Failed** | 46 (7.5%) |
| **Skipped** | 136 (22.1%) |
| **Total Duration** | ~502s (~8.4 minutes) |
| **Chunks with Failures** | 7/10 |

### Chunk-by-Chunk Results

| Chunk | Tests | Passed | Failed | Skipped | Duration | Exit Code | Status |
|-------|-------|--------|--------|---------|----------|-----------|--------|
| 01 | 71 | 60 | 2 | 9 | 52.89s | 1 | ✗ FAILURE |
| 02 | 51 | 46 | 0 | 5 | 23.66s | 0 | ✓ SUCCESS |
| 03 | 62 | 42 | 10 | 10 | 85.24s | 1 | ✗ FAILURE |
| 04 | 85 | 68 | 5 | 12 | 32.81s | 1 | ✗ FAILURE |
| 05 | 44 | 38 | 0 | 6 | 76.14s | 0 | ✓ SUCCESS |
| 06 | 72 | 51 | 8 | 13 | 61.91s | 1 | ✗ FAILURE |
| 07 | 63 | 59 | 1 | 3 | 15.19s | 1 | ✗ FAILURE |
| 08 | 117 | 58 | 0 | 59 | 44.74s | 0 | ✓ SUCCESS |
| 09 | 45 | 32 | 4 | 9 | 71.08s | 1 | ✗ FAILURE |
| 10 | 76 | 50 | 16 | 10 | 38.87s | 1 | ✗ FAILURE |

### Environment

- **Python:** (captured in `preflight/env.txt`)
- **PyTorch:** (captured in `preflight/env.txt`)
- **CUDA:** Disabled (CUDA_VISIBLE_DEVICES=-1)
- **Device:** CPU-only execution
- **KMP:** KMP_DUPLICATE_LIB_OK=TRUE

### Comparison with Previous Phase

**Previous Baseline (Phase K - 20251011T072940Z):**
- 512 passed / 31 failed / 143 skipped

**Current Baseline (Phase M0 - 20251011T153931Z):**
- 504 passed / 46 failed / 136 skipped

**Delta:**
- Passed: -8 (-1.6%)
- Failed: +15 (+48.4%)
- Skipped: -7 (-4.9%)

**Analysis:** Significant increase in failures requires detailed triage to understand regression sources.

## Failure Distribution by Test Area

Detailed failure analysis requires parsing individual chunk logs (see Phase M0c).

## Artifacts

- **Preflight:** `preflight/{collect_only.log, env.txt, pip_freeze.txt}`
- **Chunk Logs:** `chunks/chunk_NN/pytest.log` (01-10)
- **JUnit XML:** `chunks/chunk_NN/pytest.xml` (01-10)
- **Commands Log:** `commands.txt`
- **Detailed Chunk Summary:** `chunks_02_10_summary.txt`

## Next Steps (Phase M0c)

1. Parse all chunk logs to extract individual failure details
2. Classify failures: implementation bug vs deprecation candidate
3. Map failures to existing fix-plan clusters or create new entries
4. Update `docs/fix_plan.md` with Attempt #20 metadata
5. Update `remediation_tracker.md` with new baseline
6. Generate `triage_summary.md` with complete failure classification

## Notes

- All chunks completed within timeout limits (<360s per chunk)
- No execution errors or collection failures
- Environment variables properly applied (env prefix on same line)
- CPU-only execution ensured determinism
- Results ready for detailed triage (Phase M0c)
