Summary: Run the guarded full pytest suite to lock in Phase G results after clearing the Phase D/F cluster diagnostics.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-002 (Next Action 14 — Phase G rerun scheduling)
Branch: feature/spec-based-2
Mapped tests: pytest -vv tests/
Artifacts: reports/2026-01-test-suite-refresh/phase_g/$STAMP/{env/{env.txt,torch_env.txt,disk_usage.txt},logs/pytest_full.log,artifacts/{pytest.junit.xml,time.txt,exit_code.txt},analysis/summary.md}
Do Now: TEST-SUITE-TRIAGE-002#14 — (export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-refresh/phase_g/$STAMP/{env,logs,artifacts,analysis}; printenv > reports/2026-01-test-suite-refresh/phase_g/$STAMP/env/env.txt; python -m torch.utils.collect_env > reports/2026-01-test-suite-refresh/phase_g/$STAMP/env/torch_env.txt; df -h . > reports/2026-01-test-suite-refresh/phase_g/$STAMP/env/disk_usage.txt; /usr/bin/time -v -o reports/2026-01-test-suite-refresh/phase_g/$STAMP/artifacts/time.txt timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/ --junitxml=reports/2026-01-test-suite-refresh/phase_g/$STAMP/artifacts/pytest.junit.xml | tee reports/2026-01-test-suite-refresh/phase_g/$STAMP/logs/pytest_full.log; echo $? > reports/2026-01-test-suite-refresh/phase_g/$STAMP/artifacts/exit_code.txt)
If Blocked: If the suite aborts (timeout/non-zero exit), keep all artifacts under the same $STAMP, add the failure signature plus collected counts to analysis/summary.md, and note the blocker + exit status in docs/fix_plan.md before stopping.
Priorities & Rationale:
- docs/fix_plan.md:68-87 now calls for Phase G rerun (Next Action 14) after resolving F5 diagnostics.
- reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/summary.md documents the baseline we must supersede.
- reports/2026-01-test-suite-refresh/phase_f/20251015T160436Z/analysis/summary.md shows F5 resolved, so a fresh full-suite measurement is required.
- docs/development/testing_strategy.md:40-110 provides the authoritative full-suite command and guardrails.
- plans/archive/test-suite-triage-rerun.md: Phase B section defines artifact expectations we should mirror for Phase G.
How-To Map:
- Run the Do Now command inside bash so `timeout`, `/usr/bin/time`, and tee cooperate; confirm `/usr/bin/time` output exists before exiting.
- After pytest finishes, append pass/fail/skip/xpass counts from pytest output into analysis/summary.md along with any failure clusters.
- Use `rg -n "FAILED" reports/2026-01-test-suite-refresh/phase_g/$STAMP/logs/pytest_full.log` to extract nodeids for any remaining failures; include them in summary and docs/fix_plan.md.
- Update docs/fix_plan.md under TEST-SUITE-TRIAGE-002 with Attempt #15, citing the new STAMP and outcome.
- If the suite finishes clean (0 failures), note the success and recommend moving the initiative to closure; otherwise classify the failures by cluster before stopping.
Pitfalls To Avoid:
- Do not rerun the suite multiple times this loop; a single guarded attempt only.
- Keep `timeout 3600` and `PYTEST_ADDOPTS="--maxfail=200 --timeout=905"`; changing them breaks comparability.
- Ensure `NANOBRAGG_DISABLE_COMPILE=1` is set or gradcheck timings will be invalid.
- Do not overwrite existing Phase B/F artifacts; all new files must live under phase_g/$STAMP.
- Verify `/usr/bin/time` output is not truncated; rerun only if the file is empty.
- Avoid editing production code or tests while running this diagnostic loop.
- Maintain ASCII-only content in summary.md and docs/fix_plan.md updates.
- Capture env snapshots before running pytest; missing env.txt is considered an incomplete attempt.
- Keep `CUDA_VISIBLE_DEVICES=-1`; running on GPU breaks parity with the existing baseline.
Pointers:
- docs/fix_plan.md:68-87, 12-14 entries
- reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/summary.md
- reports/2026-01-test-suite-refresh/phase_f/20251015T160436Z/analysis/summary.md
- docs/development/testing_strategy.md:40-110
- plans/archive/test-suite-triage-rerun.md: Phase B artifact checklist
Next Up: If the suite passes cleanly, prepare the Phase G summary plus ledger update so we can decide on initiative closure next loop.
