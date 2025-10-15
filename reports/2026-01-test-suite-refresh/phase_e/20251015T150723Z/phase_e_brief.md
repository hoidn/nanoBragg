# Phase E Full-Suite Rerun Brief

## Context
- Initiative: TEST-SUITE-TRIAGE-002 — Relaunch full `pytest tests/` execution to capture current test suite health
- Phase: Phase E (post-Phase D cluster validation)
- Purpose: Execute comprehensive test suite rerun with guarded environment to validate Phase D cluster resolutions and capture any new failures
- Prerequisites verified: Phase D cluster diagnostics complete (Attempts #4-#10); all six Phase B clusters (CREF, CLI, TOOLS, GRAD, PERF, VEC) validated with targeted reproductions

## Prerequisites (Environment Guards)

### Required Environment Variables
The following environment guards MUST be set before execution to ensure reproducible, timeout-protected execution:

```bash
export CUDA_VISIBLE_DEVICES=-1              # Force CPU-only execution (avoid CUDA non-determinism)
export KMP_DUPLICATE_LIB_OK=TRUE            # Prevent MKL library conflicts
export NANOBRAGG_DISABLE_COMPILE=1          # Disable torch.compile (required for gradcheck tests)
export PYTEST_ADDOPTS="--maxfail=200 --timeout=905 --durations=0"  # Enforce per-test timeout and capture slowest tests
```

### Verification Steps
Before executing the rerun command, verify:
1. Editable install active: `pip show nanobrag-torch | grep Editable` shows location
2. C binary available (if parallel tests required): `which ./golden_suite_generator/nanoBragg` or `./nanoBragg` exists
3. Disk space sufficient: `df -h .` shows >=10 GB available
4. Environment captured: `python -m torch.utils.collect_env > env.txt`

### Evidence to Capture Before Rerun
Document the following baseline state:
- Python version: `python --version`
- PyTorch version: `python -c "import torch; print(torch.__version__)"`
- CUDA availability: `python -c "import torch; print(torch.cuda.is_available())"`
- Test collection count: `pytest --collect-only -q tests/ | tail -1`
- Prior baseline reference: Phase D closure (Attempts #4-#10) with STAMP 20251015T113531Z

## Proposed Command (Guarded Execution)

### Primary Full-Suite Command
Execute the following command from the repository root to run the complete test suite with timeout protection:

```bash
# Create timestamped execution directory
export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p reports/2026-01-test-suite-refresh/phase_e/$STAMP/{logs,artifacts,env,analysis}

# Run guarded full-suite execution with timing instrumentation
/usr/bin/time -v timeout 3600 \
  env CUDA_VISIBLE_DEVICES=-1 \
      KMP_DUPLICATE_LIB_OK=TRUE \
      NANOBRAGG_DISABLE_COMPILE=1 \
      PYTEST_ADDOPTS="--maxfail=200 --timeout=905 --durations=0" \
  pytest -vv tests/ \
    --junitxml=reports/2026-01-test-suite-refresh/phase_e/$STAMP/artifacts/pytest.junit.xml \
  | tee reports/2026-01-test-suite-refresh/phase_e/$STAMP/logs/pytest_full.log

# Capture exit code
echo $? > reports/2026-01-test-suite-refresh/phase_e/$STAMP/artifacts/exit_code.txt
```

### Execution Parameters Rationale
- **Timeout 3600s (60 minutes):** Provides sufficient headroom above Phase R baseline (1841s runtime); Phase K runtime was 1841.28s (30m 41s)
- **--maxfail=200:** Prevents early termination but still bounds execution time if catastrophic failures occur
- **--timeout=905:** Per-test timeout matching Phase R gradient tolerance uplift; protects against individual test hangs
- **--durations=0:** Captures timing for all tests to identify performance regressions
- **CUDA_VISIBLE_DEVICES=-1:** Enforces CPU-only execution per determinism requirements (AT-PARALLEL-013/024 compliance)
- **NANOBRAGG_DISABLE_COMPILE=1:** Required for gradient tests to pass gradcheck validation

### Expected Runtime
- Phase K baseline: 1841.28s (30m 41s) for 687 tests
- Phase R baseline: Similar runtime (~1650-1850s range typical)
- Timeout guard: 3600s (60 minutes) provides 95% headroom

## Artifact Expectations

### Required Artifacts
The following artifacts MUST be captured and committed after execution:

1. **Execution Logs**
   - `logs/pytest_full.log` — Complete pytest output with `-vv` verbosity
   - `artifacts/pytest.junit.xml` — Machine-readable test results (for tooling/CI)
   - `artifacts/exit_code.txt` — Shell exit status (0 = success, non-zero = failures/errors)

2. **Timing & Resource Metrics**
   - `artifacts/time.txt` — `/usr/bin/time -v` output (wall clock, CPU%, memory peak RSS, page faults)
   - Extract from pytest log: slowest 10 tests via `--durations=0`

3. **Environment Snapshot**
   - `env/env.txt` — Full environment variables (`printenv`)
   - `env/torch_env.txt` — PyTorch environment details (`python -m torch.utils.collect_env`)
   - `env/disk_usage.txt` — Disk space before/after (`df -h .`)

4. **Analysis Outputs**
   - `analysis/summary.md` — Executive summary with pass/fail/skip counts, runtime, comparison to Phase K baseline
   - `analysis/triage_summary.md` — If failures occur: cluster classification, root cause analysis, remediation priorities
   - `analysis/commands.txt` — Exact commands executed (reproducibility requirement)

### Success Criteria (Full-Suite Pass)
If rerun succeeds (exit code 0):
- **Pass rate target:** >=74% (Phase K baseline: 74.5%, 512/687 passed)
- **Expected skips:** ~140-145 tests (consistent with Phase K: 143 skipped)
- **Expected xfails:** 1-2 tests (Phase K: 2 xfailed)
- **Runtime tolerance:** 1600-2000s (typical range; flag if <1500s or >2200s)

### Failure Criteria (New Regressions)
If failures occur (exit code non-zero):
- **Triage threshold:** <=35 failures (Phase K baseline: 31 failures; Phase B baseline: 8 failures)
- **Cluster revalidation:** Compare failing nodeids against Phase D cluster briefs (CREF, CLI, TOOLS, GRAD, PERF, VEC)
- **New regression detection:** Flag any nodeids NOT present in Phase B/K failure sets
- **Critical blockers:** Import errors, collection failures, infrastructure crashes require immediate escalation

## Follow-up Actions

### Who Runs the Rerun
- **Primary executor:** Ralph (engineer loop) under supervisor directive via input.md
- **Handoff requirements:** STAMP, reproduction command, and environment guard documented in input.md Do Now
- **Escalation path:** If execution times out or crashes, log blocker in docs/fix_plan.md Attempts History and notify supervisor

### What Evidence to Capture Once Executed

#### If Full-Suite Passes (Exit 0)
1. Commit all Phase E artifacts (logs, junit, timing, env, summary) under STAMP directory
2. Update docs/fix_plan.md TEST-SUITE-TRIAGE-002 Attempts History:
   - Log STAMP, runtime, pass/fail/skip counts
   - Compare to Phase K baseline (delta analysis: pass rate, failure count, runtime)
   - Mark Next Action 11 (Phase E rerun brief) as ✅ COMPLETE
   - Add Next Action 12: "Archive TEST-SUITE-TRIAGE-002 plan to plans/archive/ with closure preface"
3. Update galph_memory with Action State: [test_suite_healthy] or [test_suite_passing_with_notes]

#### If Failures Occur (Non-Zero Exit)
1. Commit all Phase E artifacts (include partial logs if timeout occurred)
2. Run failure clustering analysis:
   - Extract failure nodeids: `grep "FAILED tests/" logs/pytest_full.log > analysis/failures.txt`
   - Classify into clusters: new vs. known (cross-reference Phase D briefs)
   - Draft `analysis/triage_summary.md` with cluster table (Cluster ID | Tests | Classification | Notes)
3. Update docs/fix_plan.md TEST-SUITE-TRIAGE-002 Attempts History:
   - Log STAMP, failure count, cluster summary
   - Add Next Action 12: "Author Phase E cluster remediation briefs for [new clusters]"
   - Prioritize clusters by severity (P1: infrastructure blockers, P2: implementation bugs, P3: edge cases)
4. Update galph_memory with Action State: [test_suite_regression_detected] + cluster summary

### Timing Table Template (for summary.md)
```
| Phase | STAMP           | Runtime (s) | Passed | Failed | Skipped | Pass Rate |
|-------|-----------------|-------------|--------|--------|---------|-----------|
| K     | 20251011T072940Z| 1841.28     | 512    | 31     | 143     | 74.5%     |
| E     | [STAMP]         | [runtime]   | [N]    | [M]    | [S]     | [%]       |
```

## References

### Authoritative Commands & Guidance
- `docs/development/testing_strategy.md` §§1-2 — Environment guards, pytest commands, timeout policy
- `arch.md` §§2, 15 — Device/dtype neutrality, differentiability guardrails
- `docs/development/pytorch_runtime_checklist.md` — Preflight sanity requirements

### Prior Baseline Artifacts
- Phase K full-suite: `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/` (31 failures, 1841s runtime)
- Phase D cluster diagnostics: `reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/` (Attempts #4-#10)
- Phase R closure: `plans/archive/test-suite-triage.md` (43 passed / 9 skipped / 1 xfailed; 846.60s < 905s tolerance)

### Downstream Plan Integration
- If failures cluster around vectorization: escalate to [VECTOR-PARITY-001]
- If failures cluster around gradients: escalate to [GRADIENT-FLOW-001]
- If failures cluster around C reference: escalate to [TEST-GOLDEN-001]

## Notes
- This brief is a planning artifact; execution will occur in a future Ralph loop when supervisor schedules the rerun via input.md
- Phase D validated that infrastructure gaps (C binary resolution, console scripts, golden assets, gradient timeouts, memory bandwidth, dtype neutrality) are cleared
- Phase E rerun serves as the comprehensive health check before resuming feature work
- ASCII-only formatting per project conventions; no UTF-8 decorators beyond basic markdown
