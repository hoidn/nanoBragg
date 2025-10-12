# Option A Design — MOSFLM Beam Center Offset Remediation

**STAMP:** 20251012T020840Z
**Phase:** Post-implementation retrospective (Phases B-C-D already complete)
**Status:** 📋 Redundant request — work already completed in Attempts #42-57
**Artifact Type:** Acknowledgment / Reference pointer

---

## Executive Summary

**This design document is a REDUNDANT REQUEST.** The Option A design for MOSFLM beam center offset remediation was **already completed comprehensively** in Attempt #44 (STAMP 20251011T214422Z) and **fully implemented** in Phase C (Attempt #42, commit 4e394585).

**Current Status:**
- ✅ **Phase B (Design):** COMPLETE — Multiple design documents exist, most authoritative at STAMP 20251011T214422Z (583 lines, 11 sections)
- ✅ **Phase C (Implementation):** COMPLETE — Code changes across 3 files, 5 new tests, full documentation sync
- ✅ **Phase D (Validation):** COMPLETE — Full-suite rerun (554/13/119 passed/failed/skipped), C8 test PASSING, 0 new regressions
- 📦 **[DETECTOR-CONFIG-001]:** ARCHIVED to `plans/archive/detector-config_20251011_resolved.md` (completion: 2025-10-11)

---

## Normative Design Reference

**Authoritative Design Document:**
`reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md`

**Key Design Sections:**
1. Executive summary quoting spec-a-core.md §72, arch.md §ADR-03
2. Configuration layer: `BeamCenterSource` enum with AUTO/EXPLICIT values
3. CLI detection logic: 8 explicit flags (beam_center_s/f, Xbeam/Ybeam, Xclose/Yclose, ORGX/ORGY)
4. Detector layer: Conditional offset `if convention==MOSFLM AND source==AUTO`
5. Test impact: 5 new test cases in `test_beam_center_source.py`
6. Documentation impact: detector.md, c_to_pytorch_config_map.md, findings.md
7. Risk assessment: API-002/CONVENTION-001 interactions, device/dtype neutrality
8. Implementation tasks: C1–C7 with effort estimates (3-5h total, all complete)

---

## Implementation Summary (Phase C)

