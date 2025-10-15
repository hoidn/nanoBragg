# CLUSTER-CLI-001 Resolution Summary

**Timestamp:** 2025-10-15T131048Z  
**Status:** ✅ RESOLVED (assets already present, tests passing)  
**Exit Code:** 0

## Objective
Verify and document that the golden assets required by CLI flag tests (`pix0_expected.json` and `scaled.hkl`) are present and tests pass.

## Evidence

### Asset Verification
Both required golden assets exist:
1. `reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json` (438 bytes)
2. `scaled.hkl` (1,350,993 bytes, 1.3MB)

SHA256 checksums recorded in `sha256.txt`.

### Test Results
**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py -k "pix0_vector_mm_beam_pivot or scaled_hkl_roundtrip"
```

**Results:**
- Total: 3 passed, 28 deselected
- Runtime: 2.71s
- Exit code: 0

**Test Details:**
1. `TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]` — PASSED
2. `TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cuda]` — PASSED
3. `TestHKLFdumpParity::test_scaled_hkl_roundtrip` — PASSED

## Resolution
The cluster was flagged as "missing golden assets" in Phase B/C triage, but investigation revealed:
- Assets were already regenerated in CLI-FLAGS-003 Phase H (October 6, 2025)
- `pix0_expected.json` was created during Phase H3b pix0 override analysis
- `scaled.hkl` was generated during Phase L1b HKL/Fdump parity work
- Tests execute without errors and all assertions pass

**Root Cause:** The Phase B test run occurred before these assets were committed or the test collection happened in an environment where the assets appeared missing temporarily. The current state shows all assets in place.

## Next Actions
1. Update `docs/fix_plan.md` to mark CLUSTER-CLI-001 as resolved
2. Reference this evidence bundle in `[CLI-FLAGS-003]` Attempts History
3. No code changes required; assets and tests are already green

## Artifacts
- `commands.txt` — Reproduction steps
- `env.txt` — Environment snapshot
- `pytest.log` — Full test output
- `sha256.txt` — Asset checksums
- `run_exit_code.txt` — Test exit code (0)

## References
- `cluster_CLUSTER-CLI-001.md` — Initial cluster brief
- `docs/development/testing_strategy.md §2.3` — Golden data regeneration
- `plans/active/cli-noise-pix0/plan.md` — Phase H work context
