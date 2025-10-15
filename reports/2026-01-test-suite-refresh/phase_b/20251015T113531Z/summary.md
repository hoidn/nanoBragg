# Phase B: Full Pytest Suite Execution — Summary

**STAMP:** 20251015T113531Z
**Date:** 2025-10-15
**Phase:** B (Full-suite guarded run)
**Initiative:** TEST-SUITE-TRIAGE-002

## Execution Command

```bash
timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
  NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" \
  pytest -vv tests/ --junitxml=pytest.junit.xml
```

## Results Summary

**Exit Code:** 1 (failures present)
**Runtime:** 1653.41s (27 min 33 s)
**Timeout Budget:** 3600s (1 hour) — 1946.59s spare (54.1% margin)

### Test Counts

| Metric | Count | Percentage |
|--------|-------|------------|
| **Collected** | 692 | 100% |
| **Passed** | 540 | 78.0% |
| **Failed** | 8 | 1.2% |
| **Skipped** | 143 | 20.7% |
| **XFailed** | 2 | 0.3% |
| **Collection Skipped** | 1 | N/A |
| **Warnings** | 6 | N/A |

### Key Metrics

- **Pass Rate:** 78.0% (540/692)
- **Failure Rate:** 1.2% (8/692)
- **Collection Success:** 100% (692/692, no import errors)
- **Runtime Efficiency:** Completed in 46.0% of timeout budget
- **Stability:** No timeouts during execution (test suite completed normally)

## Failure Breakdown

### F1: C-Reference Integration Failures (1 failure)
- `tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c`
- **Root Cause:** C reference run failed (NB_C_BIN not configured or binary missing)
- **Error:** `AssertionError: C reference run failed; assert None is not None`

### F2: Performance Threshold Violations (1 failure)
- `tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization`
- **Root Cause:** Bandwidth utilization drops below 50% threshold at larger sizes
- **Error:** `AssertionError: Bandwidth utilization decreases too much with size: 0.176 GB/s vs 0.364 GB/s; assert 0.176 >= (0.364 * 0.5)`

### F3: Tooling Integration Failures (1 failure)
- `tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration`
- **Root Cause:** `nb_compare.py` script path resolution failure (incorrect CWD or missing script)
- **Error:** `assert 2 in [0, 3]; CompletedProcess returncode=2: can't open file 'scripts/nb_compare.py'`

### F4: CLI Test Infrastructure Gaps (2 failures)
- `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]`
  - **Root Cause:** Missing golden reference file `reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json`
  - **Error:** `FileNotFoundError: [Errno 2] No such file or directory`

- `tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip`
  - **Root Cause:** Missing `scaled.hkl` output file (CLI invocation or file I/O issue)
  - **Error:** `AssertionError: Missing scaled.hkl; assert False`

### F5: Gradient Test Timeout (1 failure)
- `tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability`
- **Root Cause:** Test exceeded 905s timeout (known slow-gradient test)
- **Error:** `Failed: Timeout (>905.0s) from pytest-timeout`
- **Context:** Phase Q (2025-10-15T071423Z) validated this test passes with 839.14s runtime; 905s tolerance approved. **This timeout is unexpected and indicates regression.**

### F6: Dtype Mismatch Errors (2 failures)
- `tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar`
- `tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire`
- **Root Cause:** Float32/Float64 dtype mismatch in tricubic interpolation vectorization
- **Error:** `RuntimeError: Float did not match Double`

## Environment

**Inherited from Phase A (STAMP 20251015T113531Z):**
- Python: 3.13.5
- PyTorch: 2.7.1+cu126
- CUDA: 12.6 (available but disabled via `CUDA_VISIBLE_DEVICES=-1`)
- GPU: RTX 3090 (CUDA execution disabled for CPU-only determinism)
- OS: Linux 6.14.0-29-generic

**Guard Variables:**
- `CUDA_VISIBLE_DEVICES=-1` ✅ (CPU-only execution)
- `KMP_DUPLICATE_LIB_OK=TRUE` ✅ (MKL conflict prevention)
- `NANOBRAGG_DISABLE_COMPILE=1` ✅ (torch.compile disabled for gradcheck compatibility)
- `PYTEST_ADDOPTS="--maxfail=200 --timeout=905"` ✅ (failure cap + per-test timeout)

## Observations

### Improvements vs Historical Baselines

**Comparison to TEST-SUITE-TRIAGE-001 Phase R (2025-10-15T102654Z):**
- **Baseline:** 43 passed / 9 skipped / 1 xfailed / 0 failures (chunk 03 only, ~50 tests)
- **This run:** 540 passed / 143 skipped / 2 xfailed / 8 failures (full suite, 692 tests)
- **Net Change:** New full-suite baseline established; no direct chunk comparison available

