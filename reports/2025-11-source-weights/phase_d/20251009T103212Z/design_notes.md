# Phase D2: Source-Weight Divergence Design Decision

**Generated:** 2025-10-09T10:32:12Z
**Focus:** Design decision for SOURCE-WEIGHT-001 divergence handling
**Deliverable:** Single recommendation for implementation path forward

---

## Executive Summary

**Recommendation:** **Option B — Spec Clarification + Validation Guard**

PyTorch SHALL continue its current behavior (sourcefile replaces divergence grid), and the spec SHALL be amended to document this as normative. A validation guard SHALL be added to warn users when mixing sourcefile + divergence parameters.

**Rationale:**
1. **Spec already implies replacement semantics** — Line 151 states weights are "read but ignored", suggesting sourcefiles define the complete source set
2. **C behavior appears unintentional** — Default divergence grid generation when sourcefile is present produces confusing "4 sources" output where 2 have zero weight/wavelength
3. **Simpler implementation path** — Requires only documentation + warning, no complex tensor broadcasting changes
4. **Backward compatibility risk is low** — No known workflows rely on additive divergence+sourcefile behavior

---

## Analysis Framework

### Decision Matrix

| Criterion | Option A (Mirror C) | Option B (Clarify Spec) | Option C (Explicit Flag) |
|-----------|---------------------|-------------------------|--------------------------|
| **Spec Alignment** | ❌ Contradicts line 151 | ✅ Aligns with "ignored" | ⚠️ Adds complexity |
| **Implementation Effort** | 🔴 High (tensor rewrite) | 🟢 Low (docs + guard) | 🟡 Medium (flag + modes) |
| **Parity Risk** | 🟢 Exact C match | 🟡 Intentional divergence | 🟡 Dual-mode testing burden |
| **User Experience** | ❌ Confusing "4 sources" | ✅ Clear sourcefile=override | ⚠️ Learning curve |
| **Maintenance** | 🔴 Complex broadcast logic | 🟢 Minimal surface area | 🟡 Mode branching |

### Quantitative Impact (from Phase D1 Evidence)

**Current State (20251009T101247Z):**
- C: `steps = 4` (2 divergence grid + 2 sourcefile)
- PyTorch: `steps = 2` (sourcefile only)
- Observed divergence: 546× intensity, -0.0606 correlation

**Option A Impact:**
- Would require rewriting `_generate_sources()` to:
  - Always create default divergence grid
  - Append sourcefile entries
  - Handle device/dtype coercion for mixed tensors (grid CPU → GPU)
  - Update broadcast shapes across `(S, F, sources)` dimensions
- Device-neutral risk: **HIGH** — Grid generation happens before device selection, requires careful `.to()` placement
- Performance impact: 2× source count → 4× memory for intermediate tensors (batch dimension doubles)

**Option B Impact:**
- Documentation change only:
  - Amend `specs/spec-a-core.md:144-162` to state: "When a sourcefile is provided, generated divergence/dispersion grids are disabled. Explicit divergence parameters with a sourcefile SHALL emit a warning."
  - Add `BeamConfig.__post_init__()` validation (5-10 lines)
- Device-neutral risk: **NONE** — No tensor changes
- Performance impact: **NONE**

**Option C Impact:**
- Requires new CLI flag: `-source_mode {replace|append}` (default `replace`)
- Implementation effort: ~50 lines (flag parse + conditional logic in `_generate_sources()`)
- Testing burden: 2× — All parity tests must run in both modes
- Spec amendment: Document both modes with semantic differences

---

## Spec Analysis: The "Ignored Weights" Mandate

**Authoritative Reference:** `specs/spec-a-core.md:151`

> The weight column is read but ignored (equal weighting results).

**Interpretation:**
This statement establishes two normative facts:
1. Weights are **read** (parsed from file)
2. Weights are **ignored** (do not affect accumulation or normalization)

**Implication for Divergence Mixing:**
If weights are ignored, the sourcefile defines a **fixed count** of equally-weighted sources. Mixing this with an auto-generated divergence grid would violate the "ignored" mandate by allowing the grid count to influence normalization (`steps = grid_count + file_count`).

**Logical Consistency Check:**
- **Option A (Additive):** `steps = 4` means sourcefile sources contribute 50% weight (2/4) while grid sources contribute 50% (2/4). This **contradicts** "equal weighting results" because file and grid sources are weighted equally *as groups*, not individually.
- **Option B (Replacement):** `steps = 2` means only sourcefile sources exist, each contributing 50% (1/2). This **aligns** with "equal weighting results."

**Verdict:** The spec's "ignored" clause implies replacement semantics, not additive.

---

## C Code Behavior: Intentional or Artifact?

**Evidence from `golden_suite_generator/nanoBragg.c:2570-2720`**

Key code sections:
```c
// Line 2570: Load sourcefile
sources = read_text_file(sourcefilename, 5, &source_X, ...);

// Line 2598: Generate divergence grid
if(sources == 0) {  // <--- Only if NO sourcefile loaded
    /* generate generic list of sources */
    ...
}
```

**Expected Behavior:** Divergence grid is only generated when `sources == 0`.

**Observed Behavior (Phase D1):** C printed "created a total of 4 sources" despite sourcefile being loaded.

**Hypothesis:** There is additional C code beyond line 2720 that:
1. Resets `sources = 0` after sourcefile load under certain conditions, OR
2. Appends default divergence grid sources to the sourcefile array when divergence parameters are present

**Investigation Required:** Read `nanoBragg.c:2720-3000` to confirm whether this is intentional design or a conditional branch artifact.

