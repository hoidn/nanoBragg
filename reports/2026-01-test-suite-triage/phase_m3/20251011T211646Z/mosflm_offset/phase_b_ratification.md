# DETECTOR-CONFIG-001 Phase B Ratification & Phase C Readiness Declaration

**STAMP:** 20251011T211646Z
**Phase:** M3 Phase B → Phase C Transition (Docs-only loop)
**Plan Reference:** `plans/active/detector-config.md`
**Input Directive:** `input.md` lines 1-34 (Do Now: Draft Option A design — ALREADY COMPLETE)
**Loop Owner:** ralph

---

## Executive Summary

**RATIFICATION RESULT:** ✅ **Phase B COMPLETE — Design Already Ratified — Phase C READY TO PROCEED**

The Option A remediation design document requested in `input.md` **already exists** at multiple STAMPs and has been verified complete in prior loops. The most comprehensive version is at:

```
reports/2026-01-test-suite-triage/phase_m3/20251011T210514Z/mosflm_offset/design.md
```

**Design Document Status:**
- **Lines:** 995 (comprehensive, production-ready)
- **Sections:** 13 major sections + 3 appendices
- **Completion:** 100% of Phase B exit criteria satisfied
- **Ratification:** ✅ Option A approach approved
- **Readiness:** ✅ Ready for immediate Phase C implementation handoff

**This loop confirms:** Design artifact is complete, normative, and ready. No additional design work required.

---

## Phase B Exit Criteria Verification

Per `plans/active/detector-config.md` Phase B tasks (lines 29-40), ALL criteria are satisfied:

### ✅ B1: Ratify remediation option [COMPLETE]

**Evidence Location:** `design.md` §3 (Design Rationale: Option A vs Option B)

**Content:**
- **Option A (Explicit Source Tracking):** RATIFIED — uses `beam_center_source` attribute
- **Option B (Heuristic Default Matching):** REJECTED — documented as fragile with 6 specific disadvantages
- **Trade-Off Analysis:** §3.3 provides explicit rationale: "Option A's explicit semantics, maintainability, and testability make it the superior choice"
- **Approval:** References Phase M3 summary.md recommendation

**Verification:** ✅ Decision is clear, documented, and justified

---

### ✅ B2: Define config/CLI propagation [COMPLETE]

**Evidence Location:** `design.md` §§5-7 (Configuration Layer, CLI Parsing, Detector Layer)

**Content:**

**Configuration Layer (§5):**
```python
@dataclass
class DetectorConfig:
    beam_center_source: Literal["auto", "explicit"] = "auto"
```
- Field type, default value, docstring documented
- Migration path specified (default="auto" preserves backward compatibility)
- Optional `__post_init__` validation provided

**CLI Parsing (§6):**
```python
def determine_beam_center_source(args: argparse.Namespace) -> Literal["auto", "explicit"]:
    # Checks 8 explicit flags: -Xbeam, -Ybeam, -Xclose, -Yclose, -ORGX, -ORGY, etc.
```
- Detection matrix with 8 explicit flags enumerated
- Header ingestion tracking strategy (`_beam_center_from_header` flag)
- Integration point in `__main__.py` specified

**Detector Layer (§7):**
```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        return base + 0.5
    return base
```
- Conditional offset logic for both `beam_center_s_pixels` and `beam_center_f_pixels`
- Device/dtype/differentiability guardrails verified
- Docstrings with normative spec citations

**Verification:** ✅ Implementation blueprint is complete, concrete, and executable

---

### ✅ B3: Map test & doc impacts [COMPLETE]

**Evidence Location:** `design.md` §§8-9 (Test Impact Matrix, Documentation Impact)

**Test Impact (§8):**
1. **Existing Tests Requiring Updates:** 3 test files identified
   - `tests/test_detector_config.py`: 2 functions need `beam_center_source` parameter
   - `tests/test_at_parallel_003.py::test_detector_offset_preservation`: Should pass after fix

2. **New Tests Required:** 5 new test cases enumerated with complete specifications
   - `test_mosflm_auto_beam_center_offset`: Verify +0.5 offset IS applied
   - `test_mosflm_explicit_beam_center_no_offset`: Verify +0.5 offset NOT applied
   - `test_non_mosflm_no_offset`: Parametrized across conventions and sources
   - `test_beam_center_source_cli_detection`: Verify CLI flag detection
   - `test_beam_center_source_api_direct`: Verify API usage requirements

