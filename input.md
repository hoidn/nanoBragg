Summary: Re-run Phase O chunk 03 with the compile guard and refresh the ledgers so the C2 gradcheck fixes are reflected in the baseline totals.
Mode: Parity
Focus: docs/fix_plan.md#test-suite-triage-001 (Next Action 9 — ledger refresh + artifact cleanup)
Branch: feature/spec-based-2
Mapped tests: tests/test_at_cli_001.py, tests/test_at_flu_001.py, tests/test_at_io_004.py, tests/test_at_parallel_009.py, tests/test_at_parallel_020.py, tests/test_at_perf_001.py, tests/test_at_pre_002.py, tests/test_at_sta_001.py, tests/test_configuration_consistency.py, tests/test_gradients.py, tests/test_show_config.py
Artifacts: reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_03/, reports/2026-01-test-suite-triage/phase_o/$STAMP/gradients/, reports/2026-01-test-suite-triage/phase_o/$STAMP/summary.md, reports/2026-01-test-suite-triage/remediation_tracker.md
Do Now: [TEST-SUITE-TRIAGE-001] Next Action 9 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ); env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py tests/test_gradients.py tests/test_show_config.py --maxfail=0 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_03/pytest.xml | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_03/pytest.log
If Blocked: Capture the partial log under reports/2026-01-test-suite-triage/phase_o/$STAMP/gradients/blockers.md with exit status + stack trace, then update docs/fix_plan.md Attempts History and halt.
Priorities & Rationale:
- plans/active/test-suite-triage.md:304-309 keeps Phase O on O5/O6 until the guarded chunk rerun finishes.
- docs/fix_plan.md:38-59 records Next Actions 8–9; ledger refresh cannot proceed without a full chunk result.
- reports/2026-01-test-suite-triage/phase_o/20251015T020729Z/gradients/summary.md documents the partial guard run, proving the need for a complete rerun.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ) and mkdir -p reports/2026-01-test-suite-triage/phase_o/$STAMP/{chunks/chunk_03,gradients}.
- Run the Do Now command to recompute chunk 03 with the guard; after it finishes, echo $? > reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_03/exit_code.txt.
- Copy the final chunk stats into reports/2026-01-test-suite-triage/phase_o/$STAMP/summary.md (start from the 20251015T011629Z version and adjust pass/fail/skip counts so C2=0 failures, C18 only).
- Update reports/2026-01-test-suite-triage/phase_o/$STAMP/gradients/summary.md with the new gradcheck + gradient_flow_simulation status; include timing and any remaining failure signatures.
- Move reports/2026-01-test-suite-triage/phase_o/$(date -u +%Y%m%dT%H%M%SZ)/grad_guard/pytest.xml into the new $STAMP/gradients/ directory and delete the placeholder folder once empty.
- Refresh reports/2026-01-test-suite-triage/remediation_tracker.md (mark C2 resolved, add the new STAMP attempt) and align docs/fix_plan.md Attempts History + plans/active/test-suite-triage.md row O5/O6 with the new evidence.
Pitfalls To Avoid:
- Forgetting NANOBRAGG_DISABLE_COMPILE=1 (gradchecks will fail immediately).
- Overwriting existing artifacts—always write under the new $STAMP tree.
- Skipping the exit_code.txt capture; the tracker expects it.
- Leaving the stray $(date ...) xml in place—must be moved or deleted.
- Editing production code or tests; this loop is evidence-only.
- Neglecting to record the remaining failure (likely test_gradient_flow_simulation) in the summaries.
- Allowing pytest to reuse cached results—clear or ignore .pytest_cache if you rerun quickly.
- Forgetting to cite updated counts in remediation_tracker.md and docs/fix_plan.md Attempts.
- Omitting cpu-only guard (CUDA_VISIBLE_DEVICES=-1) causing accidental GPU runs.
- Skipping --maxfail=0; without it pytest may short-circuit on the first failure, losing coverage.
Pointers:
- plans/active/test-suite-triage.md:292-309 for Phase O tasks and selector list.
- docs/fix_plan.md:38-59 detailing the outstanding ledger refresh requirements.
- docs/development/testing_strategy.md:500-523 for the canonical gradcheck guard mandate.
- docs/development/pytorch_runtime_checklist.md:1-33 for runtime and compile guard expectations.
- reports/2026-01-test-suite-triage/phase_o/20251015T020729Z/gradients/summary.md for the prior guard validation context.
Next Up: Stage the C18 performance tolerance rerun once the guarded baseline is recorded.
