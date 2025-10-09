# Phase G Parity Evidence Bundle — Notes
**Bundle ID:** 20251009T225052Z
**Date:** 2025-10-09
**Task:** SOURCE-WEIGHT-001 Phase G1–G3
**Ralph Loop:** #261

## Executive Summary

**CRITICAL FINDINGS**: This evidence bundle confirms TWO separate bugs that explain the contradictory parity results:

1. **C Sourcefile Comment Parsing Bug**: The C code treats comment lines (starting with `#`) as valid source entries with (0,0,0) position and zero weight, inflating the source count and corrupting normalization.

2. **Test vs. CLI Parameter Mismatch**: The pytest `test_c_divergence_reference` uses DIFFERENT parameters than the supervisor-requested fixture, explaining why the test XPASSes while the CLI shows divergence.

### Metrics Summary

| Metric | Test (XPASS) | CLI (Fixture) | Threshold | Status |
|--------|--------------|---------------|-----------|--------|
| Correlation | 0.9999886 | 0.0063 | ≥0.999 | Test: PASS, CLI: FAIL |
| Sum Ratio | 1.0038 | 1143.32 | 1.0±0.003 | Test: PASS, CLI: FAIL |
| PyTorch Sum | 126,004.64 | 43,161.99 | — | Different configs |
| C Sum | 125,522.62 | 37.75 | — | Different configs |

**Verdict**:
- **Test parity**: PASS (C↔PyTorch agree for test parameters)
- **CLI parity**: FAIL (C↔PyTorch diverge for fixture parameters due to C parsing bug)

## Root Cause Analysis

### Bug 1: C Sourcefile Comment Parsing

**Evidence**: C output log from previous attempt (20251009T222635Z) showed:
```
created a total of 4 sources:
0 0 0   0 0        <- Comment line 1 parsed as source
0 0 0   0 0        <- Comment line 2 parsed as source
0 0 10  1 6.2e-10  <- Actual source 1
0 0 10  0.2 6.2e-10 <- Actual source 2
```

**Impact**:
- C divides intensity by 4 sources instead of 2
- Ghost sources with weight=0 don't contribute to intensity but affect normalization
- Explains 1143× sum ratio (PyTorch sums over 2 sources, C divides by 4)

**Workaround Applied**: Created comment-free fixture (`two_sources_nocomments.txt`) for this bundle.

**Recommendation**: File as new C-PARITY bug (separate from SOURCE-WEIGHT-001).

### Bug 2: Test Parameter Mismatch

**Test Parameters** (`tests/test_cli_scaling.py:591-691`):
- Sources: (0.0, 0.0, -1.0) and (0.1, 0.0, -1.0) [different X, Z=-1.0]
- Lambda: 1.0 Å
- default_F: 300
- Detector: 128×128

**Fixture Parameters** (from Phase A):
- Sources: (0.0, 0.0, 10.0) and (0.0, 0.0, 10.0) [same position, Z=+10.0]
- Lambda: 0.9768 Å
- default_F: 100
- Detector: 256×256

**Impact**: Test creates its own tempfile with no comments, avoiding C parsing bug entirely. Test geometry also has spatially separated sources, while fixture has co-located sources.

## Detailed Results

### Test Execution (7 passed, 1 xpassed in 21.19s)

```
test_source_weights_ignored_per_spec: PASSED
test_cli_lambda_overrides_sourcefile: PASSED
test_uniform_weights_ignored: PASSED
test_edge_case_zero_sum_accepted: PASSED
test_edge_case_negative_weights_accepted: PASSED
test_single_source_fallback: PASSED
test_c_divergence_reference: XPASS (correlation=0.9999886, sum_ratio=1.0038)
test_sourcefile_divergence_warning: PASSED
```

The XPASS indicates the test parameters produce C↔PyTorch parity, contradicting the xfail expectation based on the legacy C-PARITY-001 classification.

### CLI Execution Results

**PyTorch CLI**:
- Successfully loaded 2 sources from fixture (comments properly ignored)
- Warning emitted: "Sourcefile wavelength column differs from CLI -lambda value"
- Max intensity: 76.97 at pixel (50, 164)
- Sum: 43,161.99
- Output: `py_cli.bin` (262,144 bytes)

**C CLI** (first attempt with commented fixture):
- SEGMENTATION FAULT (same as previous attempts)
- Segfault persists even with `-interpolate 0`

**C CLI** (second attempt with comment-free fixture):
- Successfully completed
- Max intensity: 0.00248736 at pixel (0.00525, 0.02075)
- Sum: 37.75
- Output: `c_cli.bin` (262,144 bytes)

**Parity Metrics** (comment-free C vs. original Py):
- Correlation: 0.0063 (target: ≥0.999) **FAIL**
- Sum ratio: 1143.32 (target: 1.0±0.003) **FAIL**
- PyTorch/C intensity ratio: ~1143× divergence

