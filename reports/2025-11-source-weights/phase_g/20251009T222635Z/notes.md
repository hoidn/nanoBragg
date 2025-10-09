# Phase G Parity Evidence Bundle — Notes
**Bundle ID:** 20251009T222635Z
**Date:** 2025-10-09
**Task:** SOURCE-WEIGHT-001 Phase G1–G3

## Executive Summary

**CRITICAL FINDING**: The CLI-level parity check using the Phase A fixture (source Z=10.0) shows **divergence** between C and PyTorch, while the pytest using different parameters (source Z=-1.0) shows **convergence (XPASS)**.

### Metrics (Phase A Fixture: Z=10.0)
- **PyTorch sum:** 42,875.54
- **C sum:** 320.27
- **Sum ratio:** 133.87 (should be ~1.0 ±0.003)
- **Correlation:** 0.0297 (should be ≥0.999)

**Verdict:** C↔PyTorch **parity FAILED** for this fixture.

### Test Results (pytest with Z=-1.0)
- **test_c_divergence_reference:** XPASS (expected to fail but passed!)
- Correlation: ≥0.999 (from test logs)
- Sum ratio: ~1.0 (from test logs)

**Verdict:** C↔PyTorch **parity PASSED** for test parameters.

## Root Cause Analysis

**Parameter Mismatch**: The supervisor-requested fixture and the pytest use fundamentally different source geometries:

| Parameter | Phase A Fixture | Test Case |
|-----------|----------------|-----------|
| Source 1 X,Y,Z | 0.0, 0.0, 10.0 | 0.0, 0.0, -1.0 |
| Source 2 X,Y,Z | 0.0, 0.0, 10.0 | 0.1, 0.0, -1.0 |
| Weight 1 | 1.0 | 1.0 |
| Weight 2 | 0.2 | 0.2 |
| Lambda | 0.9768 Å | 1.0 Å |
| Distance | 100 mm | 100 mm |
| Detector | 256×256 | 128×128 |

**Key Difference**: The Phase A fixture has **both sources at the same position** (0,0,10), while the test has **different X positions** (0 vs 0.1). Additionally, the Z-direction is opposite (-1.0 vs +10.0).

## Interpretation

The XPASS result from pytest suggests that for the test's specific geometry (sources along -Z with different X positions), C and PyTorch now produce equivalent results. However, the Phase A fixture geometry (both sources at same position along +Z) still shows divergence.

**Hypothesis**: The C-code's source weight application bug may manifest differently depending on source geometry. When sources have identical positions (Phase A), the weight difference (1.0 vs 0.2) amplifies the divergence. When sources have different spatial positions (test case), the geometric effects may dominate over the weighting bug.

## Environment

- **NB_C_BIN:** /home/ollie/Documents/tmp/nanoBragg/golden_suite_generator/nanoBragg
- **Working Directory:** /home/ollie/Documents/tmp/nanoBragg/reports/2025-11-source-weights/phase_g/20251009T222635Z
- **KMP_DUPLICATE_LIB_OK:** TRUE
- **Python:** 3.13.5
- **PyTorch:** (version from environment)

## Commands Executed

See `commands.txt` for canonical reproduction commands.

## Artifacts Generated

- `py_tc_d1.bin` (256×256 float32 image from PyTorch)
- `c_tc_d3.bin` (256×256 float32 image from C)
- `py_stdout.txt` (PyTorch execution log)
- `c_stdout.txt` (C execution log with TRACE output)
- `metrics.json` (computed parity metrics)
- `pytest.log` (targeted test execution log showing XPASS)
- `collect.log` (pytest collection log)

## C-Code Analysis (from c_stdout.txt)

The C code output shows:
```
  created a total of 4 sources:
0 0 0   0 0
0 0 0   0 0
0 0 10   1 6.2e-10
0 0 10   0.2 6.2e-10
```

**CRITICAL**: The C code shows **4 sources** instead of the expected 2! The first two sources are at (0,0,0) with weight 0 and wavelength 0. This indicates a C-code parsing or initialization bug.

**Hypothesis Refinement**: The 133.87× divergence may be caused by:
1. C applying the 0.2 weight to source #4 (contributing 1/5 = 0.2 relative to source #3)
2. PyTorch ignoring weights and treating both real sources (#3, #4) equally
3. The ghost sources (#1, #2) may not contribute to intensity but affect normalization

## Next Actions (Phase H)

1. **Investigate C source parsing**: Why does the C code show 4 sources when the fixture has 2?
2. **Re-run with corrected fixture**: Create a new fixture that avoids the ghost source issue
3. **Document C-code bug**: File this under `docs/bugs/` as a separate C-PARITY issue
4. **Update test expectations**: The xfail should remain until we understand the geometry-dependent behavior

## Blocked Items

- Phase H cannot proceed until we resolve the fixture discrepancy
- The "unexpected C parity" scenario (test XPASS) requires investigation
- Need to determine whether to:
  - Update the Phase A fixture to match test parameters, OR
  - Update the test to match supervisor's fixture, OR
  - Document both as distinct test cases with different expected outcomes

## References

- Plan: `plans/active/source-weight-normalization.md`
- Fix Plan: `docs/fix_plan.md` [SOURCE-WEIGHT-001]
- Phase A Fixture: `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`
- Test Code: `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference`
- Spec: `specs/spec-a-core.md:151-153`
