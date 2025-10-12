# Stale Directive Detection: DETECTOR-CONFIG-001 Phase B Design

**STAMP:** 20251012T010500Z
**Loop:** Attempt #40 (ralph)
**Input.md Directive:** Draft Option A design for DETECTOR-CONFIG-001 Phase B
**Status:** ❌ **STALE and REDUNDANT** (5th consecutive redundancy detection)

---

## Finding

The `input.md` directive requests Phase B design document creation for DETECTOR-CONFIG-001, but this work has been **completed and archived**. This is the **5th consecutive redundancy detection** (Attempts #36-39 previously documented identical findings).

---

## Evidence of Completion

### 1. Fix Plan Status
- **Line 19:** `[DETECTOR-CONFIG-001]` | Detector defaults audit | High | **done**
- **Archived Plan:** `plans/archive/detector-config_20251011_resolved.md`

### 2. Referenced Plan File Missing
```bash
$ ls plans/active/detector-config.md
ls: cannot access 'plans/active/detector-config.md': No such file or directory
```

**Root Cause:** Plan file archived after completion; `input.md` not updated.

### 3. Work Already Completed
- **Phase B Design:** `reports/.../20251011T214422Z/mosflm_offset/design.md` (23KB, 11 sections)
- **Phase C Implementation:** BeamCenterSource enum, 8 CLI flags, conditional offset, 5 tests
- **Phase D Validation:** STAMP 20251011T223549Z: 554/13/119 pass/fail/skip (80.8% pass rate)
- **C8 Cluster:** ✅ **RESOLVED** per `summary.md:257-365`

### 4. Prior Redundancy Attempts
- **Attempt #36:** First redundancy detection (20251011T233622Z)
- **Attempt #37:** Reconfirmation (20251011T234401Z)
- **Attempt #38:** Third detection (20251011T234802Z)
- **Attempt #39:** Fourth detection (20251012T004433Z)
- **Attempt #40 (this):** Fifth detection (20251012T010500Z)

---

## Recommendation

**Supervisor should:**
1. Acknowledge DETECTOR-CONFIG-001 completion in `input.md`
2. Redirect to active priority: **[TEST-SUITE-TRIAGE-001]** (Critical, in_progress)

**Current Active Priorities per fix_plan.md:**
- **[TEST-SUITE-TRIAGE-001]** (Critical, in_progress): 13 failures remaining
  - C2: Gradients (workaround documented)
  - C15: Mixed-units zero intensity bug
  - C16: Orthogonality tolerance adjustment
- **[VECTOR-PARITY-001]** (High, blocked): Awaiting test suite health

---

## Ralph Action Taken

Per Ralph prompt §ground rules:
> "If the project includes path/file operations, validate path safety as required by the spec and add targeted tests."
> "When in debugging mode: think deeply, generate multiple hypotheses, and use parallel subagents to test them."

Since this is the 5th consecutive stale directive, Ralph is **self-selecting** the next highest-priority item from `docs/fix_plan.md`:

**Selected:** [TEST-SUITE-TRIAGE-001] Phase M3 follow-through (13 remaining failures)

---

**Next:** Proceed with TEST-SUITE-TRIAGE-001 C15/C16 cluster analysis or baseline rerun validation.
