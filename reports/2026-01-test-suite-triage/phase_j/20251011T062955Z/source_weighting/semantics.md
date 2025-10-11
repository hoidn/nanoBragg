# Source Weighting Semantics Brief (`[SOURCE-WEIGHT-002]` Phase B)

**Timestamp:** 2026-01-17 (20251011T062955Z)
**Owner:** ralph
**Phase:** B (Semantics Alignment & Design)
**Status:** Draft for supervisor review

---

## Executive Summary

This brief resolves the apparent contradiction between `specs/spec-a-core.md:151-153` ("weight and wavelength columns are read but ignored") and acceptance test AT-SRC-001 ("intensity contributions SHALL sum with per-source λ and weight"). After inspecting the C reference code, architecture documentation, and test expectations, **the normative behavior is clear**: the current spec text correctly describes the C implementation, while AT-SRC-001 appears to be a forward-looking requirement not yet implemented in either C or PyTorch.

**Recommendation:** Align AT-SRC-001 with current C/PyTorch parity (equal weighting, CLI λ authority), defer per-source weighting to a future spec revision (spec-b), and fix the dtype neutrality bug blocking tests.

---

## 1. Spec Text Analysis

### 1.1 Current Normative Text (spec-a-core.md:144-155)

```
- Sources from file:
    - Each line: X, Y, Z (position vector in meters), weight (dimensionless), λ (meters). Missing
fields default to:
        - Position along −source_distance·b (source_distance default 10 m).
        - Weight = 1.0.
        - λ = λ0.
    - Positions are normalized to unit direction vectors (X,Y,Z overwrites become unit direction).
Both the weight column and the wavelength column are read but ignored: the CLI -lambda parameter
is the sole authoritative wavelength source for all sources, and equal weighting results (all
sources contribute equally via division by total source count in the steps normalization). (C-PyTorch
parity validated: correlation ≥0.999, |sum_ratio−1| ≤5e-3; see reports/2025-11-source-weights/
phase_h/20251010T002324Z/parity_reassessment.md for C reference code inspection.)
```

**Key Assertion:** Both weight and wavelength columns are **read but ignored**. CLI `-lambda` is authoritative. Equal weighting via steps division (`steps = source_count × mosaic_domains × phisteps × oversample²`).

### 1.2 AT-SRC-001 Requirement (spec-a-core.md:496-498)

```
  - AT-SRC-001 Sourcefile and weighting
    - Setup: -sourcefile with two sources having distinct weights and λ; disable other sampling.
    - Expectation: steps = 2; intensity contributions SHALL sum with per-source λ and weight,
      then divide by steps.
```

**Key Assertion:** Intensity contributions **SHALL sum with per-source λ and weight**.

### 1.3 Contradiction Summary

| Aspect | Spec §144-155 | AT-SRC-001 |
|--------|---------------|------------|
| Weight column | Read but **ignored** | **Applied** per source |
| Wavelength column | Read but **ignored** (CLI λ authority) | **Applied** per source |
| Normalization | `steps = source_count × ...` | `steps = 2` (count, not weight sum) |

---

## 2. C Reference Code Evidence

### 2.1 C Code Inspection (from arch.md §1.1.5)

**File:** `nanoBragg.c:2570-2720`
**Evidence Document:** `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md`

**Finding:** C code reads source weights into `source_I[]` array but **never multiplies them into intensity contributions**. Steps normalization divides by `sources` (count), not by weight sum. The weight column is purely documentary (may encode flux metadata for external tools).

**PyTorch Parity Status:** `docs/architecture/pytorch_design.md:93-116` documents C-PyTorch equivalence with correlation ≥0.999 across seven validation runs. Equal weighting is the **validated C behavior**.

### 2.2 Architecture Documentation Alignment

**File:** `arch.md` ADR-05 (implicit), `docs/architecture/pytorch_design.md:93-116`

**Documented Behavior:**
1. Source weights parsed but not used as multiplicative factors
2. All sources contribute equally to pixel accumulation
3. Final normalization: `I_scaled = r_e² × fluence × I / steps` where `steps = source_count × ...`
4. Weight column serves documentary purpose only

**Known C Defect (Decoupled):** Comment lines in sourcefiles incorrectly parsed as zero-weight sources, inflating count in C binary. Tracked in `[C-SOURCEFILE-001]` and does not affect weight handling semantics.

---

## 3. Test Failure Root Causes (from Phase A)

