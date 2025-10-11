# DETECTOR-CONFIG-001 Phase B Verification

**STAMP:** 20251011T211142Z
**Phase:** M3 Phase B Verification (Docs-only loop)
**Plan Reference:** `plans/active/detector-config.md`
**Input Directive:** `input.md` lines 1-34 (Do Now: Draft Option A design)

---

## Executive Summary

**VERIFICATION RESULT:** ✅ **Phase B COMPLETE — Design Already Exists and is Ratified**

The Option A remediation design document requested in `input.md` was **already created** in Attempt #44 (2025-10-11) and exists at:

```
reports/2026-01-test-suite-triage/phase_m3/20251011T203822Z/mosflm_offset/design.md
```

**Design Document Status:**
- **Lines:** 625 (13 comprehensive sections)
- **Completion:** 100% of Phase B exit criteria satisfied
- **Ratification:** ✅ Option A approach approved
- **Readiness:** Ready for Phase C implementation handoff

---

## Phase B Exit Criteria Verification

Per `plans/active/detector-config.md` Phase B tasks (lines 29-40):

### ✅ B1: Ratify remediation option
- **Location:** `design.md` §2 (Option A Design) and §10 (Alternative Options Rejected)
- **Content:**
  - Option A (explicit source tracking via `beam_center_source` config attribute) **RATIFIED**
  - Option B (value-based heuristic) **REJECTED** with documented rationale
  - Detailed comparison on maintainability, semantic clarity, edge cases, and auditability
- **Status:** ✅ **COMPLETE**

### ✅ B2: Define config/CLI propagation
- **Location:** `design.md` §§2.2.1-2.2.3 (Core Changes)
- **Content:**
  - Config layer: `DetectorConfig.beam_center_source` field with Enum/Literal type options
  - CLI layer: `determine_beam_center_source()` helper detecting 8 explicit flags
  - Detector layer: Conditional offset in `beam_center_s_pixels` and `beam_center_f_pixels` properties
  - Complete code examples for all three components
  - Header ingestion logic (treat `-img`/`-mask` beam centers as explicit)
- **Status:** ✅ **COMPLETE**

### ✅ B3: Map test & doc impacts
- **Location:** `design.md` §3 (Test Impact Matrix) and §4 (Documentation Impact)
- **Content:**
  - **Test Impact:** 5 new test cases enumerated with setup/expectations/rationale
  - **Existing Test Updates:** 3-5 test functions in `test_detector_config.py` requiring updates
  - **Documentation Impact:** 3 files mapped (detector.md, c_to_pytorch_config_map.md, findings.md) with specific sections
  - **Device/Dtype Validation:** CPU/GPU smoke test commands specified
- **Status:** ✅ **COMPLETE**

### ✅ B4: Risk & compatibility assessment
- **Location:** `design.md` §5 (Risk Assessment)
- **Content:**
  - **Interacting Findings:** API-002 (pix0 overrides) and CONVENTION-001 (CUSTOM) analyzed
  - **Device/Dtype Neutrality:** Offset tensor creation strategy with matching dtype/device documented
  - **Differentiability:** Gradient flow preservation verified (conditional logic + tensor operations)
  - **Header Ingestion:** Edge cases for SMV header beam center handling
  - **Backward Compatibility:** Default value strategy (`beam_center_source="auto"`) preserves existing behavior
- **Status:** ✅ **COMPLETE**

---

## Design Artifact Summary

**Full Document:** `reports/2026-01-test-suite-triage/phase_m3/20251011T203822Z/mosflm_offset/design.md`

**Sections (13 total):**

