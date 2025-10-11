Summary: Relaunch the full pytest suite (Phase H) and capture fresh artifacts to feed the new failure triage cycle.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Phase H suite relaunch
Branch: feature/spec-based-2
Mapped tests: pytest tests/
Artifacts: reports/2026-01-test-suite-triage/phase_h/<STAMP>/; reports/2026-01-test-suite-triage/phase_i/<STAMP>/
Do Now: [TEST-SUITE-TRIAGE-001] Phase H H1–H4 — run `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_h/${STAMP}/artifacts/pytest_full.xml` and draft `reports/2026-01-test-suite-triage/phase_h/${STAMP}/docs/summary.md` plus the initial failure list for Phase I.
If Blocked: Capture the partial log + exit code in `reports/2026-01-test-suite-triage/phase_h/${STAMP}/full_suite/pytest_full.log`, record the blocker in `docs/summary.md`, and halt before editing docs or fix_plan.
Priorities & Rationale:
- plans/active/test-suite-triage.md (Phase H–J) — fresh run is prerequisite for the new remediation ladder.
- docs/fix_plan.md#test-suite-triage-001-full-pytest-run-and-triage — Active Focus now demands Attempt #10 artifacts before other work.
- docs/development/testing_strategy.md§1.5 — authoritative guidance for full-suite execution and artifact capture.
- reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/triage_summary.md — prior failure baseline to compare against after the rerun.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2026-01-test-suite-triage/phase_h/${STAMP}/{collect_only,full_suite,artifacts,docs}` and open `commands.txt` for the loop.
- Optional preflight: `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee reports/2026-01-test-suite-triage/phase_h/${STAMP}/collect_only/pytest.log`; gather env metadata via `python -V`, `pip list | grep torch`, and `nvidia-smi`, saving JSON to `collect_only/env.json`.
- Run the full suite command above, teeing stdout/stderr to `reports/.../full_suite/pytest_full.log`; note wall-clock runtime and pytest exit code in `commands.txt`.
- Generate `docs/summary.md` detailing pass/fail/skip counts, runtime, and top-25 durations; extract failing selectors (`pytest_full.xml` or log) into `docs/failures_raw.md` for Phase I consumption.
- Kick off Phase I by copying the Phase F template: `mkdir -p reports/2026-01-test-suite-triage/phase_i/${STAMP}` then seed `triage_summary.md` with the new failure list (classification can remain TODO markers for next loop if needed).
- Update `docs/fix_plan.md` Attempt log and this plan’s H1–H5 checkboxes only after artifacts exist.
Pitfalls To Avoid:
- Forgetting `CUDA_VISIBLE_DEVICES=-1` (TorchDynamo GPU bug) or `KMP_DUPLICATE_LIB_OK=TRUE` (MKL crash).
- Overwriting prior phase directories; always use a fresh `${STAMP}`.
- Skipping artifact capture (logs, junit, summary) — Phase I depends on these.
- Editing production code or non-doc assets during this loop.
- Neglecting to note exit code/runtime in `commands.txt` for reproducibility.
- Omitting comparison against the 20251010 baseline in `summary.md`.
Pointers:
- plans/active/test-suite-triage.md#phase-h-—-2026-suite-relaunch
- docs/fix_plan.md#test-suite-triage-001-full-pytest-run-and-triage
- docs/development/testing_strategy.md#15-loop-execution-notes-do-now--validation-scripts
- reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/triage_summary.md
Next Up: Begin Phase I classification (fill triage_summary.md and classification_overview.md) once the fresh run artifacts are in place.
