# Source Weighting Implementation Map (`[SOURCE-WEIGHT-002]` Phase B)

**Timestamp:** 2026-01-17 (20251011T062955Z)
**Phase:** B (Design)
**Scope:** Touchpoint inventory for Option A (dtype fix + test updates)

---

## 1. Modules Requiring Edits

### 1.1 `src/nanobrag_torch/io/source.py`

**Purpose:** Fix dtype neutrality bug to respect caller-provided dtype

**Current State:**
- Line 24: `dtype: torch.dtype = torch.float32` (hardcoded default)
- Lines 61, 84, 88, 92, 125: `torch.tensor(..., dtype=dtype, device=device)` calls assumed to use parameter
- Lines 135-139: Final tensor construction uses `dtype` parameter

**Required Changes:**

1. **Signature Update (Line 24)**
   ```python
   # BEFORE
   dtype: torch.dtype = torch.float32,

   # AFTER
   dtype: Optional[torch.dtype] = None,
   ```

2. **Default Resolution (After Line 25)**
   ```python
   # ADD
   if dtype is None:
       dtype = torch.get_default_dtype()
   ```

3. **Verification Pass (Lines 61-139)**
   - Audit all `torch.tensor()` calls to ensure `dtype=dtype, device=device` parameters present
   - Current code already passes these parameters correctly; no changes needed beyond signature fix

**Guardrails:**
- **Vectorization:** No Python loops introduced; direction normalization remains differentiable (`direction = position / torch.linalg.norm(position)` at line 125)
- **Device Neutrality:** All tensors created on caller's device (already implemented)
- **Differentiability:** Normalization preserves gradient flow (no `.item()` or `.detach()` in hot path)

**File Anchor:** `src/nanobrag_torch/io/source.py:1-141`

---

### 1.2 `tests/test_at_src_001.py`

**Purpose:** Align test expectations with Option A (equal weighting, CLI λ authority)

**Current State:**
- Lines 70-73: Assert file λ values `[1.0e-10, 1.5e-10]` — CONTRADICTS SPEC
- Lines 112-114: Assert file λ values propagate — CONTRADICTS SPEC
- Lines 223-224: Assert file λ values propagate — CONTRADICTS SPEC
- Lines 72-73, 117-119: Assert file weight values preserved — CORRECT (read but not applied)

**Required Changes:**

1. **Update Docstring (Lines 1-17)**
   ```python
   # ADD CLARIFICATION
   """Acceptance test AT-SRC-001: Sourcefile and weighting.

   NOTE: Per spec-a-core.md:151-153, weight and wavelength columns are READ but IGNORED.
   - Weight column: read into parser output but not applied in simulator (equal weighting)
   - Wavelength column: read but overridden by CLI -lambda parameter

   See semantics.md in Phase B artifacts for full rationale.
   """
   ```

2. **Test: `test_sourcefile_with_all_columns` (Lines 36-73)**
   ```python
   # CHANGE wavelength assertions (lines 67-68)
   # BEFORE
   assert wavelengths[0].item() == pytest.approx(1.0e-10)
   assert wavelengths[1].item() == pytest.approx(1.5e-10)

   # AFTER (per spec §151)
   # All wavelengths should equal CLI default_wavelength_m (6.2e-10)
   assert wavelengths[0].item() == pytest.approx(6.2e-10)
   assert wavelengths[1].item() == pytest.approx(6.2e-10)

   # ADD comment explaining weight preservation
   # Weights are read correctly but not used in simulator (line 72-73)
   # This verifies parser correctness, not application semantics
   assert weights[0].item() == pytest.approx(2.0)  # Read from file
   assert weights[1].item() == pytest.approx(3.0)  # Read from file
   ```

