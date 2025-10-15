Summary: Capture a clean guarded chunk-03 rerun so the Phase O baseline reflects C2=0 and only the remaining performance/tolerance issues.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py tests/test_gradients.py tests/test_show_config.py --maxfail=0 --junitxml reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest.xml
Artifacts: reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest.log; reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest.xml; reports/2026-01-test-suite-triage/phase_o/${STAMP}/gradients/summary.md; reports/2026-01-test-suite-triage/phase_o/${STAMP}/summary.md; reports/2026-01-test-suite-triage/remediation_tracker.md
Do Now: Execute [TEST-SUITE-TRIAGE-001] Next Action 9 by rerunning chunk 03 with the compile guard using the mapped pytest command (fresh STAMP, mkdir first, pipe through tee).
If Blocked: Capture the failure output, fall back to `pytest -vv tests/test_gradients.py -k "gradcheck or gradient_flow_simulation"` with the guard to isolate the blocker, and log results under the same STAMP before pausing.
Priorities & Rationale:
- docs/fix_plan.md:48-57 — Next Action 9 now requires a longer timeout and corrected tee path to finish chunk 03.
- plans/active/test-suite-triage.md:292-305 — Phase O tasks O5/O6 gate the overall test-suite directive.
- reports/2026-01-test-suite-triage/phase_o/20251015T023954Z/gradients/summary.md — Confirms C2 ✅ but highlights the timeout gaps we must close.
- docs/development/testing_strategy.md:1-80 — Canonical guardrails for grad-focused pytest runs (env vars, CPU execution).
How-To Map:
1. export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md
2. export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
3. mkdir -p reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03
4. timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py tests/test_gradients.py tests/test_show_config.py --maxfail=0 --junitxml reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest.log
5. Record exit code (`echo $? > reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/exit_code.txt`); if the guard still times out, note exact completion % in the summary.
6. Draft reports/2026-01-test-suite-triage/phase_o/${STAMP}/gradients/summary.md capturing gradcheck status, any surviving failures (esp. test_gradient_flow_simulation), runtime, and environment.
7. Summarise chunk totals in reports/2026-01-test-suite-triage/phase_o/${STAMP}/summary.md (pass/fail/skip/xfail counts + duration) and update reports/2026-01-test-suite-triage/remediation_tracker.md to set C2=0, keep C18 active, and log C19 with the new evidence STAMP.
8. Remove the stray `reports/2026-01-test-suite-triage/phase_o/$(date -u +%Y%m%dT%H%M%SZ)/grad_guard/pytest.xml` placeholder and retire only the obsolete timeout bundle after verifying the new run landed cleanly.
9. Update docs/fix_plan.md Attempts History with the new STAMP, mark Next Action 9 complete when artifacts exist, and refresh plans/active/test-suite-triage.md Phase O snapshot if counts change.
Pitfalls To Avoid:
- Do not reuse the old 600 s timeout; chunk 03 needs ≥1200 s headroom.
- Keep `NANOBRAGG_DISABLE_COMPILE=1` and `CUDA_VISIBLE_DEVICES=-1` set or gradchecks may regress.
- Ensure the tee path uses `${STAMP}` (brace expansion) so pytest.log lands under the correct folder.
- Create the chunk_03 directory before piping output; otherwise tee will fail silently.
- Capture exit_code.txt even on success to document the guarded run’s status.
- Do not delete the 20251015T023954Z attempt until the new STAMP is verified and logged.
- Avoid modifying production code or relaxing assertions; this loop is evidence-only.
- Keep the environment variable AUTHORITATIVE_CMDS_DOC exported for future traceability.
- Make sure the summaries explicitly call out test_gradient_flow_simulation outcome.
- After cleaning artifacts, double-check git status so no unintended deletions remain.
Pointers:
- docs/fix_plan.md:38
- plans/active/test-suite-triage.md:292
- reports/2026-01-test-suite-triage/phase_o/20251015T023954Z/chunks/chunk_03/summary.md
- docs/development/testing_strategy.md:1
Next Up: Begin the C18 performance tolerance review once the guarded chunk baseline is in place.
