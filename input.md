Summary: Capture Phase L detector-config baseline logs and document findings for Sprint 1.3 kickoff.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: tests/test_detector_config.py
Artifacts: reports/2026-01-test-suite-triage/phase_l/<STAMP>/detector_config/
Do Now: [TEST-SUITE-TRIAGE-001] Phase L targeted rerun — CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py --maxfail=0
If Blocked: Capture the failing console log to reports/2026-01-test-suite-triage/phase_l/<STAMP>/detector_config/blocked.log and note the blocker plus command in analysis.md.
Priorities & Rationale:
- plans/active/test-suite-triage.md:23 — Phase L pending until detector-config artifacts exist; unlocks Sprint 1.3 sequencing.
- plans/active/test-suite-triage.md:155 — Checklist defines targeted run + brief requirements; we need both before delegating implementation.
- docs/fix_plan.md:39 — Next actions now demand the Phase L rerun, summary, and tracker sync before moving on.
- reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/triage_summary.md:181 — Authoritative reproduction selector and failing tests for C8.
How-To Map:
- Run `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py --maxfail=0 | tee reports/2026-01-test-suite-triage/phase_l/$STAMP/detector_config/pytest.log` (create `$STAMP=$(date -u +%Y%m%dT%H%M%SZ)`).
- Move `pytest.xml` to the same directory and save `env/torch_env.txt`, `env/pip_freeze.txt`, and `commands.txt` capturing the exact invocation.
- Summarise failures + context into `reports/2026-01-test-suite-triage/phase_l/$STAMP/detector_config/analysis.md`, referencing spec-a-core §4 and arch.md §2 for expected defaults.
- Update `docs/fix_plan.md` attempt notes and `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` with the new stamp and counts once artifacts exist.
Pitfalls To Avoid:
- Do not modify production code or tests this loop — evidence gathering only.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` set or pytest may crash loading torch.
- Maintain vectorization/device neutrality; no ad-hoc CPU-only rewrites.
- Respect Protected Assets listed in docs/index.md (e.g., loop.sh, input.md).
- Store artifacts under the new `phase_l/$STAMP` folder; do not reuse Phase K directories.
- Record exact commands/versions via commands.txt before leaving the run.
- Avoid pruning prior Phase K/D artifacts; they stay authoritative.
- Ensure `--maxfail=0` so both detector-config tests execute.
- Include environment captures; missing env snapshots will block plan closure.
Pointers:
- plans/active/test-suite-triage.md:155 — Phase L checklist and exit criteria.
- docs/fix_plan.md:39 — Current next actions for the suite triage workstream.
- reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/triage_summary.md:181 — Detector-config failure details.
- docs/development/testing_strategy.md:44 — Runtime guardrails for targeted pytest runs.
Next Up: Draft detector-config spec vs implementation gap memo (per plans/active/test-suite-triage.md Phase L L2) once artifacts are collected.
