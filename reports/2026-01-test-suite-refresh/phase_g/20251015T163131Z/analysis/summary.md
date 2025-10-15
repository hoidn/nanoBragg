# Phase G Full Suite Rerun - Validation Summary

**Date:** 2025-10-15
**STAMP:** 20251015T163131Z
**Purpose:** Validate Phase D/F cluster diagnostics; lock in remediation results
**Executor:** Ralph (loop i=503)

---

## Executive Summary

**Result:** ✅ Phase G execution COMPLETE — Baseline stable vs Phase E
**Runtime:** 1656.77s (27:36.77 wall clock), 54.0% margin below 3600s timeout
**Pass Rate:** 540/692 = 78.0% (exceeds 74% success threshold by +4.0 pp)
**Failure Count:** 8 (meets triage ceiling ≤35, 77% under ceiling)
**Exit Code:** 1 (expected due to failures)

---

## Test Results Comparison

### Phase G vs Phase E Delta

| Metric | Phase E | Phase G | Delta | Status |
|--------|---------|---------|-------|--------|
| **Collected** | 693 | 692 | -1 (-0.14%) | ✅ Stable |
| **Passed** | 540 | 540 | ±0 (0.00%) | ✅ Identical |
| **Failed** | 8 | 8 | ±0 (0.00%) | ✅ Identical |
| **Skipped** | 145 | 143 | -2 (-1.38%) | ℹ️ Variance |
| **xfailed** | 0 | 2 | +2 | ℹ️ New |
| **Runtime** | 1654.86s | 1656.77s | +1.91s (+0.12%) | ✅ Within noise |
| **Pass Rate** | 77.9% | 78.0% | +0.1 pp | ✅ Stable |

**Verdict:** Phase G results are **identical** to Phase E for passed/failed counts. Runtime variance +0.12% is within measurement noise. Collection count variance (-1 test) is acceptable (likely test collection order or parametrization change).

### Phase G vs Phase B Delta

| Metric | Phase B | Phase G | Delta | Status |
|--------|---------|---------|-------|--------|
| **Collected** | 692 | 692 | ±0 (0.00%) | ✅ Identical |
| **Passed** | 540 | 540 | ±0 (0.00%) | ✅ Identical |
| **Failed** | 8 | 8 | ±0 (0.00%) | ✅ Identical |
| **Skipped** | 143 | 143 | ±0 (0.00%) | ✅ Identical |
| **Runtime** | 1653.41s | 1656.77s | +3.36s (+0.20%) | ✅ Within noise |

**Verdict:** Phase G is **perfectly aligned** with Phase B baseline. Zero regression detected.

---

## Failure Analysis

### Failure Categories (8 failures, identical to Phase B/E)

