Summary: Execute Phase M2 full-suite validation and queue tracker updates for TEST-SUITE-TRIAGE-001.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-001 / Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: pytest tests/ -v --durations=25 --maxfail=0
Artifacts: reports/2026-01-test-suite-triage/phase_m/$STAMP/
Do Now: [TEST-SUITE-TRIAGE-001] Full-suite validation sweep — env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_m/$STAMP/artifacts/pytest_full.xml (capture stdout to logs/pytest_full.log)
If Blocked: Run pytest --collect-only -q and log output under reports/2026-01-test-suite-triage/phase_m/$STAMP/preflight/collect_only.log, then document the blocker in docs/fix_plan.md Attempts.
Priorities & Rationale:
- plans/active/test-suite-triage.md:254 — Phase M2 is the remaining gate before sprint handoff; evidence bundle required now that detector defaults validated.
- docs/fix_plan.md:38 — Next Actions call for Phase M2 execution and tracker refresh using Attempt #40 evidence.
- docs/development/testing_strategy.md:30 — Handoff rules demand explicit pytest commands and guardrail adherence for suite runs.
- docs/development/testing_strategy.md:373 — Environment checklist mandates KMP_DUPLICATE_LIB_OK=TRUE for PyTorch execution.
- reports/2026-01-test-suite-triage/phase_m3/20251011T190855Z/mosflm_fix/summary.md:1 — Confirms Phase M1 prerequisites satisfied (MOSFLM verification) preceding this run.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
- mkdir -p reports/2026-01-test-suite-triage/phase_m/$STAMP/{artifacts,logs}
- env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_m/$STAMP/artifacts/pytest_full.xml | tee reports/2026-01-test-suite-triage/phase_m/$STAMP/logs/pytest_full.log
- Summarise totals in reports/2026-01-test-suite-triage/phase_m/$STAMP/summary.md (pass/fail/skip counts, runtime, notable slow tests); reuse template from phase_m0.
- Update docs/fix_plan.md Attempts and reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md with new counts after the run.
Pitfalls To Avoid:
- Do not drop KMP_DUPLICATE_LIB_OK=TRUE; required per runtime checklist.
- Keep CUDA_VISIBLE_DEVICES=-1 to lock execution to CPU for parity.
- Avoid using legacy chunk scripts; single command with --maxfail=0 is required unless it times out.
- Do not edit production code or tests in this loop; evidence-only per supervisor directive.
- Preserve existing Attempt numbering in docs/fix_plan.md (append Attempt #41 next).
- Ensure artifacts directories use the same STAMP for all files.
- Capture --durations=25 output; needed for future performance comparisons.
- Leave existing phase_m0 artifacts untouched; create new STAMP folder.
- If pytest fails unexpectedly, do not rerun immediately—record failure details first.
- Respect Protected Assets listed in docs/index.md (input.md already handled).
Pointers:
- plans/active/test-suite-triage.md:254
- docs/fix_plan.md:38
- docs/development/testing_strategy.md:30
- docs/development/testing_strategy.md:373
- reports/2026-01-test-suite-triage/phase_m3/20251011T190855Z/mosflm_fix/summary.md:1
Next Up: If time remains, draft Phase M3c mixed-units hypotheses per docs/fix_plan.md Next Actions step 2.