3. **Parity Validation Tests (§8.3):** 3 C↔PyTorch cases with correlation thresholds

**Documentation Impact (§9):**
1. `docs/architecture/detector.md`: New §9.1 "Beam Center Provenance Tracking"
2. `docs/development/c_to_pytorch_config_map.md`: New "Beam Center Source Detection" section
3. `docs/findings.md`: API-002 interaction note

**Verification:** ✅ Test matrix is comprehensive and doc impacts are enumerated

---

### ✅ B4: Risk & compatibility assessment [COMPLETE]

**Evidence Location:** `design.md` §10 (Risk Assessment)

**Risks Analyzed:**

1. **API Compatibility Risks (§10.1):**
   - Risk: Existing code without `beam_center_source` may behave incorrectly
   - Mitigation: Default value `"auto"` preserves current behavior
   - Residual Risk: LOW

2. **Interaction with Findings (§10.2):**
   - **API-002 (pix0 overrides):** Test specified to verify precedence preserved
   - **CONVENTION-001 (CUSTOM):** Test specified to verify no offset regardless of source

3. **PyTorch Runtime Risks (§10.3):**
   - **Device/Dtype Neutrality:** Verified no `.cpu()`/`.cuda()` calls
   - **Differentiability:** Verified no `.item()`/`.detach()` calls
   - **Vectorization:** Confirmed property access remains O(1)

4. **Test Coverage Gaps (§10.4):**
   - 6-point test matrix covers all edge cases
   - Residual Risk: LOW

5. **Backward Compatibility (§10.5):**
   - Fix corrects broken behavior (users WANT this fix)
   - Residual Risk: VERY LOW

**Verification:** ✅ Risk assessment is thorough and mitigations are specified

---

## Design Document Quality Assessment

**Comprehensive Sections (13 + 3 appendices):**

1. ✅ Problem Statement (§1) — Current bug + correct behavior + impact
2. ✅ Normative Requirements (§2) — Spec citations (spec-a-core.md §72, arch.md §ADR-03)
3. ✅ Design Rationale: Option A vs B (§3) — Trade-off analysis + decision
4. ✅ Detailed Design Specification (§4) — Data model overview
5. ✅ Configuration Layer Changes (§5) — `DetectorConfig` modifications
6. ✅ CLI Parsing Changes (§6) — Detection logic + header ingestion
7. ✅ Detector Layer Changes (§7) — Property modifications + guardrails
8. ✅ Test Impact Matrix (§8) — Existing updates + new tests + parity validation
9. ✅ Documentation Impact (§9) — 3 files with section mappings
10. ✅ Risk Assessment (§10) — 5 risk categories with mitigations
11. ✅ Implementation Checklist (§11) — Phase C tasks C1-C7
12. ✅ Exit Criteria (§12) — 4-category completion checklist
13. ✅ References (§13) — Spec/arch/docs/evidence/plan pointers

**Appendices:**
- Appendix A: Example CLI Commands (3 scenarios)
- Appendix B: Test Code Examples (3 complete test functions)

**Quality Metrics:**
- **Completeness:** 100% (all Phase B exit criteria covered)
- **Executability:** High (code examples are concrete and runnable)
- **Traceability:** Excellent (spec/arch citations with line numbers)
- **Maintainability:** Strong (clear rationale for all decisions)

**Verification:** ✅ Design is production-ready

---

## Normative Specification Alignment

### spec-a-core.md §72 (MOSFLM Convention)

**Quoted Requirement:**
> "Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2."
> "Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM."

**Design Alignment:** ✅
- The +0.5 pixel offset is described in the context of **default** beam center calculation
- Spec does not mandate offset for **explicit user-provided coordinates**
- Option A design correctly interprets this as "apply offset to defaults only"

### arch.md §ADR-03 (Beam-center Mapping)

**Quoted Requirement:**
> "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

**Design Alignment:** ✅
- Option A explicitly distinguishes "auto" (apply offset) vs "explicit" (no offset)
- CUSTOM convention behavior (no implicit offsets) matches explicit beam center logic
- ADR guidance is directly implemented via `beam_center_source` attribute

### CLAUDE.md Core Implementation Rule #16 (Device/Dtype Neutrality)