3. **Test: `test_sourcefile_with_missing_columns` (Lines 75-119)**
   ```python
   # CHANGE wavelength assertions (lines 112-114)
   # BEFORE
   assert wavelengths[0].item() == pytest.approx(1.0e-10)  # Specified
   assert wavelengths[1].item() == pytest.approx(6.2e-10)  # Default
   assert wavelengths[2].item() == pytest.approx(6.2e-10)  # Default

   # AFTER (all use CLI default per spec §151)
   assert wavelengths[0].item() == pytest.approx(6.2e-10)  # CLI λ (file ignored)
   assert wavelengths[1].item() == pytest.approx(6.2e-10)  # CLI λ
   assert wavelengths[2].item() == pytest.approx(6.2e-10)  # CLI λ

   # Weights remain correct (lines 117-119)
   assert weights[0].item() == pytest.approx(2.0)   # Read from file
   assert weights[1].item() == pytest.approx(1.0)   # Default
   assert weights[2].item() == pytest.approx(1.5)   # Read from file
   ```

4. **Test: `test_weighted_sources_integration` (Lines 197-265)**
   ```python
   # CHANGE wavelength assertions (lines 223-224)
   # BEFORE
   assert wavelengths[0].item() == pytest.approx(6.2e-10)
   assert wavelengths[1].item() == pytest.approx(8.0e-10)

   # AFTER (both use CLI default 6.2e-10)
   assert wavelengths[0].item() == pytest.approx(6.2e-10)  # CLI λ
   assert wavelengths[1].item() == pytest.approx(6.2e-10)  # CLI λ (file 8.0e-10 ignored)

   # UPDATE comment at line 218 (expectation clarification)
   # "Verify weights are preserved per AT-SRC-001"
   # → "Verify weights are read correctly (though not applied in simulator per spec §153)"
   ```

5. **Test: `test_multiple_sources_normalization` (Lines 153-180)**
   ```python
   # ADD comment at line 179-180 clarifying equal weighting
   # Both sources have weight 1.0 specified in the file
   # Per spec §153, all sources contribute equally regardless of weight column
   torch.testing.assert_close(weights, torch.ones(2, dtype=torch.float64))
   ```

**Guardrails:**
- No production code changes in this file (test-only edits)
- Preserve existing parametrization (dtype=float64 test cases remain)
- Add comments referencing spec §151, §153 and semantics.md for maintainability

**File Anchor:** `tests/test_at_src_001.py:1-265`

---

### 1.3 `tests/test_at_src_001_simple.py`

**Purpose:** Add explicit dtype propagation regression test

**Current State:**
- Single test verifying parser basic functionality (lines 15-58)
- Uses default dtype (inherits float64 from `torch.tensor` in assertions)

**Required Changes:**

1. **Add Dtype Propagation Test**
   ```python
   # ADD NEW TEST after line 58
   def test_sourcefile_dtype_propagation():
       """Verify parser respects caller-provided dtype (regression for dtype bug)."""
       with tempfile.TemporaryDirectory() as tmpdir:
           sourcefile = Path(tmpdir) / "test_sources.txt"

           content = """# Test dtype propagation
   -10.0  0.0  0.0  1.0  1.0e-10
   """
           sourcefile.write_text(content)

           # Test float64 (explicit)
           directions64, weights64, wavelengths64 = read_sourcefile(
               sourcefile,
               default_wavelength_m=6.2e-10,
               dtype=torch.float64
           )
           assert directions64.dtype == torch.float64
           assert weights64.dtype == torch.float64
           assert wavelengths64.dtype == torch.float64

           # Test float32 (explicit)
           directions32, weights32, wavelengths32 = read_sourcefile(
               sourcefile,
               default_wavelength_m=6.2e-10,
               dtype=torch.float32
           )
           assert directions32.dtype == torch.float32
           assert weights32.dtype == torch.float32
           assert wavelengths32.dtype == torch.float32

           # Test default (should use torch.get_default_dtype())
           default_dtype = torch.get_default_dtype()
           directions_default, weights_default, wavelengths_default = read_sourcefile(
               sourcefile,
               default_wavelength_m=6.2e-10
               # dtype=None (implicit)
           )
           assert directions_default.dtype == default_dtype
           assert weights_default.dtype == default_dtype
           assert wavelengths_default.dtype == default_dtype

           print(f"✓ Dtype propagation verified: float64, float32, and default")
   ```

