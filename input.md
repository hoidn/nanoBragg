Summary: Finish the Phase K full-suite rerun with a 60-minute timeout and refresh the triage artifacts.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: pytest tests/
Artifacts: reports/2026-01-test-suite-triage/phase_k/$STAMP/{commands.txt,logs/pytest_full.log,artifacts/pytest_full.xml,analysis/triage_summary.md,analysis/classification_overview.md,summary.md,env/torch_env.txt}
Do Now: Phase K rerun (timeout 60 min) — export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-triage/phase_k/$STAMP/{artifacts,logs,analysis,env}; timeout 3600 CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_k/$STAMP/artifacts/pytest_full.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_k/$STAMP/logs/pytest_full.log
If Blocked: Capture stderr/stdout plus junit into the same $STAMP directory, write blocked.md describing the failure (include last test seen, runtime, exit code, and whether timeout 3600 elapsed), then stop and flag the issue in Attempts History.
Priorities & Rationale:
- docs/fix_plan.md:1-90 — Next Actions now demand a ≥60 min rerun with STAMP pre-created directories before any other work resumes.
- plans/active/test-suite-triage.md:1-180 — Phase K checklist spells out the timeout, directory creation, and tracker update expectations.
- reports/2026-01-test-suite-triage/phase_k/20251011T070734Z/blocked.md — Documents the 600 s timeout and path bug we must avoid this loop.
- docs/development/testing_strategy.md:18-33 — Authoritative guardrails for full-suite execution (device neutrality, logging requirements).
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ) and echo the value into reports/2026-01-test-suite-triage/phase_k/$STAMP/commands.txt before each major step.
- mkdir -p reports/2026-01-test-suite-triage/phase_k/$STAMP/{artifacts,logs,analysis,env} and double-check the paths contain the timestamp (no double slashes).
- timeout 3600 CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_k/$STAMP/artifacts/pytest_full.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_k/$STAMP/logs/pytest_full.log.
- After the run, append the exact pytest command, runtime, and exit code to commands.txt; run `pytest --version` and `python -m torch.utils.collect_env` and store outputs in env/torch_env.txt.
- Rebuild analysis/triage_summary.md and analysis/classification_overview.md by diffing against Phase I (reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/); call out pass/fail/skip deltas and note any newly passing clusters.
- Copy reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/ into phase_j/$STAMP/, update remediation_tracker.md and remediation_sequence.md with new counts/owners, and summarize the changes inside phase_k/$STAMP/summary.md.
- Log Attempt #15 in docs/fix_plan.md with artifact paths, runtime, pass/fail counts, and any blockers; update galph_memory Attempts History as usual.
Pitfalls To Avoid:
- Do not forget to export STAMP before running pytest; missing it recreates the double-slash bug.
- Keep timeout at 3600 seconds; shorter limits will kill the suite mid-gradient tests.
- No production code or test edits during this evidence loop.
- Ensure commands.txt records every shell command executed for provenance.
- Capture full stdout/stderr via tee; do not truncate logs or skip junit XML.
- Preserve prior Phase H/I artifacts; stage new outputs under the new timestamp only.
- Verify disk space before start (>40 GB free) to avoid partial logs.
Pointers:
- docs/fix_plan.md:1-90 — Active focus and Next Actions for Phase K.
- plans/active/test-suite-triage.md:140-175 — Phase K checklist (K1–K3) and tracker update guidance.
- reports/2026-01-test-suite-triage/phase_k/20251011T070734Z/blocked.md — Root-cause summary of the previous timeout.
Next Up: After the rerun, prioritise recomputing the classification deltas and refreshing the remediation tracker so Sprint 1 sequencing can resume.
