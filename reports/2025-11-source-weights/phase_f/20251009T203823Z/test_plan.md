# SOURCE-WEIGHT-001 Phase F: Test Realignment Design Packet

**Date:** 2025-10-09T20:38:23Z
**Status:** READY FOR IMPLEMENTATION (Phase G)
**Prerequisites:** Phase E decision memo (`phase_e/20251009T202432Z/spec_vs_c_decision.md`)
**Target:** Redesign `tests/test_cli_scaling.py` source weight tests to enforce spec compliance

---

## 1. Executive Summary

This design packet provides concrete specifications for updating the source weight test suite to enforce spec compliance per `specs/spec-a-core.md:151`. The tests will verify that PyTorch correctly **ignores** sourcefile weights and wavelengths, using equal weighting and CLI lambda override.

**Key Changes:**
- Replace C-parity assertions with PyTorch self-consistency checks
- Add spec-based acceptance criteria (weighted vs unweighted equivalence)
- Document expected C divergence with `@pytest.mark.xfail` references
- Update tolerance thresholds to reflect spec-based validation (no C correlation requirement)

---

## 2. Affected Tests Inventory (Phase F1)

### 2.1 TestSourceWeights Class

**File:** `tests/test_cli_scaling.py:252-470`

| Test Method | Current Behavior | Proposed Change | Rationale |
|-------------|------------------|-----------------|-----------|
| `test_weighted_source_matches_c` | Enforces C parity (correlation ≥0.999) | **REMOVE** — Replaced by spec compliance test | C diverges from spec (C-PARITY-001) |
| `test_uniform_weights_ignored` | ✅ Already spec-compliant | **KEEP** — No changes | Validates config acceptance |
| `test_edge_case_zero_sum_accepted` | ✅ Already spec-compliant | **KEEP** — No changes | Validates spec's "read but ignored" rule |
| `test_edge_case_negative_weights_accepted` | ✅ Already spec-compliant | **KEEP** — No changes | Validates spec's "read but ignored" rule |
| `test_single_source_fallback` | ✅ Already spec-compliant | **KEEP** — No changes | Validates single-source behavior |

### 2.2 TestSourceWeightsDivergence Class

**File:** `tests/test_cli_scaling.py:473-761`

| Test Method | Current Behavior | Proposed Change | Rationale |
|-------------|------------------|-----------------|-----------|
| `test_sourcefile_only_parity` | Enforces C parity (sum_ratio ~1.0) | **REMOVE** — Replaced by spec equality test | C diverges from spec |
| `test_sourcefile_divergence_warning` | ✅ Validates warning emission | **KEEP** — Update assertion details | Correct but needs tighter assertions |
| `test_divergence_only_grid_generation` | Enforces C parity for divergence grid | **MARK XFAIL** — Document expected divergence | C bug affects this case |
| `test_c_parity_explicit_oversample` | Enforces C parity | **REMOVE** — Redundant with spec test | Delegates to TC-D1 which will be replaced |

---

## 3. New Test Specifications (Phase F2)

### 3.1 Test: `test_source_weights_ignored_per_spec`

**Purpose:** Verify that sourcefile weights are ignored (equal weighting per spec §4).

**Strategy:** Run PyTorch twice with same sourcefiles:
1. **Run A:** Sourcefile with varying weights [1.0, 0.2]
2. **Run B:** Manually constructed equal sources (no weights)
3. **Assert:** Outputs are identical (within numerical precision)

**Fixture:** `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`
```
# X    Y    Z    weight  lambda(m)
0    0    10   1.0     6.2e-10
0    0    10   0.2     6.2e-10
```

