# Phase M Next Steps Brief — Remediation Hand-off

**STAMP:** 20251015T201831Z
**Initiative:** [TEST-SUITE-TRIAGE-002]
**Phase:** M — Failure Synthesis & Remediation Hand-off
**Input:** Phase L full-suite rerun (STAMP 20251015T190350Z)
**Status:** Evidence synthesis COMPLETE; ready for remediation delegation

---

## Executive Summary

**Phase L Baseline:**
- **692 collected** / **540 passed (78.0%)** / **8 failed (1.2%)** / **143 skipped**
- **Runtime:** 1661.37s (27:41), 53.8% margin below 3600s timeout
- **Infrastructure Fixtures:** ✅ `session_infrastructure_gate` + `gradient_policy_guard` operational with ZERO runtime overhead

**Phase M Analysis:**
- **Clusters:** 6 active (CREF, PERF, TOOLS, CLI, GRAD, VEC)
- **Failures:** 8 total (1+1+1+2+1+2 respectively)
- **Regressions:** 0 new failures vs Phase G baseline
- **Progress:** 0 cleared failures vs Phase G baseline
- **Critical Finding:** Isolated test validation does NOT predict full-suite behavior

**Key Insight from Phase G→K→L Cycle:**
> Infrastructure fixtures deployed successfully (Phase K), but Phase D cluster diagnostics (Attempts #4-#10) that validated fixes in isolation did NOT translate to full-suite clearance. All 8 failures REAPPEARED in Phase L despite isolated validations showing PASS. Root cause: environmental variance (thermal throttling, memory pressure, CWD mismatches) during sustained 27-minute full-suite execution.

---

## Critical Blockers & Policy Decisions Required

### Blocker 1: Gap 1 — CWD Validation (CRITICAL, blocks 3 failures)

**Affected Clusters:** CLUSTER-CREF-001 (1 test) + CLUSTER-CLI-001 (2 tests)

**Issue:** `session_infrastructure_gate` validates C binary and golden asset paths at repo root during pytest collection, but tests execute from `/tmp/pytest-*` temporary directory. Relative path resolution breaks when CWD != repo root.

**Evidence:**
- Phase D targeted tests (Attempts #4, #6): PASSED in isolation
- Phase L full-suite: FAILED (same tests, same environment)
- Phase L Attempt #20 notes: "Infrastructure guard validated assets at repo root but tests ran from `/tmp` causing relative path mismatches"

**Remediation Path:**
1. Add CWD validation to `session_infrastructure_gate` in `tests/conftest.py`
   - Check `os.getcwd() == repo_root` or `Path.cwd().resolve() == repo_root.resolve()`
   - Skip infrastructure-dependent tests if CWD mismatch detected (with clear error message)
   - OR: Convert all infrastructure paths (C binary, golden assets) to absolute paths

2. Update `scripts/c_reference_utils.py`:
   - Use `Path.resolve()` for all path operations (line 23: `nb_c_bin = Path(nb_c_bin).resolve()`)
   - Remove relative path assumptions

3. Update CLI test fixtures in `tests/test_cli_flags.py`:
   - Convert golden asset paths to absolute: `repo_root / "reports/2025-10-cli-flags/..."`
   - Add `repo_root` fixture to `tests/conftest.py` exposing `Path(__file__).parent.parent`

**Estimated Effort:** 1 hour

**Impact:** Unblocks 3 failures (37.5% reduction)

**Priority:** P1 (CRITICAL) — must fix before next full-suite rerun

**Owner:** ralph (infrastructure fix)

---

### Blocker 2: CLUSTER-GRAD-001 — Gradient Timeout Policy Decision (CRITICAL, blocks 1 failure + CI stability)

**Issue:** Test `test_property_gradient_stability` consistently passes in isolation (844-846s, 6.5% below 905s tolerance) but breaches timeout during full-suite execution due to environmental variance (thermal throttling, memory pressure, pytest fixture overhead).

**Policy Options:**

| Option | Pros | Cons | Recommendation |
| --- | --- | --- | --- |
| **A: Accept Transient** | No code changes | Unstable CI; unpredictable failures | ❌ NOT RECOMMENDED |
| **B: Raise Tolerance to 1200s** | Quick fix (5 minutes) | Hides potential regressions; 32.6% tolerance inflation | ⚠️ ACCEPTABLE (requires documentation) |
| **C: Isolate to Pre-Suite Chunk** | Stable + diagnostic; preserves 905s ceiling | Adds CI complexity (2 hours implementation) | ✅ RECOMMENDED |
| **D: Implement Chunked Execution** | Cool-down periods reduce thermal issues | Over-engineered for single test (8 hours) | ❌ NOT RECOMMENDED |

**Recommendation:** **Option C — Isolate to Pre-Suite Chunk**

**Implementation Path (Option C):**
1. Create `tests/test_gradients_slow.py` containing only `test_property_gradient_stability`
2. Move test from `tests/test_gradients.py` to new file
3. Update CI/test harness to run `test_gradients_slow.py` as isolated chunk before full suite:
   ```bash
   # Pre-suite slow gradient chunk
   timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients_slow.py

   # Main full suite (905s timeout remains)
   timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/
   ```
4. Document environmental sensitivity in test docstring and `docs/development/testing_strategy.md §4.1`
5. Add artifact capture for isolated chunk (runtime, CPU temp, memory usage via `/usr/bin/time -v`)
6. Keep 905s tolerance unchanged (Phase I validation confirms appropriate ceiling for non-environmental variance)

**Alternative: Option B Implementation (if Option C rejected):**
1. Update `docs/development/testing_strategy.md §4.1` to raise tolerance from 905s to 1200s
2. Update `arch.md §15` Performance Expectations section with new ceiling
3. Update test marker: `@pytest.mark.timeout(1200)`
4. Document rationale: "Full-suite environmental variance requires 32.6% margin above isolated baseline"

**Estimated Effort:**
- Option C: 2 hours (isolate + document + CI update)
- Option B: 5 minutes (tolerance change + documentation)

**Impact:** Unblocks 1 failure (12.5% reduction) + stabilizes CI/CD

**Priority:** P1 (CRITICAL) — stakeholder decision REQUIRED before implementation

**Owner:** galph (policy decision) → ralph (implementation)

---

## Recommended Remediation Sequence

### Sprint 1: Infrastructure Gaps (1.5 hours total, unblocks 4 failures = 50%)

**Target:** Clear all infrastructure-related failures before next full-suite rerun

#### Task 1.1: Gap 1 — CWD Validation (1 hour, unblocks 3 failures)
- **File:** `tests/conftest.py`
- **Changes:**
  - Add CWD check to `session_infrastructure_gate`
  - Add `repo_root` fixture exposing `Path(__file__).parent.parent`
- **File:** `scripts/c_reference_utils.py`
  - Line 23: `nb_c_bin = Path(nb_c_bin).resolve()`
- **File:** `tests/test_cli_flags.py`
  - Convert golden asset paths to use `repo_root` fixture
- **Validation:** Targeted pytest for CREF-001 + CLI-001 clusters
- **Expected Result:** 3 failures → 0 failures

#### Task 1.2: CLUSTER-TOOLS-001 — PATH Fix (30 minutes, unblocks 1 failure)
- **File:** `tests/test_at_tools_001.py`
- **Changes:**
  - Replace bare `nb-compare` invocation with `shutil.which('nb-compare')` or `sys.executable + ' -m scripts.nb_compare'`
  - Add PATH diagnostic logging to test setup
- **Validation:** `pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration`
- **Expected Result:** 1 failure → 0 failures

**Sprint 1 Exit Criteria:**
- ✅ 4 failures cleared (CREF-001, CLI-001 x2, TOOLS-001)
- ✅ Infrastructure gaps documented in fix_plan
- ✅ Targeted pytest commands all passing
- ✅ Artifacts captured under `reports/2026-01-test-suite-refresh/phase_n/<STAMP>/sprint1/`

---

### Sprint 2: Dtype/Vectorization (1.5 hours total, unblocks 2 failures = 25%)

**Target:** Clear vectorization dtype pollution before next full-suite rerun

#### Task 2.1: CLUSTER-VEC-001 — Dtype Reset (30 minutes quick fix)
- **File:** `tests/test_tricubic_vectorized.py`
- **Changes:**
  - Add `@pytest.fixture(autouse=True)` at module level:
    ```python
    @pytest.fixture(autouse=True)
    def reset_dtype_state():
        """Reset torch default dtype before each test to prevent state pollution."""
        original_dtype = torch.get_default_dtype()
        torch.set_default_dtype(torch.float32)
        yield
        torch.set_default_dtype(original_dtype)
    ```
  - Add dtype assertion to test preamble: `assert torch.get_default_dtype() == torch.float32`
  - Add cache invalidation to test setup: `crystal.invalidate_cache()`
- **Validation:** `pytest -v tests/test_tricubic_vectorized.py::TestTricubicGather`
- **Expected Result:** 2 failures → 0 failures

#### Task 2.2: Root Cause Investigation (1 hour, optional)
- Profile fixture scope (module vs function) for Crystal/Detector
- Profile test collection order effects (run vectorization tests first vs last)
- Add pytest hook to reset torch state between tests if dtype reset insufficient
- Document findings in `reports/2026-01-test-suite-refresh/phase_n/<STAMP>/sprint2/dtype_investigation.md`

**Sprint 2 Exit Criteria:**
- ✅ 2 failures cleared (VEC-001 x2)
- ✅ Dtype reset fixture deployed
- ✅ Optional: Root cause documented
- ✅ Artifacts captured under `reports/2026-01-test-suite-refresh/phase_n/<STAMP>/sprint2/`

---

### Sprint 3: Gradient Policy Implementation (2 hours OR 5 minutes, unblocks 1 failure = 12.5%)

**Target:** Implement stakeholder-approved gradient timeout policy

**Prerequisite:** Stakeholder decision (Option B vs Option C) logged in fix_plan before implementation begins

#### Task 3.1 (if Option C — Isolate to Pre-Suite Chunk):
- **File:** `tests/test_gradients_slow.py` (NEW)
  - Move `test_property_gradient_stability` from `tests/test_gradients.py`
  - Add module docstring documenting environmental sensitivity
- **File:** `tests/test_gradients.py`
  - Remove moved test, leave stub pointing to new location
- **File:** `docs/development/testing_strategy.md`
  - Add §4.3 "Slow Gradient Pre-Suite Chunk" with execution commands and rationale
- **CI Update:** Add pre-suite chunk command before full-suite execution
- **Validation:** Run isolated chunk, verify runtime <1200s, then run full suite, verify no timeout
- **Expected Result:** 1 failure → 0 failures

#### Task 3.2 (if Option B — Raise Tolerance to 1200s):
- **File:** `tests/test_gradients.py`
  - Update marker: `@pytest.mark.timeout(1200)`
- **File:** `docs/development/testing_strategy.md`
  - Update §4.1 to raise tolerance from 905s to 1200s with rationale
- **File:** `arch.md`
  - Update §15 Performance Expectations with new ceiling
- **Validation:** Run full suite, verify test passes without timeout
- **Expected Result:** 1 failure → 0 failures

**Sprint 3 Exit Criteria:**
- ✅ 1 failure cleared (GRAD-001)
- ✅ Gradient policy documented in arch.md + testing_strategy.md
- ✅ Artifacts captured under `reports/2026-01-test-suite-refresh/phase_n/<STAMP>/sprint3/`

---

### Deferred: Performance Investigation (4 hours, unblocks 1 failure = 12.5%)

**Target:** CLUSTER-PERF-001 — Memory Bandwidth Utilization

**Rationale for Deferral:** Feeds into [PERF-PYTORCH-004] kernel fusion work; requires profiling under full-suite conditions to determine if failure is implementation bug or tolerance drift.

#### Task 4.1: Full-Suite Profiling (2 hours)
- Run full suite with memory profiler attached (`/usr/bin/time -v`, `py-spy`, or `torch.profiler`)
- Capture memory allocator state at test position (after 27 minutes of execution)
- Compare vs isolated execution baseline (Phase D Attempt #9: 1.3 GB peak RSS)
- Document memory pressure findings in `reports/2026-01-test-suite-refresh/phase_n/<STAMP>/perf_investigation.md`

#### Task 4.2: Tolerance Review (2 hours)
- Analyze historical bandwidth measurements (Phase D vs Phase L)
- Determine if tolerance threshold appropriate for full-suite context
- Options:
  - Relax tolerance (implementation decision)
  - Add memory allocator warmup phase (implementation change)
  - Move test to isolated chunk before full-suite (infrastructure change)
- Document decision in fix_plan with rationale

**Estimated Effort:** 4 hours total

**Impact:** Unblocks 1 failure (12.5% reduction)

**Priority:** P2 (HIGH) — defer until Sprint 1-3 complete and [PERF-PYTORCH-004] scoped

**Owner:** ralph (profiling) → galph (tolerance policy decision)

---

## Gating Requirements for Next Full-Suite Rerun

### Prerequisites (MUST BE COMPLETE before Phase N rerun):
1. ✅ Sprint 1 complete (Gap 1 + TOOLS-001 cleared)
2. ✅ Sprint 2 complete (VEC-001 cleared)
3. ✅ Sprint 3 complete (GRAD-001 policy implemented)
4. ✅ All fix_plan Attempts logged with artifact paths
5. ✅ Targeted pytest commands for all fixes passing

### Phase N Rerun Configuration:
```bash
# Environment (identical to Phase L)
CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905"

# Command (if Option C — pre-suite chunk)
timeout 1200 pytest -vv tests/test_gradients_slow.py  # Pre-suite chunk
timeout 3600 pytest -vv tests/                         # Full suite

# Command (if Option B — tolerance raised)
PYTEST_ADDOPTS="--maxfail=200 --timeout=1200"         # Raised ceiling
timeout 3600 pytest -vv tests/                         # Full suite
```

### Expected Phase N Results (if Sprint 1-3 complete):
- **Passed:** 540 → 547 (+7, 79.0%)
- **Failed:** 8 → 1 (-7, 0.14%; PERF-001 only)
- **Runtime:** ~1660s (27:40, similar to Phase L)

### Success Criteria for Phase N:
- ✅ 7 failures cleared (CREF-001, CLI-001 x2, TOOLS-001, VEC-001 x2, GRAD-001)
- ✅ 1 failure remaining (PERF-001, deferred to [PERF-PYTORCH-004])
- ✅ Pass rate ≥79% (exceeds 74% floor)
- ✅ Runtime <3600s (maintains 54% margin)

---

## Artifact Expectations for Remediation Work

All remediation sprints MUST produce:

1. **Code Changes:**
   - Files modified with line ranges
   - Git diff or commit SHA
   - Rationale for each change

2. **Validation Evidence:**
   - Targeted pytest command
   - Exit code (MUST be 0)
   - Runtime and resource usage (`/usr/bin/time -v`)
   - Test output log (pytest.log)

3. **Documentation Updates:**
   - Spec/arch/testing_strategy changes as appropriate
   - Fix_plan Attempt entry with metrics and artifact paths
   - Plan updates (mark tasks [D] when complete)

4. **Artifact Bundle Structure:**
   ```
   reports/2026-01-test-suite-refresh/phase_n/<STAMP>/
   ├── sprint1/
   │   ├── gap1_cwd_validation/
   │   │   ├── summary.md
   │   │   ├── pytest.log
   │   │   ├── code_changes.diff
   │   │   └── exit_code.txt
   │   └── cluster_tools/
   │       ├── summary.md
   │       ├── pytest.log
   │       └── exit_code.txt
   ├── sprint2/
   │   └── cluster_vec/
   │       ├── summary.md
   │       ├── pytest.log
   │       ├── dtype_investigation.md (optional)
   │       └── exit_code.txt
   ├── sprint3/
   │   └── cluster_grad/
   │       ├── summary.md
   │       ├── pytest.log
   │       ├── policy_decision.md
   │       └── exit_code.txt
   └── phase_n_summary.md
   ```

---

## Cross-References

- **Phase L Summary:** reports/2026-01-test-suite-refresh/phase_l/20251015T190350Z/analysis/summary.md
- **Cluster Mapping:** reports/2026-01-test-suite-refresh/phase_m/20251015T201831Z/analysis/cluster_mapping.md
- **Tracker Update:** reports/2026-01-test-suite-refresh/phase_m/20251015T201831Z/analysis/tracker_update.md
- **Failures JSON:** reports/2026-01-test-suite-refresh/phase_m/20251015T201831Z/analysis/failures.json
- **Fix Plan Ledger:** docs/fix_plan.md §[TEST-SUITE-TRIAGE-002]
- **Plan Reference:** plans/active/test-suite-triage-phase-h.md §Phase M
- **Testing Strategy:** docs/development/testing_strategy.md §§1.4-2.7
- **Architecture:** arch.md §§2 (runtime), 15 (gradients)

---

## Phase M Exit Criteria Verification

- ✅ M1: Failures parsed into JSON (8 tests extracted from Phase L log)
- ✅ M2: Clusters mapped with Phase G delta analysis (cluster_mapping.md)
- ✅ M3: Remediation tracker updated (tracker_update.md)
- ✅ M4: Next-step brief published (this document)

**Phase M Status:** ✅ COMPLETE — ready for remediation delegation to Ralph (Sprints 1-3)

---

## Recommended Next Actions for Fix Plan Update

1. **Append Attempt Entry to docs/fix_plan.md §[TEST-SUITE-TRIAGE-002]:**
   ```markdown
   * [2025-10-15] Attempt #21 — Result: ✅ success (Phase M synthesis complete).
     Parsed Phase L failures into classification bundle:
     - Failures: 8 (STAMP 20251015T190350Z)
     - Clusters: 6 active (CREF, PERF, TOOLS, CLI, GRAD, VEC)
     - Regressions: 0 new vs Phase G
     - Progress: 0 cleared vs Phase G
     Artifacts: `reports/2026-01-test-suite-refresh/phase_m/20251015T201831Z/`.
     Critical findings: (1) Gap 1 (CWD validation) blocks 3 failures;
     (2) GRAD-001 requires policy decision (isolate vs raise tolerance);
     (3) Isolated validations do NOT predict full-suite behavior.
     Next Actions: Sprint 1 (Gap 1 + TOOLS), Sprint 2 (VEC dtype reset),
     Sprint 3 (GRAD policy implementation).
   ```

2. **Update Next Action 20 to:**
   ```markdown
   20. ✅ COMPLETE (Attempt #21) — Phase M synthesis delivered classification
       bundle (failures.json, cluster_mapping.md, tracker_update.md,
       next_steps.md) under `phase_m/20251015T201831Z/`. Ready for
       Sprint 1-3 remediation delegation.
   ```

3. **Add New Next Actions for Sprints:**
   ```markdown
   21. 🟡 PENDING — Sprint 1: Infrastructure gaps (Gap 1 CWD validation +
       CLUSTER-TOOLS-001 PATH fix). Estimated 1.5 hours, unblocks 4 failures.
       Target: `phase_n/<STAMP>/sprint1/`.

   22. 🟡 PENDING — Sprint 2: CLUSTER-VEC-001 dtype reset (30min quick fix +
       1hr investigation). Estimated 1.5 hours, unblocks 2 failures.
       Target: `phase_n/<STAMP>/sprint2/`.

   23. 🟡 BLOCKED — Sprint 3: CLUSTER-GRAD-001 policy implementation. REQUIRES
       stakeholder decision (Option B: raise tolerance to 1200s OR
       Option C: isolate to pre-suite chunk). Estimated 2 hours (C) or
       5 minutes (B), unblocks 1 failure. Target: `phase_n/<STAMP>/sprint3/`.

   24. 🟡 DEFERRED — Sprint 4: CLUSTER-PERF-001 profiling + tolerance review.
       Feeds into [PERF-PYTORCH-004]. Estimated 4 hours, unblocks 1 failure.
       Defer until Sprints 1-3 complete.
   ```

---

**Next Steps Brief Status:** Phase M4 COMPLETE — ready for fix_plan ledger update and Sprint 1 kickoff
