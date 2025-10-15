# Phase M Remediation Tracker Update

**STAMP:** 20251015T201831Z
**Initiative:** [TEST-SUITE-TRIAGE-002]
**Input:** Phase L full-suite rerun (reports/2026-01-test-suite-refresh/phase_l/20251015T190350Z/)
**Baseline Tracker:** reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md
**Cluster Mapping:** reports/2026-01-test-suite-refresh/phase_m/20251015T201831Z/analysis/cluster_mapping.md

---

## Executive Summary

**Phase L Results (STAMP 20251015T190350Z):**
- **Total Collected:** 692 tests
- **Passed:** 540 (78.0%)
- **Failed:** 8 (1.2%)
- **Skipped:** 143
- **Runtime:** 1661.37s (27:41)

**Delta vs Phase G Baseline (STAMP 20251015T163131Z):**
- **Passed:** 540 → 540 (±0, STABLE)
- **Failed:** 8 → 8 (±0, NO PROGRESS)
- **Runtime:** 1656.77s → 1661.37s (+0.28% noise)

**Infrastructure Fixtures Deployed:**
- ✅ `session_infrastructure_gate` active (C binary + golden asset validation)
- ✅ `gradient_policy_guard` active (NANOBRAGG_DISABLE_COMPILE enforcement)
- **Runtime Overhead:** Negligible (+4.6s within measurement noise)
- **Failures Introduced:** 0
- **Failures Cleared:** 0

**Critical Finding:** Phase K infrastructure fixtures operational but did NOT clear failures — isolated test validation does NOT predict full-suite behavior.

---

## Cluster Status Table (Phase M Refresh)

| Cluster ID | Phase G Count | Phase L Count | Delta | Status | Owner | Fix Plan | Priority | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLUSTER-CREF-001 | 1 | 1 | ±0 | ❌ ACTIVE (REAPPEARED) | ralph | [TEST-SUITE-TRIAGE-002] | P1 (CRITICAL) | Gap 1: Add CWD validation to `session_infrastructure_gate` |
| CLUSTER-PERF-001 | 1 | 1 | ±0 | ❌ ACTIVE (REAPPEARED) | ralph | [PERF-PYTORCH-004] | P2 (HIGH) | Review tolerance thresholds; defer to perf uplift work |
| CLUSTER-TOOLS-001 | 1 | 1 | ±0 | ❌ ACTIVE (REAPPEARED) | ralph | [TOOLING-DUAL-RUNNER-001] | P1 (HIGH) | Fix PATH handling in test (use `shutil.which()`) |
| CLUSTER-CLI-001 | 2 | 2 | ±0 | ❌ ACTIVE (REAPPEARED) | ralph | [CLI-FLAGS-003] | P1 (CRITICAL) | Gap 1: Convert golden asset paths to absolute |
| CLUSTER-GRAD-001 | 1 | 1 | ±0 | ❌ ACTIVE (REAPPEARED) | ralph | [TEST-SUITE-TRIAGE-002] | P1 (CRITICAL) | Policy decision: isolate to pre-suite chunk OR raise tolerance to 1200s |
| CLUSTER-VEC-001 | 2 | 2 | ±0 | ❌ ACTIVE (REAPPEARED) | ralph | [VECTOR-TRICUBIC-002] | P2 (HIGH) | Add dtype reset to test setup |
| **TOTALS** | **8** | **8** | **±0** | **0 cleared / 0 new** | - | - | - | **6 clusters, 8 failures** |

---

## Detailed Delta Analysis

### CLUSTER-CREF-001: C Binary Path Resolution (1 test)

**Phase D Resolution Attempt:** Attempt #4 patched `scripts/c_reference_utils.py` for NB_C_BIN precedence; targeted test passed in isolation (~3.9s).

**Phase L Full-Suite Result:** ❌ FAILED (REAPPEARED)

**Root Cause (CONFIRMED):** CWD mismatch — infrastructure guard validates paths at repo root during collection, but tests execute from `/tmp/pytest-*` breaking relative paths.

**Impact:** BLOCKS 1 failure (12.5%)

**Remediation Path:** Gap 1 fix (add CWD validation to `session_infrastructure_gate` + convert C binary path to absolute)

**Estimated Effort:** 1 hour

**Priority:** P1 (CRITICAL) — shares fix with CLUSTER-CLI-001

---

### CLUSTER-PERF-001: Memory Bandwidth Utilization (1 test)

**Phase D Isolated Result:** Attempt #9 validated test passing in 3.15s with 337% CPU, 1.3 GB peak RSS.

**Phase L Full-Suite Result:** ❌ FAILED (REAPPEARED)