**Comparison to TEST-SUITE-TRIAGE-001 Phase K (2025-10-11T072940Z):**
- **Baseline:** 512 passed / 31 failed / 143 skipped / 2 xfailed (687 collected)
- **This run:** 540 passed / 8 failed / 143 skipped / 2 xfailed (692 collected)
- **Net Change:** +28 passed (+5.5%), -23 failures (-74.2%), +5 collected tests (+0.7%)
- **Significant improvement:** 74% reduction in failures (31→8)

### New vs Known Failures

| Category | New in Phase B? | Notes |
|----------|-----------------|-------|
| F1 (C-reference) | Yes | C binary integration not configured |
| F2 (perf threshold) | Yes | New bandwidth degradation detected |
| F3 (tooling) | Yes | Script path resolution issue |
| F4 (CLI infrastructure) | Partial | pix0_expected.json may be new; scaled.hkl likely pre-existing |
| F5 (gradient timeout) | **YES (CRITICAL)** | Regression vs Phase Q validation (839.14s) |
| F6 (dtype mismatch) | Yes | Tricubic vectorization dtype handling regression |

### Runtime Characteristics

- **Gradient test dominance:** No detailed breakdown in this summary, but historical data (Phase K) suggests ~1660s of 1653s runtime (>100% paradox indicates parallel execution or measurement artifact). Gradient tests typically comprise ~90% of wall-clock time.
- **Timeout handling:** Suite completed normally without global timeout. One test (F5) breached per-test 905s limit.
- **Collection stability:** 692/692 tests collected successfully (100%), no import errors.

## Artifacts

All artifacts stored under `reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/`:

- ✅ `commands.txt` — Exact reproduction command
- ✅ `pytest.log` — Full verbose output (1562 lines)
- ✅ `pytest.junit.xml` — JUnit XML report (137K)
- ✅ `run_exit_code.txt` — Exit code (1)
- ✅ `env.txt` — Environment snapshot (inherited from Phase A)
- ✅ `summary.md` — This file

## Phase B Tasks Status

Per `plans/active/test-suite-triage-rerun.md`:

- ✅ **B1:** Create Phase B directory structure with STAMP 20251015T113531Z
- ✅ **B2:** Execute guarded full suite with timeout/env guards
- ✅ **B3:** Capture `pytest.log`, junit XML, exit code, and timing data
- ✅ **B4:** Draft Phase B summary with pass/fail/skip counts and artifact inventory

**Phase B Status:** ✅ COMPLETE

## Next Actions (Phase C)

Per plan `plans/active/test-suite-triage-rerun.md` §Phase C:

1. **Cluster Failures:** Extract the 8 failures into thematic groups (C-integration, performance, tooling, CLI, gradient regression, dtype issues)
2. **Map to Prior IDs:** Cross-reference Phase B failures against `docs/fix_plan.md` entries and TEST-SUITE-TRIAGE-001 historical clusters
3. **Draft Triage Summary:** Create `phase_c/20251015T113531Z/triage_summary.md` with:
   - Per-cluster failure descriptions
   - Reproduction commands
   - Spec/arch citation for expected behavior
   - Blocker/dependency analysis
   - Owner/priority assignment
4. **Update Fix Plan:** Refresh Next Actions in `docs/fix_plan.md` [TEST-SUITE-TRIAGE-002] entry with Phase C artifact links and remediation sequencing

**Critical Findings for Phase C:**

- **F5 (gradient timeout) is a BLOCKER:** Phase Q validation (2025-10-15T071423Z) confirmed 839.14s runtime with 6.7% margin below 905s ceiling. This test timing out at 905s indicates a >7.8% performance regression since Phase Q.
- **F6 (dtype mismatch) is NEW:** Tricubic vectorization dtype handling was not flagged in TEST-SUITE-TRIAGE-001 Phase K (2025-10-11T072940Z). This suggests recent code changes introduced the regression.
- **F1/F3/F4 are infrastructure gaps:** Not code regressions; require environment setup (C binary path, script paths, golden reference files).

## Recommendations

1. **Immediate (Phase C triage):**
   - Prioritize F5 gradient timeout investigation (performance regression vs Phase Q)
   - Classify F6 dtype mismatch as high-priority vectorization regression
   - Classify F1/F3/F4 as infrastructure setup issues (medium priority)

2. **Remediation sequencing:**
   - **Sprint 0:** Resolve infrastructure gaps (F1/F3/F4) to unblock C-parity and tooling tests
   - **Sprint 1:** Investigate F5 gradient timeout (critical regression vs approved tolerance)
   - **Sprint 2:** Fix F6 dtype handling in tricubic vectorization
   - **Sprint 3:** Review F2 performance threshold (may be test-side tolerance issue vs real regression)

3. **Evidence requirements:**
   - F5: Run targeted gradient test with detailed timing trace to identify performance degradation source
   - F6: Inspect `test_tricubic_vectorized.py` changes since Phase K baseline
   - F2: Profile memory bandwidth test across multiple runs to assess flakiness vs systematic degradation

---

**Phase B Execution:** ✅ SUCCESS
**Full-suite baseline:** 540/8/143/2 (passed/failed/skipped/xfailed)
**Ready for Phase C triage**
