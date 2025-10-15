# Phase M — Cluster Mapping & Regression Analysis (STAMP 20251015T201831Z)

## Overview
- Initiative: TEST-SUITE-TRIAGE-002
- Input: Phase L full-suite rerun (reports/2026-01-test-suite-refresh/phase_l/20251015T190350Z/)
- Baseline: Phase G summary (reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/)
- Scope: 8 failures identified (identical to Phase G baseline)
- Comparison: Phase K infrastructure fixtures deployed; no observable change to failure set

## Executive Summary

**Phase L vs Phase G Delta:** ZERO changes
- Failures: 8 → 8 (±0)
- Passed: 540 → 540 (±0)
- Skipped: 143 → 143 (±0)
- Runtime: 1656.77s → 1661.37s (+0.28% noise)

**Infrastructure Fixture Impact:** ZERO failures introduced or cleared
- `session_infrastructure_gate` and `gradient_policy_guard` both executed successfully
- No runtime overhead observed
- CWD validation gap identified (Gap 1, see Phase L summary.md)

**Cluster Status:** All 6 Phase C clusters remain ACTIVE
- No new failure modes detected
- No cleared failure modes observed
- Isolated test validations (Phase D Attempts #4-#10) did NOT predict full-suite behavior

## Cluster Mapping Table

| Cluster ID | Nodeids (Phase L) | Status vs Phase G | Classification | Root Cause | Remediation Plan | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| CLUSTER-CREF-001 | tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c | ❌ ACTIVE (REAPPEARED) | Infrastructure | C binary path resolution fails during full-suite despite Phase D Attempt #4 fix; `session_infrastructure_gate` validates NB_C_BIN at collection but test runs from `/tmp` causing relative path mismatch | Gap 1: Add CWD validation to infrastructure guard; verify tests run from repo root or update path resolution to use absolute paths | P1 (CRITICAL) |
| CLUSTER-PERF-001 | tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization | ❌ ACTIVE (REAPPEARED) | Implementation/Perf | Bandwidth tolerance breach; Phase D Attempt #9 isolated validation passed but full-suite execution may introduce memory pressure or concurrent test interference | Feeds into [PERF-PYTORCH-004]; review tolerance thresholds or isolate test to dedicated chunk | P2 (HIGH) |
| CLUSTER-TOOLS-001 | tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration | ❌ ACTIVE (REAPPEARED) | Infrastructure | nb-compare console script path resolution; Phase D Attempt #7 verified script exists at `/home/ollie/miniconda3/bin/nb-compare` but test may invoke via incorrect path or missing env | Verify test uses `which nb-compare` or `sys.executable -m scripts.nb_compare`; ensure editable install active during test execution | P1 (HIGH) |
| CLUSTER-CLI-001 (2 tests) | tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu] ; tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip | ❌ ACTIVE (REAPPEARED) | Infrastructure | Golden assets (`pix0_expected.json`, `scaled.hkl`) validated present at repo root (Phase D Attempt #6) but tests run from `/tmp` causing relative path failures; `session_infrastructure_gate` checks repo-root paths only | Gap 1: Add CWD validation to infrastructure guard and/or convert golden asset paths to absolute in test fixtures | P1 (CRITICAL) |
| CLUSTER-GRAD-001 | tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability | ❌ ACTIVE (REAPPEARED) | Environmental Variance | Timeout >905s during full-suite execution; Phase D Attempt #8 (844.94s), Phase F Attempt #14 (844.15s), Phase I Attempt #17 (846.13s) all passed in isolation with 6.5% margin, indicating thermal throttling or memory pressure during sustained 27-minute full-suite load | Policy decision required: (1) Accept transient timeout as environmental noise, (2) Raise tolerance to 1200s, (3) Move test to isolated pre-suite chunk, or (4) Implement chunked execution with cool-down periods | P1 (CRITICAL) |
| CLUSTER-VEC-001 (2 tests) | tests/test_tricubic_vectorized.py::TestTricubicGather::{test_vectorized_matches_scalar,test_oob_warning_single_fire} | ❌ ACTIVE (REAPPEARED) | Implementation Regression | Dtype mismatch float32 vs float64; Phase D Attempt #10 validated both tests pass on CPU/GPU in isolation with correct dtype coercion behavior, suggesting full-suite execution introduces dtype state pollution or fixture ordering dependency | Investigate test collection order effects, fixture scope, and global dtype state; add explicit dtype reset to test setup; may require test isolation or fixture redesign | P2 (HIGH) |

## Detailed Cluster Analysis

### CLUSTER-CREF-001: C Binary Path Resolution (Infrastructure, CRITICAL)

**Phase L Status:** ❌ FAILED (REAPPEARED after Phase D Attempt #4 resolution)

**Phase D Resolution Attempt:** Phase D Attempt #4 patched `scripts/c_reference_utils.py` to honour NB_C_BIN precedence (env → golden_suite_generator → root fallback); targeted rerun passed with ~3.9s runtime.

**Phase L Failure Mode:** Test fails during full-suite execution despite infrastructure guard validation at collection time.

**Root Cause Hypothesis:** `session_infrastructure_gate` validates C binary path at repo root during pytest collection, but tests execute from `/tmp/pytest-*` temporary directory due to pytest tmpdir mechanics. Relative path resolution breaks when CWD != repo root.

**Evidence:**
- Phase D targeted test: `NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_026.py::...` → PASSED
- Phase L full-suite: Same test → FAILED
- Phase L Attempt #20 notes: "F4 golden asset failures indicate CWD validation gap—infrastructure guard validated assets at repo root but tests ran from `/tmp` causing relative path mismatches"

**Remediation Path:**
1. Add CWD validation to `session_infrastructure_gate` (verify pytest running from repo root or tests using absolute paths)
2. Convert all infrastructure paths (C binary, golden assets) to absolute paths during collection
3. Update `scripts/c_reference_utils.py` to use `Path.resolve()` for all path operations
4. Add pytest fixture to print CWD at collection vs execution time for diagnostic logging

**Blocker:** Gap 1 (CWD validation) blocks F1 (CREF) and F4 (CLI) clusters.

---

### CLUSTER-PERF-001: Memory Bandwidth Utilization (Performance, HIGH)

**Phase L Status:** ❌ FAILED (REAPPEARED after Phase D Attempt #9 isolated validation)

**Phase D Isolated Result:** Test PASSED in 3.15s wall-clock time with 337% CPU, 1.3 GB peak RSS, zero page faults.

**Phase L Full-Suite Result:** Test FAILED (tolerance breach or transient performance degradation).

**Root Cause Hypothesis:** Full-suite execution introduces memory pressure, cache contention, or concurrent test interference that isolated execution does not reproduce. Test may be sensitive to system load state or memory allocator behavior after sustained 27-minute run.

**Evidence:**
- Phase D Attempt #9: "Test validated as passing in isolated execution—Phase B triage flag was transient (likely due to concurrent test execution or different pytest collection order during full-suite run)"
- Phase L Attempt #20: F2 performance threshold flagged; identical failure mode to Phase G

**Remediation Path:**
1. Review test tolerance thresholds (current bandwidth requirement may be too strict for full-suite context)
2. Add memory allocator warmup phase to test setup (pre-allocate tensors to stabilize allocator state)
3. Consider moving test to isolated chunk before full-suite to avoid memory pressure effects
4. Profile full-suite execution at test position to capture concurrent memory state

**Priority:** P2 (HIGH) — feeds into [PERF-PYTORCH-004] kernel fusion work; defer until tolerance policy clarified.

---

### CLUSTER-TOOLS-001: nb-compare Script Integration (Infrastructure, HIGH)

**Phase L Status:** ❌ FAILED (REAPPEARED after Phase D Attempt #7 verification)

**Phase D Resolution Attempt:** Phase D Attempt #7 verified nb-compare installed at `/home/ollie/miniconda3/bin/nb-compare` via `pip install -e .`; test passed in isolated execution (~10s runtime, exit code 0).

**Phase L Failure Mode:** Test fails during full-suite execution despite console script availability.

**Root Cause Hypothesis:** Test invokes nb-compare via incorrect path (not using `which nb-compare` or `sys.executable -m scripts.nb_compare`), or editable install becomes stale during long full-suite run, or PATH pollution from concurrent tests.

**Evidence:**
- Phase D Attempt #7: "Console script configured in `pyproject.toml:39` as `nb-compare = "scripts.nb_compare:main"`. The reported Phase B failure was transient or already addressed by editable install."
- Phase L Attempt #20: F3 tooling path resolution flagged; identical failure mode to Phase G

**Remediation Path:**
1. Update test to use `shutil.which('nb-compare')` or `sys.executable + ' -m scripts.nb_compare'` instead of bare `nb-compare` command
2. Add pytest fixture to verify editable install freshness at test execution time (check `pip show nanobrag-torch`)
3. Add PATH diagnostic logging to test setup (print `echo $PATH` and `which nb-compare` before test execution)
4. Consider adding `session_infrastructure_gate` check for console script availability (not just C binary)

**Priority:** P1 (HIGH) — blocks tooling validation; may be quick fix with PATH handling improvement.

---

### CLUSTER-CLI-001: Golden Asset Path Resolution (Infrastructure, CRITICAL)

**Phase L Status:** ❌ FAILED (2 tests; REAPPEARED after Phase D Attempt #6 verification)

**Phase D Resolution Attempt:** Phase D Attempt #6 verified golden assets present at repo root (`pix0_expected.json`, `scaled.hkl`) with SHA256 checksums; targeted tests passed in isolated execution (3 passed / 0 failed in 2.71s).

**Phase L Failure Mode:** Both tests fail during full-suite execution despite assets existing at repo root.

**Root Cause Hypothesis:** IDENTICAL to CLUSTER-CREF-001 — `session_infrastructure_gate` validates golden asset paths at repo root during collection, but tests execute from `/tmp/pytest-*` temporary directory. Relative path resolution breaks when CWD != repo root.

**Evidence:**
- Phase D Attempt #6: "Assets already existed from CLI-FLAGS-003 Phase H/L work (October 6, 2025); Phase B/C triage flag was transient."
- Phase L Attempt #20: "F4 golden asset failures indicate CWD validation gap—infrastructure guard validated assets at repo root but tests ran from `/tmp` causing relative path mismatches"
- Phase L Attempt #20 Recommendations: "(1) Add CWD validation to `session_infrastructure_gate` (Gap 1, blocks F4 resolution)"

**Remediation Path:**
1. **SHARED WITH CLUSTER-CREF-001:** Add CWD validation to `session_infrastructure_gate`
2. Convert all golden asset paths to absolute paths in test fixtures (use `Path(__file__).parent.parent / 'reports/...'` pattern)
3. Add pytest fixture to expose repo root as `repo_root` fixture for tests to use
4. Update test assertions to log absolute paths when failures occur (diagnostic aid)

**Blocker:** Gap 1 (CWD validation) blocks F4 (CLI golden assets) resolution. **SAME FIX AS CLUSTER-CREF-001.**

**Priority:** P1 (CRITICAL) — blocks CLI validation; shares remediation with CREF cluster.

---

### CLUSTER-GRAD-001: Gradient Stability Timeout (Environmental, CRITICAL)

**Phase L Status:** ❌ FAILED (REAPPEARED despite Phase D/F/I isolated validations)

**Isolated Test Results:**
- Phase D Attempt #8: 844.94s (6.6% below 905s tolerance)
- Phase F Attempt #14: 844.15s (6.7% below 905s tolerance)
- Phase I Attempt #17: 846.13s (6.5% below 905s tolerance)

**Phase L Full-Suite Result:** Timeout >905s (breach occurred during full-suite execution)

**Root Cause Hypothesis:** Environmental variance during sustained 27-minute full-suite load:
1. **Thermal throttling:** CPU frequency reduction after prolonged high load
2. **Memory pressure:** Cache eviction or page swapping after 27 minutes of tensor operations
3. **Test collection order:** Gradient test may run later in suite when system resources depleted
4. **Pytest fixture overhead:** Full-suite fixture setup/teardown adds cumulative latency

**Evidence:**
- Phase I Attempt #17 Conclusion: "Retain current 905s timeout per `arch.md §15` and `docs/development/testing_strategy.md §4.1`. No timeout increase needed (6.5% margin accommodates system variance)."
- Phase L Attempt #20: "F5 gradient timeout breached >905s despite Phase D/F/I isolated validations showing 844-846s runtimes, indicating environmental variance (thermal throttling, memory pressure) during sustained 27-minute full-suite load"
- Phase G Attempt #15 (identical baseline): Same F5 failure observed; isolated validations also passed

**Key Insight from Phase G/L Comparison:** "Isolated test execution does NOT predict full-suite behavior. Infrastructure and environmental validation must occur in full-suite context to be considered truly resolved."

**Remediation Policy Decision Required:**

| Option | Pros | Cons | Recommendation |
| --- | --- | --- | --- |
| **Accept Transient** | No code changes; acknowledge environmental limits | Test remains unstable; may fail unpredictably | ❌ NOT RECOMMENDED (blocks CI/CD reliability) |
| **Raise Tolerance to 1200s** | Accommodates worst-case full-suite variance | Hides potential performance regressions | ⚠️ ACCEPTABLE if documented with rationale |
| **Isolate to Pre-Suite Chunk** | Runs test before thermal/memory pressure builds | Adds complexity to test harness; requires chunked execution | ✅ RECOMMENDED (best balance) |
| **Implement Chunked Execution** | Cool-down periods between chunks reduce thermal issues | Increased total runtime; CI complexity | ⚠️ OVER-ENGINEERED for single test |

**Recommendation:** **Isolate test to dedicated pre-suite chunk** with documentation noting environmental sensitivity.

**Implementation Path:**
1. Create `tests/test_gradients_slow.py` containing only `test_property_gradient_stability`
2. Update CI/test harness to run `test_gradients_slow.py` as isolated chunk before full suite
3. Document environmental sensitivity in test docstring and testing_strategy.md
4. Add artifact capture for isolated chunk (runtime, CPU temp, memory usage)
5. Keep 905s tolerance unchanged (Phase I validation confirms appropriate ceiling)

**Priority:** P1 (CRITICAL) — blocks test suite stability; policy decision required before remediation.

---

### CLUSTER-VEC-001: Tricubic Vectorization Dtype Mismatch (Implementation, HIGH)

**Phase L Status:** ❌ FAILED (2 tests; REAPPEARED after Phase D Attempt #10 validation)

**Phase D Isolated Result:** Both tests PASSED on CPU (1.93s) and GPU (2.06s) with correct dtype coercion (float64 inputs → float32 outputs via `crystal.dtype`).

**Phase L Full-Suite Result:** Both tests FAILED with dtype mismatch error.

**Root Cause Hypothesis:** Full-suite execution introduces dtype state pollution or fixture ordering dependency:
1. **Global dtype state:** Preceding tests call `torch.set_default_dtype()` affecting subsequent tests
2. **Fixture scope issue:** Crystal fixture may inherit dtype from previous test's configuration
3. **Test collection order:** Vectorization tests may run after tests that modify global torch state
4. **Cache state:** Detector/crystal caches may retain dtype from previous test invocations

**Evidence:**
- Phase D Attempt #10: "Dtype snapshot confirmed correct coercion behavior—float64 inputs produce float32 outputs via `crystal.dtype` (expected per device/dtype neutrality guidelines). No float/double mismatch detected."
- Phase L Attempt #20: "F6 dtype mismatch flagged; identical failure mode to Phase G"
- Phase D Attempt #10 Verdict: "Phase B failure appears to have been transient (test collection order or environmental state)"

**Remediation Path:**
1. Add explicit `torch.set_default_dtype(torch.float32)` to test setup/teardown
2. Investigate fixture scope (module vs function) for Crystal/Detector objects
3. Add `crystal.invalidate_cache()` + `detector.invalidate_cache()` to test setup
4. Profile test collection order effects (run vectorization tests first vs last)
5. Add dtype assertion to test preamble (`assert torch.get_default_dtype() == torch.float32`)

**Implementation Priority:**
1. **Quick fix:** Add dtype reset to test setup (10-minute fix)
2. **Root cause:** Profile fixture scope and cache state (1-hour investigation)
3. **Systemic fix:** Add pytest hook to reset torch state between tests (architecture change)

**Priority:** P2 (HIGH) — feeds into [VECTOR-TRICUBIC-002] plan; likely quick fix with dtype reset.

---

## Regression Analysis

### New Failures Since Phase G
**Count:** 0
**Verdict:** ✅ NO NEW REGRESSIONS

### Cleared Failures Since Phase G
**Count:** 0
**Verdict:** ❌ NO PROGRESS

### Infrastructure Fixture Effectiveness
**`session_infrastructure_gate`:** ✅ EXECUTED (C binary + golden assets validated at collection)
**`gradient_policy_guard`:** ✅ EXECUTED (NANOBRAGG_DISABLE_COMPILE enforced)
**Runtime Overhead:** 0.28% (+4.6s runtime delta within measurement noise)
**New Failures Introduced:** 0
**Failures Cleared:** 0

**Critical Gap Identified:** CWD validation missing (Gap 1)
- Infrastructure guard validates paths at repo root during collection
- Tests execute from `/tmp/pytest-*` breaking relative paths
- Blocks 3 failures (CREF-001: 1 test, CLI-001: 2 tests)

## Cluster Prioritization for Remediation

### Immediate (P1, CRITICAL — blocks test suite stability)
1. **Gap 1: CWD Validation** → Unblocks CLUSTER-CREF-001 (1 test) + CLUSTER-CLI-001 (2 tests)
   - Estimated Effort: 1 hour (add CWD check + convert paths to absolute)
   - Impact: -3 failures (37.5% reduction)

2. **CLUSTER-GRAD-001: Gradient Timeout Policy** → Requires stakeholder decision (accept transient vs isolate vs raise tolerance)
   - Estimated Effort: 2 hours (implement pre-suite chunk) OR 5 minutes (raise tolerance to 1200s)
   - Impact: -1 failure (12.5% reduction) + CI/CD stability

### High Priority (P1-P2 — affects tooling/implementation quality)
3. **CLUSTER-TOOLS-001: nb-compare Path** → Quick fix (PATH handling improvement)
   - Estimated Effort: 30 minutes (update test to use `shutil.which()`)
   - Impact: -1 failure (12.5% reduction)

4. **CLUSTER-VEC-001: Dtype Reset** → Quick fix (add dtype reset to test setup)
   - Estimated Effort: 30 minutes (add dtype reset + cache invalidation)
   - Impact: -2 failures (25% reduction)

### Deferred (P2 — investigation required)
5. **CLUSTER-PERF-001: Memory Bandwidth** → Feeds into [PERF-PYTORCH-004]; requires profiling + tolerance policy
   - Estimated Effort: 4 hours (profiling + tolerance analysis)
   - Impact: -1 failure (12.5% reduction)

### Total Potential Impact (P1 + P2)
- **Immediate fixes:** -6 failures (75% reduction)
- **Deferred fix:** -1 failure (12.5% reduction)
- **Remaining after all fixes:** 1 failure (PERF-001 pending policy decision)

## Phase M Exit Criteria Check
- ✅ M1: Failures parsed into `analysis/failures.json` (8 tests extracted)
- ✅ M2: Clusters mapped with Phase G delta analysis (COMPLETE — this document)
- ⏳ M3: Remediation tracker refresh (NEXT ACTION)
- ⏳ M4: Next-step brief publication (NEXT ACTION)

## Cross-References
- **Phase L Summary:** reports/2026-01-test-suite-refresh/phase_l/20251015T190350Z/analysis/summary.md
- **Phase G Summary:** reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/analysis/summary.md
- **Phase C Triage:** reports/2026-01-test-suite-refresh/phase_c/20251015T113531Z/triage_summary.md
- **Phase D Cluster Briefs:** reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_*/
- **Remediation Tracker (Baseline):** reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md
- **Fix Plan Ledger:** docs/fix_plan.md §[TEST-SUITE-TRIAGE-002]
- **Testing Strategy:** docs/development/testing_strategy.md §§1.4-2.7

---

**Cluster Mapping Status:** Phase M2 COMPLETE — ready for tracker refresh (M3)