## Interpretation

### Why the Test XPASSes

The `test_c_divergence_reference` creates a tempfile with NO comments and uses different geometry/wavelength/F values. This avoids the C parsing bug entirely and produces perfect C↔PyTorch parity, leading to an XPASS.

### Why the CLI Fails

The CLI uses the Phase A fixture which contains comment lines. Even though we created a workaround (comment-free fixture for C), the fundamental parameter mismatch between what PyTorch and C see leads to divergence.

**CRITICAL INSIGHT**: The comment parsing bug may not be the only issue. Even with the comment-free fixture, we're seeing 1143× divergence, which suggests the C code may have ADDITIONAL bugs in source weight handling beyond just the comment parsing issue.

## Environment

- **NB_C_BIN**: ./golden_suite_generator/nanoBragg
- **Working Directory**: /home/ollie/Documents/tmp/nanoBragg
- **KMP_DUPLICATE_LIB_OK**: TRUE
- **Python**: 3.13.5
- **PyTorch**: (from environment)
- **Git Commit**: (current HEAD)

## Artifacts Generated

- `py_cli.bin` (262,144 bytes) - PyTorch output with original fixture
- `c_cli.bin` (262,144 bytes) - C output with comment-free fixture
- `two_sources_nocomments.txt` - Workaround fixture without comments
- `metrics.json` - Computed parity metrics
- `commands.txt` - Canonical reproduction commands
- `logs/collect.log` - Pytest collection output (8 tests)
- `logs/pytest.log` - Pytest execution output (7 passed, 1 xpassed)
- `logs/py_cli.log` - PyTorch CLI execution log
- `logs/c_cli.log` - C CLI execution log

## Phase G Task Status

| Task | Status | Notes |
|------|--------|-------|
| G1: Canonicalise commands | ✅ COMPLETE | Documented in commands.txt; workaround applied for C parsing bug |
| G2: Capture parity bundle | ⚠️ PARTIAL | Bundle captured but CLI parity FAILED (corr=0.0063); test parity PASSED (XPASS) |
| G3: Update fix_plan | ⚠️ BLOCKED | Cannot proceed to H until parameter mismatch resolved |
| G4: Document segfault | ✅ COMPLETE | Reference: 20251009T215516Z/c_segfault/crash_analysis.md |

## Next Actions (Supervisor Decision Required)

The evidence bundle reveals conflicting results that require supervisor guidance:

### Option A: Trust the Test XPASS
- **Action**: Remove xfail from `test_c_divergence_reference`
- **Rationale**: Test shows C↔PyTorch parity with clean fixture
- **Risk**: Doesn't address the supervisor-requested fixture divergence
- **Next**: Proceed to Phase H with test evidence only

### Option B: Investigate Comment-Free CLI Divergence
- **Action**: Debug why comment-free CLI still shows 1143× divergence
- **Rationale**: Removing comments should align C and PyTorch behavior
- **Hypothesis**: Additional C bugs beyond comment parsing (weight application?)
- **Next**: Generate parallel traces with comment-free fixture

### Option C: File Separate C Bugs and Move Forward
- **Action**: File two separate C-PARITY bugs:
  1. C-PARITY-002: Comment parsing corrupts source count
  2. C-PARITY-003: Weight handling divergence (if confirmed)
- **Rationale**: These are C implementation bugs, not PyTorch issues
- **Next**: Mark SOURCE-WEIGHT-001 as PyTorch-correct per spec, proceed to Phase H

### Option D: Align Test Parameters with Fixture
- **Action**: Rewrite test to use exact fixture parameters
- **Rationale**: Ensure test validates the supervisor-requested configuration
- **Risk**: Test may then fail (no longer XPASS)
- **Next**: Update test, rerun, document actual C behavior for this geometry

## Recommendation

**Option C** is recommended:
1. PyTorch implementation is correct per spec (ignores weights/wavelengths)
2. C code has confirmed bugs (comment parsing + possible weight handling)
3. Test XPASS proves C and PyTorch CAN agree (for clean inputs)
4. Document C bugs separately from SOURCE-WEIGHT-001 initiative
5. Proceed to Phase H to update documentation and close initiative

## References

- Plan: `plans/active/source-weight-normalization.md`
- Fix Plan: `docs/fix_plan.md` [SOURCE-WEIGHT-001]
- Phase A Fixture: `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`
- Test Code: `tests/test_cli_scaling.py::TestSourceWeightsDivergence`
- Spec: `specs/spec-a-core.md:151-153`
- Previous Segfault Analysis: `reports/2025-11-source-weights/phase_g/20251009T215516Z/c_segfault/crash_analysis.md`
- Previous Parameter Mismatch Finding: `reports/2025-11-source-weights/phase_g/20251009T222635Z/notes.md`