1. **Executive Summary** — Classification (P2.1 implementation bug), effort estimate (2-3h)
2. **Normative Requirements** (§1) — Spec citations (spec-a-core.md §§68-73, arch.md §ADR-03), current bug description
3. **Option A Design** (§2) — Three-layer implementation blueprint (config, CLI, detector)
4. **Test Impact Matrix** (§3) — 5 new tests + existing test updates + validation commands
5. **Documentation Impact** (§4) — 3 files requiring updates (detector.md §§8.2/9, c_to_pytorch_config_map.md, findings.md)
6. **Risk Assessment** (§5) — API-002/CONVENTION-001 interactions, device/dtype neutrality, differentiability, header ingestion edge cases, backward compatibility
7. **Implementation Sequence** (§6) — Phase C tasks C1-C7 with effort estimates (10-60min each, 3-5h total)
8. **Exit Criteria** (§7) — 13-point checklist (4 sub-categories: implementation, test coverage, validation, documentation)
9. **Artifact Expectations** (§8) — 4 categories (implementation, test, validation, documentation artifacts)
10. **Spec/Arch Alignments** (§9) — Normative spec citations, ADR alignment, MOSFLM convention semantics
11. **Alternative Options Rejected** (§10) — Option B value-based heuristic rejection rationale, implicit detection rejection rationale
12. **Glossary** (§11) — 7 key terms defined
13. **References** (§12) — Primary/supporting documents + test files
14. **Approval & Next Steps** (§13) — Phase B completion checklist, Phase C readiness, timeline estimates

**Key Design Decisions Documented:**

1. **`beam_center_source` attribute:** Enum/Literal type with values `"auto"` (default) or `"explicit"`
2. **CLI Detection Logic:** 8 explicit flags trigger `beam_center_source="explicit"` (Xbeam, Ybeam, beam_center_s/f/x/y, Xclose, Yclose)
3. **Conditional Offset Formula:** `if convention==MOSFLM AND source=="auto": offset +0.5 pixel`
4. **Device/Dtype Preservation:** Offset tensor created with `dtype=value.dtype, device=value.device`
5. **Header Ingestion:** `-img`/`-mask` beam centers treated as explicit
6. **Default Value Strategy:** `beam_center_source="auto"` preserves backward compatibility

---

## Spec/Arch Alignment

### Normative Requirements

**spec-a-core.md §§68-73** (MOSFLM Convention):
```
- Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
- Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM.
```

**Interpretation (documented in design.md §1.2):**
The +0.5 pixel offset is part of the **mapping formula** from Xbeam/Ybeam (mm) to Fbeam/Sbeam (meters), applied when beam centers are **derived from detector size defaults**. The spec does not mandate this offset for **explicit user-provided coordinates**.

**arch.md §ADR-03** (Beam-center Mapping):
```
- MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels).
  CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets
  unless provided by user inputs.
```

**Alignment:**
Option A implements this ADR by distinguishing explicit vs auto-calculated sources. CUSTOM convention behavior (no implicit offsets) matches explicit beam center behavior.

### Implementation Guardrails

**arch.md §15 (Differentiability Guidelines):**
- Offset created with `torch.tensor(0.5, dtype=..., device=...)` (differentiable)
- Conditional logic evaluated at property access (preserves computation graph)

**CLAUDE.md Core Implementation Rules §16 (Device/Dtype Neutrality):**
- Offset tensor matches calling tensor's dtype/device
- CPU + CUDA smoke tests required before marking complete

---

## Phase C Readiness

### Prerequisites (All Satisfied)

- ✅ Design artifact exists (`design.md` at STAMP 20251011T203822Z)
- ✅ All Phase B exit criteria met (B1-B4 complete)
- ✅ Normative requirements documented (spec-a-core.md §72, arch.md §ADR-03)
- ✅ Implementation sequence defined (C1-C7 tasks with effort estimates)
- ✅ Test impact mapped (5 new tests + 3-5 existing updates)
- ✅ Documentation impact mapped (3 files requiring sync)
- ✅ Risk assessment complete (API-002/CONVENTION-001 interactions documented)

### Next Actions

**Phase C Implementation** (per `plans/active/detector-config.md` lines 42-58):

| Task | Description | Effort Estimate |
|------|-------------|-----------------|
| C1 | Update configuration layer (`config.py`) | 15 min |
| C2 | Adjust CLI parsing (`__main__.py`) | 30-45 min |
| C3 | Apply conditional offset in Detector (`detector.py`) | 20-30 min |
| C4 | Expand regression coverage (5 new tests) | 45-60 min |
| C5 | Targeted validation bundle (pytest runs + artifacts) | 30 min |
| C6 | Documentation sync (3 files) | 30 min |
| C7 | Ledger & tracker update (`fix_plan.md`, `remediation_tracker.md`) | 15 min |

**Total Estimated Effort:** 3-5 hours

### Awaiting

- **Supervisor Approval:** `input.md` update with Phase C "Do Now" directive
- **Engineer Assignment:** ralph to execute C1-C7 tasks
- **Artifact Directory:** Prepare `reports/.../phase_m3/<NEW_STAMP>/mosflm_fix/` for validation logs