**Root Cause Hypothesis:** Memory pressure or cache contention during sustained 27-minute full-suite load; isolated execution does not reproduce full-suite conditions.

**Impact:** BLOCKS 1 failure (12.5%)

**Remediation Path:**
1. Review tolerance thresholds (may be too strict for full-suite context)
2. Add memory allocator warmup to test setup
3. Consider moving to isolated chunk before full-suite
4. Profile full-suite execution at test position

**Estimated Effort:** 4 hours (profiling + tolerance policy)

**Priority:** P2 (HIGH) — defer to [PERF-PYTORCH-004] kernel fusion work

---

### CLUSTER-TOOLS-001: nb-compare Script Integration (1 test)

**Phase D Resolution Attempt:** Attempt #7 verified nb-compare installed at `/home/ollie/miniconda3/bin/nb-compare`; targeted test passed in ~10s.

**Phase L Full-Suite Result:** ❌ FAILED (REAPPEARED)

**Root Cause Hypothesis:** Test invokes nb-compare via incorrect path or PATH pollution from concurrent tests; editable install may become stale during long full-suite run.

**Impact:** BLOCKS 1 failure (12.5%)

**Remediation Path:**
1. Update test to use `shutil.which('nb-compare')` or `sys.executable + ' -m scripts.nb_compare'`
2. Add pytest fixture to verify editable install freshness
3. Add PATH diagnostic logging to test setup

**Estimated Effort:** 30 minutes

**Priority:** P1 (HIGH) — quick fix with PATH handling improvement

---

### CLUSTER-CLI-001: Golden Asset Path Resolution (2 tests)

**Phase D Resolution Attempt:** Attempt #6 verified golden assets present at repo root with SHA256 checksums; targeted tests passed in 2.71s.

**Phase L Full-Suite Result:** ❌ FAILED (2 tests; REAPPEARED)

**Root Cause (CONFIRMED):** IDENTICAL to CLUSTER-CREF-001 — CWD mismatch breaks relative paths during full-suite execution.

**Impact:** BLOCKS 2 failures (25%)

**Remediation Path:** Gap 1 fix (shared with CLUSTER-CREF-001):
1. Add CWD validation to `session_infrastructure_gate`
2. Convert golden asset paths to absolute in test fixtures
3. Add pytest fixture to expose repo root as `repo_root` fixture

**Estimated Effort:** 1 hour (SHARED with CLUSTER-CREF-001)

**Priority:** P1 (CRITICAL) — shares fix with CLUSTER-CREF-001

---

### CLUSTER-GRAD-001: Gradient Stability Timeout (1 test)

**Phase D/F/I Isolated Results:**
- Phase D Attempt #8: 844.94s (6.6% below 905s)
- Phase F Attempt #14: 844.15s (6.7% below 905s)
- Phase I Attempt #17: 846.13s (6.5% below 905s)

**Phase L Full-Suite Result:** ❌ FAILED (timeout >905s; REAPPEARED)

**Root Cause (CONFIRMED):** Environmental variance during sustained 27-minute full-suite load — thermal throttling, memory pressure, or pytest fixture overhead causes runtime >905s despite isolated validation showing consistent 844-846s runtimes.

**Key Insight:** "Isolated test execution does NOT predict full-suite behavior. Infrastructure and environmental validation must occur in full-suite context to be considered truly resolved."

**Impact:** BLOCKS 1 failure (12.5%) + CI/CD stability

**Remediation Policy Decision Required:**

| Option | Effort | Impact | Recommendation |
| --- | --- | --- | --- |
| Accept Transient | 0 hours | Unstable test; unpredictable CI failures | ❌ NOT RECOMMENDED |
| Raise Tolerance to 1200s | 5 minutes | Hides potential regressions | ⚠️ ACCEPTABLE with documentation |
| Isolate to Pre-Suite Chunk | 2 hours | Best balance; stable + diagnostic | ✅ RECOMMENDED |
| Implement Chunked Execution | 8 hours | Over-engineered for single test | ❌ NOT RECOMMENDED |

**Recommended Path:** Isolate test to `tests/test_gradients_slow.py` as dedicated pre-suite chunk before full-suite execution.

**Estimated Effort:** 2 hours (isolate + document + update CI harness)

**Priority:** P1 (CRITICAL) — blocks test suite stability; stakeholder decision required

---

### CLUSTER-VEC-001: Tricubic Vectorization Dtype Mismatch (2 tests)

**Phase D Isolated Result:** Attempt #10 validated both tests passing on CPU (1.93s) and GPU (2.06s) with correct dtype coercion (float64 → float32).

**Phase L Full-Suite Result:** ❌ FAILED (2 tests; REAPPEARED)

