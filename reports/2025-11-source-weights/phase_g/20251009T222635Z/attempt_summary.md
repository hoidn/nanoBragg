# Attempt #30 Summary - SOURCE-WEIGHT-001 Phase G Evidence Bundle

**Loop ID:** ralph #260
**Date:** 2025-10-09
**Bundle:** `20251009T222635Z`
**Result:** **BLOCKED (critical C parsing bug + test parameter mismatch discovered)**

## Executive Summary

**This attempt uncovered multiple interconnected issues that block Phase G completion:**

1. **C-code sourcefile parsing bug**: nanoBragg.c treats comment lines as sources with (0,0,0) position and zero weights, inflating source count from 2 to 4
2. **Test/Fixture parameter mismatch**: The pytest `test_c_divergence_reference` uses DIFFERENT source geometry than the supervisor-requested Phase A fixture
3. **Geometry-dependent parity behavior**: The pytest shows XPASS (C↔Py agree), but the CLI commands using Phase A fixture show 134× divergence
4. **Evidence incomplete**: Cannot complete Phase G2 exit criteria (correlation ≥0.999, |ratio−1| ≤3e-3) with current C-code bug

## Metrics

### PyTorch (successful)
- **Sum:** 42,875.54
- **Max:** 76.97
- **Mean:** 0.659
- **Command:** `python -m nanobrag_torch -sourcefile <fixture> -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -nointerpolate -nonoise -floatfile py_tc_d1.bin`

### C (successful but buggy)
- **Sum:** 320.27
- **Max:** 0.005
- **Sources shown:** 4 (should be 2!)
- **Comment:** "created a total of 4 sources: 0 0 0 0 0 / 0 0 0 0 0 / 0 0 10 1 6.2e-10 / 0 0 10 0.2 6.2e-10"

### Parity Metrics
- **Correlation:** 0.0297 (target: ≥0.999) ❌
- **Sum ratio:** 133.87 (target: ~1.0 ±0.003) ❌
- **Verdict:** **FAILED** - divergence caused by C parsing bug

### Test Results (pytest with different parameters)
- **7 passed, 1 xpassed** in 21.24s
- **test_c_divergence_reference:** XPASS (expected divergence but got parity!)
- **Implication:** C↔Py parity exists for the test's geometry (Z=-1.0, X-offset sources) but not for Phase A fixture (Z=10.0, co-located sources)

## Critical Findings

### Finding 1: C Sourcefile Parsing Bug

The nanoBragg.c binary reads the 4-line fixture file (2 comments + 2 data lines) and creates **4 sources** instead of 2:

```
# Input file (reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt):
# Weighted two-source fixture
# X Y Z weight wavelength(m)
0.0 0.0 10.0 1.0 6.2e-10
0.0 0.0 10.0 0.2 6.2e-10

# C-code stdout shows:
  created a total of 4 sources:
0 0 0   0 0         ← GHOST SOURCE (from comment line)
0 0 0   0 0         ← GHOST SOURCE (from comment line)
0 0 10   1 6.2e-10  ← Real source 1
0 0 10   0.2 6.2e-10 ← Real source 2
```

**Impact**: The ghost sources may not contribute to intensity (zero weight) but likely affect the normalization divisor (`n_sources=4` instead of 2), causing 2× reduction in C intensity. Combined with the C weight application bug (0.2 weight reduces source #4 contribution), this could explain the 134× divergence.

**Action Required**: Either (1) fix C parsing to skip comment lines, (2) provide fixture without comments, or (3) document as C-PARITY bug and adjust test expectations.

### Finding 2: Test Parameter Mismatch

The `test_c_divergence_reference` uses **different source positions** than the Phase A fixture requested by the supervisor:

| Parameter | Test Case | Phase A Fixture |
|-----------|-----------|-----------------|
| Source 1 (X,Y,Z) | 0.0, 0.0, -1.0 | 0.0, 0.0, 10.0 |
| Source 2 (X,Y,Z) | 0.1, 0.0, -1.0 | 0.0, 0.0, 10.0 |
| Key Difference | Different X + opposite Z | Co-located sources |

**Impact**: The test creates a **tempfile sourcefile without comments**, avoiding the C parsing bug, and uses **spatially separated sources**, which may mask the weight application bug through geometric effects.

**Action Required**: Align test and supervisor fixture OR document as separate test cases with different expected outcomes.

### Finding 3: Geometry-Dependent Parity

The XPASS indicates C and PyTorch **agree** when:
- Sources are spatially separated (X-offset)
- Z=-1.0 (sources behind sample)
- No comment lines in sourcefile

But they **diverge** when:
- Sources are co-located (same position)
- Z=10.0 (sources in front of sample)
- Comment lines present in sourcefile

**Hypothesis**: The C weight bug's effect depends on whether geometric differences dominate over weight differences.

## Artifacts Generated

All files in `reports/2025-11-source-weights/phase_g/20251009T222635Z/`:
- `commands.txt` — Canonical CLI commands for PyTorch and C
- `notes.md` — Comprehensive analysis of findings
- `py_tc_d1.bin` — PyTorch output image (256×256 float32)
- `c_tc_d3.bin` — C output image (256×256 float32)
- `py_stdout.txt` — PyTorch execution log
- `c_stdout.txt` — C execution log with TRACE output showing 4 sources
- `metrics.json` — Parity metrics (correlation=0.0297, ratio=133.87)
- `pytest.log` — Test execution showing XPASS
- `collect.log` — Test collection validation
- `attempt_summary.md` — This file

## Blockers

1. **Phase G2 exit criteria cannot be met** with current C parsing bug (correlation << 0.999)
2. **Phase H parity reassessment blocked** until G2 delivers valid evidence
3. **Test expectations unclear**: Should test expect divergence (xfail) or parity (pass)?
4. **C-code fix required**: Either patch nanoBragg.c to skip comment lines OR use comment-free fixtures

## Recommendations

**Option A (Quick):** Create comment-free fixture matching test parameters and rerun Phase G2
**Option B (Thorough):** Fix C parsing bug in nanoBragg.c, rebuild binary, rerun all evidence
**Option C (Pragmatic):** Document the test parameter mismatch as intentional (two separate test cases), mark Phase G complete with notes documenting the C bug, proceed to Phase H using only the XPASS test case as evidence

**Recommended Path:** Option C + file C parsing bug as separate C-PARITY issue to track independently

## Next Actions (for Supervisor)

1. Decide on Option A/B/C path forward
2. Update `test_c_divergence_reference` expectations (remove xfail if parity is real)
3. Create new fix_plan entry for C sourcefile parsing bug
4. Update Phase G plan tasks with resolution choice
5. Queue Phase H once evidence strategy is finalized
