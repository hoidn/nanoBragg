Summary: Capture Phase A preflight for full-suite pytest triage and log authoritative artifacts.
Mode: Docs
Focus: TEST-SUITE-TRIAGE-001 Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: `pytest --collect-only tests -q`
Artifacts: reports/2026-01-test-suite-triage/phase_a/<STAMP>/{preflight.md,collect_only.log,commands.txt}
Do Now: [TEST-SUITE-TRIAGE-001] Phase A — run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests -q` after capturing env + disk notes per plan.
If Blocked: Capture whatever partial data you can (env snapshot, df -h) and log blockers in preflight.md plus Attempt history before pausing.
Priorities & Rationale:
- tests/development/testing_strategy.md: Phase A relies on §§1.4–1.5 for env + command discipline.
- docs/fix_plan.md: New Critical item mandates suspending other work until triage evidence exists.
- plans/active/test-suite-triage.md: Provides the Phase A checklist you must satisfy this loop.
- arch.md§15: Ensure differentiability/device guardrails noted in preflight to catch regressions early.
How-To Map:
- `mkdir -p reports/2026-01-test-suite-triage/phase_a/$STAMP && cd` into that dir for artifact capture.
- Record env info: `python -m site > env.txt`, `python - <<'PY'` snippet to print torch version + cuda availability.
- Log disk headroom: `df -h . | tee disk_usage.txt`.
- Run command (Do Now) with `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests -q | tee collect_only.log`.
- Summarise all findings in `preflight.md` (phases/tasks A1–A3) and list env/disk/collect outputs; document command list in `commands.txt`.
- Update Attempt history under `[TEST-SUITE-TRIAGE-001]` with artifact paths.
Pitfalls To Avoid:
- Do not start Phase B (full suite) yet; finish Phase A checklist first.
- Respect Protected Assets listed in docs/index.md (especially loop.sh, supervisor.sh, input.md).
- Keep artifact timestamps unique; reuse `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` to avoid overwrites.
- Ensure env variable `KMP_DUPLICATE_LIB_OK=TRUE` is set inline when calling pytest.
- Avoid ad-hoc script edits or code changes; this loop is evidence-only.
- Don’t discard collect-only output even if failures occur—archive raw log.
- Guard GPU inspection with `torch.cuda.is_available()`; don’t assume availability.
Pointers:
- docs/fix_plan.md#test-suite-triage-001-full-pytest-run-and-triage
- plans/active/test-suite-triage.md:Phase A checklist
- docs/development/testing_strategy.md#14-pytorch-device--dtype-discipline
- arch.md#15-differentiable-programming-principles
- docs/development/pytorch_runtime_checklist.md
Next Up: Phase B full-suite execution once Phase A artifacts are committed and logged.
