# MOSFLM Beam Center Offset Remediation Design (Option A)

**Initiative:** DETECTOR-CONFIG-001 — Detector defaults audit (COMPLETED)
**Cluster:** C8 (MOSFLM Beam Center Offset)
**STAMP:** 20251012T001444Z
**Phase:** M3 Design Document (Redundancy Check-In)
**Status:** ✅ WORK ALREADY COMPLETED

---

## ⚠️ REDUNDANCY NOTICE

This document was generated in response to a **stale input.md directive** requesting design documentation for DETECTOR-CONFIG-001 Phase B. However, **all requested work has been completed** in prior loops.

**Evidence of Completion:**

1. **Comprehensive Design Document Already Exists:**
   - Location: `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md`
   - Size: 23KB (583 lines)
   - Content: Complete 11-section design with all Phase B exit criteria (B1-B4) satisfied

2. **Implementation Complete:**
   - **Phase C (Code Changes):**
     - Added `BeamCenterSource` enum to `src/nanobrag_torch/config.py`
     - Extended `DetectorConfig` with `beam_center_source` field
     - Implemented `determine_beam_center_source()` CLI detection (8 explicit flags)
     - Modified `detector.py` beam center properties with two-condition offset guard
     - Created `tests/test_beam_center_source.py` with 5 new test cases
   - **Validation Results:** 16/16 targeted tests PASSED (1.95s runtime)
   - **Documentation:** synced detector.md, c_to_pytorch_config_map.md, findings.md

3. **Phase D (Full-Suite Validation) Complete:**
   - STAMP: 20251011T223549Z
   - Results: 554 passed / 13 failed / 119 skipped (80.8% pass rate)
   - **C8 Test Status:** `test_at_parallel_003.py::test_detector_offset_preservation` ✅ PASSES
   - **Regression Analysis:** 0 new regressions introduced

4. **Fix Plan Status:**
   - Entry: `docs/fix_plan.md:232` ([DETECTOR-CONFIG-001])
   - Status: **done (archived)**
   - Plan File: Archived to `plans/archive/detector-config_20251011_resolved.md`

5. **Prior Redundancy Detections:**
   - Attempt #36 (STAMP 20251011T233622Z): First redundancy detection
   - Attempt #37 (STAMP 20251011T234401Z): Redundancy reconfirmation
   - Attempt #38 (STAMP 20251011T234802Z): Third consecutive stale directive detection

---

## What Was Implemented (Summary)

For completeness, this section summarizes the already-completed Option A remediation design:

### Configuration Layer
- **BeamCenterSource Enum:** `AUTO` (convention defaults) vs `EXPLICIT` (user-provided)
- **DetectorConfig Extension:** Added `beam_center_source: BeamCenterSource = AUTO` field

### CLI Parsing Layer
- **Explicit Detection:** 8 CLI flags indicate explicit beam center: `--beam_center_s/f`, `-Xbeam/-Ybeam`, `-Xclose/-Yclose`, `-ORGX/-ORGY`
- **Helper Function:** `determine_beam_center_source(args) → BeamCenterSource`

### Detector Layer
- **Conditional Offset:**
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

### Test Coverage
- **New Tests:** 5 test cases in `tests/test_beam_center_source.py`
  1. MOSFLM auto-calculated → offset applied ✅
  2. MOSFLM explicit → no offset ✅
  3. Non-MOSFLM conventions → no offset ✅
  4. CLI detection → correct source assignment ✅
  5. Edge case: explicit matches default → explicit wins ✅

### Parity Validation
- **MOSFLM AUTO:** Both C and PyTorch apply +0.5 offset (correlation ≥0.999)
- **MOSFLM EXPLICIT:** PyTorch now matches C behavior (no offset, correlation ≥0.999)
- **XDS/DIALS/CUSTOM:** No offset for any source (correlation ≥0.999)

---

## Normative References (For Completeness)

**specs/spec-a-core.md §72 (MOSFLM Convention):**
> "Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM."

**arch.md §ADR-03 (Beam-center Mapping):**
> "MOSFLM applies +0.5 pixel offset to beam center calculations when deriving from detector geometry defaults. Explicit user-provided beam centers must not be adjusted."