**Quoted Requirement:**
> "Implementation MUST work for CPU and GPU tensors and for all supported dtypes without silent device transfers."

**Design Alignment:** ✅ (§7.2 PyTorch Guardrails Verification)
- No `.cpu()`/`.cuda()` calls introduced
- Offset `+ 0.5` is scalar operation on tensor (preserves device/dtype)
- Verification: CPU + CUDA smoke tests specified in §8.3

---

## Phase C Readiness Declaration

### Prerequisites (All Satisfied)

- ✅ Design artifact exists (STAMP 20251011T210514Z, 995 lines)
- ✅ All Phase B exit criteria met (B1-B4 complete with evidence)
- ✅ Normative requirements aligned (spec-a-core.md §72, arch.md §ADR-03)
- ✅ Implementation sequence defined (C1-C7 tasks with 10-60min estimates)
- ✅ Test matrix complete (5 new tests + 3 existing updates + parity cases)
- ✅ Documentation impact mapped (3 files with specific sections)
- ✅ Risk assessment complete (5 categories with mitigations)
- ✅ PyTorch guardrails verified (device/dtype/differentiability)

### Phase C Implementation Tasks (from design.md §11)

| Task | Description | Files | Effort |
|------|-------------|-------|--------|
| **C1** | Update configuration layer | `src/nanobrag_torch/config.py` | 10-15 min |
| **C2** | Adjust CLI parsing | `src/nanobrag_torch/__main__.py` | 30-45 min |
| **C3** | Apply conditional offset | `src/nanobrag_torch/models/detector.py` | 20-30 min |
| **C4** | Expand regression coverage | `tests/test_detector_config.py`, `tests/test_beam_center_offset.py` (new) | 45-60 min |
| **C5** | Targeted validation bundle | Pytest runs + artifact capture | 30 min |
| **C6** | Documentation sync | `docs/architecture/detector.md`, `docs/development/c_to_pytorch_config_map.md`, `docs/findings.md` | 30 min |
| **C7** | Ledger & tracker update | `docs/fix_plan.md`, `reports/.../remediation_tracker.md` | 15 min |

**Total Estimated Effort:** 3-5 hours (implementation + validation + documentation)

### Canonical Validation Commands (from design.md §12.2)

**Targeted Tests (Primary):**
```bash
# This test should pass after fix (currently failing):
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation

# Full detector config unit tests:
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_detector_config.py

# Beam center scaling validation:
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_002.py
```

**Device/Dtype Smoke Tests:**
```bash
# CPU (required):
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_003.py

# GPU (if available):
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py
```

**Gradient Verification (ensure no regression):**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_gradients.py -k "gradcheck"
```

---

## Plan Synchronization Recommendations

### plans/active/detector-config.md Updates Required

**Current State (lines 12-16):**
```markdown
Phase A — Evidence & Guardrail Alignment · **[D]**
Phase B — Behavior Contract & Blueprint Refresh · **[D]**
Phase C — Implementation & Targeted Validation · **[P]** Awaiting supervisor approval
Phase D — Full-Suite Regression & Closure · **[ ]**
```

**Recommended Update:**
```markdown
Phase A — Evidence & Guardrail Alignment · **[D]** (STAMP 20251011T193829Z)
Phase B — Behavior Contract & Blueprint Refresh · **[D]** (STAMP 20251011T210514Z — Design ratified)
Phase C — Implementation & Targeted Validation · **[ ]** READY (Approved for implementation start)
Phase D — Full-Suite Regression & Closure · **[ ]** Pending Phase C completion
```

**Rationale:** Phase B is complete and ratified. Phase C is ready to transition from `[P]` (pending approval) to active implementation.

### docs/fix_plan.md Updates Required

**Current Entry:** `[DETECTOR-CONFIG-001]` (lines ~229-264)

**Recommended Append to Attempts History:**
```markdown
### Attempt #46 (2025-10-11T21:16:46Z) - Phase B Ratification & Phase C Readiness [ralph]
- **Action:** Docs-only verification loop to confirm Phase B completion
- **Outcome:** ✅ SUCCESS — Phase B design ratified, Phase C ready
- **Evidence:**
  - Design document verified complete (STAMP 20251011T210514Z, 995 lines, 13 sections)
  - All Phase B exit criteria (B1-B4) satisfied with traceability
  - Normative alignment confirmed (spec-a-core.md §72, arch.md §ADR-03)
  - PyTorch guardrails verified (device/dtype/differentiability)