### 3.1 Dtype Mismatch (5/6 failures)

**Symptom:** Tests expect `torch.float64`, but `read_sourcefile()` defaults to `torch.float32`.

**Evidence:** `src/nanobrag_torch/io/source.py:24` — `dtype: torch.dtype = torch.float32`

**Impact:**
- `test_sourcefile_with_all_columns` expects `dtype=float64` in assertions
- `test_weighted_sources_integration` instantiates `Crystal` with `dtype=torch.float64` but `BeamConfig` sources remain float32

**Root Cause:** Boundary enforcement failure — parser does not respect caller-provided dtype when tests pass it explicitly.

### 3.2 Wavelength Column Ignored (2/6 failures)

**Symptom:** Tests assert `wavelengths[0] == 1.0e-10` (from file), but parser overrides with CLI λ.

**Evidence:** `src/nanobrag_torch/io/source.py:121-122`

```python
# Always use CLI wavelength (Option B from lambda_semantics.md)
wavelength = default_wavelength_m
```

**Impact:**
- `test_sourcefile_with_all_columns:67-68` — expects file λ values `[1.0e-10, 1.5e-10]`
- `test_weighted_sources_integration:223-224` — expects file λ values `[6.2e-10, 8.0e-10]`

**Root Cause:** AT-SRC-001 test expectations contradict current spec §151 and C reference behavior.

### 3.3 Weight Column Preserved (no failures, but test assertions exist)

**Observation:** Parser correctly reads weights into output tensor; tests verify they match file values (e.g., `test_at_src_001.py:72-73`).

**Status:** Weights are **read** and **returned** but **not applied in simulator normalization** (per spec §153). Tests do not currently verify weighted contribution semantics, only that parsing succeeds.

---

## 4. Proposed Resolution

### 4.1 Option A: Align AT-SRC-001 with Current C/PyTorch Behavior (RECOMMENDED)

**Rationale:**
1. Spec §151-153 is normative and validated against C reference
2. C code inspection confirms equal weighting (correlation ≥0.999 parity)
3. Per-source weighting is a **future enhancement**, not current behavior
4. Unblocks Sprint 1.2 immediately without physics changes

**Actions:**
1. **Update AT-SRC-001 text** (spec-a-core.md:496-498):
   ```diff
   - AT-SRC-001 Sourcefile and weighting
   -   - Setup: -sourcefile with two sources having distinct weights and λ; disable other sampling.
   -   - Expectation: steps = 2; intensity contributions SHALL sum with per-source λ and weight,
   -     then divide by steps.
   +   - Setup: -sourcefile with two sources having distinct positions and file λ/weight metadata; disable other sampling.
   +   - Expectation: steps = 2; both sources contribute equally (weight column ignored per §151); all sources use CLI -lambda (file λ ignored per §151); final intensity divided by steps.
   ```

2. **Update test expectations** (`tests/test_at_src_001.py`):
   - Remove assertions expecting file λ values to propagate
   - Update docstrings to note "weights read but currently ignored (equal weighting)"
   - Add note referencing spec §151 and `arch.md` §1.1.5

3. **Fix dtype neutrality bug** (Task B2 below)

4. **Defer per-source weighting** to `specs/spec-b.md` with explicit feature flag and gradient tests

**Advantages:**
- Minimal code changes (dtype fix only)
- Maintains C-PyTorch parity
- Unblocks Sprint 1.2 immediately
- Clear path for future enhancement

**Disadvantages:**
- Defers per-source weighting feature (accepted tradeoff for parity)

### 4.2 Option B: Implement Per-Source Weighting (NOT RECOMMENDED)

**Rationale:** Would deliver AT-SRC-001 as written but **violates C parity** and requires physics changes mid-sprint.

**Actions:**
1. Update spec §151-153 to **remove "ignored" text**
2. Modify `simulator.py` accumulation logic to multiply `I_term` by `source_weights[i]`
3. Change steps normalization to divide by `sum(weights)` instead of `count`
4. Add gradient tests for weight parameters
5. Re-run full C-PyTorch parity suite (expect failures)

**Advantages:**
- Matches literal AT-SRC-001 text

**Disadvantages:**
- Breaks C-PyTorch parity (correlation will drop below 0.999)
- Requires extensive physics validation
- Extends Sprint 1.2 timeline significantly
- Risks introducing numerical instability

---

## 5. Dtype Neutrality Strategy (Task B2)

### 5.1 Current Bug