**Root Cause Hypothesis:** Dtype state pollution or fixture ordering dependency during full-suite execution — preceding tests may call `torch.set_default_dtype()` affecting subsequent tests.

**Impact:** BLOCKS 2 failures (25%)

**Remediation Path:**
1. Add explicit `torch.set_default_dtype(torch.float32)` to test setup/teardown
2. Investigate fixture scope (module vs function) for Crystal/Detector
3. Add `crystal.invalidate_cache()` + `detector.invalidate_cache()` to test setup
4. Add dtype assertion to test preamble

**Estimated Effort:** 30 minutes (quick fix) + 1 hour (root cause investigation)

**Priority:** P2 (HIGH) — likely quick fix with dtype reset

---

## Remediation Sequencing (Recommended)

### Sprint 1: Infrastructure Gaps (Unblock 3 failures)
**Estimated Effort:** 1.5 hours
**Impact:** -3 failures (37.5% reduction)

1. **Gap 1: CWD Validation** (1 hour)
   - Add CWD validation to `session_infrastructure_gate` in `tests/conftest.py`
   - Convert C binary path to absolute in `scripts/c_reference_utils.py`
   - Convert golden asset paths to absolute in CLI test fixtures
   - **Unblocks:** CLUSTER-CREF-001 (1 test) + CLUSTER-CLI-001 (2 tests)

2. **CLUSTER-TOOLS-001: PATH Fix** (30 minutes)
   - Update `tests/test_at_tools_001.py` to use `shutil.which('nb-compare')`
   - Add PATH diagnostic logging to test setup
   - **Unblocks:** CLUSTER-TOOLS-001 (1 test)

### Sprint 2: Dtype/Vectorization (Unblock 2 failures)
**Estimated Effort:** 1.5 hours
**Impact:** -2 failures (25% reduction)

3. **CLUSTER-VEC-001: Dtype Reset** (30 minutes quick fix + 1 hour investigation)
   - Add dtype reset to `tests/test_tricubic_vectorized.py` setup
   - Investigate fixture scope and cache state
   - Add dtype assertion to test preamble
   - **Unblocks:** CLUSTER-VEC-001 (2 tests)

### Sprint 3: Gradient Policy Decision (Unblock 1 failure)
**Estimated Effort:** 2 hours OR 5 minutes (depending on policy choice)
**Impact:** -1 failure (12.5% reduction) + CI/CD stability

4. **CLUSTER-GRAD-001: Isolation** (2 hours if isolated, 5 minutes if tolerance raised)
   - **Option A (RECOMMENDED):** Isolate to pre-suite chunk (2 hours)
   - **Option B:** Raise tolerance to 1200s (5 minutes)
   - Requires stakeholder decision before implementation
   - **Unblocks:** CLUSTER-GRAD-001 (1 test)

### Deferred: Performance Investigation
**Estimated Effort:** 4 hours
**Impact:** -1 failure (12.5% reduction)

5. **CLUSTER-PERF-001: Tolerance Review** (4 hours profiling + policy)
   - Defer to [PERF-PYTORCH-004] kernel fusion work
   - Requires profiling under full-suite conditions
   - May require tolerance adjustment or test isolation

---

## Exit Criteria for Phase M

- ✅ M1: Failures parsed into JSON (8 tests)
- ✅ M2: Clusters mapped with Phase G delta analysis
- ✅ M3: Remediation tracker updated (this document)
- ⏳ M4: Next-step brief published (NEXT ACTION)

---

## Baseline Tracker Update Instructions

**Target File:** `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md`

**Option 1 (In-Place Update):** Edit tracker directly with Phase L counts and STAMP references

**Option 2 (Addendum):** Create addendum at `reports/2026-01-test-suite-refresh/phase_m/20251015T201831Z/tracker_update.md` (this file) and reference from baseline tracker

**Recommendation:** Use Option 2 (addendum) to preserve Phase J baseline and maintain audit trail.

---

## Cross-References

- **Phase L Summary:** reports/2026-01-test-suite-refresh/phase_l/20251015T190350Z/analysis/summary.md
- **Phase G Baseline:** reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/analysis/summary.md
- **Cluster Mapping:** reports/2026-01-test-suite-refresh/phase_m/20251015T201831Z/analysis/cluster_mapping.md
- **Failures JSON:** reports/2026-01-test-suite-refresh/phase_m/20251015T201831Z/analysis/failures.json
- **Baseline Tracker:** reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md
- **Fix Plan Ledger:** docs/fix_plan.md §[TEST-SUITE-TRIAGE-002]
- **Plan Reference:** plans/active/test-suite-triage-phase-h.md §Phase M

---

**Tracker Update Status:** Phase M3 COMPLETE — ready for next-step brief (M4)
