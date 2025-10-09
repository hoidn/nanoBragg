# Phase D3: SOURCE-WEIGHT-001 Acceptance Harness Summary

**Generated:** 2025-10-09T10:43:10Z
**Purpose:** Acceptance criteria scaffolding for Phase E implementation
**Status:** Harness staged (tests pending Phase E)

---

## Executive Summary

This document defines the acceptance metrics and validation criteria for Phase E implementation of SOURCE-WEIGHT-001. The harness is **currently in staging mode** - all test cases (TC-D1 through TC-D4) are documented but not yet executable because `TestSourceWeightsDivergence` requires implementation in Phase E.

**Phase D2 Design Decision (Option B):** PyTorch SHALL continue its current behavior (sourcefile replaces divergence grid), and the spec SHALL be amended to document this as normative. A validation guard SHALL emit a `UserWarning` when mixing sourcefile + divergence parameters.

---

## Acceptance Metrics (Phase E Gate)

### Quantitative Thresholds

**All metrics MUST be satisfied for Phase E closure:**

- [ ] **Correlation (TC-D1, TC-D4):** `corr ≥ 0.999` between C and PyTorch outputs
- [ ] **Sum Ratio (TC-D1, TC-D4):** `|PyTorch_sum / C_sum - 1.0| ≤ 1e-3`
- [ ] **Steps Consistency:** `steps_pytorch == steps_c` for identical source counts
- [ ] **Warning Emission (TC-D2):** `UserWarning` captured in stderr when `-sourcefile` + `-hdivrange` both provided
- [ ] **Pytest Collection:** `pytest --collect-only -q` exits with code 0 (682+ tests discovered)
- [ ] **Targeted Test Pass:** `pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v` shows 4/4 passing

### Test Coverage Matrix

| Test Case | Scenario | Expected Behavior | Validation Method |
|-----------|----------|-------------------|-------------------|
| **TC-D1** | Sourcefile-only (baseline) | Correlation ≥0.999, sum_ratio ∈ [0.999, 1.001] | C↔PyTorch float32 parity |
| **TC-D2** | Sourcefile + divergence | UserWarning emitted, sourcefile sources only | stderr capture + assert |
| **TC-D3** | Divergence-only (no sourcefile) | Grid generation active, correct source count | Steps verification |
| **TC-D4** | C parity with explicit `-oversample 1` | Same as TC-D1 but with explicit oversample flag | Regression against TC-D1 |

---

## Current Status (Phase D3 Staging)

### What Exists

✅ **Design Decision:** Option B rationale documented in `reports/2025-11-source-weights/phase_d/20251009T103212Z/design_notes.md`
✅ **Commands Bundle:** Explicit C/Py CLI invocations in `commands.txt` (this directory)
✅ **Pytest Collection:** Confirmed 682 tests collected successfully (no import errors)
✅ **Fixture Availability:** `reports/2025-11-source-weights/fixtures/two_sources.txt` (weights 1.0, 0.2)

### What Is Pending (Phase E Implementation)

❌ **Test Class:** `tests/test_cli_scaling.py::TestSourceWeightsDivergence` does not exist yet
❌ **BeamConfig Guard:** Validation warning in `src/nanobrag_torch/config.py::BeamConfig.__post_init__()` not yet implemented
❌ **Spec Amendment:** `specs/spec-a-core.md:144-162` update per Option B not yet applied
❌ **Parity Metrics:** No metrics.json or correlation.txt yet (awaits Phase E test execution)

---

## Expected Warning Text (TC-D2 Acceptance)

Phase E implementation SHALL emit the following warning when `-sourcefile` and divergence parameters are both provided:

```
UserWarning: Divergence/dispersion parameters ignored when sourcefile is provided.
Sources are loaded from file only (see specs/spec-a-core.md:151-162).
```

**Validation:** `pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_divergence_warning -v` MUST capture this exact text (modulo whitespace).

---

## Metrics Capture Format (Phase E)

Phase E artifacts SHALL include the following files under `reports/2025-11-source-weights/phase_e/<STAMP>/`:

### Required Files

1. **metrics.json** — Machine-readable metrics:
   ```json
   {
     "tc_d1_correlation": 0.999123,
     "tc_d1_sum_ratio": 1.000456,
     "tc_d1_c_sum": 463.4,
     "tc_d1_py_sum": 463.6,
     "tc_d2_warning_captured": true,
     "tc_d3_steps_c": 9,
     "tc_d3_steps_py": 9,
     "tc_d4_correlation": 0.999234,
     "tc_d4_sum_ratio": 1.000567,
     "device": "cpu",
     "dtype": "float32"
   }
   ```

2. **pytest_TestSourceWeightsDivergence.log** — Full pytest output (verbose mode)

3. **warning_capture.log** — Stderr from TC-D2 containing the UserWarning

