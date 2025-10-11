Summary: Run the Phase D2 full-suite regression to retire the remaining source-weighting failures and prep docs for closure.
Mode: Docs
Focus: [SOURCE-WEIGHT-002] Simulator source weighting
Branch: feature/spec-based-2
Mapped tests: pytest tests/ --maxfail=5
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/source_weighting/
Do Now: [SOURCE-WEIGHT-002] Phase D2 regression delta — run `STAMP=$(date -u +%Y%m%dT%H%M%SZ); CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ --maxfail=5 --junitxml=reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting/artifacts/pytest_full.xml`
If Blocked: Capture the partial `pytest_full.log` with the failure/context you reached, store it under the same Phase D stamp, and note the interruption plus reason in the Attempt history before exiting.
Priorities & Rationale:
- docs/fix_plan.md:155 — Next Actions now isolate Phase D2/D4; we need the regression artifact to flip the ledger.
- plans/active/source-weighting.md:6 — Status snapshot marks D2+D4 as the remaining blockers for Sprint 1.2.
- docs/development/testing_strategy.md:67 — mandates using the documented full-suite command and env guardrails.
- specs/spec-a-core.md:496 — AT-SRC-001 acceptance requires confirming the source weighting fixes across the whole suite.
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; mkdir -p `reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting/{logs,artifacts,env}` before running tests.
- From repo root run `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ --maxfail=5 --junitxml=reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting/artifacts/pytest_full.xml | tee reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting/logs/pytest_full.log`. The Do Now command already sets `STAMP`; reuse it here.
- Verify the junit file exists (size >0) and copy the combined log summary into `reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting/logs/summary.md` with the headline counts (pass/fail/skip, runtime, top 25 durations).
- Record environment via `python -m torch.utils.collect_env > reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting/env/torch_env.txt` and `pip freeze > reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting/env/pip_freeze.txt` once the run finishes.
- Update `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md` and `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/classification_overview.md` delta tables with the new pass/fail counts (target: C3 resolved, overall failures drop by ≥4).
- Append C3 progress to `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` (mark cluster resolved with Attempt #18 follow-up) and `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_sequence.md` Sprint 1 progress table.
- Log Attempt #18 follow-up in `docs/fix_plan.md` with artifact paths, new failure counts, and confirmation that D2 is complete. Set yourself up to finish Phase D4 next loop.
Pitfalls To Avoid:
- Don’t skip `KMP_DUPLICATE_LIB_OK=TRUE`; PyTorch will crash mid-suite without it.
- Keep the run CPU-only (`CUDA_VISIBLE_DEVICES=-1`) per plan so results match previous baselines.
- Do not overwrite earlier Phase D artifacts—use a fresh timestamp directory.
- No code changes; this loop is evidence + documentation only.
- Preserve device/dtype neutrality when interpreting failures; note any CUDA-specific skips but don’t re-enable GPU here.
- Avoid pruning Protected Assets referenced in docs/index.md when tidying artifacts.
- If the run exceeds 3600s, allow it to finish; only interrupt for real blockers and document them.
Pointers:
- docs/fix_plan.md:155
- plans/active/source-weighting.md:69
- reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md
- reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md
- docs/development/testing_strategy.md:60
Next Up:
1. [SOURCE-WEIGHT-002] Phase D4 closure — sync plan + tracker updates once the regression delta artifacts are logged.
