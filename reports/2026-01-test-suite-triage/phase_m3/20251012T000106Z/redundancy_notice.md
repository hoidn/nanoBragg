# Redundant Request Notice — DETECTOR-CONFIG-001

**STAMP:** 20251012T000106Z
**Loop:** Ralph Attempt #62
**Status:** ⚠️ **STALE DIRECTIVE — No Action Required**

## Finding

The `input.md` directive (dated 2025-10-11) requests drafting an Option A design document for DETECTOR-CONFIG-001 Phase B (tasks B1–B4). This work is **already complete and archived**.

## Evidence Summary

### 1. Design Documentation
**Multiple comprehensive design documents exist** across Attempts #42–61:
- **Most authoritative**: `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md` (583+ lines, 11 sections)
- All B1–B4 exit criteria satisfied per archived plan `plans/archive/detector-config_20251011_resolved.md`

### 2. Phase C Implementation Complete
Per C8 summary (`reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md:257-365`):
- **BeamCenterSource enum** added to `config.py`
- **CLI detection logic** implemented in `__main__.py` with 8 explicit flags
- **Conditional offset** applied in `detector.py` properties
- **5 new tests** added in `test_beam_center_source.py`
- **Documentation synced**: `detector.md`, `c_to_pytorch_config_map.md`, `findings.md`

### 3. Phase D Validation Complete
**STAMP 20251011T223549Z** (Attempt #56):
- **Test results**: 554 passed (80.8%), 13 failed (1.9%), 119 skipped (17.4%)
- **C8 test status**: `test_at_parallel_003::test_detector_offset_preservation` **PASSES** ✅
- **Net regression**: 0 new failures
- **Runtime**: 1841s (30.7 min) via chunked execution

### 4. Current Status
- **fix_plan.md line 232**: Status = **"done (archived)"**
- **Completion date**: 2025-10-11
- **Plan location**: `plans/archive/detector-config_20251011_resolved.md`
- **C8 cluster**: ✅ **RESOLVED**

## Root Cause

Referenced plan file `plans/active/detector-config.md:12-68` does not exist (archived after completion). `input.md` was not updated after DETECTOR-CONFIG-001 closure.

## Recommendation

**Supervisor should update `input.md` to acknowledge DETECTOR-CONFIG-001 completion and redirect to active priority:**

### Current Active Priority: [TEST-SUITE-TRIAGE-001]
- **Status**: Critical, in_progress
- **Current state**: Phase M2 complete (Attempt #35, STAMP 20251011T193829Z)
- **Results**: 561 passed (81.7%), 13 failed (1.9%), 112 skipped (16.3%)
- **Remaining clusters**:
  - **C2 Gradients** (10 failures): torch.compile limitation, workaround documented in `arch.md` §15, KNOWN ISSUE
  - **C8 MOSFLM Offset** (RESOLVED in DETECTOR-CONFIG-001)
  - **C15 Mixed Units** (1 failure): zero intensity bug, needs callchain investigation
  - **C16 Orthogonality** (1 failure): tolerance adjustment needed, not physics bug

### Alternative Priorities
- **[VECTOR-PARITY-001]** (High, blocked on suite health)
- **[SOURCE-WEIGHT-002]** (High, done per Attempt #15)

## Next Steps

1. **Acknowledge completion**: DETECTOR-CONFIG-001 is fully resolved
2. **Update input.md**: Remove stale directive, add TEST-SUITE-TRIAGE-001 focus
3. **Resume active work**: Phase M3 follow-through per `docs/fix_plan.md:48-51`

## Artifacts

- **Design**: `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md` (583 lines)
- **Implementation**: `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md:257-365`
- **Validation**: `reports/2026-01-test-suite-triage/phase_m/20251011T223549Z/summary.md` (Phase D full-suite rerun)
- **Archived plan**: `plans/archive/detector-config_20251011_resolved.md`

## Environment

- Python 3.13.5
- PyTorch 2.7.1+cu126
- Linux 6.14.0-29-generic
- CUDA 12.6 (disabled via `CUDA_VISIBLE_DEVICES=-1`)

---

**Loop scope**: Observation only (no code/docs/test execution)
**Runtime**: 0s (redundancy detection)
**Exit**: Awaiting updated input.md directive for active priority
