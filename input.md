Summary: Capture Phase D Attempt #1 for the minimal `-default_F` CLI failure (C1) so we can unblock remediation work.
Mode: none
Focus: [CLI-DEFAULTS-001] Minimal -default_F CLI invocation
Branch: feature/spec-based-2
Mapped tests: - pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/attempt_cli_defaults/
Do Now: Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` and archive stdout/stderr as `pytest.log` plus `commands.txt` under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/attempt_cli_defaults/`.
If Blocked: Capture `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_at_cli_002.py` with the same artifact layout and record the failure mode in `attempt_notes.md`.
Priorities & Rationale:
- docs/fix_plan.md:67 — C1 is tagged High priority; Phase D requires this failure to be reproduced before fixes start.
- plans/active/test-suite-triage.md:14 — Phase D D1–D3 are complete; D4 (this input) is the remaining gate.
- reports/2026-01-test-suite-triage/phase_d/20260113T000000Z/handoff.md — Priority ladder calls out `[CLI-DEFAULTS-001]` as first P1 remediation item.
- docs/development/c_to_pytorch_config_map.md — Validate CLI flag expectations while inspecting the failure.
How-To Map:
- Pick a new UTC stamp (`STAMP=$(date -u +%Y%m%dT%H%M%SZ)`) and create `reports/2026-01-test-suite-triage/phase_d/$STAMP/attempt_cli_defaults/`.
- Write the executed commands to `commands.txt` (one line per invocation) before running the test.
- Execute the Do Now pytest command with `KMP_DUPLICATE_LIB_OK=TRUE`, capturing full stdout/stderr into `pytest.log`.
- After the run, jot a short `attempt_notes.md` summarising exit code, stack trace head, and immediate suspicion (default_F fallback vs HKL lookup).
Pitfalls To Avoid:
- Do not run the full suite yet; stay on the single selector above until a fix is ready.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` set for every PyTorch invocation.
- Avoid mutating docs/specs during this loop; focus on evidence capture first.
- Preserve vectorized code paths; no temporary Python loops in any quick experiments.
- Log every command in `commands.txt` before execution to keep provenance complete.
Pointers:
- docs/fix_plan.md:67
- plans/active/test-suite-triage.md:60
- reports/2026-01-test-suite-triage/phase_d/20260113T000000Z/handoff.md
- tests/test_at_cli_002.py
Next Up: If this attempt is wrapped early, line up `[DETERMINISM-001]` reproduction using `pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py`.