**Completed:** 2025-10-11 (Attempt #42, STAMP 20251011T213351Z)

**Code Changes:**
1. **src/nanobrag_torch/config.py** (lines 46-49):
   ```python
   class BeamCenterSource(Enum):
       AUTO = "auto"        # Convention defaults → apply MOSFLM offset
       EXPLICIT = "explicit"  # User-provided → no offset

   @dataclass
   class DetectorConfig:
       # ... existing fields ...
       beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
   ```

2. **src/nanobrag_torch/__main__.py** (CLI detection helper):
   - Detects 8 explicit flags: `--beam_center_s/f`, `-Xbeam/-Ybeam`, `-Xclose/-Yclose`, `-ORGX/-ORGY`
   - Header ingestion treated as explicit
   - Sets `beam_center_source=EXPLICIT` when any explicit flag present

3. **src/nanobrag_torch/models/detector.py** (properties, lines ~110-145):
   ```python
   @property
   def beam_center_s_pixels(self) -> torch.Tensor:
       base = self.config.beam_center_s_mm / self.config.pixel_size_mm
       # Apply MOSFLM offset ONLY to auto-calculated defaults
       if (self.config.detector_convention == DetectorConvention.MOSFLM and
           self.config.beam_center_source == BeamCenterSource.AUTO):
           return base + 0.5
       return base
   ```

**Test Coverage (tests/test_beam_center_source.py):**
1. MOSFLM auto-calculated → offset applied ✅
2. MOSFLM explicit → no offset ✅
3. Non-MOSFLM conventions → no offset ✅
4. CLI detection → correct source assignment ✅
5. Edge case: explicit matches default → explicit wins ✅

**Documentation:**
- `docs/architecture/detector.md` §8.2: Beam center source tracking subsection
- `docs/development/c_to_pytorch_config_map.md`: DETECTOR-CONFIG-001 section with CLI examples
- `docs/findings.md`: API-002 interaction note

---

## Validation Results (Phase D)

**Completed:** 2025-10-11 (Attempt #56, STAMP 20251011T223549Z)

**Full-Suite Regression (10-chunk ladder, 686 tests):**
- **554 passed** (80.8%)
- **13 failed** (1.9%) — all pre-existing in baseline
- **119 skipped** (17.4%)
- **Runtime:** ~410s

**C8 Cluster Resolution:**
- **Test:** `tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`
- **Status:** ✅ **PASSING** (was failing in baseline 20251011T193829Z)
- **Validation:** Explicit beam center coordinates preserved exactly as provided (no unintended +0.5 offset)

**C-PyTorch Parity (6×3 matrix):**
- MOSFLM AUTO: Both C and PyTorch apply +0.5 offset (correlation ≥0.999) ✅
- MOSFLM EXPLICIT: PyTorch matches C behavior (no offset, correlation ≥0.999) ✅
- XDS/DIALS/CUSTOM: No offset for any source (correlation ≥0.999) ✅

**Net Regressions:** **0 new failures** — implementation successful

---

## Spec/Arch References

**Normative:**
- **specs/spec-a-core.md §72** (lines 68-73): MOSFLM beam center mapping formula
  > "Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
  > Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel."

- **arch.md §ADR-03** (line 80): Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets
  > "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels).
  > CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

**Key Interpretation:**
The +0.5 pixel offset is a **convention-specific default behavior**, not a mandatory transformation for all coordinates. Explicit user-provided beam centers must not be adjusted.

---

## Alternative Designs Considered (Option B Rejected)

**Option B: Value-based heuristic**
Compare beam center values against computed defaults; if they match defaults, apply offset.

**Rejected for:**
1. **Fragility:** Numerical coincidence (user coincidentally provides default value) causes ambiguity
2. **Coupling:** Ties beam center logic to detector size logic (hard to maintain)
3. **Obscurity:** Heuristic behavior harder to reason about and test
4. **Future-proofing:** Cannot generalize to future conventions with different offset semantics

**Option A advantages:**
- Explicit semantic distinction (AUTO vs EXPLICIT)
- Easy to audit CLI → config → detector pipeline
- Minimal code changes (3 files, ~50 LOC)
- Backward compatible (default=AUTO preserves existing behavior)

---

## References

**Design Documentation:**
- Authoritative: `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md`
- Previous versions: Attempts #42-57 (STAMPs 20251011T201712Z through 20251011T230052Z)

**Implementation Artifacts:**
- Phase C summary: `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md` (lines 263-365)
- Phase D validation: `reports/2026-01-test-suite-triage/phase_m/20251011T223549Z/summary.md`

**Plan Status:**
- Active plan: `plans/active/detector-config.md` (Phases B-C-D all marked [D] complete)
- Archived: `plans/archive/detector-config_20251011_resolved.md` (completion: 2025-10-11)
- Fix plan: `docs/fix_plan.md` lines 238-268 (status: "done (archived)")

**Normative Specs:**
- `specs/spec-a-core.md` §§68-73 (MOSFLM convention)
- `arch.md` §ADR-03 (Beam-center Mapping)
- `docs/development/c_to_pytorch_config_map.md` (Beam Center Source Detection section)

---

## Recommendation

**This input.md directive appears STALE.** The requested Phase B design work was completed 12+ times in Attempts #42-57, and the entire [DETECTOR-CONFIG-001] item is archived as "done".

**Recommended Actions:**
1. Acknowledge completion of [DETECTOR-CONFIG-001] (Phases B-C-D all complete)
2. Update input.md to reference next priority item from `docs/fix_plan.md`
3. Suggested next priorities:
   - **[TEST-SUITE-TRIAGE-001]** (Critical, in_progress): Address remaining 13 failures (4 clusters: C2 gradients workaround, C15 mixed-units zero intensity, C16 orthogonality tolerance)
   - **[VECTOR-PARITY-001]** (High, blocked): Awaiting suite health improvement

**Avoid Further Redundancy:**
Do not request additional Phase B design documents for [DETECTOR-CONFIG-001]. All design work is complete, implementation validated, and plan archived.

---

**Artifact Status:** 📋 Acknowledgment complete (no new design work performed)
**Next Action:** Update input.md to reference active work items
**Completion:** 2025-10-11 (already done)
