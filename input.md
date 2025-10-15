Summary: Run the guarded Phase B full-suite pytest to capture fresh failure data for the triage relaunch.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-002] Full pytest rerun and triage refresh
Branch: feature/spec-based-2
Mapped tests: pytest -vv tests/
Artifacts: reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/
Do Now: [TEST-SUITE-TRIAGE-002] Phase B — execute `timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/ --junitxml=pytest.junit.xml | tee reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/pytest.log`
If Blocked: Stop the run, preserve partial `pytest.log`, capture stderr/stdout in `phase_b/20251015T113531Z/blocked_summary.md`, and note exit code for supervisor review.
Priorities & Rationale:
- docs/fix_plan.md:39-53 — Next Action 2 mandates the guarded `pytest tests/` execution and reuse of STAMP 20251015T113531Z.
- plans/active/test-suite-triage-rerun.md:30-40 — Phase B tasks (B1–B4) define folder prep, command shape, junit/timing capture, and summary expectations.
- reports/2026-01-test-suite-refresh/phase_a/20251015T113531Z/summary.md:65-84 — Preflight recommendations call for the exact timeout/env guard, junit option, and artifact checklist.
- docs/development/testing_strategy.md:32-34 — Supervisor handoffs must include precise pytest commands and cadence (one full-suite run per loop).
- docs/development/pytorch_runtime_checklist.md:41 — Slow gradient tests may legitimately run up to 905 s, so the timeout guard is non-negotiable.
How-To Map:
- Export `STAMP=20251015T113531Z`; run `mkdir -p reports/2026-01-test-suite-refresh/phase_b/$STAMP` and `cp reports/2026-01-test-suite-refresh/phase_a/$STAMP/env.txt reports/2026-01-test-suite-refresh/phase_b/$STAMP/`.
- Append the exact command to `reports/2026-01-test-suite-refresh/phase_b/$STAMP/commands.txt` before execution (use `printf` so the env vars are captured verbatim).
- Execute the Do Now command from repo root; the `tee` target must be `reports/2026-01-test-suite-refresh/phase_b/$STAMP/pytest.log`.
- After the run, write `$?` to `reports/2026-01-test-suite-refresh/phase_b/$STAMP/run_exit_code.txt` and move `pytest.junit.xml` and `pytest.log` into the same folder (rename junit file if the test writes it to CWD).
- Capture timing either via `/usr/bin/time -v` (redirect to `time.txt`) or, if unavailable, log total wall-clock in `summary.md`.
- Draft `reports/2026-01-test-suite-refresh/phase_b/$STAMP/summary.md` covering pass/fail/skip counts, slowest tests, and any infrastructure issues.
Pitfalls To Avoid:
- Do not generate a new STAMP; Phase B must reuse 20251015T113531Z for cross-phase linkage.
- Keep `CUDA_VISIBLE_DEVICES=-1`; no GPU runs unless the supervisor revises scope.
- Preserve `PYTEST_ADDOPTS="--maxfail=200 --timeout=905"`; altering limits will invalidate tolerance tracking.
- Do not truncate `pytest.log`; the full verbose output is required for later clustering.
- Avoid rerunning the suite multiple times this loop; capture exactly one guarded execution.
- Ensure junit XML and timing files land under the phase_b folder before concluding the loop.
- If pytest aborts early, do not delete partial artifacts—document the failure instead.
- Leave Phase A artifacts untouched; only copy what is needed.
Pointers:
- docs/fix_plan.md:39-53
- plans/active/test-suite-triage-rerun.md:30-40
- reports/2026-01-test-suite-refresh/phase_a/20251015T113531Z/summary.md:65-84
- docs/development/testing_strategy.md:30-34
- docs/development/pytorch_runtime_checklist.md:41
Next Up: Phase C failure clustering once the full-suite log, junit XML, and summary are in place.
