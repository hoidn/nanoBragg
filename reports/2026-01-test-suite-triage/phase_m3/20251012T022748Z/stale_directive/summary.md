# Stale Directive Detection — Attempt #46

**STAMP:** 20251012T022748Z
**Loop:** Ralph Attempt #46
**Mode:** Evidence-only (docs loop per input.md constraint)
**Issue:** 8th consecutive redundant request for completed work

---

## Executive Summary

**Input.md** continues to request drafting the DETECTOR-CONFIG-001 Phase B Option A design document, but **this work was comprehensively completed** across fix_plan.md Attempts #42-57 (spanning 2025-10-11 through completion).

**Status:**
- **[DETECTOR-CONFIG-001]:** ✅ **DONE (archived)** per fix_plan.md:242
- **Plan archived to:** `plans/archive/detector-config_20251011_resolved.md`
- **All phases complete:** B (design), C (implementation), D (validation)
- **C8 cluster:** ✅ **RESOLVED** per Phase M3 Attempt #41 evidence

---

## Evidence of Completion

### 1. Fix Plan Status

**Location:** `docs/fix_plan.md:239-267`

```
## [DETECTOR-CONFIG-001] Detector defaults audit
- Spec/AT: `specs/spec-a-core.md` §§68-73 (MOSFLM convention)
- Priority: High
- Status: done (archived)
- Owner/Date: ralph/2025-10-10
- Completion Date: 2025-10-11
- Plan Reference: `plans/archive/detector-config_20251011_resolved.md`
```

### 2. Phase B Design Document

**Most Comprehensive Version:** `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md`

**Size:** 23KB, 11 sections, 583 lines

**Sections:**
1. Executive Summary
2. Configuration Layer Changes (BeamCenterSource enum)
3. CLI Parsing Layer Changes (8 explicit flags)
4. Detector Layer Changes (conditional offset properties)
5. Test Impact Matrix (5 new tests)
6. Documentation Impact (3 files)
7. Risk Assessment (API-002/CONVENTION-001 interactions)
8. Acceptance Criteria (13-point checklist)
9. Implementation Sequence (C1-C7 tasks, 3-5h estimate)
10. Alternative Approaches (Option B rejected)
11. References

**Exit Criteria:** All Phase B tasks (B1-B4) complete per archived plan

### 3. Phase C Implementation

**STAMP:** 20251011T213351Z

**Code Changes:**
- **C1:** `src/nanobrag_torch/config.py` — BeamCenterSource enum (AUTO/EXPLICIT)
- **C2:** `src/nanobrag_torch/__main__.py` — CLI detection (8 explicit flags)
- **C3:** `src/nanobrag_torch/models/detector.py` — Conditional offset properties
- **C4:** `tests/test_beam_center_source.py` — 5 new test cases
- **C5:** Targeted validation: 16/16 tests PASSED
- **C6:** Documentation synced (detector.md, c_to_pytorch_config_map.md, findings.md)
- **C7:** Ledger updated

### 4. Phase D Validation

**STAMP:** 20251011T223549Z

**Full-Suite Rerun Results:**
- **687 tests collected**
- **554 passed (80.8%)**
- **13 failed (1.9%)**
- **119 skipped (17.4%)**
- **Runtime:** ~410s (chunked execution)

**C8 Test Status:** ✅ **PASSING**
- `tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`
- Was failing in Phase M2 baseline (20251011T193829Z)
- Now PASSES after MOSFLM beam center fix

**No New Regressions:** All 13 failures pre-existed in Phase M2 baseline

### 5. Phase M3 Current Evidence (Attempt #41)

**STAMP:** 20251012T012246Z

