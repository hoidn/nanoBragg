# Phase B Execution Summary

**Status:** ⚠️ PARTIAL (timeout after 10 minutes)
**Timestamp:** 2025-10-10T13:24:06Z
**Bundle:** `reports/2026-01-test-suite-triage/phase_b/20251010T132406Z/`

## Execution Details
- **Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=artifacts/pytest_full.xml`
- **Runtime:** 600s (10 minutes, timeout limit)
- **Progress:** ~75% complete (reached test_gradients.py::test_gradcheck_cell_alpha)
- **Collection:** 692 tests, 1 skipped initially
- **Exit status:** Timeout (signal/interruption)

## Results (Partial)
- **Failures observed:** 34 test nodes
- **Tests executed:** ~520 (estimated from 75% progress)
- **Tests not reached:** ~172 (25% remaining)
- **Artifacts:**
  - `logs/pytest_full.log` (530 lines, truncated at timeout)
  - `artifacts/pytest_full.xml` (may be incomplete/absent)
  - `failures_raw.md` (34 observed failures catalogued)
  - `commands.txt` (reproduction command)

## Environment
- **Python:** 3.13.5
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6 (RTX 3090 available)
- **Platform:** Linux 6.14.0-29-generic
- **KMP_DUPLICATE_LIB_OK:** TRUE (set per requirement)

## Failure Patterns (Preliminary)
- **Determinism tests:** 6 failures across AT-PARALLEL-013 and AT-PARALLEL-024 (RNG/seed issues)
- **Sourcefile handling:** 6 failures in AT-SRC-001 suite (parsing/weighting)
- **Grazing incidence:** 4 failures in AT-PARALLEL-017 (extreme detector angles)
- **Detector geometry:** 5 failures (pivot behavior, conventions, initialization)
- **Debug/trace features:** 4 failures (printout, trace_pixel flags)
- **CLI flags:** 3 failures (pix0_vector, HKL/Fdump parity)
- **Lattice shape models:** 2 failures (GAUSS model, shape comparison)
- **Mixed units:** 1 failure (AT-PARALLEL-015)
- **Triclinic position:** 1 failure (AT-PARALLEL-026)
- **Dual runner tools:** 1 failure (AT-TOOLS-001 integration)
- **Minimal CLI:** 1 failure (AT-CLI-002 default_F render)

## Observations
1. **Timeout root cause:** Suite runtime exceeds 10-minute budget. Likely candidates:
   - Large detector simulations (4096×4096 tests in AT-PARALLEL-012 and similar)
   - Gradient checks with float64 (computationally intensive)
   - Parity tests running live C comparisons (double execution overhead)

2. **Device coverage:** Most tests show CPU/CUDA parametrization; CUDA availability confirmed in Phase A

3. **Skipped tests:** Minimal skipping observed in partial run (test_cli_scaling.py shows 5 skips for HKL device tests, test_configuration_consistency.py has 5 skips + 1 xfail)

4. **No collection errors:** Unlike some past runs, pytest collection succeeded cleanly

## Blockers for Phase C
- **Incomplete coverage:** Cannot classify failures for tests not reached (25% of suite unknown)
- **Missing metrics:** No final pass/fail counts, no complete --durations=25 data
- **junit XML:** May not contain complete failure details if pytest was interrupted mid-write

## Recommendations
1. **Phase C triage:** Proceed with 34 observed failures; flag "partial coverage" caveat in triage_summary.md
2. **Phase D split runs:** Divide suite into batches (e.g., `tests/test_at_*.py`, `tests/test_detector_*.py`, etc.) with individual timeouts
3. **Timeout tuning:** Increase to 30-60 minutes for future full-suite runs, or implement pytest-timeout plugin with per-test limits
4. **Fast-track analysis:** Prioritize determinism and sourcefile failures (high counts, clustered themes)
5. **Defer slow tests:** Consider marking large-detector parity tests with `@pytest.mark.slow` and excluding from default runs

## Exit Criteria Status
- ✅ Phase B1 (reporting directory) — complete
- ⚠️ Phase B2 (execute full suite) — partial (timeout)
- ⚠️ Phase B3 (extract failure list) — partial (34 failures documented)
- 🔲 Phase B4 (update fix_plan) — pending (next step)

## Next Actions
1. Update `docs/fix_plan.md` [TEST-SUITE-TRIAGE-001] Attempts History with this timestamp, runtime=600s, failures=34 (partial), artifact path
2. Proceed to Phase C with partial data; document "coverage incomplete" disclaimer
3. Capture Phase C hypothesis: split execution strategy for Phase D
