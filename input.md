Summary: Complete the Phase B full-suite pytest rerun with extended timeout and capture fresh artifacts.
Mode: none
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: pytest tests/ -v --durations=25 --maxfail=0
Artifacts: reports/2026-01-test-suite-triage/phase_b/<STAMP>/{commands.txt,logs/pytest_full.log,artifacts/pytest_full.xml,failures_raw.md,summary.md}
Do Now: [TEST-SUITE-TRIAGE-001] — Run Phase B rerun via KMP_DUPLICATE_LIB_OK=TRUE timeout 3600 pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_b/<STAMP>/artifacts/pytest_full.xml
If Blocked: Record partial progress in reports/2026-01-test-suite-triage/phase_b/<STAMP>/summary.md (note stop reason) and flag the issue in docs/fix_plan.md Attempts History before exiting.
Priorities & Rationale:
- docs/fix_plan.md:29-45 elevates the rerun as Next Action #1 blocking all other initiatives.
- plans/active/test-suite-triage.md:27-37 keeps Phase B2 open until a full-duration run completes and artifacts are archived.
- reports/2026-01-test-suite-triage/phase_b/20251010T132406Z/failures_raw.md:1-88 shows the current coverage gap (172 unexecuted tests) we must eliminate.
- docs/development/testing_strategy.md:12-65 mandates authoritative suite coverage before shifting to targeted remediation.
How-To Map:
1) export STAMP=$(date -u +%Y%m%dT%H%M%SZ) and mkdir -p reports/2026-01-test-suite-triage/phase_b/$STAMP/{logs,artifacts}.
2) Record the exact command in reports/2026-01-test-suite-triage/phase_b/$STAMP/commands.txt before execution (include env vars).
3) Run KMP_DUPLICATE_LIB_OK=TRUE timeout 3600 pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_b/$STAMP/artifacts/pytest_full.xml | tee reports/2026-01-test-suite-triage/phase_b/$STAMP/logs/pytest_full.log.
4) After completion, capture failures with python scripts/parse_failures.py reports/2026-01-test-suite-triage/phase_b/$STAMP/logs/pytest_full.log > reports/2026-01-test-suite-triage/phase_b/$STAMP/failures_raw.md (or note "full pass" if empty) and summarise runtime, pass/fail counts, and coverage notes in summary.md.
5) Update docs/fix_plan.md Attempts History with Attempt #5 details (runtime, counts, exit status) referencing the new STAMP directory.
Pitfalls To Avoid:
- Do not reuse the 20251010T132406Z directory; every rerun needs a fresh STAMP.
- Keep KMP_DUPLICATE_LIB_OK=TRUE on the command; missing it can crash torch imports.
- Do not shorten the timeout below 3600 seconds without supervisor approval.
- Avoid editing production code or tests during this loop; this is an evidence run only.
- Ensure tee writes the complete pytest output; no truncated logs or redirected stderr omissions.
- Capture junit XML even on failure so we can parse partial results later.
Pointers:
- docs/fix_plan.md:29-45
- plans/active/test-suite-triage.md:27-37
- docs/development/testing_strategy.md:12-65
- reports/2026-01-test-suite-triage/phase_b/20251010T132406Z/failures_raw.md:1-92
Next Up: If time remains, draft a bullets-only outline for Phase D handoff in plans/active/test-suite-triage.md focusing on prioritising determinism vs CLI fixes.