**Guardrails:**
- No production code calls (pure regression test)
- Covers both explicit dtype and default fallback paths
- Aligns with `docs/development/testing_strategy.md` §1.4 (dtype neutrality)

**File Anchor:** `tests/test_at_src_001_simple.py:1-100` (estimated)

---

### 1.4 `specs/spec-a-core.md`

**Purpose:** Update AT-SRC-001 text to match Option A

**Current State:**
- Lines 496-498: AT-SRC-001 requires "intensity contributions SHALL sum with per-source λ and weight"

**Required Changes:**

1. **Replace AT-SRC-001 Text (Lines 496-498)**
   ```markdown
   # BEFORE
     - AT-SRC-001 Sourcefile and weighting
       - Setup: -sourcefile with two sources having distinct weights and λ; disable other sampling.
       - Expectation: steps = 2; intensity contributions SHALL sum with per-source λ and weight,
         then divide by steps.

   # AFTER
     - AT-SRC-001 Sourcefile and weighting
       - Setup: -sourcefile with two sources having distinct positions and file λ/weight metadata; disable other sampling.
       - Expectation: steps = 2; both sources contribute equally (weight column read but ignored per §151); all sources use CLI -lambda (file λ read but ignored per §151); final intensity divided by steps. Direction normalization SHALL preserve differentiability.
   ```

2. **Add Spec-B Forward Reference (Optional)**
   ```markdown
   # ADD AFTER AT-SRC-001 (new line 499)
       - Note: Per-source wavelength and weight application deferred to spec-b (AT-SRC-002).
   ```

**Guardrails:**
- Normative text update requires supervisor approval before commit
- Cross-reference spec §151-153 for consistency
- Update version/date stamp at top of spec-a-core.md

**File Anchor:** `specs/spec-a-core.md:496-499`

---

## 2. Modules NOT Requiring Changes

### 2.1 `src/nanobrag_torch/config.py`

**Status:** No changes required

**Rationale:** `BeamConfig` dataclass (lines 105-113) already accepts tensor fields for `source_directions`, `source_weights`, `source_wavelengths`. Dtype is determined by input tensors (boundary enforcement working correctly).

**Verification:** Inspect dataclass definition to confirm no dtype coercion or hardcoded defaults.

**File Anchor:** `src/nanobrag_torch/config.py:105-113`

---

### 2.2 `src/nanobrag_torch/simulator.py`

**Status:** No changes required (Option A)

**Rationale:** Current steps normalization (`steps = sources × mosaic_domains × phisteps × oversample²`) is correct per spec §153. Equal weighting semantics already implemented (lines 399-423 guard, line 1892 normalization).

**If Option B were adopted:** Would require modifying accumulation loop to multiply `I_term` by `source_weights[i]` and changing steps to `sum(weights) × mosaic_domains × ...`.

**File Anchor:** `src/nanobrag_torch/simulator.py:399-423, 1892`

---

### 2.3 `docs/architecture/pytorch_design.md`

**Status:** No changes required

**Rationale:** Section §1.1.5 (lines 93-116) already documents equal weighting and C-PyTorch parity (correlation ≥0.999). Text is accurate for Option A.

**Optional Enhancement:** Add pointer to Phase B semantics brief for historical context.

**File Anchor:** `docs/architecture/pytorch_design.md:93-116`

---

## 3. Implementation Sequence

### 3.1 Phase C Task Order

