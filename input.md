Summary: Capture the directive-mandated full-suite baseline and refresh failure triage before resuming MOSFLM remediation.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests; pytest tests/ -v --durations=25 --maxfail=0
Artifacts: reports/2026-01-test-suite-triage/phase_m0/$STAMP/{preflight,artifacts,triage_summary.md}
Do Now: [TEST-SUITE-TRIAGE-001] Full pytest run and triage — KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/artifacts/pytest_full.xml
If Blocked: Stop after logging the failure in reports/2026-01-test-suite-triage/phase_m0/$STAMP/attempt_blocked.md and update docs/fix_plan.md + plans/active/test-suite-triage.md (Phase M0 table) with the observed blocker.
Priorities & Rationale:
- plans/active/test-suite-triage.md:168 — Phase M0 mandates the preflight snapshot, full-suite rerun, and refreshed triage package before other work.
- docs/fix_plan.md:38 — Next Actions now require Phase M0a–M0c artifacts and ledger sync; completing them unblocks downstream remediation.
- docs/development/testing_strategy.md:18 — Device/dtype discipline plus full-suite cadence guardrails apply while collecting this baseline.
- docs/development/pytorch_runtime_checklist.md:12 — Reconfirm runtime guardrails (dtype neutrality, vectorization) before entering the long run.
How-To Map:
- Export STAMP=`date -u +%Y%m%dT%H%M%SZ`; mkdir -p reports/2026-01-test-suite-triage/phase_m0/$STAMP/{preflight,artifacts}.
- Preflight (Phase M0a): `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/preflight/collect_only.log`; capture `python -m pip freeze > .../preflight/pip_freeze.txt` and `python - <<'PY'` env summary (Python, torch, CUDA) into `env.txt`.
- Full-suite run (Phase M0b): `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/artifacts/pytest_full.xml | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/artifacts/pytest_full.log`; note runtime + exit code in `commands.txt`.
- Post-run triage (Phase M0c): parse failures into `reports/2026-01-test-suite-triage/phase_m0/$STAMP/triage_summary.md`, flag each as implementation bug vs deprecation candidate, and log counts in `summary.md`.
- Update docs: append Attempt entry under `[TEST-SUITE-TRIAGE-001]` in docs/fix_plan.md with metrics, link new artifacts, and note any novel failure classes.
- Prep follow-up: if detector-config regressions resurface, open a new row in remediation_tracker.md with cluster IDs; otherwise, document confirmation so `[DETECTOR-CONFIG-001]` stays marked done.
Pitfalls To Avoid:
- Do not shorten runtime options; allow the run to exceed 30 minutes if needed rather than splitting unless timeout recurs.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` on every pytest invocation to avoid MKL crashes.
- No implementation edits this loop; capture evidence only.
- Store artifacts exactly under the phase_m0/$STAMP/ hierarchy to keep history consistent.
- Watch disk usage; abort if <10 GB free and record the blockage.
Pointers:
- plans/active/test-suite-triage.md:168
- docs/fix_plan.md:38
- docs/development/testing_strategy.md:18
- docs/development/pytorch_runtime_checklist.md:12
Next Up: If time remains after triage, stage the remediation_tracker.md updates so Phase M gating can resume once MOSFLM fixes land.
