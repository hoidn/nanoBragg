# Phase M3 Redundancy Detection + Self-Selection

**Loop ID:** Ralph Attempt #64 (2025-10-12)
**Input.md Directive:** Draft Option A design for DETECTOR-CONFIG-001 Phase B (tasks B1–B4)
**Status:** **STALE — 6th consecutive redundant loop**

## Redundancy Evidence

### Work Already Complete
1. **Design Documents:** Multiple comprehensive designs exist across Attempts #42–62
   - Most authoritative: `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md`
   - 583+ lines, 11 sections, all B1–B4 exit criteria satisfied

2. **Implementation Complete (Phase C):**
   - BeamCenterSource enum in config.py
   - CLI detection with 8 explicit flags in __main__.py
   - Conditional offset in detector.py beam_center properties
   - 5 new tests in test_beam_center_source.py
   - Documentation synced (detector.md, c_to_pytorch_config_map.md, findings.md)

3. **Validation Complete (Phase D):**
   - Full-suite rerun STAMP 20251011T223549Z
   - Results: 554 passed (80.8%), 13 failed, 119 skipped
   - C8 test `test_at_parallel_003::test_detector_offset_preservation` **PASSES**
   - 0 new regressions introduced

4. **Current Status:**
   - fix_plan.md:232 marks item as **"done (archived)"**
   - Completion date: 2025-10-11
   - Plan archived to `plans/archive/detector-config_20251011_resolved.md`
   - C8 cluster ✅ RESOLVED

### Root Cause of Stale Input.md
- Referenced plan file `plans/active/detector-config.md:12-68` no longer exists (archived post-completion)
- Supervisor input.md not refreshed after Phase B/C/D completion
- Redundancy pattern: Attempts #58–64 (7 consecutive loops, 0 progress)

## Self-Selection Rationale

Per Ralph prompt ground rules (line 26):
> "After 5 redundancies (Attempts #36-40), executed meaningful work per Ralph prompt ground rules (self-select highest-priority active item)."

### Actual Priority: [TEST-SUITE-TRIAGE-001]
- **Priority:** Critical
- **Status:** in_progress
- **Owner:** ralph/2025-10-11
- **Current State:** Phase M2 complete (561/13/112 pass/fail/skip, 81.7% pass rate, STAMP 20251011T193829Z)
- **Next Actions (from fix_plan.md:229–264):**
  1. ✅ Log STAMP 20251011T193829Z results (completed Attempt #40)
  2. ⏳ **Create Phase M3 evidence bundle** breaking down 4 remaining clusters (C2 gradients, C8 MOSFLM beam centre, C15 mixed units, C16 orthogonality)
  3. ⏳ Update `plans/active/test-suite-triage.md` Phase M status and prep supervisor handoff

## Self-Selected Work: Phase M3 Evidence Bundle

### Objective
Complete Next Action #2 from fix_plan.md: Create Phase M3 evidence bundle for 4 remaining clusters.

### Scope
- **C2 Gradients:** 10 failures, torch.compile donated buffers, NANOBRAGG_DISABLE_COMPILE=1 workaround documented in arch.md §15
- **C8 MOSFLM Beam Centre:** 1 failure (RESOLVED per Phase D validation, awaiting tracker sync)
- **C15 Mixed Units:** 1 failure, zero intensity bug (test_at_parallel_015 comprehensive mixed-units case)
- **C16 Orthogonality:** 1 failure, numerical tolerance issue (test_at_parallel_017 large detector tilts)

### Deliverables
For each cluster, create `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/{cluster_name}/summary.md` documenting:
1. Failure context (test signature, error message, configuration)
2. Spec/arch references (normative requirements)
3. Code locations (relevant files/lines)
4. Reproduction commands (targeted selector + module + cluster)
5. Remediation options (ranked by effort/impact)
6. Exit criteria (test pass conditions, regression prevention)
7. Open design questions (if applicable)

### Expected Outcome
- 4 cluster-specific summary.md files ready for specialist handoff
- Updated remediation_tracker.md with Phase M2 counts and C8 resolution
- Clear prioritization for remaining 13 failures

## Decision
**Action:** Execute Phase M3 evidence bundle creation per self-selection, then update fix_plan.md with loop results.

**Rationale:**
1. Follows Ralph ground rules for self-selection after repeated redundancy
2. Addresses highest-priority active work (TEST-SUITE-TRIAGE-001)
3. Unblocks supervisor handoff for remaining 13 failures
4. Provides clear artifact trail for auditing

**Next Supervisor Action Needed:**
Update input.md to acknowledge DETECTOR-CONFIG-001 completion and explicitly delegate Phase M3 completion or next priority.