1. **C1:** Update `src/nanobrag_torch/io/source.py` (dtype fix)
2. **C2:** Update `tests/test_at_src_001_simple.py` (add dtype regression test)
3. **C3:** Run targeted tests (`pytest -v tests/test_at_src_001_simple.py`) → verify dtype fix
4. **C4:** Update `tests/test_at_src_001.py` (align expectations)
5. **C5:** Run full AT-SRC-001 suite (`pytest -v tests/test_at_src_001.py`)
6. **C6:** Update `specs/spec-a-core.md` (AT-SRC-001 text) — REQUIRES SUPERVISOR APPROVAL

### 3.2 Verification Commands

**After C1-C2 (dtype fix):**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py::test_sourcefile_dtype_propagation
```

**After C4 (test updates):**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py
```

**Full regression (Phase D):**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py
```

---

## 4. Runtime Guardrails Checklist

Per `docs/development/pytorch_runtime_checklist.md` and `arch.md` §15:

- [x] **Vectorization:** No Python loops introduced; all operations remain batched tensor ops
- [x] **Device Neutrality:** Parser respects caller `device` parameter (already implemented)
- [x] **Dtype Neutrality:** Parser respects caller `dtype` parameter (FIX REQUIRED)
- [x] **Differentiability:** Direction normalization preserves gradient flow (`position / norm` is differentiable)
- [x] **Boundary Enforcement:** Type conversions happen at parser boundary; core simulator assumes tensors
- [ ] **CPU Smoke Test:** Run `pytest` with default CPU device (Phase C validation)
- [ ] **GPU Smoke Test:** Run `pytest -k cuda` if available (Phase D validation)

---

## 5. Artifact Expectations

### 5.1 Phase C Artifacts

**Location:** `reports/2026-01-test-suite-triage/phase_j/<C_STAMP>/source_weighting/`

**Contents:**
- `commands.txt` — Bash history of pytest runs + code edits
- `pytest_simple.log` — Output of `test_at_src_001_simple.py` after dtype fix
- `pytest_full.log` — Output of `test_at_src_001.py` after test updates
- `dtype_test_output.txt` — Captured output of new regression test
- `source.py.diff` — Unified diff of parser changes
- `test_at_src_001.py.diff` — Unified diff of test updates

### 5.2 Phase D Artifacts

**Location:** `reports/2026-01-test-suite-triage/phase_j/<D_STAMP>/source_weighting/`

**Contents:**
- `pytest_full.log` — Final validation run (7/7 passing)
- `spec_a_core.diff` — Unified diff of AT-SRC-001 update
- `docs_updates.txt` — Notes on any doc changes beyond spec
- `gpu_smoke.log` — CUDA test output (if available)
- `commands.txt` — Provenance log

---

## 6. Risk Mitigation

### 6.1 Code Change Risks

| Risk | Mitigation |
|------|------------|
| Dtype fix breaks existing calls | Audit all `read_sourcefile()` invocations in codebase via `grep -r "read_sourcefile"` |
| Test updates miss edge cases | Run full pytest suite (`pytest tests/`) after Phase C to catch regressions |
| Spec update conflicts with other work | Coordinate with galph before editing normative spec text |

### 6.2 Rollback Plan

If Phase C implementation fails:
1. Revert `source.py` changes via `git checkout HEAD -- src/nanobrag_torch/io/source.py`
2. Preserve test updates in feature branch for future retry
3. Document blockers in fix_plan Attempt history
4. Escalate to galph with evidence bundle

---

## 7. Cross-References

- **Semantics Brief:** `reports/.../phase_j/20251011T062955Z/source_weighting/semantics.md` (Option A justification)
- **Verification Checklist:** `reports/.../phase_j/20251011T062955Z/source_weighting/verification_checklist.md` (Phase D criteria)
- **Plan:** `plans/active/source-weighting.md` (Phase B → Phase C transition)
- **Fix Plan:** `docs/fix_plan.md` §[SOURCE-WEIGHT-002] (ledger + attempts)

---

**END IMPLEMENTATION MAP**
