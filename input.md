Summary: Capture a fresh performance profile for the gradient stability test after the Phase E timeout.
Mode: Perf
Focus: TEST-SUITE-TRIAGE-002 (Next Action 13 — F5 gradient timeout regression)
Branch: feature/spec-based-2
Mapped tests: pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability
Artifacts: reports/2026-01-test-suite-refresh/phase_f/$STAMP/{env/{env.txt,torch_env.txt,disk_usage.txt},logs/pytest.log,artifacts/{pytest.junit.xml,time.txt,exit_code.txt},analysis/summary.md}
Do Now: TEST-SUITE-TRIAGE-002#13 — (export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-refresh/phase_f/$STAMP/{env,logs,artifacts,analysis}; printenv > reports/2026-01-test-suite-refresh/phase_f/$STAMP/env/env.txt; python -m torch.utils.collect_env > reports/2026-01-test-suite-refresh/phase_f/$STAMP/env/torch_env.txt; df -h . > reports/2026-01-test-suite-refresh/phase_f/$STAMP/env/disk_usage.txt; /usr/bin/time -v -o reports/2026-01-test-suite-refresh/phase_f/$STAMP/artifacts/time.txt timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=0 --timeout=1200 --durations=0" pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability --junitxml=reports/2026-01-test-suite-refresh/phase_f/$STAMP/artifacts/pytest.junit.xml | tee reports/2026-01-test-suite-refresh/phase_f/$STAMP/logs/pytest.log; echo $? > reports/2026-01-test-suite-refresh/phase_f/$STAMP/artifacts/exit_code.txt)
If Blocked: If the run still times out or aborts, keep all partial artifacts under the same STAMP, append the failure signature to analysis/summary.md, and log the blocker plus exit code in docs/fix_plan.md before stopping.
Priorities & Rationale:
- docs/fix_plan.md:72 mandates isolating the F5 regression with profiling and storing evidence under phase_f.
- reports/2026-01-test-suite-refresh/phase_e/20251015T152031Z/analysis/summary.md:60 documents the timeout breach we must reproduce and explain.
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-GRAD-001/20251015T134434Z/summary.md:32 records the 844.94s / 1294% CPU baseline we must compare against.
- docs/development/testing_strategy.md:526 reminds us the approved ceiling is 905s and frames the tolerance history we reference.
- docs/development/pytorch_runtime_checklist.md:41 reinforces the compile guard and device/dtype neutrality expectations for gradient tests.
How-To Map:
- Use bash -lc for the Do Now command so `timeout`, `time`, and tee work together.
- After the run, extract key metrics with `rg "User time|System time|Elapsed|Percent of CPU|Maximum resident set size" reports/2026-01-test-suite-refresh/phase_f/$STAMP/artifacts/time.txt >> reports/2026-01-test-suite-refresh/phase_f/$STAMP/analysis/time_metrics.txt` to simplify summary writing.
- Draft reports/2026-01-test-suite-refresh/phase_f/$STAMP/analysis/summary.md covering runtime, CPU %, RSS, comparison vs the Phase D baseline, and whether the 905s tolerance is satisfied.
- Update docs/fix_plan.md (same section) with Attempt #14, citing the new STAMP, runtime delta vs 844.94s, and CPU utilization comparison.
- If the test finishes well under 905s, note the margin; if it exceeds 905s despite 1200s timeout, capture the exact elapsed time from pytest output before the kill.
Pitfalls To Avoid:
- Do not rerun the test multiple times this loop; one profiled attempt only.
- Keep `timeout 1200` and the extended pytest timeout; otherwise we will relive the 905s kill.
- Ensure `NANOBRAGG_DISABLE_COMPILE=1` is set; missing it invalidates gradient metrics.
- Do not relocate or overwrite Phase E artifacts; this run belongs in `phase_f/`.
- Avoid editing production code or test fixtures during this diagnostic pass.
- Verify the `time.txt` file is non-empty before exiting; rerun command only if it failed to emit data.
- Maintain ASCII-only content in summary.md and doc edits.
- Respect the single-loop policy: update docs/fix_plan.md in the same run you gather evidence.
- Do not change PYTEST_ADDOPTS elsewhere in the environment; use the inline override only.
- Preserve the existing conda/python environment; do not upgrade packages mid-run.
Pointers:
- docs/fix_plan.md:68-75
- reports/2026-01-test-suite-refresh/phase_e/20251015T152031Z/analysis/summary.md:9-118
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-GRAD-001/20251015T134434Z/summary.md:10-58
- docs/development/testing_strategy.md:520-540
- docs/development/pytorch_runtime_checklist.md:35-55
Next Up: If the gradient test runtime is back under tolerance, proceed by refreshing CLUSTER-PERF-001 metrics to reconfirm bandwidth baselines.
