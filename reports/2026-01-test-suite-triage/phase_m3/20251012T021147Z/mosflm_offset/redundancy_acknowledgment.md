# [DETECTOR-CONFIG-001] Redundancy Acknowledgment

**STAMP:** 20251012T021147Z
**Loop:** Attempt #60
**Status:** REDUNDANT REQUEST (Phase B-C-D already complete)

---

## Executive Summary

Input.md requested drafting the Option A remediation design for MOSFLM beam center offset handling (Phase B tasks B1-B4). However, this work was **comprehensively completed** in Attempts #42-57, implemented in Phase C, and validated in Phase D.

**Current Status:** [DETECTOR-CONFIG-001] is **done (archived)** per `docs/fix_plan.md:241`, completion date 2025-10-11.

---

## Evidence of Completion

### Phase B (Design)
**Authoritative Design Document:** `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md`
- 583 lines, 11 sections
- All B1-B4 exit criteria satisfied:
  - ✅ B1: Option A ratified with vs-B comparison
  - ✅ B2: Config/CLI propagation defined with code examples
  - ✅ B3: Test/doc impacts mapped (5 new tests + 3 existing updates + 3 doc files)
  - ✅ B4: Risk assessment complete (API-002/CONVENTION-001/PyTorch neutrality)

### Phase C (Implementation)
**Summary:** `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md:257-365`
- BeamCenterSource enum added to `src/nanobrag_torch/config.py`
- CLI detection logic in `src/nanobrag_torch/__main__.py` (8 explicit flags)
- Conditional offset in `src/nanobrag_torch/models/detector.py`
- 5 new tests in `tests/test_beam_center_source.py`
- Documentation synced: `detector.md`, `c_to_pytorch_config_map.md`, `findings.md`
- Git commit reference: 4e394585 (per Attempt #42)

### Phase D (Validation)
**Results:** Attempt #56 (STAMP 20251011T223549Z)
- Full-suite chunked rerun: 554 passed / 13 failed / 119 skipped (80.8% pass rate)
- **C8 test PASSES:** `test_at_parallel_003::test_detector_offset_preservation` ✅
- **0 new regressions:** All 13 failures pre-existed in baseline
- Runtime: ~410s (10 chunks)

### Archival
**Plan archived:** `plans/archive/detector-config_20251011_resolved.md`

---

## Input.md Staleness Analysis

**Issue:** Input.md (lines 1-34) contains outdated directive:
```
Do Now: Draft the Option A remediation design under reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_offset/design.md (plan Phase B tasks B1–B4).
```

**Problem:** This directive references work completed 2025-10-11. Multiple redundancy acknowledgments created:
- Attempt #58 (first redundancy notice)
- Attempt #59 (second redundancy notice)
- Attempt #60 (this document, third redundancy notice)

**Recommendation:** Supervisor (galph) should update `input.md` with next active priority.

---

## Next Active Priorities

### Option 1: [TEST-SUITE-TRIAGE-001]
**Status:** in_progress (Critical priority)
**Failures:** 13 remaining across 4 clusters
- C2: Gradient infrastructure (10 tests, torch.compile issue, workaround documented, P3)
- C8: MOSFLM offset ✅ **RESOLVED**
- C15: Mixed-units zero intensity (1 test, physics/unit bug, P2)
- C16: Detector orthogonality tolerance (1 test, precision issue, P3)
- Polarization regression (2 tests, AttributeError, P2)

**Recommended Action:** Triage C15 (zero intensity bug, high impact) or Polarization regression (2 failures, moderate impact).

### Option 2: [VECTOR-PARITY-001]
**Status:** blocked (High priority)
**Blocker:** Test suite health (13 failures need resolution first)

---

## Recommendation

**For Supervisor (galph):**
1. Acknowledge [DETECTOR-CONFIG-001] completion
2. Update `input.md` with next active work item:
   - Either: Triage C15 (mixed-units zero intensity) via callchain analysis
   - Or: Fix polarization regression (2 failures, AttributeError)
3. Remove Mode: Docs constraint if test execution required

**For Engineer (ralph):**
- No action required this loop
- Await updated `input.md` directive

---

## Artifacts

**This Document:** `reports/2026-01-test-suite-triage/phase_m3/20251012T021147Z/mosflm_offset/redundancy_acknowledgment.md`

**Prior Redundancy Notices:**
- Attempt #58: `docs/fix_plan.md:268`
- Attempt #59: `docs/fix_plan.md:269`

---

**Loop Status:** ⏸ AWAITING INPUT.MD UPDATE