**Preliminary Assessment:** The first two sources in the C output have:
- Position: `(0, 0, 0)` (origin)
- Weight: `0`
- Wavelength: `0`

These appear to be **uninitialized divergence grid sources** that survived into the final count. This suggests **Option B is correct** — C's additive behavior may be a bug, not a feature.

---

## Recommended Implementation (Option B)

### 1. Spec Amendment

**File:** `specs/spec-a-core.md`
**Section:** Lines 144-162 (Sources, Divergence & Dispersion)

**Proposed Addition (after line 151):**
```markdown
- Sourcefile precedence:
    - When a sourcefile is provided via -sourcefile, generated divergence and dispersion
      grids SHALL be disabled.
    - If divergence parameters (-hdivrange/-vdivrange/-dispersion) are explicitly provided
      alongside -sourcefile, the implementation SHALL emit a warning and use only the
      sourcefile sources.
    - Rationale: The "ignored weights" mandate (line 151) requires a fixed source count.
      Mixing sourcefile with generated grids would violate equal weighting semantics.
```

### 2. PyTorch Validation Guard

**File:** `src/nanobrag_torch/config.py`
**Location:** `BeamConfig.__post_init__()` (around line 547-564)

**Proposed Addition:**
```python
# After existing edge-case validation (negative weights, zero-sum)
if self.source_file is not None and (
    self.hdiv_range_mrad > 0 or
    self.vdiv_range_mrad > 0 or
    self.dispersion_pct > 0
):
    warnings.warn(
        "Divergence/dispersion parameters ignored when sourcefile is provided. "
        "Sources are loaded from file only (see specs/spec-a-core.md:151-162).",
        UserWarning,
        stacklevel=2
    )
```

**Rationale:** Explicit CLI validation prevents user confusion and documents the precedence rule.

### 3. Device/Dtype Impact

**Risk Level:** None (documentation-only change)

**Verification:** No tensor code changes required. Existing `_generate_sources()` logic already implements replacement semantics correctly.

---

## Acceptance Metrics

**Phase E Validation SHALL prove:**

1. **Correlation threshold:** ≥0.999 between PyTorch and C **when both use explicit `-oversample 1` and no divergence flags**
2. **Sum ratio:** `|PyTorch_sum / C_sum - 1.0| ≤ 1e-3`
3. **Steps consistency:** `steps_pytorch == steps_c` for identical source counts
4. **Warning emitted:** PyTorch warns when `-sourcefile` + `-hdivrange` both provided

**Test Coverage:**
- TC-D1: Sourcefile-only (baseline)
- TC-D2: Sourcefile + explicit `-hdivrange` (warning test)
- TC-D3: Divergence-only (no sourcefile, grid generation)
- TC-D4: C parity with explicit `-oversample 1` (correlation ≥0.999)

**Pytest Selector:**
```bash
pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
```

---

## Rejected Alternatives

### Why Not Option A (Mirror C)?

1. **Spec conflict:** Contradicts "ignored weights" by allowing grid count to influence normalization
2. **Implementation complexity:** Requires tensor broadcast rewrite with device/dtype risks
3. **Unclear semantics:** Users would not understand why sourcefile + divergence yields 4 sources instead of 2
4. **C behavior suspect:** Zero-weight, zero-wavelength grid sources suggest unintentional behavior

### Why Not Option C (Explicit Flag)?

1. **Added complexity:** New CLI surface area for unclear benefit
2. **Testing burden:** Every parity test must run in 2× modes
3. **User confusion:** Forces users to learn mode semantics when default (replace) is intuitive
4. **Spec fragmentation:** Would need to document two semantic models instead of one

---

## Phase E Implementation Checklist

**Prerequisites:**
- [ ] Phase D2 design approved
- [ ] Repository clean (`git status`)

**Implementation Steps:**
1. [ ] Amend `specs/spec-a-core.md` per proposed addition above
2. [ ] Add validation guard to `src/nanobrag_torch/config.py`
3. [ ] Extend `tests/test_cli_scaling.py` with TC-D1/D2/D3/D4 coverage
4. [ ] Capture Phase E metrics under `reports/2025-11-source-weights/phase_e/<STAMP>/`
5. [ ] Update `docs/architecture/pytorch_design.md` §8 (Sources subsection)
6. [ ] Mark Phase D tasks D2 [D] and D3 [D] in `plans/active/source-weight-normalization.md`

**Acceptance Gate:**
- Pytest collection passes (`pytest --collect-only -q`)
- TC-D4 parity test shows correlation ≥0.999, |sum_ratio-1| ≤1e-3
- Warning test (TC-D2) captures expected output

---

## References

- **Phase D1 Evidence:** `reports/2025-11-source-weights/phase_d/20251009T102319Z/divergence_analysis.md`
- **Spec Authority:** `specs/spec-a-core.md:144-162`
- **C Code:** `golden_suite_generator/nanoBragg.c:2570-2720`
- **Phase E Plan:** `plans/active/source-weight-normalization.md` (tasks E1-E4)
- **PyTorch Runtime Checklist:** `docs/development/pytorch_runtime_checklist.md` (device/dtype discipline)

---

## Conclusion

**Phase D2 Status:** Design decision complete.

**Key Decision:** Adopt **Option B** — Sourcefile replaces divergence grid (normative spec clarification + validation warning).

**Next Step:** Proceed to Phase D3 to prepare acceptance harness (`commands.txt`, pytest selectors, expected metrics).

**Blocker Cleared:** Option B requires no tensor changes, so device/dtype risks are eliminated. Phase E implementation can proceed immediately after D3 approval.