**Implementation Pseudocode:**
```python
def test_source_weights_ignored_per_spec():
    """
    Verify that source weights are ignored per specs/spec-a-core.md:151.

    This test replaces test_weighted_source_matches_c (which enforced C-PARITY-001 bug).
    Expected: PyTorch treats weighted and unweighted sourcefiles identically.
    """
    # Run A: Weighted sourcefile
    result_weighted = simulate(
        sourcefile="two_sources.txt",
        lambda_A=0.9768,
        cell=(100, 100, 100, 90, 90, 90),
        default_F=100,
        distance_mm=100,
        detpixels=256
    )

    # Run B: Equal-weight equivalent (manual source construction)
    # Sources at same positions, but constructed without weights
    result_equal = simulate(
        sources=[
            Source(position=(0, 0, 10), wavelength=0.9768),
            Source(position=(0, 0, 10), wavelength=0.9768)
        ],
        lambda_A=0.9768,
        cell=(100, 100, 100, 90, 90, 90),
        default_F=100,
        distance_mm=100,
        detpixels=256
    )

    # Assertions
    sum_ratio = result_weighted.sum() / result_equal.sum()
    correlation = np.corrcoef(result_weighted.flatten(), result_equal.flatten())[0, 1]

    # Spec-based tolerance: 0.3% for sum ratio (accounts for numeric precision)
    assert abs(sum_ratio - 1.0) <= 3e-3, \
        f"Weighted vs equal runs differ by {abs(sum_ratio - 1.0):.6f} (> 3e-3). " \
        f"Spec violation: weights should be ignored."

    assert correlation >= 0.999, \
        f"Weighted vs equal correlation {correlation:.6f} < 0.999. Spec violation."
```

**Acceptance Criteria:**
- `sum_ratio ∈ [0.997, 1.003]` (0.3% tolerance for float32 precision)
- `correlation ≥ 0.999`
- **No C comparison required** (spec self-consistency check only)

---

### 3.2 Test: `test_cli_lambda_overrides_sourcefile`

**Purpose:** Verify CLI `-lambda` parameter overrides all sourcefile wavelength values.

**Strategy:**
1. Sourcefile contains wavelengths λ=6.2 Å
2. CLI specifies `-lambda 0.9768`
3. Verify all physics used λ=0.9768 (not 6.2)
4. Verify warning was emitted about wavelength mismatch

**Implementation Pseudocode:**
```python
def test_cli_lambda_overrides_sourcefile():
    """
    Verify CLI -lambda parameter overrides sourcefile wavelengths per spec §4.

    Expected behavior:
    1. UserWarning emitted when sourcefile wavelengths differ from CLI
    2. All source contributions use CLI wavelength (not file values)
    3. Physics calculations consistent with CLI lambda only
    """
    # Sourcefile has lambda=6.2e-10, CLI specifies lambda=0.9768
    with pytest.warns(UserWarning, match="Sourcefile wavelength column differs"):
        result = simulate(
            sourcefile="two_sources.txt",  # Contains lambda=6.2e-10
            lambda_A=0.9768,  # CLI override
            cell=(100, 100, 100, 90, 90, 90),
            default_F=100,
            distance_mm=100,
            detpixels=256
        )

    # Indirect verification: Compare against reference run with CLI lambda only
    reference = simulate(
        sources=[Source(position=(0, 0, 10), wavelength=0.9768)] * 2,
        lambda_A=0.9768,
        cell=(100, 100, 100, 90, 90, 90),
        default_F=100,
        distance_mm=100,
        detpixels=256
    )

    # If CLI override worked, outputs should match
    sum_ratio = result.sum() / reference.sum()
    assert abs(sum_ratio - 1.0) <= 3e-3, \
        f"CLI lambda override failed: sum_ratio={sum_ratio:.6f}"
```

**Acceptance Criteria:**
- `UserWarning` emitted with substring `"Sourcefile wavelength column differs"`
- `sum_ratio ∈ [0.997, 1.003]` vs reference (CLI lambda only)
- Warning message references spec section (e.g., `"spec-a-core.md:151"`)

---

### 3.3 Test: `test_c_divergence_reference` (Optional, marked XFAIL)

**Purpose:** Document expected C divergence for future reference and regression detection.

**Strategy:** Run both C and PyTorch, expect mismatch, document metrics.

**Implementation Pseudocode:**
```python
@pytest.mark.xfail(reason="C-PARITY-001: C applies source weights, violating spec §4")
@pytest.mark.skipif(not is_parallel_enabled(), reason="NB_RUN_PARALLEL=1 required")
def test_c_divergence_reference():
    """
    Reference test documenting expected C vs PyTorch divergence on weighted sources.

    This test is marked XFAIL because C behavior diverges from spec (C-PARITY-001).
    It serves as a regression detector: if it starts passing, investigate whether
    C or PyTorch changed unexpectedly.

    Expected divergence (from Phase E analysis):
    - Correlation < 0.8 (C applies weights, PyTorch ignores them)
    - C intensity lower by ~546× (due to C's steps inflation bug)
    """
    c_result = run_c_reference(
        sourcefile="two_sources.txt",
        lambda_A=0.9768,
        default_F=100,
        distance_mm=100,
        detpixels=256
    )

    py_result = simulate(
        sourcefile="two_sources.txt",
        lambda_A=0.9768,
        default_F=100,
        distance_mm=100,
        detpixels=256
    )

    correlation = np.corrcoef(c_result.flatten(), py_result.flatten())[0, 1]

    # This assertion is EXPECTED TO FAIL (hence @pytest.mark.xfail)
    assert correlation >= 0.999, \
        f"C-PARITY-001: Expected divergence detected. Correlation={correlation:.6f}. " \
        f"See reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md"
```

