Summary: Capture fresh determinism Phase A evidence now that dtype crashes are gone.
Mode: Parity
Focus: [DETERMINISM-001] PyTorch RNG determinism
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_013.py; tests/test_at_parallel_024.py
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/determinism/phase_a/
Do Now: [DETERMINISM-001] Phase A1–A3 — run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` then `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py --maxfail=0 --durations=10 --tb=short`, archiving logs under phase_a/.
If Blocked: If TorchDynamo aborts before the tests finish, rerun each file with `--maxfail=1 --tb=long`, save the output to phase_a/debug/, and stop for supervisor review.
Priorities & Rationale:
- docs/fix_plan.md:90-104 — Next Actions demand a fresh AT-013/024 rerun now that dtype crashes are resolved.
- plans/active/determinism.md:14-28 — Phase A tasks reopened post dtype fix; artifacts must live under phase_a/<STAMP>/.
- plans/active/dtype-neutral.md:12-16 — Phase D closed the cache bug, so determinism work is officially unblocked.
- docs/development/testing_strategy.md:19-34 — Authoritative commands and env guardrails for PyTorch parity runs.
How-To Map:
- Stamp a new directory: `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and mkdir -p `reports/2026-01-test-suite-triage/phase_d/${STAMP}/determinism/phase_a/{collect_only,at_parallel_013,at_parallel_024}`.
- `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee reports/2026-01-test-suite-triage/phase_d/${STAMP}/determinism/phase_a/collect_only/pytest.log`.
- `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py --maxfail=0 --durations=10 --tb=short | tee reports/2026-01-test-suite-triage/phase_d/${STAMP}/determinism/phase_a/at_parallel_013/pytest.log`.
- `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py --maxfail=0 --durations=10 --tb=short | tee reports/2026-01-test-suite-triage/phase_d/${STAMP}/determinism/phase_a/at_parallel_024/pytest.log`.
- Summarise key failures and device notes in `reports/2026-01-test-suite-triage/phase_d/${STAMP}/determinism/phase_a/summary.md`, include `commands.txt`, and update attempts history per fix_plan instructions.
Pitfalls To Avoid:
- No production code edits this loop; evidence capture only.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` on every pytest invocation.
- Do not flip env vars like `NB_RUN_PARALLEL`; we’re reproducing current defaults.
- Store logs only under the stamped phase_a/ folders; avoid ad-hoc paths.
- Capture TorchDynamo stack traces verbatim—don’t trim unless instructed.
- Note GPU availability but don’t run additional suites beyond the mapped tests.
Pointers:
- docs/fix_plan.md:90-104
- plans/active/determinism.md:14-28
- plans/active/dtype-neutral.md:12-33
- docs/development/testing_strategy.md:19-34
Next Up: Phase E validation bundle for `[DTYPE-NEUTRAL-001]` or Phase B callchain tracing once determinism logs are archived.
