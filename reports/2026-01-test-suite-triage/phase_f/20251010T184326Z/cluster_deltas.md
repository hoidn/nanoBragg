# Cluster Deltas: Phase C (Attempt #5) vs Phase F (Attempt #7)

**Comparison Period:** 2025-10-10 (Phase C 20251010T135833Z) → 2025-10-10 (Phase F 20251010T184326Z)
**Artifact Roots:**
- Phase C: `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/`
- Phase F: `reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/`

## Summary

**Net Change:** +1 passed, -1 failure (516 passed vs 515; 49 failed vs 50)
**Runtime:** Virtually unchanged (1860.74s vs 1864.76s)
**Cluster Changes:** 1 resolved (C1), 17 remain active

| Metric | Phase C (Attempt #5) | Phase F (Attempt #7) | Delta |
| --- | --- | --- | --- |
| Tests Executed | 691/692 | 691/692 | 0 |
| Passed | 515 | 516 | +1 |
| Failed | 50 | 49 | -1 |
| Skipped | 126 | 126 | 0 |
| Runtime (seconds) | 1864.76 | 1860.74 | -4.02 |
| Active Clusters | 18 | 17 | -1 |

## Cluster-by-Cluster Delta Table

| Cluster ID | Category | Count (Phase C) | Count (Phase F) | Delta | Status Change | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | CLI Defaults | 1 | 0 | -1 | ✅ in_planning → done | Resolved by [CLI-DEFAULTS-001] Attempt #6 |
| C2 | Determinism | 6 | 6 | 0 | in_planning → in_progress | Blocked by dtype issue; plan created |
| C3 | CUDA Graphs | 6 | 6 | 0 | unassigned → in_planning | New fix-plan entry created |
| C4 | Grazing Incidence | 4 | 4 | 0 | in_planning | No change; blocked by [VECTOR-PARITY-001] |
| C5 | Unit Conversion | 1 | 1 | 0 | unassigned → in_planning | New fix-plan entry created |
| C6 | Tricubic Vectorization | 2 | 2 | 0 | in_progress | No change; galph ownership |
| C7 | Source Weighting | 6 | 6 | 0 | in_planning | No change; regression noted |
| C8 | Lattice Shape Models | 2 | 2 | 0 | unassigned → in_planning | New fix-plan entry created |
| C9 | Dual Runner Tooling | 1 | 1 | 0 | in_planning | No change |
| C10 | CLI Flags | 3 | 3 | 0 | in_progress | No change |
| C11 | Debug Trace | 4 | 4 | 0 | in_planning | No change |
| C12 | Detector Config | 2 | 2 | 0 | in_planning | No change |
| C13 | Detector Conventions (DENZO) | 1 | 1 | 0 | unassigned → in_planning | New fix-plan entry created |
| C14 | Detector Pivots | 2 | 2 | 0 | unassigned → in_planning | New fix-plan entry created |
| C15 | dtype Support | 2 | 2 | 0 | unassigned → in_progress | Elevated to critical blocker for C2 |
| C16 | Legacy Suite | 5 | 5 | 0 | unassigned → in_planning | New fix-plan entry created |
| C17 | Gradient Flow | 1 | 1 | 0 | unassigned → in_planning | New fix-plan entry created |
| C18 | Triclinic Parity | 1 | 1 | 0 | unassigned → in_planning | New fix-plan entry created |
| **TOTAL** | **18 Clusters** | **50** | **49** | **-1** | **1 done, 17 active** | **Net improvement** |

## Resolved Clusters

### C1: CLI Defaults ✅
**Resolution Date:** 2025-10-10 (between Phase C and Phase F)
**Fix Plan:** [CLI-DEFAULTS-001]
**Implementation:** Attempt #6
**Root Cause:** HKL guard logic in `__main__.py` incorrectly triggered when no `-hkl` file provided, preventing `default_F` fallback.
**Fix:** Removed sentinel `config['hkl_data'] = None` (line 443) and tightened guard to use `config.get('hkl_data')` semantics (lines 1089-1090).
**Validation:** Targeted test `test_minimal_render_with_default_F` now passes (4.81s runtime); full suite confirms no regression.

**Previously Failing Test (now passing):**
- `tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` ✅

**Artifacts:**
- Implementation plan: `reports/2026-01-test-suite-triage/phase_d/20251010T161925Z/cli-defaults/phase_c/remediation_plan.md`
- Attempt notes: `docs/fix_plan.md` [CLI-DEFAULTS-001] Attempts #1-#6

## Status Transitions

### Ownership Changes
**None** - All clusters retain original owners (ralph or galph).

### Status Upgrades (unassigned → in_planning)
Eight clusters received fix-plan entries between Phase C and Phase F:
1. **C3:** [CUDA-GRAPHS-001] - CUDA graphs compatibility testing
2. **C5:** [UNIT-CONV-001] - Mixed unit conversion parity
3. **C8:** [LATTICE-SHAPE-001] - GAUSS/TOPHAT lattice shape models
4. **C13:** [DENZO-CONVENTION-001] - DENZO convention support
5. **C14:** [PIVOT-MODE-001] - Detector pivot modes (BEAM/SAMPLE)
6. **C16:** [LEGACY-SUITE-001] - Legacy translation suite upkeep
7. **C17:** [GRADIENT-FLOW-001] - Gradient flow regression
8. **C18:** [TRICLINIC-PARITY-001] - Triclinic parity alignment

### Status Upgrades (in_planning → in_progress)
Two clusters advanced to active remediation:
1. **C2:** [DETERMINISM-001] - Plan created; blocked by [DTYPE-NEUTRAL-001]
2. **C15:** [DTYPE-NEUTRAL-001] - Elevated to critical blocker status

## Active Blockers

### Critical Path Blockers
1. **[DTYPE-NEUTRAL-001]** (C15) blocks **[DETERMINISM-001]** (C2)
   - Detector basis vectors remain float32 when float64 requested
   - Prevents determinism tests from reaching seed-dependent code
   - Priority: P1 (must resolve before C2 can proceed)

2. **[VECTOR-PARITY-001]** (external to triage) blocks **[DETECTOR-GRAZING-001]** (C4)
   - Tap 5 completion required before grazing incidence work begins
   - Priority: P2 (after dtype fix)

## Observations

### Positive Trends
1. **CLI Defaults Resolved:** Fastest fix in triage cycle (6 attempts, ~8 hours elapsed)
2. **No New Failures:** All 49 failures are pre-existing from Phase C
3. **Runtime Stability:** <1% variance (1860.74s vs 1864.76s) indicates consistent test performance
4. **Planning Progress:** 8 new fix-plan entries created, moving clusters from unassigned to in_planning

### Concerns
1. **Blocker Chain:** C15 blocks C2; resolving dtype issue is now critical path
2. **No Additional Resolutions:** Only 1/18 clusters resolved since Phase C despite multiple in_progress items
3. **Low Priority Backlog:** C16 (legacy suite) deferred; may accumulate technical debt

### Remediation Velocity
- **Resolved:** 1 cluster (C1) in ~1 day between Phase B and Phase E
- **Remaining:** 17 clusters across 3 priorities (P1: 3, P2: 7, P3-P4: 7)
- **Estimated Effort:** P1 items (dtype, determinism, debug trace) likely require 2-3 loops each; P2 items vary by complexity

## Next Actions (Phase G Coordination)

1. **Priority Ladder Update:**
   - Move [DTYPE-NEUTRAL-001] to P1.1 (critical blocker)
   - Cascade [DETERMINISM-001] to P1.2 (blocked)
   - Retain [DEBUG-TRACE-001] at P1.3 (infrastructure)

2. **Handoff Refresh:**
   - Update `reports/2026-01-test-suite-triage/phase_d/20260113T000000Z/handoff.md` with Phase F metrics
   - Reference Phase F artifacts in supervisor input template

3. **Supervisor Coordination:**
   - Issue [DTYPE-NEUTRAL-001] Phase C blueprint to ralph
   - Hold [DETERMINISM-001] delegation until dtype fix attempt completes
   - Monitor [VECTOR-PARITY-001] Tap 5 for [DETECTOR-GRAZING-001] unblocking

## References

- **Phase C Triage:** `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/triage_summary.md`
- **Phase E Summary:** `reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/summary.md`
- **CLI Defaults Resolution:** `docs/fix_plan.md` [CLI-DEFAULTS-001] Attempt #6
- **Fix Plan Ledger:** `docs/fix_plan.md` (lines 1-100)
- **Test Suite Triage Plan:** `plans/active/test-suite-triage.md`

---

**Phase F2 Complete:** Cluster deltas documented; ownership and priority changes captured.
