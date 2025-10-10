Summary: Execute Phase B full-suite pytest run and capture failure inventory for triage.
Mode: none
Focus: TEST-SUITE-TRIAGE-001 Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: `pytest tests/ -v --durations=25 --maxfail=0`
Artifacts: reports/2026-01-test-suite-triage/phase_b/<STAMP>/{logs/pytest_full.log,artifacts/pytest_full.xml,failures_raw.md,commands.txt,summary.md}
Do Now: [TEST-SUITE-TRIAGE-001] Phase B — run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=artifacts/pytest_full.xml | tee logs/pytest_full.log` from a fresh `reports/2026-01-test-suite-triage/phase_b/<STAMP>/` workspace, then draft `failures_raw.md` with module::test and error excerpts.
If Blocked: Capture whatever portion completed (partial log, junit if emitted), note exit code + blocker in `failures_raw.md`, update Attempt history, and stop before retrying.
Priorities & Rationale:
- docs/fix_plan.md:22-35 — Critical ledger item freezing other work until full-suite evidence exists.
- plans/active/test-suite-triage.md:27-37 — Phase B checklist defining required artifacts and logging steps.
- docs/development/testing_strategy.md:18-33 — Mandates explicit Do Now command and guards device/dtype discipline during long runs.
- docs/development/pytorch_runtime_checklist.md:12-27 — Reinforces env guardrails (KMP env, device neutrality) while tests execute.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `BASE=reports/2026-01-test-suite-triage/phase_b/$STAMP`.
- `mkdir -p "$BASE"/logs "$BASE"/artifacts` and record commands in `$BASE/commands.txt` as you run them.
- From repo root, run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml="$BASE"/artifacts/pytest_full.xml | tee "$BASE"/logs/pytest_full.log`; capture wall-clock runtime in `summary.md`.
- Parse the log (grep for `= FAILURES =` / `FAILED ` footer) to build `$BASE/failures_raw.md` with one entry per failing node, including top traceback snippet and markers/xfail counts.
- Note exit status, runtime, collected/failed totals, and env (Python, torch versions) in `$BASE/summary.md`; reuse Phase A env snapshot but mention if anything changed.
- Update Attempt history for `[TEST-SUITE-TRIAGE-001]` in docs/fix_plan.md with the new `$STAMP`, runtime, fail count, and artifact list.
Pitfalls To Avoid:
- Do not reuse the Phase A directory; create a new timestamp to keep artifacts immutable.
- Ensure `KMP_DUPLICATE_LIB_OK` is set on the pytest command; missing it risks MKL crashes mid-run.
- Don’t split the suite unless runtime constraints force it—document before deviating from canonical command.
- Leave code untouched; this loop is evidence collection only.
- Avoid truncating `pytest_full.log`; keep the full stream even if very large.
- Record skipped/xfail counts explicitly so Phase C classification has baseline data.
- Preserve Protected Assets (`loop.sh`, `input.md`, `docs/index.md`) and avoid cleanup passes.
Pointers:
- docs/fix_plan.md:22-35 — Active ledger entry and updated Next Actions.
- plans/active/test-suite-triage.md:27-37 — Phase B tasks and exit criteria.
- docs/development/testing_strategy.md:18-33 — Execution discipline for suite runs.
- docs/development/pytorch_runtime_checklist.md:12-27 — Runtime guardrails to cite in summary.
Next Up: Phase C triage worksheet (`triage_summary.md`) once Phase B bundle is archived and logged.