**Location:** `src/nanobrag_torch/io/source.py:18-24`

```python
def read_sourcefile(
    filepath: Path,
    default_wavelength_m: float,
    default_source_distance_m: float = 10.0,
    beam_direction: Optional[torch.Tensor] = None,
    dtype: torch.dtype = torch.float32,  # ← HARDCODED DEFAULT
    device: torch.device = torch.device('cpu'),
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
```

**Problem:** Caller passes `dtype=torch.float64` but parser ignores it during internal tensor construction (lines 84, 88, 92).

### 5.2 Fix Strategy

**Principle:** Boundary enforcement (per `arch.md` §15) — parser respects caller dtype/device throughout.

**Implementation:**
1. Update signature to accept `Optional[torch.dtype] = None`, default to `torch.get_default_dtype()` when omitted
2. Ensure all internal `torch.tensor()` calls use provided `dtype` and `device` parameters
3. Add dtype propagation tests to `tests/test_at_src_001_simple.py`

**Example Fix:**
```python
def read_sourcefile(
    filepath: Path,
    default_wavelength_m: float,
    default_source_distance_m: float = 10.0,
    beam_direction: Optional[torch.Tensor] = None,
    dtype: Optional[torch.dtype] = None,  # ← CHANGED
    device: torch.device = torch.device('cpu'),
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    if dtype is None:
        dtype = torch.get_default_dtype()
    # ... rest of function uses `dtype` consistently
```

**Verification:**
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py` (should pass after fix)
- Add explicit `dtype=torch.float64` test case to regression suite

---

## 6. Implementation Touchpoint Map (Task B3)

### 6.1 Modules Requiring Changes

| Module | File:Line | Change Type | Guardrails |
|--------|-----------|-------------|------------|
| `io/source.py` | `src/nanobrag_torch/io/source.py:24` | Dtype default → `Optional` | Preserve vectorization (no loops), maintain differentiable direction normalization |
| `io/source.py` | `src/nanobrag_torch/io/source.py:84,88,92` | Add `dtype=` arg to `torch.tensor()` | Ensure all internal tensors use caller dtype/device |
| `config.py` | `src/nanobrag_torch/config.py:105-113` | BeamConfig dataclass | Verify `source_weights` and `source_wavelengths` fields accept tensors with arbitrary dtype |
| `tests/test_at_src_001.py` | `tests/test_at_src_001.py:1-265` | Update expectations | Align with Option A (equal weighting, CLI λ authority); add dtype propagation checks |
| `tests/test_at_src_001_simple.py` | `tests/test_at_src_001_simple.py:29-32` | Dtype handling | Add explicit `dtype=torch.float64` test case |

### 6.2 Modules NOT Requiring Changes

**Simulator accumulation:** No changes to `simulator.py` physics path if Option A is adopted. Current equal-weighting logic (`steps = sources × ...`) is correct per spec §153.

**BeamConfig plumbing:** Existing fields (`source_directions`, `source_weights`, `source_wavelengths`) already accept tensors. No schema changes needed.

---

## 7. Verification Checklist (Task B4)

### 7.1 Phase C (Implementation) Exit Criteria

**Targeted Tests (must pass after dtype fix):**
- `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py` (currently 1 test)
- `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_all_columns`
- `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_sourcefile_with_missing_columns`

**New Regression Test (add to Phase C):**
- Explicit float32/float64 dtype propagation test in `test_at_src_001_simple.py`

**Gradient Checks (if per-source λ/weight ever enabled):**
- `torch.autograd.gradcheck` on `source_weights` parameter (deferred to spec-b)
- `torch.autograd.gradcheck` on `source_wavelengths` parameter (deferred to spec-b)

### 7.2 Phase D (Parity & Documentation) Exit Criteria

**CPU Validation:**
- All 7 tests in `test_at_src_001.py` pass (currently 1/7 passing)
- Correlation ≥0.999 maintained vs C reference (if parallel tests exist)

**GPU Validation (if CUDA available):**
- Smoke test with `device='cuda'` per `docs/development/testing_strategy.md` §1.4

**Documentation Updates:**
- Update `specs/spec-a-core.md:496-498` (AT-SRC-001 text per Option A)
- Update `docs/architecture/pytorch_design.md:93-116` (no changes if Option A; already documents equal weighting)
- Update `docs/development/pytorch_runtime_checklist.md` (add dtype propagation reminder for parsers)
- Note in `docs/fix_plan.md` that per-source weighting deferred to spec-b

**Artifact Expectations:**
- Phase C: `reports/.../phase_c/<STAMP>/source_weighting/{pytest.log, dtype_test.py, commands.txt}`
- Phase D: `reports/.../phase_d/<STAMP>/source_weighting/{pytest.log, spec_diff.patch, docs_updates.txt, commands.txt}`

---

## 8. Spec Amendment Proposal

### 8.1 Recommended Change to spec-a-core.md

**Location:** Lines 496-498 (AT-SRC-001)

**Current Text:**
```
  - AT-SRC-001 Sourcefile and weighting
    - Setup: -sourcefile with two sources having distinct weights and λ; disable other sampling.
    - Expectation: steps = 2; intensity contributions SHALL sum with per-source λ and weight,
      then divide by steps.
