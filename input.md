Summary: Measure the slow-gradient runtime under Phase I so we know whether the 905 s ceiling still holds during an isolated run.
Mode: Perf
Focus: TEST-SUITE-TRIAGE-002 (Next Action 19 — Phase I gradient timeout mitigation study)
Branch: feature/spec-based-2
Mapped tests: tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability
Artifacts: reports/2026-01-test-suite-refresh/phase_i/$STAMP/{env/{env.txt,torch_env.txt,disk_usage.txt,system_load.txt},logs/pytest.log,artifacts/{time.txt,pytest.junit.xml,exit_code.txt},analysis/{gradient_cpu_time.txt,gradient_gpu_time.txt?,timeout_decision.md}}
Do Now: TEST-SUITE-TRIAGE-002#19 — (export STAMP=$(date -u +%Y%m%dT%H%M%SZ); BASE=reports/2026-01-test-suite-refresh/phase_i/$STAMP; mkdir -p $BASE/{env,logs,artifacts,analysis}; printenv | sort > $BASE/env/env.txt; python -m torch.utils.collect_env > $BASE/env/torch_env.txt; df -h . > $BASE/env/disk_usage.txt; { lscpu; echo; cpupower frequency-info; echo; sensors 2>&1 || echo "sensors command unavailable"; } > $BASE/env/system_load.txt; /usr/bin/time -v -o $BASE/artifacts/time.txt timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=0 --timeout=1200 --durations=0" pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability --junitxml=$BASE/artifacts/pytest.junit.xml | tee $BASE/logs/pytest.log; status=${PIPESTATUS[0]}; echo $status > $BASE/artifacts/exit_code.txt; grep -E "User time|System time|Percent of CPU|Elapsed|Maximum resident set size" $BASE/artifacts/time.txt > $BASE/analysis/gradient_cpu_time.txt )
If Blocked: If the timeout fires or pytest exits non-zero, stop after capturing the artifacts, note the failure mode at the top of $BASE/analysis/gradient_cpu_time.txt, and record the blocking signature in docs/fix_plan.md Attempts History before rerunning anything.
Priorities & Rationale:
- docs/fix_plan.md:104-108 keeps Next Action 19 open; we need fresh timing evidence before revising the 905 s threshold.
- plans/active/test-suite-triage-phase-h.md:48-94 defines the Phase I deliverables (time command, system load snapshot, timeout memo).
- reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/analysis/summary.md:150-214 shows the timeout only appears during the full suite, so we must compare under isolated load.
- reports/2026-01-test-suite-refresh/phase_f/20251015T160436Z/analysis/summary.md confirms the last isolated run passed in 844.15 s; we need to verify nothing has drifted since.
How-To Map:
- After Do Now, append a short narrative (headlines, runtime delta vs Phase F, any CPU throttling notes) to $BASE/analysis/timeout_decision.md; include references to time.txt and system_load.txt.
- If CUDA smoke is available and time permits, rerun with CUDA_VISIBLE_DEVICES=0 and write metrics to $BASE/analysis/gradient_gpu_time.txt using the same grep pattern.
- Log Attempt #?? with STAMP, key metrics, and next-step recommendation under docs/fix_plan.md `[TEST-SUITE-TRIAGE-002]` once the memo is drafted.
- Update plans/active/test-suite-triage-phase-h.md Phase I checklist states (I1-I4) to reflect progress.
Pitfalls To Avoid:
- Do not run the full pytest suite; this loop only profiles the single gradient test.
- Keep NANOBRAGG_DISABLE_COMPILE=1 set before pytest imports torch.
- Do not trim the /usr/bin/time output; store the full file for later analysis.
- Respect the STAMP hierarchy; never overwrite an existing STAMP directory.
- Stay on CPU for the primary run (CUDA_VISIBLE_DEVICES=-1) so results line up with Phase F; note any GPU rerun separately.
- Avoid sensors output failures breaking the script—capture stderr and move on.
Pointers:
- docs/fix_plan.md:104-108
- plans/active/test-suite-triage-phase-h.md:48-94
- reports/2026-01-test-suite-refresh/phase_f/20251015T160436Z/analysis/summary.md:1-120
- reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/analysis/summary.md:150-214
Next Up: Draft the timeout decision memo (Phase I exit criterion) once the new measurement is captured.
