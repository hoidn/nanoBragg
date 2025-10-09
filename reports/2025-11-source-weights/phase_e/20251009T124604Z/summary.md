# SOURCE-WEIGHT-001 Phase E2 Evidence Capture

**Date:** 2025-10-09  
**Commit:** 0ebddbd  
**Test Run:** pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v

## Executive Summary

Phase E2 test execution confirms that the SOURCE-WEIGHT-001 normalization issue remains unresolved. While TC-D2 (warning guard) PASSES, all parity tests (TC-D1, TC-D3, TC-D4) FAIL with 140–300× intensity divergence.

## Test Results

| Test Case | Status | Correlation | Sum Ratio | C Sum | PyTorch Sum |
|-----------|--------|-------------|-----------|-------|-------------|
| TC-D1 (sourcefile only) | ❌ FAILED | -0.297 | 302.6× | 179.6 | 54352.6 |
| TC-D2 (warning guard) | ✅ PASSED | N/A | N/A | N/A | N/A |
| TC-D3 (divergence grid) | ❌ FAILED | 0.070 | 141.7× | 358.2 | 50745.9 |
| TC-D4 (explicit oversample) | ❌ FAILED | -0.297 | 302.6× | 179.6 | 54352.6 |

## Acceptance Criteria (from Phase E)

| Criterion | Target | TC-D1 | TC-D3 | Status |
|-----------|--------|-------|-------|--------|
| Correlation | ≥0.999 | -0.297 | 0.070 | ❌ FAIL |
| Sum Ratio | |1-ratio| ≤1e-3 | 301.6 | 140.7 | ❌ FAIL |

## Interpretation

### TC-D2 Success (Guard Working)
The UserWarning guard added in commit 3140629 correctly fires when `-sourcefile` + `-hdivrange` are both provided. This validates Phase E1 implementation.

### TC-D1/TC-D3/TC-D4 Failure (Normalization Bug)
Despite the warning guard, the PyTorch simulator still produces 140–300× higher intensities than C reference. This indicates:

1. **Root Cause Location:** The issue is NOT in divergence auto-selection (guard proves no extra sources generated)
2. **Suspected Path:** Normalization pipeline (`steps` or `fluence` calculation) in `simulator.py`
3. **Blocking Phase E3:** Cannot proceed with C parity metrics until we diagnose PyTorch-only behavior

## Next Actions (Phase E2 Continuation)

Per plan Phase E2 blocking status, before touching tests again:

1. **PyTorch-Only Diagnostics (TC-D1)**
   - Run PyTorch CLI for TC-D1 with full stdout capture
   - Extract: `n_sources`, `steps`, `fluence` reported values
   - Compare to expected: n_sources=2, steps=2 (sourcefile + oversample=1 + mosaic=1 + phi=1)

2. **PyTorch-Only Diagnostics (TC-D3)**
   - Run PyTorch CLI for TC-D3 with full stdout capture
   - Extract: `n_sources`, `steps`, `fluence` reported values
   - Expected: n_sources=3 (hdivsteps=3), steps=3

3. **Create Diagnostic Script**
   - Add temporary trace output to `simulator.py` showing normalization factors
   - Rerun TC-D1/TC-D3 to capture intermediate values

4. **Update Plan**
   - Record diagnostic findings in `plans/active/source-weight-normalization.md` Attempt History
   - Propose normalization fix based on evidence

## Evidence Artifacts

- `pytest.log`: Full test output
- `commands.txt`: Reproduction commands
- `env.json`: Environment snapshot
- `reports/2025-11-source-weights/phase_e/*/metrics.json`: Per-test failure metrics

## References

- Plan: `plans/active/source-weight-normalization.md` Phase E2
- Spec: `specs/spec-a-core.md:142-190` (Sources normative)
- Fix Plan: `docs/fix_plan.md` [SOURCE-WEIGHT-001]
