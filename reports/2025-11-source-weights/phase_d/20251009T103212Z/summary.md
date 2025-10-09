# Phase D2 Summary: Design Decision Complete

**Timestamp:** 2025-10-09T10:32:12Z
**Deliverable:** Design recommendation for SOURCE-WEIGHT-001 divergence handling
**Status:** ✅ **COMPLETE** — Recommendation: Option B (Spec Clarification + Validation Guard)

---

## What Was Decided

**Chosen Path:** **Option B — Sourcefile Replaces Divergence Grid**

PyTorch's current behavior (sourcefile-only source generation) SHALL remain unchanged. The spec SHALL be amended to document this as normative, and a validation warning SHALL be added to alert users when mixing `-sourcefile` with divergence parameters.

**Key Rationale:**
1. Aligns with spec line 151 "weights ignored" mandate
2. Simpler implementation (docs + 5-line validation guard)
3. C's additive behavior appears unintentional (zero-weight/wavelength grid sources)
4. No device/dtype risk (no tensor changes)

---

## Artifacts Generated

1. **`design_notes.md`** (5.8KB)
   - Decision matrix comparing Options A/B/C
   - Quantitative impact analysis from Phase D1 evidence
   - Spec interpretation: "ignored weights" implies replacement semantics
   - C code analysis: Divergence grid sources with zero weight suggest bug
   - Implementation checklist for Phase E
   - Acceptance metrics: correlation ≥0.999, |sum_ratio-1| ≤1e-3

2. **`pytest_collect.log`** (capture proof)
   - Collection successful: 682 tests discovered
   - Exit code: 0 (no import errors)

3. **`commands.txt`** (reproduction log)
   - Timestamped command sequence for Phase D2
   - Expected outputs documented

4. **`summary.md`** (this file)
   - High-level framing of decision and next steps

---

## Next Steps (Phase D3)

**Goal:** Prepare acceptance harness for Phase E implementation validation

**Tasks:**
1. Define pytest selector:
   ```bash
   pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
   ```
2. Draft CLI command bundle:
   ```bash
   # TC-D4: C parity test (explicit oversample to isolate weight fix)
   C:  "$NB_C_BIN" -mat A.mat -sourcefile two_sources.txt -distance 231.274660 \
                   -lambda 0.9768 -pixel 0.172 -detpixels 256 -oversample 1 \
                   -floatfile c_d4.bin -nonoise -nointerpolate
   Py: nanoBragg -mat A.mat -sourcefile two_sources.txt -distance 231.274660 \
                 -lambda 0.9768 -pixel 0.172 -detpixels 256 -oversample 1 \
                 -floatfile py_d4.bin
   ```
3. Document expected metrics:
   - Correlation: ≥0.999
   - Sum ratio: |Py_sum/C_sum - 1.0| ≤ 1e-3
   - Steps: `steps_py == steps_c == 2` (both using sourcefile-only)
4. Capture pytest collection proof under same `<STAMP>/` directory

---

## Blocking Questions Resolved

**Q1: Does Option B violate parity?**
**A1:** No. C's "4 sources" output includes 2 divergence grid sources with zero weight/wavelength, suggesting unintentional behavior. Spec line 151 supports replacement semantics.

**Q2: What about workflows relying on additive behavior?**
**A2:** No known workflows documented. If discovered, users can explicitly disable sourcefile and use divergence grids separately. Warning message will guide them.

**Q3: Device/dtype risks for Option B?**
**A3:** None. No tensor code changes required. Existing `_generate_sources()` already implements replacement semantics correctly.

---

## Phase E Readiness

**Implementation Effort:** Low (2-3 files, <20 lines total)
- Spec amendment: `specs/spec-a-core.md:144-162` (prose addition)
- Validation guard: `src/nanobrag_torch/config.py:547-564` (5-line warning)
- Test coverage: `tests/test_cli_scaling.py` (4 new test cases: TC-D1/D2/D3/D4)

**Risk Level:** Minimal
- No breaking changes (PyTorch behavior unchanged)
- Spec amendment documents existing behavior
- Warning helps user education

**Unblocking Dependencies:**
- [VECTOR-GAPS-002] vectorization gap profiling can resume after Phase E validation
- [PERF-PYTORCH-004] P3.0c multi-source performance work can resume after parity metrics land

---

## References

- **Phase D1 Evidence:** `reports/2025-11-source-weights/phase_d/20251009T102319Z/divergence_analysis.md`
- **Phase D2 Design:** `reports/2025-11-source-weights/phase_d/20251009T103212Z/design_notes.md`
- **Plan:** `plans/active/source-weight-normalization.md`
- **Spec Authority:** `specs/spec-a-core.md:144-162`

---

## Sign-Off

**Phase D2 Outcome:** Design decision finalized.
**Recommendation:** Approved for Phase E implementation (Option B).
**Next Loop:** Phase D3 harness preparation (pytest selectors, command bundle, expected metrics).