4. **summary.md** — Human-readable report with pass/fail status per metric

5. **commands.txt** — Exact reproduction commands (copy from this Phase D3 bundle)

6. **env.json** — Environment metadata (Python version, PyTorch version, git commit, NB_C_BIN path)

### Optional Files (If Failures Occur)

- **diff_tc_d1.png** — Heatmap showing C vs PyTorch pixel-by-pixel difference
- **trace_divergence.md** — Parallel trace comparison (if correlation < threshold)
- **steps_debug.txt** — Source count breakdown for TC-D3

---

## Pytest Selector (Phase E Execution)

```bash
# Preflight (must pass before Phase E work begins)
KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q

# Primary Validation (Phase E gate)
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v

# Individual Test Cases (for debugging)
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_only_parity -v
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_divergence_warning -v
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_divergence_only_grid_generation -v
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_parity_explicit_oversample -v
```

---

## Dependencies & Blockers

### Prerequisites (MUST be satisfied before Phase E)

- ✅ **Phase D2 Design Approved:** Option B rationale documented and agreed
- ✅ **Repository Clean:** `git status` shows no uncommitted changes at Phase E start
- ✅ **Fixtures Available:** `two_sources.txt` and `A.mat` in `reports/.../fixtures/`
- ✅ **C Binary Accessible:** `NB_C_BIN` resolves to working nanoBragg.c executable

### Known Risks

1. **C Reference Behavior:** Phase D1 evidence showed C generates "4 sources" (2 grid + 2 file) despite spec statement. Option B treats this as unintentional; if C behavior is actually correct, Option B spec amendment is invalid.
   - **Mitigation:** Phase E parity testing will reveal if C vs PyTorch divergence is sustainable. If TC-D1 fails correlation threshold, reopen Phase D2 design decision.

2. **Device/Dtype Sensitivity:** Metrics thresholds assume CPU + float32. CUDA execution may show lower correlation due to numerical precision.
   - **Mitigation:** Phase E acceptance requires CPU pass; CUDA is optional (document any correlation drop in summary.md).

3. **Warning Detection:** TC-D2 relies on stderr capture. If warning goes to stdout or is silenced by pytest configuration, test will fail.
   - **Mitigation:** Use `pytest.warns(UserWarning)` context manager in test implementation.

---

## Next Steps (Phase E Roadmap)

### E1: Implementation

1. Add `BeamConfig.__post_init__()` guard (5-10 lines in `src/nanobrag_torch/config.py`)
2. Extend `tests/test_cli_scaling.py` with `TestSourceWeightsDivergence` class (4 test methods)
3. Verify implementation with `pytest --collect-only -q` (expect 686 tests, +4 from current 682)

### E2: Validation

1. Run `pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v` (expect 4/4 passing)
2. Capture metrics under `reports/2025-11-source-weights/phase_e/<STAMP>/metrics.json`
3. Verify all checkboxes in "Acceptance Metrics" section above are satisfied

### E3: Documentation

1. Amend `specs/spec-a-core.md:144-162` per Option B design notes
2. Update `docs/architecture/pytorch_design.md` §8 (Sources subsection)
3. Add Phase E attempt to `docs/fix_plan.md` with artifact paths

### E4: Closure

1. Mark `plans/active/source-weight-normalization.md` Phase D3 task `[D]` (done)
2. Notify `[VECTOR-GAPS-002]` and `[PERF-PYTORCH-004]` that profiling can resume
3. Archive plan to `plans/archive/` when stable

---

## References

- **Phase D2 Design:** `reports/2025-11-source-weights/phase_d/20251009T103212Z/design_notes.md`
- **Phase D1 Evidence:** `reports/2025-11-source-weights/phase_d/20251009T102319Z/divergence_analysis.md`
- **Spec Authority:** `specs/spec-a-core.md:144-162` (to be amended in Phase E)
- **PyTorch Runtime Checklist:** `docs/development/pytorch_runtime_checklist.md`
- **Testing Strategy:** `docs/development/testing_strategy.md` §2.5 (Parallel Validation Matrix)
- **Active Plan:** `plans/active/source-weight-normalization.md`

---

## Conclusion

**Phase D3 Status:** Harness staged successfully.

**Key Deliverables:**
- ✅ `commands.txt` — Exact C/Py CLI reproduction commands for all test cases
- ✅ `pytest_collect.log` — Collection proof (682 tests, no import errors)
- ✅ `pytest_TestSourceWeightsDivergence.log` — Documented test class not found (expected)
- ✅ `summary.md` — This file (acceptance metrics, thresholds, Phase E roadmap)

**Phase E Ready:** Implementation can proceed immediately. All scaffolding and acceptance criteria are defined.

**Blocking Issues:** None. Phase D3 is documentation-only; no code changes required.