**Acceptance Criteria:**
- Test marked with `@pytest.mark.xfail(reason="C-PARITY-001...")`
- Correlation documented in failure message
- Reference to decision memo included in assertion text

---

## 4. Fixture Mappings

### 4.1 Required Fixtures

| Fixture Name | Location | Purpose | Format |
|--------------|----------|---------|--------|
| `two_sources.txt` | `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/` | Weighted source test case | 2 sources, weights [1.0, 0.2], lambda=6.2e-10 |
| (None additional) | — | Equal-weight tests construct sources programmatically | N/A |

### 4.2 Fixture Access Pattern

**Problem:** Fixture paths must be resolved robustly (tests run from repo root).

**Solution:** Use fallback path resolution:
```python
fixture_paths = [
    Path('reports/2025-11-source-weights/fixtures/two_sources.txt'),
    Path('reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt')
]
sourcefile = next((p for p in fixture_paths if p.exists()), None)
if sourcefile is None:
    pytest.skip("two_sources.txt fixture not found")
```

---

## 5. Pytest Selectors & Commands (Phase F3)

### 5.1 Test Collection Verification

**Command:**
```bash
pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
```

**Output (from `collect.log`):**
```
tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c
tests/test_cli_scaling.py::TestSourceWeights::test_uniform_weights_ignored
tests/test_cli_scaling.py::TestSourceWeights::test_edge_case_zero_sum_accepted
tests/test_cli_scaling.py::TestSourceWeights::test_edge_case_negative_weights_accepted
tests/test_cli_scaling.py::TestSourceWeights::test_single_source_fallback
tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_only_parity
tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_divergence_warning
tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_divergence_only_grid_generation
tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_parity_explicit_oversample

9 tests collected
```

### 5.2 Post-Phase G Expected Selectors

**After implementation, collection should show:**
```
tests/test_cli_scaling.py::TestSourceWeights::test_source_weights_ignored_per_spec
tests/test_cli_scaling.py::TestSourceWeights::test_cli_lambda_overrides_sourcefile
tests/test_cli_scaling.py::TestSourceWeights::test_uniform_weights_ignored
tests/test_cli_scaling.py::TestSourceWeights::test_edge_case_zero_sum_accepted
tests/test_cli_scaling.py::TestSourceWeights::test_edge_case_negative_weights_accepted
tests/test_cli_scaling.py::TestSourceWeights::test_single_source_fallback
tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_divergence_warning
tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference  # (marked xfail)

8 tests collected (1 xfail expected)
```

**Removed:**
- `test_weighted_source_matches_c` (replaced by `test_source_weights_ignored_per_spec`)
- `test_sourcefile_only_parity` (C-parity no longer required)
- `test_divergence_only_grid_generation` (move to xfail or remove)
- `test_c_parity_explicit_oversample` (redundant)

**Added:**
- `test_source_weights_ignored_per_spec` (spec self-consistency)
- `test_cli_lambda_overrides_sourcefile` (CLI precedence validation)
- `test_c_divergence_reference` (optional C-bug documentation)

### 5.3 Authoritative Test Execution Command

**Full suite run (Phase G validation):**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_cli_scaling.py::TestSourceWeights \
  tests/test_cli_scaling.py::TestSourceWeightsDivergence
```

**Spec-only subset (no C comparison required):**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_cli_scaling.py::TestSourceWeights::test_source_weights_ignored_per_spec \
  tests/test_cli_scaling.py::TestSourceWeights::test_cli_lambda_overrides_sourcefile
```

**C-divergence reference (expected xfail):**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg \
  pytest -v tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference
```

---

## 6. CLI Bundle for Comparison Artifacts

### 6.1 TC-Spec-1: PyTorch Weighted vs Equal Run

**Purpose:** Generate side-by-side outputs for spec compliance validation.

**Commands:**
```bash
# Setup
export KMP_DUPLICATE_LIB_OK=TRUE
FIXTURE_DIR="reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures"
OUT_DIR="reports/2025-11-source-weights/phase_f/20251009T203823Z/cli"
mkdir -p "$OUT_DIR"

# Run A: Weighted sourcefile (weights should be ignored)
python -m nanobrag_torch \
  -sourcefile "$FIXTURE_DIR/two_sources.txt" \
  -lambda 0.9768 \
  -default_F 100 \
  -cell 100 100 100 90 90 90 \
  -distance 100 \
  -detpixels 256 \
  -pixel 0.1 \
  -oversample 1 \
  -phisteps 1 \
  -mosaic_dom 1 \
  -floatfile "$OUT_DIR/py_weighted.bin"

# Run B: Equal-weight manual construction
# (This requires scripting; not available via CLI)
# Alternative: Use sourcefile with all weights = 1.0
cat > "$OUT_DIR/equal_sources.txt" << EOF
# X    Y    Z    weight  lambda(m)
0    0    10   1.0     6.2e-10
0    0    10   1.0     6.2e-10
EOF

python -m nanobrag_torch \
  -sourcefile "$OUT_DIR/equal_sources.txt" \
  -lambda 0.9768 \
  -default_F 100 \
  -cell 100 100 100 90 90 90 \
  -distance 100 \
  -detpixels 256 \
  -pixel 0.1 \
  -oversample 1 \
  -phisteps 1 \
  -mosaic_dom 1 \
  -floatfile "$OUT_DIR/py_equal.bin"

# Compare outputs
python << EOF_PYTHON
import numpy as np
from pathlib import Path

out_dir = Path("$OUT_DIR")
weighted = np.fromfile(out_dir / "py_weighted.bin", dtype=np.float32).reshape(256, 256)
equal = np.fromfile(out_dir / "py_equal.bin", dtype=np.float32).reshape(256, 256)

sum_ratio = weighted.sum() / equal.sum()
correlation = np.corrcoef(weighted.flatten(), equal.flatten())[0, 1]

metrics = {
    "weighted_sum": float(weighted.sum()),
    "equal_sum": float(equal.sum()),
    "sum_ratio": float(sum_ratio),
    "correlation": float(correlation),
    "tolerance": 3e-3
}

import json
with open(out_dir / "metrics_spec_compliance.json", "w") as f:
    json.dump(metrics, f, indent=2)

print(f"Sum ratio: {sum_ratio:.6f}")
print(f"Correlation: {correlation:.6f}")
print(f"Metrics saved to {out_dir / 'metrics_spec_compliance.json'}")
EOF_PYTHON
```

**Expected Metrics:**
- `sum_ratio ∈ [0.997, 1.003]`
- `correlation ≥ 0.999`

### 6.2 TC-Spec-2: CLI Lambda Override Validation

**Purpose:** Verify CLI lambda overrides sourcefile wavelengths.

**Commands:**
```bash
# Run: Sourcefile with lambda=6.2, CLI specifies lambda=0.9768
python -m nanobrag_torch \
  -sourcefile "$FIXTURE_DIR/two_sources.txt" \
  -lambda 0.9768 \
  -default_F 100 \
  -cell 100 100 100 90 90 90 \
  -distance 100 \
  -detpixels 256 \
  -pixel 0.1 \
  -floatfile "$OUT_DIR/py_lambda_override.bin" \
  2> "$OUT_DIR/py_lambda_override_stderr.txt"

# Check for warning in stderr
grep -q "Sourcefile wavelength column differs" "$OUT_DIR/py_lambda_override_stderr.txt"
if [ $? -eq 0 ]; then
    echo "✅ Warning emitted as expected"
else
    echo "❌ Warning NOT emitted (spec violation)"
fi
```

**Expected Outcome:**
- Warning emitted to stderr
- Output image uses CLI wavelength (verified via comparison with reference run)

### 6.3 TC-C-Divergence: C vs PyTorch Reference (Optional)

**Purpose:** Document expected C divergence metrics for archival.

**Commands:**
```bash
# Run C
./golden_suite_generator/nanoBragg \
  -sourcefile "$FIXTURE_DIR/two_sources.txt" \
  -lambda 0.9768 \
  -default_F 100 \
  -cell 100 100 100 90 90 90 \
  -distance 100 \
  -detpixels 256 \
  -pixel 0.1 \
  -floatfile "$OUT_DIR/c_weighted.bin"