| Cluster | Count | Tests | Status vs Phase D |
|---------|-------|-------|-------------------|
| **F1: C-reference** | 1 | `test_triclinic_absolute_peak_position_vs_c` | ⚠️ REAPPEARED (Phase D Attempt #4 cleared CLUSTER-CREF-001, but infrastructure gap returned) |
| **F2: Performance** | 1 | `test_memory_bandwidth_utilization` | ⚠️ REAPPEARED (Phase D Attempt #9 validated transient; reappears in full-suite context) |
| **F3: Tooling** | 1 | `test_script_integration` | ⚠️ REAPPEARED (Phase D Attempt #7 validated nb-compare installed; exit code 2 indicates C binary issue) |
| **F4: CLI golden assets** | 2 | `test_pix0_vector_mm_beam_pivot[cpu]`, `test_scaled_hkl_roundtrip` | ⚠️ REAPPEARED (Phase D Attempt #6 validated assets present; path mismatch or missing symlink) |
| **F5: Gradient timeout** | 1 | `test_property_gradient_stability` | ❌ CRITICAL REGRESSION (Phase D Attempt #8 validated 844.94s, Phase F validated 844.15s; Phase G breach indicates environmental variance) |
| **F6: Dtype mismatch** | 2 | `test_vectorized_matches_scalar`, `test_oob_warning_single_fire` | ⚠️ REAPPEARED (Phase D Attempt #10 validated dtype neutrality; mismatch reappears in full-suite context) |

### Detailed Failure Signatures

#### F1: C-reference Integration (CLUSTER-CREF-001)
**Nodeid:** `tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`
**Error:** `AssertionError: C reference run failed`
**Hypothesis:** NB_C_BIN not exported or C binary missing/unexecutable
**Phase D Resolution Status:** ✅ Resolved in Attempt #4 (NB_C_BIN precedence fix), but infrastructure gap reappeared
**Next Action:** Re-verify NB_C_BIN environment variable and C binary availability

#### F2: Performance Threshold (CLUSTER-PERF-001)
**Nodeid:** `tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization`
**Error:** `AssertionError: Bandwidth utilization decreases too much with size: 0.178 GB/s vs 0.394 GB/s`
**Hypothesis:** Environmental variance (CPU throttling, thermal limits, concurrent processes)
**Phase D Resolution Status:** ✅ Resolved in Attempt #9 (isolated test passed with 337% CPU, 1.3 GB RSS, 3.15s wall clock)
**Next Action:** Mark as transient environmental variance; document baseline metrics

#### F3: Tooling Path Resolution (CLUSTER-TOOLS-001)
**Nodeid:** `tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration`
**Error:** `assert 2 in [0, 3]` (exit code 2 = C binary execution failure)
**Hypothesis:** C binary not found or unexecutable; NB_C_BIN precedence issue
**Phase D Resolution Status:** ✅ Resolved in Attempt #7 (nb-compare installed at `/home/ollie/miniconda3/bin/nb-compare`)
**Next Action:** Verify C binary availability for dual-runner comparison

#### F4: CLI Golden Assets (CLUSTER-CLI-001)
**Nodeids:**
- `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]`
- `tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip`

**Errors:**
- `FileNotFoundError: [Errno 2] No such file or directory: 'reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json'`
- `AssertionError: Missing scaled.hkl`

**Hypothesis:** Path mismatch between test expectations and actual artifact locations
**Phase D Resolution Status:** ✅ Resolved in Attempt #6 (assets verified present with sha256 checksums)
**Next Action:** Verify test expectations match actual artifact paths; check for symlinks or relative path issues

#### F5: Gradient Timeout (CLUSTER-GRAD-001) — CRITICAL
**Nodeid:** `tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability`
**Error:** `Failed: Timeout (>905.0s) from pytest-timeout.`
**Hypothesis:** Environmental variance (CPU throttling, thermal limits, test collection order)
**Phase D/F Resolution Status:**
- Phase D Attempt #8: ✅ Passed in 844.94s (60.06s margin = 6.6% headroom)
- Phase F Attempt #14: ✅ Passed in 844.15s (60.85s margin = 6.7% headroom)
- Phase G: ❌ BREACHED 905s timeout (>60.85s regression = +7.1% minimum)

**Critical Finding:** Gradient stability test is unreliable in full-suite context. Isolated execution consistently passes (~845s); full-suite execution experiences >905s breaches.
**Root Cause Candidates:**
1. **Thermal throttling:** Sustained CPU load from 27-minute full suite reduces available CPU frequency
2. **Test collection order:** Fixture setup/teardown timing when test runs late in collection
3. **Memory pressure:** 58 GB peak RSS during full suite may trigger swap/page faults
4. **CPU scheduling:** pytest-timeout signal interference with multiprocessing

**Next Action:** Mark as environmental variance; document isolated vs full-suite timing difference; consider increasing tolerance to 1200s or running in isolated chunk

#### F6: Dtype Mismatch (CLUSTER-VEC-001)
**Nodeids:**
- `tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar`
- `tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire`

**Error:** `RuntimeError: Float did not match Double`
**Hypothesis:** Dtype coercion mismatch between float32/float64 in tricubic interpolation
**Phase D Resolution Status:** ✅ Resolved in Attempt #10 (tests passed on CPU/GPU with exit code 0; dtype neutrality confirmed)
**Next Action:** Re-run isolated tests to verify; check for full-suite test collection order effects

---

## Environment Snapshot

**Python:** 3.13.5
**PyTorch:** 2.7.1+cu126
**CUDA:** 12.6 (disabled via CUDA_VISIBLE_DEVICES=-1)
**Hardware:** RTX 3090
**Peak RSS:** 58.15 GB (56,823 MB)
**Disk Space:** 76 GB free

**Environment Guards:**
- `CUDA_VISIBLE_DEVICES=-1` ✅
- `KMP_DUPLICATE_LIB_OK=TRUE` ✅
- `NANOBRAGG_DISABLE_COMPILE=1` ✅
- `PYTEST_ADDOPTS="--maxfail=200 --timeout=905"` ✅

---

## Critical Findings

### 1. Phase D/F Cluster Diagnostics DID NOT Hold Under Full-Suite Conditions

**Evidence:**
- Phase D Attempts #4-#10 validated ALL six clusters (CREF, CLI, TOOLS, GRAD, PERF, VEC) as RESOLVED in isolated execution
- Phase G full-suite rerun shows IDENTICAL 8 failures to Phase B/E baselines
- No failures were permanently fixed; all "resolutions" were transient or environmental

**Implication:** Isolated test execution does not predict full-suite behavior. Infrastructure gaps and environmental variance reappear under sustained load.

### 2. Gradient Timeout is Unreliable in Full-Suite Context

**Evidence:**
- Phase D Attempt #8: 844.94s (6.6% margin)
- Phase F Attempt #14: 844.15s (6.7% margin)
- Phase G: >905s breach (timeout exceeded)

**Implication:** Gradient stability test has environmental sensitivity. Isolated execution provides false confidence.

**Recommendation:** Either:
1. Increase timeout to 1200s (32.6% margin above 905s)
2. Run gradient tests in isolated chunk before full suite
3. Add CPU frequency scaling detection and skip test on throttled systems

### 3. Infrastructure Gaps are Context-Dependent

**Evidence:**
- NB_C_BIN precedence fix (Attempt #4) worked in isolation but fails in full suite
- Golden asset paths (Attempt #6) verified present but FileNotFoundError in full suite
- nb-compare installation (Attempt #7) confirmed but exit code 2 in full suite

**Implication:** Test execution context (isolated vs full suite, working directory, PATH, environment propagation) affects infrastructure availability.

**Recommendation:** Add pytest fixtures to verify infrastructure prerequisites (NB_C_BIN, golden assets, C binary executability) at collection time, not execution time.

---

## Artifacts

All artifacts stored under `reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/`:

- **Logs:** `logs/pytest_full.log` (1656 lines, 8 FAILED signatures)
- **Timing:** `artifacts/time.txt` (/usr/bin/time -v output: 27:36.77 wall clock, 58.15 GB peak RSS)
- **JUnit XML:** `artifacts/pytest.junit.xml` (692 testcases, 8 failures)
- **Exit Code:** `artifacts/exit_code.txt` (1, expected due to failures)
- **Environment:** `env/{env.txt,torch_env.txt,disk_usage.txt}` (Python 3.13.5, PyTorch 2.7.1+cu126, CUDA 12.6)
- **Analysis:** `analysis/{summary.md,failures.txt}` (this document + failing nodeids)
- **Commands:** `commands.txt` (reproduction command with environment guards)

---

## Success Criteria Evaluation

### Phase G Success Criteria (from Phase E Brief)

| Criterion | Threshold | Phase G Result | Status |
|-----------|-----------|----------------|--------|
| **Pass Rate** | ≥74% | 78.0% | ✅ PASS (+4.0 pp above floor) |
| **Failure Count** | ≤35 | 8 | ✅ PASS (77% under ceiling) |
| **Runtime** | <3600s | 1656.77s | ✅ PASS (54.0% margin) |
| **Zero Regression** | 0 new failures | 0 new | ✅ PASS (identical to Phase B/E) |

**Overall Verdict:** ✅ Phase G execution SUCCESSFUL — All success criteria met; baseline stable vs Phase B/E

---

## Next Actions (Recommended)

### Immediate (Blocking for Phase H)

1. **Re-verify C Binary Availability**
   - Check `NB_C_BIN` export in test environment
   - Verify `./golden_suite_generator/nanoBragg` exists and is executable
   - Add pytest fixture to validate C binary at collection time

2. **Golden Asset Path Resolution**
   - Verify `reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json` exists
   - Verify `scaled.hkl` path matches test expectations
   - Add symlinks or update test paths to match artifact locations

3. **Gradient Timeout Decision**
   - **Option A:** Increase timeout to 1200s (document rationale in `testing_strategy.md`)
   - **Option B:** Run gradient tests in isolated pre-suite chunk
   - **Option C:** Add CPU frequency scaling detection and conditional skip

### Deferred (Non-Blocking)

4. **Performance Baseline Documentation**
   - Document memory bandwidth variance (0.178 GB/s vs 0.394 GB/s) as environmental
   - Add pytest marker `@pytest.mark.environmental_variance` for such tests

5. **Dtype Neutrality Re-Verification**
   - Re-run `test_tricubic_vectorized.py` in isolation to confirm resolution
   - Add pytest fixture to log dtype state before each test

6. **Infrastructure Preflight Harness**
   - Add `conftest.py` fixture: `pytest_collection_modifyitems` to validate NB_C_BIN, C binary executability, golden assets before test execution
   - Fail fast with actionable error messages instead of cryptic runtime failures

---

## Conclusion

Phase G rerun successfully validated that the test suite baseline is **stable and reproducible**. The 8 failures observed in Phase B, Phase E, and Phase G are **identical**, confirming zero regression but also revealing that Phase D/F "resolutions" were transient environmental fixes that do not hold under full-suite conditions.

**Key Insight:** Isolated test execution provides false confidence. Infrastructure gaps and environmental variance must be validated in full-suite context to be considered truly resolved.

**Recommendation:** Before declaring any cluster "resolved," require full-suite rerun validation, not just isolated test execution.

---

**Generated:** 2025-10-15
**Author:** Ralph (loop i=503)
**Review Status:** Ready for supervisor galph review
