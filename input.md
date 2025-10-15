Summary: Execute the guarded Phase E full-suite rerun and capture a complete failure/pass snapshot.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-002 (Next Action 12 – Phase E rerun execution)
Branch: feature/spec-based-2
Mapped tests: pytest -vv tests/
Artifacts: reports/2026-01-test-suite-refresh/phase_e/$STAMP/{logs/pytest_full.log,artifacts/{pytest.junit.xml,time.txt,exit_code.txt},env/{env.txt,torch_env.txt},analysis/summary.md}
Do Now: TEST-SUITE-TRIAGE-002#12 — (/usr/bin/time -v timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905 --durations=0" pytest -vv tests/ --junitxml=reports/2026-01-test-suite-refresh/phase_e/$STAMP/artifacts/pytest.junit.xml) 2>reports/2026-01-test-suite-refresh/phase_e/$STAMP/artifacts/time.txt | tee reports/2026-01-test-suite-refresh/phase_e/$STAMP/logs/pytest_full.log
If Blocked: Capture partial logs under reports/2026-01-test-suite-refresh/phase_e/$STAMP/, log the blocker in analysis/summary.md + docs/fix_plan.md Attempts History, and ping supervisor with exit code & failure mode.
Priorities & Rationale:
- docs/fix_plan.md:70 records Next Action 12 as the mandated full-suite execution.
- reports/2026-01-test-suite-refresh/phase_e/20251015T150723Z/phase_e_brief.md:18 defines the guarded command, env guards, and artifact expectations.
- docs/development/testing_strategy.md:18 enforces timeout/compile-guard policy for suite runs.
- plans/archive/test-suite-triage-rerun.md:24 outlines Phase B/E deliverables we must refresh.
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-VEC-001/20251015T143055Z/summary.md:7 confirms Phase D clusters are ready for rerun.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-refresh/phase_e/$STAMP/{logs,artifacts,env,analysis}.
- Record env guards: printenv > reports/2026-01-test-suite-refresh/phase_e/$STAMP/env/env.txt; python -m torch.utils.collect_env > reports/2026-01-test-suite-refresh/phase_e/$STAMP/env/torch_env.txt; df -h . > reports/2026-01-test-suite-refresh/phase_e/$STAMP/env/disk_usage.txt.
- Verify editable install (`pip show nanobrag-torch | grep Location`); confirm CUDA disabled via python -c "import torch; print(torch.cuda.is_available())" >> env/torch_env.txt.
- Run the Do Now command exactly once; after it finishes, echo $? > reports/2026-01-test-suite-refresh/phase_e/$STAMP/artifacts/exit_code.txt.
- Parse failures with grep "FAILED tests/" reports/2026-01-test-suite-refresh/phase_e/$STAMP/logs/pytest_full.log > reports/2026-01-test-suite-refresh/phase_e/$STAMP/analysis/failures.txt and draft analysis/summary.md with counts, runtime, Phase K deltas, and noting whether thresholds (pass rate ≥74%, failures ≤35) are met.
- Update docs/fix_plan.md TEST-SUITE-TRIAGE-002 Attempts History with STAMP, results, and next remediation steps before ending the loop.
Pitfalls To Avoid:
- Do not omit required env guards (CUDA_VISIBLE_DEVICES, KMP_DUPLICATE_LIB_OK, NANOBRAGG_DISABLE_COMPILE, PYTEST_ADDOPTS).
- Avoid re-running pytest; the guarded full-suite run may execute only once this loop.
- Ensure time.txt captures /usr/bin/time output; verify the file is non-empty before exit.
- Keep repository tidy: stage artifacts and docs updates, no stray tmp files.
- Abort immediately if timeout triggers; do not relaunch without supervisor approval.
- Maintain ASCII-only content in analysis summaries and filenames.
- Do not modify production code while triaging; evidence collection only.
- Respect protected assets called out in docs/index.md.
- Confirm ≥10 GB free disk space before the run to avoid partial logs.
- Ensure PYTEST_ADDOPTS is quoted exactly to preserve spaces.
Pointers:
- docs/fix_plan.md:70
- reports/2026-01-test-suite-refresh/phase_e/20251015T150723Z/phase_e_brief.md:18
- docs/development/testing_strategy.md:18
- plans/archive/test-suite-triage-rerun.md:24
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-VEC-001/20251015T143055Z/summary.md:7
Next Up: 1) If the run finishes early with manageable failures, begin drafting analysis/triage_summary.md per the brief to map failures → clusters.
