# SOURCE-WEIGHT-001 Phase E Attempt #12 — Loop Summary

**Date**: 2025-10-09
**Actor**: ralph
**Mode**: Parity
**Status**: ⚠️ PARTIAL SUCCESS — TC-D2 conversion complete, but blocking bug discovered

---

## Objectives (from input.md)

1. ✅ Convert TC-D2 test from subprocess stderr parsing to in-process `pytest.warns(UserWarning)`
2. ❌ Run parity validation and capture TC-D1/TC-D3 metrics (correlation ≥0.999, |sum_ratio−1| ≤1e-3)
3. ❌ Archive metrics under `phase_e/<STAMP>/`

---

## Accomplishments

### TC-D2 Test Conversion ✅

**File**: `tests/test_cli_scaling.py:586-658`

**Changes**:
- Replaced subprocess stderr parsing with in-process `pytest.warns(UserWarning)` assertion
- Used `monkeypatch.setattr(sys, 'argv', args_with_warning)` to set CLI arguments
- Called `nanobrag_torch.__main__.main()` directly under `pytest.warns` context
- Validated warning message contains required fragments:
  - "Divergence/dispersion parameters ignored"
  - "sourcefile is provided"
  - "spec-a-core.md:151-162"

**Result**: Test PASSES in 5.43s ✅

---

## Critical Findings — Blocking Issue Discovered

### TC-D1/TC-D3/TC-D4 Parity Failures

When running the full `TestSourceWeightsDivergence` suite to capture parity metrics, discovered **massive divergence** from C reference:

| Test | Correlation | Sum Ratio | C Sum | PyTorch Sum | Status |
|------|-------------|-----------|--------|-------------|--------|
| TC-D1 | -0.297 | 302.6× | 179.6 | 54352.6 | ❌ FAIL |
| TC-D3 | 0.070 | 141.7× | 358.2 | 50745.9 | ❌ FAIL |
| TC-D4 | (delegates to TC-D1) | — | — | — | ❌ FAIL |

**Thresholds**: correlation ≥0.999, |sum_ratio−1| ≤1e-3
**Actual**: Divergence is 140-300× instead of <0.5%

---

## Root Cause Analysis

### Bug Location: `src/nanobrag_torch/__main__.py:747`

**Current (INCORRECT) Code**:
```python
elif 'sources' not in config:
    # Auto-select divergence parameters
    hdiv_params, vdiv_params = auto_select_divergence(...)
    # ... generates sources from divergence/dispersion ...
```

**Problem**:
- Condition checks if `'sources'` key exists in config dict
- The `sources` field **won't exist** until AFTER this block executes
- Therefore, divergence grid generation runs EVEN when sourcefile is loaded
- Result: Both sourcefile sources (2) AND divergence grid sources are accumulated → double-counting

**Should be**:
```python
elif 'sourcefile' not in config:
    # Only generate divergence sources when no sourcefile provided
```

---

## Impact Assessment

### Phase C Implementation Was Incomplete

- **Attempt #6** (Phase C) claimed success with correlation=0.9999886, sum_ratio=1.0038
- That test used explicit `-lambda` which masked the divergence grid bug
- CLI runs without explicit wavelength expose the double-counting issue
- Phase C should have been marked "incomplete" — test coverage was insufficient

### Spec Requirement Violation

Per `specs/spec-a-core.md:151-162`:
> "Generated sources (when no file provided):"

Current implementation generates sources even when file IS provided, violating spec precedence rule documented in Option B design.

---

## Artifacts Created

All artifacts archived under `reports/2025-11-source-weights/phase_e/20251009T115838Z/`:

- ✅ `summary.md` — Detailed failure analysis with root cause hypothesis
- ✅ `pytest.log` — Full test suite run output
- ✅ `commands.txt` — Timestamped command log
- ✅ `env.json` — Environment snapshot (Python 3.13.5, PyTorch 2.7.1+cu126, git SHA 964f869)
- ✅ `LOOP_SUMMARY.md` — This document

---

## Documentation Updates

### `docs/fix_plan.md`

Added **Attempt #12** entry documenting:
- TC-D2 conversion success
- TC-D1/TC-D3/TC-D4 parity failures with quantitative metrics
- Root cause: `__main__.py:747` condition bug
- Artifact path reference

### `plans/active/source-weight-normalization.md`

Updated Phase E status:
- Changed Status Note to document Attempt #12 findings
- E2: Changed state from `[P]` (Pending) to `[B]` (Blocked) with explanation
- E3: Changed state from `[ ]` to `[B]` (Blocked) — cannot capture metrics until bug fixed

---

## Next Steps (Supervisor Decision Required)

### Option 1: Fix Bug in This Loop (Scope Creep)

**Pros**:
- Single-line fix at `__main__.py:747`
- Could immediately validate parity and complete Phase E

**Cons**:
- Violates Ralph protocol: "One thing per loop"
- Original task (TC-D2 conversion) is already complete
- Expands beyond initial scope defined in `input.md`

### Option 2: Document and Escalate (Ralph Protocol Compliant)

**Pros**:
- Respects "One thing per loop" principle
- Original task (TC-D2 conversion) successfully completed
- Blocking issue documented with clear root cause

**Cons**:
- Phase E remains incomplete
- Requires additional loop to fix divergence bug

---

## Recommendation

**STOP THIS LOOP** per Ralph protocol rules:

> "One thing per loop" — The TC-D2 conversion task is complete. The discovered bug is a separate, blocking issue that should be addressed in a dedicated loop with proper scope.

The next loop should focus exclusively on:
1. Fix `__main__.py:747` condition to check `'sourcefile' not in config`
2. Re-run TC-D1/TC-D3/TC-D4 parity validation
3. Capture fresh metrics meeting correlation ≥0.999 threshold

---

## Files Modified This Loop

- ✅ `tests/test_cli_scaling.py` (lines 586-658) — TC-D2 converted to pytest.warns
- ✅ `docs/fix_plan.md` — Added Attempt #12 entry
- ✅ `plans/active/source-weight-normalization.md` — Updated Phase E status

**No production code changes** — test update only.

---

## Validation Commands

### What Works ✅

```bash
# TC-D2 warning validation (PASSING)
NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_divergence_warning -v
```

### What's Broken ❌

```bash
# Full parity suite (TC-D1/D3/D4 FAILING due to divergence grid bug)
NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
```

---

**End of Loop Summary**