---

## Artifacts (All Phases Complete)

### Design Phase (Phase B)
- **Primary Design:** `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md`
- **Alternate Designs:** Multiple iterations at STAMPs 20251011T{203303Z, 215044Z, 230052Z}

### Implementation Phase (Phase C)
- **Validation Summary:** `reports/2026-01-test-suite-triage/phase_m3/20251011T213351Z/mosflm_fix/summary.md`
- **Targeted Test Results:** 16/16 tests PASSED (1.95s runtime)

### Full-Suite Validation (Phase D)
- **Validation Summary:** `reports/2026-01-test-suite-triage/phase_m/20251011T223549Z/summary.md`
- **Full Results:** 554 passed / 13 failed / 119 skipped (80.8% pass rate)
- **C8 Cluster:** ✅ RESOLVED (0 failures)

### Archived Plan
- **Location:** `plans/archive/detector-config_20251011_resolved.md`
- **All Phases:** A-B-C-D marked [D] (Done)

---

## Recommendation

**To Supervisor (galph):**

The `input.md` directive requesting DETECTOR-CONFIG-001 Phase B design is **stale and outdated**. All requested work has been completed as documented above. Please update `input.md` to redirect to active priorities:

**Active Priority Recommendations:**

1. **[TEST-SUITE-TRIAGE-001]** (Critical, in_progress)
   - **Status:** 13 failures remaining (Phase M2 baseline)
   - **Active Clusters:**
     - C2: Gradient tests (torch.compile workaround documented)
     - C15: Mixed units / zero intensity bug (needs callchain investigation)
     - C16: Detector orthogonality tolerance (needs adjustment)
   - **Next Actions:** See `docs/fix_plan.md:229-264`

2. **[VECTOR-PARITY-001]** (High, in_progress)
   - **Status:** Blocked on test suite health
   - **Dependency:** Requires C15 (zero intensity) resolution first

3. **[SOURCE-WEIGHT-002]** (High, done per Attempt #15)
   - May require ledger update to mark as complete

---

## Exit Criteria (All Met ✅)

- [x] BeamCenterSource enum added to config.py
- [x] DetectorConfig.beam_center_source field added with default AUTO
- [x] determine_beam_center_source() helper function in __main__.py
- [x] Beam center properties in detector.py use two-condition offset guard
- [x] 5 new test cases in tests/test_beam_center_source.py PASS
- [x] test_at_parallel_003.py::test_detector_offset_preservation PASSES
- [x] C-PyTorch parity validated (correlation ≥0.999 for all cases)
- [x] Documentation synced (detector.md, c_to_pytorch_config_map.md, findings.md)
- [x] No new regressions in full Phase M chunked suite
- [x] C8 cluster marked ✅ RESOLVED in remediation tracker

---

**Loop Status:** ✅ REDUNDANCY DOCUMENTED — Work already complete, no action required.

**Next:** Await updated input.md directive for active priority (TEST-SUITE-TRIAGE-001 recommended).

**Runtime:** Docs-only verification loop
**Environment:** Python 3.13.5, PyTorch 2.7.1+cu126, linux 6.14.0-29-generic

---

## References (Complete Evidence Trail)

### Fix Plan Attempts
- Attempt #31-40: Phase M3a-M3d documentation sync
- Attempt #42: Phase B design blueprint (STAMP 20251011T214422Z)
- Attempt #43-55: Phase C implementation + validation
- Attempt #56: Phase D full-suite validation (COMPLETE)
- Attempt #36-38: Prior redundancy detections

### Key Artifacts
- **Design:** `phase_m3/20251011T214422Z/mosflm_offset/design.md`
- **Implementation:** `phase_m3/20251011T213351Z/mosflm_fix/summary.md`
- **Validation:** `phase_m/20251011T223549Z/summary.md`
- **Archived Plan:** `plans/archive/detector-config_20251011_resolved.md`

### Spec References
- **spec-a-core.md:** §72 (MOSFLM +0.5 pixel offset normative requirement)
- **arch.md:** §ADR-03 (Beam-center mapping auto vs explicit distinction)
- **detector.md:** §8.2 (Beam center mapping implementation details)
