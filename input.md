Summary: Refresh the full pytest suite run and capture 2026 triage artifacts for Phase E.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q | pytest tests/ -v --durations=25 --maxfail=0
Artifacts: reports/2026-01-test-suite-triage/phase_e/<STAMP>/
Do Now: [TEST-SUITE-TRIAGE-001] Phase E1/E2 — run `pytest --collect-only -q` then `STAMP=$(date -u +%Y%m%dT%H%M%SZ) ROOT=reports/2026-01-test-suite-triage/phase_e/$STAMP; mkdir -p "$ROOT"/{logs,artifacts}; KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml="$ROOT"/artifacts/pytest_full.xml | tee "$ROOT"/logs/pytest_full.log`
If Blocked: Capture the partial log under `reports/2026-01-test-suite-triage/phase_e/$STAMP/logs/` with notes in `attempt_failed.md`, update fix_plan Attempt history, and halt further execution.
Priorities & Rationale:
- plans/active/test-suite-triage.md:11-79 flags Phase E as reactivated and assigns the rerun tasks we must complete before remediation.
- docs/fix_plan.md:39-51 makes the Phase E rerun the top Next Action for this initiative; without it the backlog stays frozen.
- docs/development/testing_strategy.md:18-33 defines the guardrails (device/dtype neutrality, Do Now command fidelity) we need to respect during the suite run.
- reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/summary.md:1-160 provides the 2025 baseline we’ll compare against when drafting the new summary.
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `ROOT=reports/2026-01-test-suite-triage/phase_e/$STAMP`; `mkdir -p "$ROOT"/{logs,artifacts}` before running commands.
- Preflight: `pytest --collect-only -q | tee "$ROOT"/collect_only.log`; capture `python -m torch.utils.collect_env > "$ROOT"/env.txt` and `df -h . > "$ROOT"/disk_usage.txt` to mirror Phase A metadata.
- Full run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml="$ROOT"/artifacts/pytest_full.xml | tee "$ROOT"/logs/pytest_full.log`; expect ~30 min runtime, do not interrupt.
- Post-process summary: copy `reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/summary.md` as a template, then fill in new totals using the final `===` line from `tail -n 40 "$ROOT"/logs/pytest_full.log` and the `--durations=25` block from the same log; save as `$ROOT/summary.md`.
- Failure list: `rg '^FAILED ' "$ROOT"/logs/pytest_full.log | sed 's/^FAILED //' > "$ROOT"/failures_raw.txt`; convert to markdown bullets in `$ROOT/failures_raw.md` noting test node, markers, and any captured error text snippets.
- Ledger: record the exact commands in `$ROOT/commands.txt`, update `docs/fix_plan.md` Attempt #7 with counts/runtime/artifact paths, and leave a short note in Phase E table if clarifications are needed (no production code edits expected).
Pitfalls To Avoid:
- Do not run the suite without `KMP_DUPLICATE_LIB_OK=TRUE`; MKL crashes invalidate the attempt.
- Avoid overwriting Phase B artifacts—always use the new `phase_e/$STAMP` directory.
- No partial `-k` subsets; the directive is the full `tests/` run with `--maxfail=0`.
- Keep logs and summaries in ASCII; don’t drop binary artifacts into git.
- Verify disk space before the run to prevent truncated logs.
- Refrain from editing production code or tests; this loop is evidence-only.
- Note GPU availability in `env.txt` so future comparisons stay reproducible.
Pointers:
- plans/active/test-suite-triage.md:11-104
- docs/fix_plan.md:39-51
- docs/development/testing_strategy.md:18-33
- reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/summary.md:1-160
Next Up: Phase F triage refresh once the new summary and failures ledger are captured.
