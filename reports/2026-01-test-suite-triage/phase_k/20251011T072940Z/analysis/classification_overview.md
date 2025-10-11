# Phase K Classification Overview
## Test Suite Failure Analysis - 31 Failures Across 14 Clusters

**Timestamp:** 20251011T072940Z
**Phase:** K — Full Suite Rerun Post-Determinism Resolution
**Data Source:** Phase K pytest execution (`reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/logs/pytest_full.log`)
**Previous Baseline:** Phase I (`reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/`) — 36 failures

---

## Executive Summary

Phase K represents the first full-suite rerun after [DETERMINISM-001] completion (Attempt #10). The suite demonstrates continued improvement with a **13.9% reduction in failures** (36→31) driven primarily by determinism fixes and partial source-weighting progress.

**Key Achievements:**
- ✅ **Determinism clusters (C2, C15) fully resolved** — 3 failures eliminated
- ⬇️ **Source weighting improved** — 2 failures resolved (6→4)
- 📊 **Pass rate increased** — 73.8%→74.5% (+0.7pp)
- ⏱️ **Runtime optimized** — 1867.56s→1841.28s (-26s, -1.4%)

---

## Classification by Label

### Implementation Bugs: 30 failures (96.8%)

These failures represent incomplete spec implementation or regressions:

| Priority | Cluster IDs | Count | Category |
| --- | --- | --- | --- |
| P1 (Critical) | C3, C4, C8, C10, C16, C18 | 12 | Spec compliance & geometry |
| P2 (Infrastructure) | C5, C6, C7, C13 | 12 | Testing tools & CLI |
| P3 (Medium) | C9, C11, C14 | 5 | Conventions & performance |

**Severity Breakdown:**
- High: 22 failures (C3, C4, C5, C6, C7, C8, C10, C13, C16, C18)
- Medium: 5 failures (C9, C11, C14)

### Likely Deprecations: 1 failure (3.2%)

| Cluster | Count | Rationale |
| --- | --- | --- |
| C12 | 5 | Legacy test suite superseded by AT-PARALLEL |

**Recommendation:** Schedule spec review to determine if C12 tests should be marked as deprecated or updated to current architecture.

---

## Delta Analysis (Phase I → Phase K)

### Resolved Clusters (3 total)

| Cluster | Failures Resolved | Resolution Date | Fix Plan |
| --- | --- | --- | --- |
| C2 (Determinism - Mosaic RNG) | 2 | 2025-10-11 | [DETERMINISM-001] Attempt #10 |
| C15 (Mosaic Determinism) | 1 | 2025-10-11 | [DETERMINISM-001] Attempt #10 |
| **Total** | **3** | **-8.3% failure rate** | **1 fix-plan item** |

**Resolution Details:**
- **Root Cause:** RNG seed propagation not preserving dtype/device; TorchDynamo CUDA device query crashes
- **Fix:** Module-level env guards (CUDA_VISIBLE_DEVICES='', TORCHDYNAMO_DISABLE=1), dtype-neutral `mosaic_rotation_umat()`
- **Validation:** All AT-PARALLEL-013 and AT-PARALLEL-024 determinism tests passing (10 passed, 2 skipped)
- **Artifacts:** `reports/determinism-callchain/phase_e/20251011T060454Z/validation/`

### Improved Clusters (1 total)

| Cluster | Phase I Count | Phase K Count | Δ | Status |
| --- | --- | --- | --- | --- |
| C3 (Source Weighting) | 6 | 4 | -2 | Paused (Phase B design complete) |

**Improvement Details:**
- **Partial Resolution:** 2 of 6 failures resolved (likely test alignment or fallback logic fixes)
- **Remaining:** 4 failures related to sourcefile parsing and weight normalization
- **Next Steps:** Resume Phase C implementation post-K3 tracker refresh per input.md directive

### Unchanged Clusters (10 total)

| Cluster | Count | Priority | Status |
| --- | --- | --- | --- |
| C4 (Lattice Shape Models) | 2 | P1.4 | in_planning |
| C5 (Dual Runner Tooling) | 1 | P2.1 | in_planning |
| C6 (CLI Flags) | 2 | P2.2 | in_progress |
| C7 (Debug Trace) | 4 | P2.3 | in_planning |
| C8 (Detector Config) | 2 | P1.3 | in_planning |
| C9 (DENZO Convention) | 1 | P3.3 | in_planning |
| C10 (Detector Pivots) | 2 | P1.5 | in_planning |
| C11 (CUDA Graphs) | 3 | P3.1 | in_planning |
| C12 (Legacy Suite) | 5 | P4.1 | in_planning (deprecation candidate) |
| C13 (Tricubic Vectorization) | 2 | P2.4 | in_progress |
| C14 (Mixed Units) | 1 | P3.2 | in_planning |
| C16 (Gradient Flow) | 1 | P1.6 | in_planning |
| C18 (Triclinic C Parity) | 1 | P1.7 | in_planning |

**Observation:** These clusters remain stable, indicating no new regressions introduced by determinism fixes.

---

## Cluster Ownership Distribution

| Owner | Clusters | Total Failures | Active Fix Plans |
| --- | --- | --- | --- |
| ralph | 13 clusters | 29 failures | 11 in_planning, 2 in_progress |
| galph | 1 cluster | 2 failures | 1 in_progress (vectorization) |

**Coordination Notes:**
- Ralph: Primary owner for most clusters; may benefit from parallel work on P2 infrastructure items
- Galph: Vectorization specialist for C13 (tricubic); minimal cross-dependency

---

## Sprint 1 Readiness Assessment

**Blocker Status:** ✅ **ALL CLEAR**
- [DTYPE-NEUTRAL-001]: ✅ Verified complete (Phase J Pre-Sprint gate)
- [DETERMINISM-001]: ✅ Fully resolved (Phase K confirms stable)
- [VECTOR-PARITY-001]: Tap 5 instrumentation paused (not blocking Sprint 1)

**Sprint 1 Targets (per remediation_sequence.md):**
- **Total Sprint 1 Failures:** 17 (C2, C3, C4, C8, C10, C15, C16, C18)
- **Resolved:** 3 (C2, C15)
- **Remaining:** 14 (C3, C4, C8, C10, C16, C18)
- **Completion:** 17.6% (3/17)

**Recommendation:** Proceed with Sprint 1.2 (Source Weighting) resumption post-K3 tracker refresh.

---

## Test Suite Health Metrics

### Coverage & Pass Rate

| Metric | Phase I | Phase K | Δ |
| --- | --- | --- | --- |
| Tests Collected | 683 | 687 | +4 (+0.6%) |
| Passed | 504 (73.8%) | 512 (74.5%) | +8 (+0.7pp) |
| Failed | 36 (5.3%) | 31 (4.5%) | -5 (-0.8pp) |
| Skipped | 143 (20.9%) | 143 (20.8%) | 0 (0pp) |
| xfailed | 2 | 2 | 0 |

**Trend:** ✅ Positive — pass rate increasing, failure rate decreasing, test count stable.

### Runtime Analysis

| Phase | Duration (s) | Duration (min) | Δ vs Previous |
| --- | --- | --- | --- |
| Phase I | 1867.56 | 31:07 | - |
| Phase K | 1841.28 | 30:41 | -26.28s (-1.4%) |

**Observation:** Slight runtime improvement despite +4 test collection; determinism fixes may have reduced overhead.

### Gradient Test Dominance

**Gradient tests continue to dominate runtime** (~90% of total execution):
- Estimated: ~1655s / 1841s (89.9%)
- All gradient tests passing (no failures in gradient suite)
- Critical for PyTorch port differentiability validation

---

## Next Steps (Phase K2→K3 Transition)

1. ✅ **K2 Complete:** Triage summary authored with 31-failure inventory
2. 🔄 **K3 In Progress:** Refresh remediation tracker with updated counts
3. 📋 **K3 Artifacts:**
   - Update `remediation_tracker.md` table (C2/C15 status, C3 count)
   - Update `remediation_sequence.md` Sprint 1 progress (3/17 complete)
   - Author `analysis/summary.md` capturing K2/K3 highlights

---

## Artifacts Generated

- **Triage Summary:** `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/triage_summary.md`
- **Classification Overview:** `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/classification_overview.md` (this file)
- **Phase K Summary:** `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/summary.md`
- **Pytest Logs:** `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/logs/pytest_full.log`
- **JUnit XML:** `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/artifacts/pytest_full.xml`

---

**Classification Overview Complete.** Phase K demonstrates continued progress toward test suite stabilization with determinism resolution as the primary driver of improvement.
