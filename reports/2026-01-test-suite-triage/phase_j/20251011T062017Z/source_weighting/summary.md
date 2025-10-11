# Source Weighting Baseline Capture Summary

**Timestamp:** 20251011T062017Z
**Initiative:** [SOURCE-WEIGHT-002] Sprint 1.2, Phase A
**Status:** COMPLETE — Evidence captured, ready for implementation planning

---

## Test Results

**Command:** `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py`

**Outcome:**
- **Total tests:** 7
- **Passed:** 1 (14.3%)
- **Failed:** 6 (85.7%)
- **Runtime:** 2.08s
- **Exit code:** 1 (failures present)

---

## Failure Analysis

### Root Causes Identified

**1. dtype Mismatch (5 failures)**
- Tests expect `float64` but implementation returns `float32`
- Affected tests:
  - `test_sourcefile_with_all_columns` (line 64)
  - `test_sourcefile_default_position` (line 148)
  - `test_multiple_sources_normalization` (line 180)
  - `test_weighted_sources_integration` (line 224, indirect)
  - `test_sourcefile_parsing` (line 41)
- **Cause:** `read_sourcefile()` in `io/source.py` likely defaults to float32
- **Fix:** Add explicit `dtype=torch.float64` parameter or match test expectations

**2. Wavelength Column Ignored (2 failures)**
- Wavelength values from sourcefile are not being read/applied
- Affected tests:
  - `test_sourcefile_with_missing_columns` — expects 1.0e-10, got default 6.2e-10
  - `test_weighted_sources_integration` — expects 8.0e-10, got default 6.2e-10
- **Spec contradiction noted:** Spec line 150-151 states "wavelength column is read but ignored", but AT-SRC-001 requires per-source λ
- **Current behavior:** Warning message confirms "sourcefile wavelengths are ignored" (line 51 warning)
- **Fix:** Implement per-source wavelength support as required by AT-SRC-001

### Passed Test

**`test_empty_sourcefile`** — Correctly raises `ValueError` for empty source files

---

## Failure Categorization

| Category | Count | Description |
|----------|-------|-------------|
| Implementation Bugs | 6 | Missing features or incorrect behavior |
| dtype Mismatch | 5 | float32/float64 inconsistency |
| Wavelength Parsing | 2 | Sourcefile λ column ignored |

---

## Key Observations

1. **Primary blocker:** dtype mismatch is systematic across all I/O tests
2. **Spec clarification needed:** Lines 150-151 contradict AT-SRC-001 requirement
3. **Warning behavior:** Implementation correctly warns about ignored wavelengths, but AT-SRC-001 requires them
4. **Weight column:** Weight values appear to be preserved (no failures on weight assertions)

---

## Environment

- **Python:** 3.13.5
- **PyTorch:** 2.7.1+cu126
- **CUDA:** Available (12.6)
- **Git branch:** feature/spec-based-2
- **Git commit:** fa4995a8 [SYNC i=349] actor=ralph status=running

---

## Next Steps (Phase B)

1. **Fix dtype consistency:**
   - Update `read_sourcefile()` to accept/default to `dtype=torch.float64`
   - Ensure all returned tensors match the specified dtype

2. **Implement per-source wavelength:**
   - Parse wavelength column from sourcefile
   - Return as 5th column in result tensor
   - Update spec interpretation (resolve lines 150-151 vs AT-SRC-001 contradiction)

3. **Validate against AT-SRC-001:**
   - Ensure `steps = 2` calculation includes source count
   - Verify intensity normalization uses per-source weights and wavelengths
   - Add integration test demonstrating correct weighted multi-source calculation

---

## Artifacts

- **Pytest log:** `logs/pytest.log` (full test output with stack traces)
- **JUnit XML:** `artifacts/pytest.xml` (machine-readable test results)
- **Environment:** `env/python_version.txt`, `env/pytorch_version.txt`, `env/git_status.txt`, `env/git_commit.txt`
- **Commands:** `commands.txt` (exact reproduction commands)

---

**Phase A Status:** ✅ COMPLETE — All baseline evidence captured and categorized
**Next:** Proceed to Phase B implementation planning once approved