# Run PyTorch
python -m nanobrag_torch \
  -sourcefile "$FIXTURE_DIR/two_sources.txt" \
  -lambda 0.9768 \
  -default_F 100 \
  -cell 100 100 100 90 90 90 \
  -distance 100 \
  -detpixels 256 \
  -pixel 0.1 \
  -floatfile "$OUT_DIR/py_weighted_for_c_compare.bin"

# Compare (expected: correlation < 0.8)
python << EOF_PYTHON
import numpy as np
from pathlib import Path

out_dir = Path("$OUT_DIR")
c_img = np.fromfile(out_dir / "c_weighted.bin", dtype=np.float32).reshape(256, 256)
py_img = np.fromfile(out_dir / "py_weighted_for_c_compare.bin", dtype=np.float32).reshape(256, 256)

correlation = np.corrcoef(c_img.flatten(), py_img.flatten())[0, 1]
sum_ratio = py_img.sum() / c_img.sum()

metrics = {
    "c_sum": float(c_img.sum()),
    "py_sum": float(py_img.sum()),
    "sum_ratio": float(sum_ratio),
    "correlation": float(correlation),
    "expected": "correlation < 0.8 (C-PARITY-001)"
}

import json
with open(out_dir / "metrics_c_divergence.json", "w") as f:
    json.dump(metrics, f, indent=2)

print(f"Correlation: {correlation:.6f} (expected < 0.8 per C-PARITY-001)")
print(f"Sum ratio (Py/C): {sum_ratio:.6f}")
EOF_PYTHON
```

**Expected Metrics:**
- `correlation < 0.8` (C divergence confirmed)
- `sum_ratio ~546` (C intensity under-scaled due to steps bug)

---

## 7. Tolerance Policy & Acceptance Criteria

### 7.1 Spec-Based Tolerance (PyTorch self-consistency)

**Context:** No C comparison required; validate against spec requirements.

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| **Sum Ratio** | `∈ [0.997, 1.003]` | 0.3% tolerance for float32 precision; weighted vs equal runs should be identical |
| **Correlation** | `≥ 0.999` | High correlation required for self-consistency; any deviation indicates spec violation |
| **Warning Emission** | Required substring match | CLI lambda override must emit UserWarning per spec §4 |

**Reference:** `docs/development/testing_strategy.md` (Tier 1 translation correctness)

### 7.2 C-Divergence Tolerance (Optional reference test)

**Context:** Document expected mismatch for regression detection.

| Metric | Expected Value | Notes |
|--------|----------------|-------|
| **Correlation** | `< 0.8` | C diverges from spec; low correlation is **expected** |
| **Sum Ratio (Py/C)** | `~546` | C under-scales by ~546× due to steps inflation bug (4 sources instead of 2) |

**Status:** Marked `@pytest.mark.xfail(reason="C-PARITY-001")`

---

## 8. Implementation Guidance for Phase G

### 8.1 Step-by-Step Checklist

**G1: Update Test Suite**
- [ ] **Remove:** `test_weighted_source_matches_c` (lines 256-363)
- [ ] **Add:** `test_source_weights_ignored_per_spec` (new method, ~50 lines)
  - Implement weighted vs equal comparison logic
  - Use fixture `two_sources.txt` with fallback path resolution
  - Assert `sum_ratio ∈ [0.997, 1.003]` and `correlation ≥ 0.999`
- [ ] **Add:** `test_cli_lambda_overrides_sourcefile` (new method, ~40 lines)
  - Use `pytest.warns(UserWarning, match="Sourcefile wavelength column differs")`
  - Compare result against reference run with CLI lambda only
  - Assert warning message contains spec reference
- [ ] **Remove:** `test_sourcefile_only_parity` (lines 476-584)
- [ ] **Remove:** `test_c_parity_explicit_oversample` (lines 752-761)
- [ ] **Update:** `test_sourcefile_divergence_warning` (lines 586-656)
  - Tighten assertion: verify warning contains `"spec-a-core.md:151-162"`
  - Ensure test still passes (no logic change, just stricter checks)
- [ ] **Optional Add:** `test_c_divergence_reference` (new method, marked xfail)
  - Implement C vs PyTorch comparison
  - Mark with `@pytest.mark.xfail(reason="C-PARITY-001: C applies source weights...")`
  - Include decision memo reference in assertion message

**G2: Capture Evidence Bundle**
- [ ] Run targeted pytest:
  ```bash
  KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
    tests/test_cli_scaling.py::TestSourceWeights \
    tests/test_cli_scaling.py::TestSourceWeightsDivergence \
    | tee reports/2025-11-source-weights/phase_g/<STAMP>/pytest_run.log
  ```
- [ ] Execute CLI commands from Section 6 (TC-Spec-1, TC-Spec-2, TC-C-Divergence)
- [ ] Save all metrics JSON files to `reports/2025-11-source-weights/phase_g/<STAMP>/cli/`
- [ ] Verify `sum_ratio ∈ [0.997, 1.003]` for spec-based tests
- [ ] Document expected C divergence (correlation < 0.8) in notes

**G3: Update Fix Plan Attempts**
- [ ] Record Attempt #N in `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` section
- [ ] Include:
  - Metrics: sum_ratio, correlation from pytest run
  - Artifacts: paths to `phase_g/<STAMP>/pytest_run.log`, `metrics_*.json`
  - Observations: Note that C parity < 0.8 is expected per C-PARITY-001
  - Next Actions: Proceed to Phase H (documentation updates)

### 8.2 Key Implementation Notes

**Fixture Loading:**
```python
# Use fallback path resolution (existing tests already use this pattern)
fixture_paths = [
    Path('reports/2025-11-source-weights/fixtures/two_sources.txt'),
    Path('reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt')
]
sourcefile = next((p for p in fixture_paths if p.exists()), None)
if sourcefile is None:
    pytest.skip("two_sources.txt fixture not found")