---

## Validation Strategy (from design.md §7.3)

**Targeted Tests (Primary):**
```bash
# Failing test that should pass after fix:
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation

# Full detector config unit tests:
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py

# Beam center scaling validation:
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py
```

**C-Code Parity Validation:**
- Correlation ≥0.999 for MOSFLM explicit beam center case
- Sum ratio within 0.1% of unity
- RMSE ≤0.01 (or spec-appropriate tolerance for geometry)

**Gradient Tests (Verification):**
```bash
# Existing gradient tests should remain passing:
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_gradients.py -k "gradcheck"
```

**Device/Dtype Smoke Tests:**
```bash
# CPU (required):
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py

# GPU (if available):
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py
```

---

## Observations & Recommendations

### 1. **Design Already Complete**

The `input.md` directive to "draft the Option A remediation design" was **already fulfilled** in Attempt #44 (2025-10-11). The existing design document at STAMP 20251011T203822Z is comprehensive (625 lines, 13 sections) and satisfies all Phase B exit criteria.

**Recommendation:** Acknowledge design completion and proceed to Phase C approval rather than re-drafting.

### 2. **No Outstanding Phase B Tasks**

All Phase B tasks (B1-B4) from `plans/active/detector-config.md` are documented as complete:
- B1: Option A vs B comparison → §2 & §10
- B2: Config/CLI propagation → §§2.2.1-2.2.3
- B3: Test/doc impacts → §§3-4
- B4: Risk assessment → §5

**Recommendation:** Mark Phase B status as `[D]` (done) in `plans/active/detector-config.md`.

### 3. **Phase C Blocking on Supervisor Approval**

Per `docs/fix_plan.md` Attempt #44 and `plans/active/detector-config.md` line 43, Phase C is "awaiting supervisor approval via input.md."

**Recommendation:** Update `input.md` with Phase C "Do Now" directive to unblock implementation:
```
Do Now: Execute Phase C implementation tasks C1-C7 per design.md (STAMP 20251011T203822Z).
Targeted validation required for each task. Capture artifacts under reports/.../phase_m3/<STAMP>/mosflm_fix/.
```

### 4. **Documentation Hygiene**

The fix_plan.md Attempts History contains 45 entries spanning multiple loops. Some entries are redundant (e.g., Attempts #42-45 all related to Phase B design).

**Recommendation:** After Phase C completion, consolidate Attempts History by archiving pre-Phase-C entries to `archive/fix_plan_archive.md` per CLAUDE.md guidance (line 448: "if docs/fix_plan.md is longer than 500 lines...").

---

## Artifacts Referenced

- **Design Document:** `reports/2026-01-test-suite-triage/phase_m3/20251011T203822Z/mosflm_offset/design.md` (625 lines, Attempt #44)
- **Phase B Completion Summary:** `reports/2026-01-test-suite-triage/phase_m3/20251011T204530Z/mosflm_offset/phase_b_complete.md` (Attempt #45)
- **Plan:** `plans/active/detector-config.md` (Phase B tasks lines 29-40, Phase C tasks lines 42-58)
- **Fix Plan:** `docs/fix_plan.md` lines 229-264 ([DETECTOR-CONFIG-001] entry with Attempts History)
- **Input Directive:** `input.md` lines 1-34

---

## Loop Summary

**Loop Type:** Docs-only verification (no code/test execution)

**Mission:** Verify Phase B design document completeness and confirm readiness for Phase C implementation.

**Result:** ✅ **SUCCESS — Phase B Complete, Design Ratified**

**Key Findings:**
1. Design document already exists and is comprehensive (625 lines, 13 sections)
2. All Phase B exit criteria (B1-B4) satisfied
3. No additional design work required
4. Phase C ready for supervisor approval and implementation handoff

**Next Action:** Await `input.md` update with Phase C "Do Now" directive for ralph to execute C1-C7 tasks.

**Runtime:** Docs-only (no pytest execution)

**Artifacts:** This verification document (`phase_b_verification.md` at STAMP 20251011T211142Z)

---

**Phase B Status:** ✅ **COMPLETE**
**Phase C Status:** ⏸️ **READY — Awaiting Approval**
**Blocking:** Supervisor approval required (via input.md update)