**Cluster Status Validation:**
- **C8 (MOSFLM):** ✅ **RESOLVED** (test PASSING, 1.92s)
- **C15 (mixed units):** ❌ STILL FAILING (zero intensity, 3.84s)
- **C16 (orthogonality):** ✅ **RESOLVED** (Attempt #43, tolerance fix, 3.76s)

**Comprehensive Evidence Bundle:** `reports/2026-01-test-suite-triage/phase_m3/20251012T012246Z/remaining_clusters/summary.md`

---

## Redundancy Timeline

This is the **8th consecutive loop** detecting stale input.md directives:

1. **Attempt #36** (20251011T233622Z) — First detection, documented redundancy
2. **Attempt #37** (20251011T234401Z) — Reconfirmed redundancy
3. **Attempt #38** (20251011T234802Z) — 3rd detection, self-selected baseline rerun (timed out)
4. **Attempt #39** (20251012T004433Z) — 4th detection, comprehensive evidence analysis
5. **Attempt #40** (20251012T010425Z) — 5th detection, executed Phase M2 ledger refresh (high-value work)
6. **Attempt #41** (20251012T012246Z) — 6th detection, created Phase M3 evidence bundle (high-value work)
7. **Attempt #45** (20251012T022113Z) — 7th detection, documented missing plan file
8. **Attempt #46** (CURRENT, 20251012T022748Z) — 8th detection

---

## Root Cause

**Input.md references a plan file that no longer exists:**
```
- plans/active/detector-config.md:12-68 — Phase B tasks B1–B4
```

**Verification:**
```bash
$ ls plans/active/detector-config.md
ls: cannot access 'plans/active/detector-config.md': No such file or directory
```

**Actual Location:** `plans/archive/detector-config_20251011_resolved.md`

**Issue:** Supervisor input.md not refreshed after plan archival on 2025-10-11

---

## Recommendation to Supervisor (Galph)

**Acknowledge DETECTOR-CONFIG-001 completion** and update input.md to delegate **active priority work**:

### Option A: Continue [TEST-SUITE-TRIAGE-001] (RECOMMENDED)

**Current Status:** 13 failures remaining (Phase M2 STAMP 20251011T193829Z)

**Active Clusters:**
- **C2:** Gradient Infrastructure (10 failures, workaround documented, P3)
- **C15:** Mixed Units Zero Intensity (1 failure, physics bug, P2 — **HIGH VALUE**)
- **C16:** Detector Orthogonality (1 failure, RESOLVED Attempt #43)
- **C17:** Polarization (2 failures, AttributeError, P2)
- **C18:** Performance (1 failure, edge case, P3)

**Recommended Next Action:** Sprint 1.3 — C15 mixed-units debugging (4-6h parallel trace + hypothesis testing per evidence bundle 20251012T012246Z)

**Why:** C15 is a **physics/unit conversion bug** (zero intensity despite valid triclinic+XDS+rotations+dmin config), high impact, requires parallel trace debugging per `docs/debugging/debugging.md` SOP

### Option B: Resume [VECTOR-PARITY-001]

**Status:** High priority, blocked on test suite health

**Condition:** Acceptable if remaining 13 failures (minus C2 infrastructure) deemed low-risk

---

## Files Requiring Update

1. **input.md** — Update "Do Now" to reference active priority work
2. **input.md** — Remove "Mode: Docs" constraint for pytest execution
3. **galph_memory** (if present) — Acknowledge DETECTOR-CONFIG-001 completion

---

## Artifacts

- **This summary:** `reports/2026-01-test-suite-triage/phase_m3/20251012T022748Z/stale_directive/summary.md`
- **Phase B design (authoritative):** `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md`
- **Phase C implementation:** `reports/2026-01-test-suite-triage/phase_m3/20251011T213351Z/mosflm_fix/summary.md`
- **Phase D validation:** `reports/2026-01-test-suite-triage/phase_m/20251011T223549Z/summary.md`
- **Phase M3 evidence:** `reports/2026-01-test-suite-triage/phase_m3/20251012T012246Z/remaining_clusters/summary.md`
- **Archived plan:** `plans/archive/detector-config_20251011_resolved.md`

---

## Next Steps

**For Ralph (this loop):**
- Document this 8th redundancy detection
- Update fix_plan.md Attempts History
- Await supervisor guidance

**For Galph (supervisor):**
- Update input.md to acknowledge DETECTOR-CONFIG-001 completion
- Delegate Sprint 1.3 (C15 mixed-units debugging) OR alternative active priority
- Remove "Mode: Docs" constraint to enable pytest execution

---

**Status:** Evidence-only loop complete. DETECTOR-CONFIG-001 is definitively complete and archived. Awaiting updated input.md directive for active priority work.