```

**Proposed Text (Option A):**
```
  - AT-SRC-001 Sourcefile and weighting
    - Setup: -sourcefile with two sources having distinct positions and file λ/weight metadata; disable other sampling.
    - Expectation: steps = 2; both sources contribute equally (weight column read but ignored per §151); all sources use CLI -lambda (file λ read but ignored per §151); final intensity divided by steps. Direction normalization SHALL be preserved for differentiability.
```

**Rationale:** Aligns acceptance test with validated C behavior and current spec text §151-153.

### 8.2 Future Spec-B Enhancement (Deferred)

**Feature:** Per-source wavelength and weight application

**Proposal for spec-b.md:**
```
  - AT-SRC-002 Per-source wavelength and weight application (future)
    - Setup: -sourcefile with two sources having distinct weights and λ; enable via -apply_source_weights flag.
    - Expectation: For each source i, compute q_i = (d − i) / λ_i (using file λ_i); multiply I_term by weight_i before accumulation; normalize by sum(weights) instead of source count.
    - Gradient checks: torch.autograd.gradcheck SHALL pass for source_weights and source_wavelengths parameters (dtype=torch.float64, eps=1e-6).
```

**Blockers:**
- Requires C reference implementation first (for parity validation)
- Needs physics review (wavelength-dependent q affects Ewald sphere filtering)
- Must verify differentiability of per-source accumulation

---

## 9. Risk Assessment

### 9.1 Option A Risks (RECOMMENDED)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Test authors intended per-source weighting | Medium | Low | Document deferral in spec-b; obtain supervisor approval before Phase C |
| Users expect per-source λ from file | Low | Low | Spec §151 is normative; warning emitted when file λ differs from CLI |
| C reference later adds weighting | Low | Medium | Track C updates in fix_plan; revisit if parity breaks |

### 9.2 Option B Risks (NOT RECOMMENDED)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| C-PyTorch parity breaks | High | Critical | Full parity revalidation required; blocks other sprints |
| Gradient instability with weights | Medium | High | Extensive gradcheck tests; potential numeric issues |
| Timeline extension | High | High | None — conflicts with Sprint 1 goals |

---

## 10. Supervisor Decision Point

**Question for galph:**

Do you approve **Option A** (align AT-SRC-001 with current C behavior, defer per-source weighting to spec-b)?

**If YES:**
- Ralph proceeds to Phase C with dtype fix + test updates
- Expected Phase C duration: 1 loop (2-4 hours)
- Expected Phase D duration: 1 loop (1-2 hours)
- Sprint 1.2 closure: within 1 day

**If NO (require Option B per-source weighting):**
- Ralph authors expanded Phase C plan with physics changes
- Expected Phase C duration: 3-4 loops (1-2 days)
- Requires C reference reimplementation or parity waiver
- Sprint 1.2 closure: 3-5 days

**Request:** Please confirm Option A approval in next supervisor sync before ralph launches Phase C implementation.

---

## References

- **Phase A Evidence:** `reports/2026-01-test-suite-triage/phase_j/20251011T062017Z/source_weighting/`
- **Spec Text:** `specs/spec-a-core.md:144-155` (§Sources), `specs/spec-a-core.md:496-498` (AT-SRC-001)
- **Architecture:** `arch.md` §8, §15; `docs/architecture/pytorch_design.md:93-116`
- **C Reference:** `nanoBragg.c:2570-2720`
- **Parity Report:** `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md`
- **Test Files:** `tests/test_at_src_001.py`, `tests/test_at_src_001_simple.py`
- **Parser:** `src/nanobrag_torch/io/source.py`

---

**END SEMANTICS BRIEF**