```

**Warning Assertion:**
```python
# Ensure pytest.warns is used (not subprocess stderr parsing)
with pytest.warns(UserWarning, match="Sourcefile wavelength column differs") as record:
    result = simulate(sourcefile="two_sources.txt", lambda_A=0.9768, ...)

assert len(record) >= 1, "No UserWarning raised"
assert "spec-a-core.md:151" in str(record[0].message.args[0]), \
    "Warning missing spec reference"
```

**XFAIL Marking:**
```python
@pytest.mark.xfail(
    reason="C-PARITY-001: C applies source_I weights during accumulation, "
           "violating spec requirement for equal weighting (spec-a-core.md:151). "
           "See reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md"
)
@pytest.mark.skipif(not is_parallel_enabled(), reason="NB_RUN_PARALLEL=1 required")
def test_c_divergence_reference():
    ...
```

---

## 9. Exit Criteria for Phase F

This design packet is considered complete when:
- [X] **F1:** All affected tests inventoried with current/proposed changes documented
- [X] **F2:** New acceptance criteria defined (spec-based tolerance thresholds)
- [X] **F3:** Pytest selectors validated and authoritative commands recorded in `commands.txt`
- [X] CLI bundle commands written and tested for generating comparison artifacts
- [X] Implementation guidance checklist provided for Phase G

**Status:** ✅ COMPLETE — Ready for Phase G implementation.

---

## 10. References

### Normative Documents
- **Spec:** `specs/spec-a-core.md:151` — Source weight/wavelength handling
- **Decision Memo:** `reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md` — C-PARITY-001 classification
- **Testing Strategy:** `docs/development/testing_strategy.md` — Tolerance policy

### Evidence Bundles
- **Phase A:** `reports/2025-11-source-weights/phase_a/20251009T071821Z/` — Baseline fixtures
- **Phase E:** `reports/2025-11-source-weights/phase_e/20251009T195032Z/` — Trace analysis

### Test Files
- **Target File:** `tests/test_cli_scaling.py`
- **Fixture:** `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`

### Plans
- **Initiative Plan:** `plans/active/source-weight-normalization.md` — Phase roadmap
- **Fix Plan Ledger:** `docs/fix_plan.md:4035` — SOURCE-WEIGHT-001 tracking

---

**Prepared by:** Ralph (engineer)
**Approved by:** Galph (supervisor) — Phase E completed, Phase F design packet ready
**Next Step:** Phase G implementation (Update test suite per this design packet)
