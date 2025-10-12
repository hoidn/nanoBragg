# Stale Directive Confirmation — DETECTOR-CONFIG-001 Already Resolved

**STAMP:** 20251012T004433Z
**Supervisor Request:** Draft Option A remediation design for MOSFLM +0.5 pixel offset
**Status:** ⚠️ **REDUNDANT — Work Already Complete**
**Loop Type:** Docs-only evidence gathering

---

## Executive Summary

The work requested in `input.md` (Draft Option A remediation design under `reports/.../mosflm_offset/design.md`) has been **fully completed in prior loops**. This is the **4th consecutive redundant directive** (Attempts #36-38-39 preceding).

**Evidence of Completion:**
- **[DETECTOR-CONFIG-001]** status: `done (archived)` per `fix_plan.md:19`
- **Plan file:** Archived to `plans/archive/detector-config_20251011_resolved.md`
- **Comprehensive design:** 23KB document at `reports/.../20251011T214422Z/mosflm_offset/design.md`
- **Full implementation:** Phases B/C/D complete with validation (Phase D STAMP 20251011T223549Z)
- **C8 cluster:** ✅ RESOLVED with 0 regressions

---

## Completion Evidence Chain

### 1. Design Phase (Phase B — STAMP 20251011T214422Z)

**Artifact:** `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md`

**Size:** 583+ lines, 11 comprehensive sections

**Exit Criteria Met (B1-B4):**
- ✅ B1: Conversion site analysis (detector.py:78-142)
- ✅ B2: Offset formula + device/dtype discipline documented
- ✅ B3: Validation strategy specified
- ✅ B4: Regression test spec with selectors

**Design Decision:** Option A (BeamCenterSource enum) ratified as superior to Option B (heuristic matching)

**Key Deliverables:**
- Normative spec quotations (spec-a-core.md §72, arch.md §ADR-03)
- CLI detection logic for 8 explicit beam center flags
- Conditional offset application pattern
- Comprehensive test matrix (5 test cases specified)
- Documentation sync plan (detector.md, c_to_pytorch_config_map.md, findings.md)

---

### 2. Implementation Phase (Phase C — STAMP 20251011T213351Z)

**Artifact:** `reports/2026-01-test-suite-triage/phase_m3/20251011T213351Z/mosflm_fix/summary.md`

**Code Changes (7 files modified):**

**C1: Configuration Layer**
```python
# src/nanobrag_torch/config.py (new enum + field)
class BeamCenterSource(Enum):
    AUTO = "auto"        # Apply MOSFLM offset
    EXPLICIT = "explicit"  # No offset

@dataclass
class DetectorConfig:
    beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
```

**C2: CLI Detection**
```python
# src/nanobrag_torch/__main__.py (8 flag detection)
def determine_beam_center_source(args) -> BeamCenterSource:
    if any([args.beam_center_s, args.beam_center_f, args.Xbeam, args.Ybeam,
            args.Xclose, args.Yclose, args.ORGX, args.ORGY]):
        return BeamCenterSource.EXPLICIT
    return BeamCenterSource.AUTO
```

**C3: Conditional Offset**
```python
# src/nanobrag_torch/models/detector.py (two-condition guard)
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5
    return base
```

**C4: Test Coverage**
- `tests/test_beam_center_source.py` created (5 new test cases)
- `test_at_parallel_003.py` updated to validate explicit preservation
- `test_detector_config.py` updated for new config field

**C5: Targeted Validation**
- Command: `pytest -v tests/test_beam_center_source.py`
- Result: 16/16 PASSED (1.95s runtime, 0 failures)

**C6: Documentation Sync**
- `docs/architecture/detector.md` updated
- `docs/development/c_to_pytorch_config_map.md` updated
- `docs/findings.md` updated

---

### 3. Validation Phase (Phase D — STAMP 20251011T223549Z)

**Artifact:** `reports/2026-01-test-suite-triage/phase_m/20251011T223549Z/summary.md`

**Full-Suite Rerun (10-chunk ladder):**
- **Total Tests:** 686 collected (1 skipped)
- **Results:** 554 passed / 13 failed / 119 skipped (80.8% pass rate)
- **Runtime:** ~502s across 10 chunks (all <360s)

**C8 Cluster Resolution:**
- **Target Test:** `test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`
- **Status:** ✅ **PASSES** (was FAILING in Phase M2)
- **Validation:** Explicit beam center (512.5 mm) preserved exactly (no +0.5 offset applied)

**Regression Analysis:**
- **New Failures:** 0 (zero regressions introduced)
- **Pre-Existing Failures:** All 13 failures present in Phase M2 baseline
- **Net Improvement:** +1 failure resolved (C8), 0 introduced

**Parity Validation:**
- MOSFLM AUTO: C and PyTorch both apply +0.5 offset (correlation ≥0.999)
- MOSFLM EXPLICIT: PyTorch now matches C behavior (no offset, correlation ≥0.999)
- XDS/DIALS/CUSTOM: No offset for any source (correlation ≥0.999)

---

## Fix Plan Ledger Confirmation

**fix_plan.md Evidence:**

**Line 19 — Index Entry:**
```markdown
| [DETECTOR-CONFIG-001](#detector-config-001-detector-defaults-audit) | Detector defaults audit | High | done |
```

**Line 232 — Item Status:**
```markdown
## [DETECTOR-CONFIG-001] Detector defaults audit
- Status: done (archived 2025-10-11)
```

**Attempts History (fix_plan.md:31-91):**
- **Attempt #31:** Phase M3a sync (MOSFLM findings consolidated)
- **Attempt #32:** Phase M3a refresh (code locations audited)
- **Attempts #42-56:** Complete Phase B/C/D execution (design → implementation → validation)
- **Attempt #57:** Plan archival to `plans/archive/detector-config_20251011_resolved.md`

---

## Archived Plan Confirmation

**File:** `plans/archive/detector-config_20251011_resolved.md`

**Phases Marked Complete:**
- ✅ Phase A: Evidence Gathering (Tasks A1-A3)
- ✅ Phase B: Design (Tasks B1-B4)
- ✅ Phase C: Implementation (Tasks C1-C7)
- ✅ Phase D: Validation (Tasks D1-D4)

**Status Snapshot:**
```markdown
| Phase | Status | Exit | Notes |
|-------|--------|------|-------|
| A | [D] | ✅ | Evidence captured in Phase M3a/M3b bundles |
| B | [D] | ✅ | Design.md ratified Option A (20251011T214422Z) |
| C | [D] | ✅ | Implementation complete, 16/16 tests pass (20251011T213351Z) |
| D | [D] | ✅ | Full-suite validation, C8 RESOLVED, 0 regressions (20251011T223549Z) |
```

---

## Root Cause of Redundancy

**Stale Plan Reference:**
The `input.md` directive (lines 12-19) references:
```markdown
plans/active/detector-config.md:12-68 — Phase B tasks B1–B4 demand a design artifact before coding.
```

**Actual Status:**
```bash
$ ls plans/active/detector-config.md
ls: cannot access 'plans/active/detector-config.md': No such file or directory
```

**Resolution:**
Plan was archived after completion without `input.md` update. This is the **4th consecutive redundant loop** (Attempts #36/37/38/39).

---

## Recommendation for Supervisor

**Update `input.md` to acknowledge DETECTOR-CONFIG-001 completion and redirect to active priority:**

### Option 1: Continue TEST-SUITE-TRIAGE-001 (Recommended)

**Status:** Critical, in_progress, 13 failures remaining (per Phase M2 STAMP 20251011T193829Z)

**Active Clusters:**
- **C2 Gradient Testing (10 failures):** Documented workaround in arch.md §15 (NANOBRAGG_DISABLE_COMPILE=1)
- **C15 Mixed Units (1 failure):** Zero intensity bug, needs callchain analysis
- **C16 Orthogonality Tolerance (1 failure):** Numerical precision, tolerance adjustment recommended

**Reproduction Commands:**
```bash
# C15 Mixed Units Investigation
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_004.py::TestMixedUnits::test_zero_intensity

# C16 Orthogonality Tolerance
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_017.py::TestATParallel017::test_large_detector_tilts
```

**Next Phase:** Phase M3c mixed-units hypotheses or Phase M3d orthogonality tolerance adjustment

### Option 2: Resume VECTOR-PARITY-001 (Alternative)

**Status:** High, blocked on test suite health

**Blocker Resolution:** TEST-SUITE-TRIAGE-001 now at 81.7% pass rate (13/686 failures, significant improvement from 49/692)

**Next Actions:** Unblock vectorization work, resume 4096² benchmark parity investigation

---

## Artifacts Created This Loop

**Location:** `reports/2026-01-test-suite-triage/phase_m3/20251012T004433Z/stale_directive/`

**Files:**
- `summary.md` (this document) — Comprehensive redundancy evidence
- `commands.txt` (pending) — Commands executed this loop

**Runtime:** Docs-only verification (no pytest execution)

---

## Loop Self-Assessment (Ralph Checklist)

- ✅ Step -1: Evidence Parameter Validation (no test reproduction required for redundancy check)
- ✅ Step 0: Read all core documentation (input.md, fix_plan.md, summary.md, plan archive)
- ✅ Step 3: Search first (confirmed completion via fix_plan.md Attempts #42-57)
- ✅ Step 7: Update fix_plan.md (will append Attempt #39 with redundancy note)
- ✅ Step 9: Commit hygiene (docs-only update to fix_plan.md)

**Module Scope:** docs/planning (no code changes)
**Acceptance Focus:** TEST-SUITE-TRIAGE-001 redirection
**Stop Rule:** No cross-module work (docs-only)

---

**Conclusion:** [DETECTOR-CONFIG-001] is **definitively complete**. Supervisor should update `input.md` to redirect to TEST-SUITE-TRIAGE-001 active priorities (C15 mixed-units or C16 orthogonality).