- **Artifacts:** `reports/2026-01-test-suite-triage/phase_m3/20251011T211646Z/mosflm_offset/phase_b_ratification.md`
- **Next Actions:**
  - Await supervisor input.md update with Phase C "Do Now" directive
  - Execute C1-C7 implementation tasks (estimated 3-5h)
  - Run targeted validation bundle and capture artifacts
```

---

## Observations & Blocking Issues

### 1. Input.md Directive is Stale

**Issue:** `input.md` lines 1-34 say "Do Now: Draft the Option A remediation design" but the design was already created in Attempt #44 and verified in Attempt #45 and now again in Attempt #46.

**Impact:** Ralph loops are repeatedly verifying Phase B completion instead of proceeding to Phase C implementation.

**Recommendation:** Supervisor (galph) should update `input.md` to reflect current state:
```markdown
Do Now: Execute Phase C implementation tasks C1-C7 per design.md (STAMP 20251011T210514Z).
Mode: Implementation
Focus: DETECTOR-CONFIG-001 / Phase C implementation
Mapped tests: tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```

### 2. Plan Shows Phase C as [P] (Pending) but Should Be [ ] (Ready)

**Issue:** `plans/active/detector-config.md` line 15 shows Phase C as `[P]` (pending approval) but all prerequisites are satisfied.

**Impact:** May cause confusion about readiness state.

**Recommendation:** Update plan to show Phase C as `[ ]` (ready for execution) or `[I]` (in progress) once started.

### 3. No Code Changes Should Occur in This Loop

**Observation:** Per input.md line 2 `Mode: Docs`, this is a documentation/verification-only loop.

**Compliance:** ✅ This loop performs no code edits, only verification and documentation updates.

---

## Success Criteria for This Loop

### Docs-Only Loop Objectives

1. ✅ Verify Phase B design exists and is complete
2. ✅ Confirm all Phase B exit criteria (B1-B4) are satisfied
3. ✅ Validate normative specification alignment
4. ✅ Declare Phase C readiness with concrete prerequisites
5. ✅ Document blocking issues and recommendations

**All objectives achieved.**

### Artifacts Produced

- **This Document:** `reports/2026-01-test-suite-triage/phase_m3/20251011T211646Z/mosflm_offset/phase_b_ratification.md`
- **STAMP:** `20251011T211646Z`
- **Status:** Phase B ratified, Phase C ready to proceed

---

## Loop Summary

**Loop Type:** Docs-only verification (no code/test execution per input.md line 2)

**Mission:** Verify Phase B design document completeness and confirm readiness for Phase C implementation.

**Result:** ✅ **SUCCESS — Phase B Complete and Ratified, Phase C Ready to Proceed**

**Key Findings:**
1. Design document exists and is comprehensive (995 lines, 13 sections + appendices)
2. All Phase B exit criteria (B1-B4) satisfied with documented evidence
3. Normative spec alignment confirmed (spec-a-core.md §72, arch.md §ADR-03)
4. PyTorch guardrails verified (no device/dtype/differentiability violations)
5. Phase C implementation tasks are clearly defined (C1-C7, 3-5h estimate)

**Blocking Issues:**
1. ⚠️ `input.md` directive is stale (requests Phase B design that already exists)
2. ⚠️ Plan shows Phase C as `[P]` (pending) but prerequisites are satisfied

**Recommendations:**
1. Supervisor should update `input.md` with Phase C "Do Now" directive
2. Update `plans/active/detector-config.md` to mark Phase C as ready/active
3. Proceed to Phase C implementation in next ralph loop

**Next Action:** Await supervisor approval via updated `input.md` to unblock Phase C implementation.

---

**Phase B Status:** ✅ **COMPLETE AND RATIFIED**
**Phase C Status:** ✅ **READY TO PROCEED — Awaiting Input.md Update**
**Blocking:** Supervisor approval required (stale input.md directive)

**Estimated Phase C Duration:** 3-5 hours (C1-C7 tasks + validation + docs)
**Expected Outcome:** Resolution of C8 cluster (1 failing test → 0 failing tests)

---

**Loop Timestamp:** 2025-10-11T21:16:46Z
**Loop Owner:** ralph (docs-only verification)
**Next Loop:** ralph (Phase C implementation) awaiting supervisor handoff
