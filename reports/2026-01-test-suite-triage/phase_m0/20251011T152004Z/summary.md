# Phase M0 Test Suite Triage - Summary

**Timestamp:** 2025-10-11T15:20:04Z
**Total Tests Collected:** 687
**Total Chunks:** 10
**Total Runtime:** 993.87s (~16.6 minutes)

## Overall Results

| Metric | Count | Percentage |
|--------|-------|------------|
| **Passed** | 512 | 74.5% |
| **Failed** | 53 | 7.7% |
| **Skipped** | 136 | 19.8% |
| **xfailed** | 1 | 0.1% |

**Exit Code Summary:** 7 chunks with failures (exit=1), 3 chunks clean (exit=0)

## Per-Chunk Breakdown

| Chunk | Failed | Passed | Skipped | xfailed | Time (s) | Exit |
|-------|--------|--------|---------|---------|----------|------|
| 01 | 2 | 60 | 9 | 0 | 84.58 | 1 |
| 02 | 0 | 46 | 5 | 0 | 44.99 | 0 |
| 03 | 10 | 42 | 10 | 1 | 89.72 | 1 |
| 04 | 6 | 67 | 12 | 0 | 76.61 | 1 |
| 05 | 0 | 38 | 6 | 0 | 134.96 | 0 |
| 06 | 9 | 50 | 13 | 0 | 136.65 | 1 |
| 07 | 1 | 59 | 3 | 0 | 23.96 | 1 |
| 08 | 0 | 58 | 59 | 0 | 79.80 | 0 |
| 09 | 4 | 32 | 9 | 0 | 123.45 | 1 |
| 10 | 16 | 50 | 10 | 0 | 102.74 | 1 |
| **TOTAL** | **53** | **512** | **136** | **1** | **993.87** | - |

## Failure Categories

### 1. CLI Flag Implementation Issues (16 failures - Chunk 10)
**File:** `tests/test_cli_flags.py`
- TestPix0VectorAlias: 7 failures
- TestNoiseSuppressionFlag: 4 failures
- TestCLIIntegrationSanity: 4 failures
- TestCLIPix0Override: 1 failure

**Impact:** HIGH - New CLI features not working correctly
**Priority:** P0 - Blocking new feature adoption

### 2. Gradient Correctness Issues (10 failures - Chunk 03)
**File:** `tests/test_gradients.py`
- TestCellParameterGradients: 6 failures (cell_a, cell_b, cell_c, cell_alpha, cell_beta, cell_gamma)
- TestAdvancedGradients: 3 failures (joint_gradcheck, gradgradcheck, gradient_flow)
- TestPropertyBasedGradients: 1 failure (property_gradient_stability)

**Impact:** HIGH - Differentiability broken for optimization workflows
**Priority:** P0 - Core architectural requirement violated

### 3. Debug Output Bug (9 failures - Chunk 06)
**Files:** `tests/test_debug_trace.py`, `tests/test_oversample_autoselect.py`
- UnboundLocalError: `I_before_normalization_pre_polar` not initialized (4 failures)
- MOSFLM beam center offset logic (2 failures)
- Simulator requires non-None detector (2 failures)
- sincg performance regression: 5.8 M/s vs 10 M/s threshold (1 failure)

**Impact:** MEDIUM - Debug paths broken, affecting troubleshooting
**Priority:** P1 - Fix before next debugging session

### 4. Detector API Mismatch (6 failures - Chunk 04)
**File:** `tests/test_suite.py`
- AttributeError: 'float' object has no attribute 'to' (5 failures)
- Thread scaling performance below threshold (1 failure)

**Impact:** MEDIUM - Performance tests and device transfer broken
**Priority:** P1 - Fix Detector.to() method tensor conversion

### 5. Simulator Configuration Issues (4 failures - Chunk 09)
**Files:** `tests/test_perf_pytorch_005_cudagraphs.py`, `tests/test_at_parallel_015.py`
- TypeError: Simulator.__init__() unexpected keyword 'detector_config' (3 failures)
- Mixed units test failure (1 failure)

**Impact:** MEDIUM - API inconsistency and unit handling
**Priority:** P1 - Standardize Simulator initialization

### 6. Minor Issues (5 failures - scattered)
- Chunk 01: Source weights ignored (1), large detector tilts (1)
- Chunk 07: Detector offset preservation (1)
- Chunk 09: Mixed units comprehensive (1)
- Performance regressions (thread scaling)

**Impact:** LOW to MEDIUM
**Priority:** P2 - Address after P0/P1 blockers

## Cluster Analysis

### Implementation Bugs (Priority Order)
1. **CLI flags** (16 failures) - New feature incomplete
2. **Gradient checks** (10 failures) - Core differentiability broken
3. **Debug output** (4 failures) - UnboundLocalError in trace paths
4. **Detector.to()** (5 failures) - Device transfer API broken
5. **Simulator API** (3 failures) - Constructor parameter mismatch

### Deprecation Candidates
None identified - all failures appear to be implementation bugs requiring fixes.

## Recommendations

### Immediate Actions (P0 - Block Next Loop)
1. Fix gradient correctness (Chunk 03) - restore differentiability
2. Fix CLI flag implementation (Chunk 10) - complete new features
3. Fix debug output UnboundLocalError (Chunk 06) - restore observability

### Short-Term Actions (P1 - Next 1-2 Loops)
4. Fix Detector.to() tensor conversion (Chunk 04)
5. Standardize Simulator initialization API (Chunk 09)
6. Fix MOSFLM beam center offset logic (Chunk 06)

### Medium-Term Actions (P2 - Backlog)
7. Address performance regressions (sincg, thread scaling)
8. Review and fix mixed units handling
9. Investigate detector offset preservation edge cases

## Artifacts Location
- **Logs:** `reports/2026-01-test-suite-triage/phase_m0/20251011T152004Z/chunks/chunk_*/pytest.log`
- **XML Reports:** `reports/2026-01-test-suite-triage/phase_m0/20251011T152004Z/chunks/chunk_*/pytest.xml`
- **Commands:** `reports/2026-01-test-suite-triage/phase_m0/20251011T152004Z/commands.txt`
- **Environment:** `reports/2026-01-test-suite-triage/phase_m0/20251011T152004Z/preflight/{env.txt,pip_freeze.txt}`

## Notes
- No chunk exceeded the 360s timeout limit (longest: Chunk 06 at 136.65s)
- All chunks executed successfully on CPU with CUDA_VISIBLE_DEVICES=-1
- 59 parity matrix tests skipped in Chunk 08 (expected - require NB_RUN_PARALLEL=1)
- 1 xfailed test is expected (test_gradcheck in Chunk 03 marked as known issue)
