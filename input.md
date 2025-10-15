Summary: Rerun Phase O chunk 03 with the compile guard so the C2 gradcheck failures disappear and baseline counts drop to the remaining C18 tolerances.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage — O5 chunk 03 revalidation
Branch: main
Mapped tests: chunk 03 set (tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py tests/test_gradients.py tests/test_show_config.py)
Artifacts: reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_03/; reports/2026-01-test-suite-triage/phase_o/$STAMP/gradients/summary.md; reports/2026-01-test-suite-triage/phase_o/$STAMP/summary.md
Do Now: [TEST-SUITE-TRIAGE-001] O5 chunk 03 revalidation — run `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py tests/test_gradients.py tests/test_show_config.py --maxfail=0 --durations=25 --junitxml "$PHASE_O/chunks/chunk_03/pytest.xml" 2>&1 | tee "$PHASE_O/chunks/chunk_03/pytest.log"`
If Blocked: Keep the failed pytest output in `$PHASE_O/chunks/chunk_03/blocked.log`, record the exit code, and update docs/fix_plan.md Attempts + plan O5 with the blocker before stopping.
Priorities & Rationale:
- docs/fix_plan.md:56-57 mark O5/O6 as the next actions and expect C2 removal after the guarded rerun.
- plans/active/test-suite-triage.md:297-305 lists O5/O6 tasks and points to chunk 03 plus artifact cleanup.
- reports/2026-01-test-suite-triage/phase_o/20251015T011629Z/summary.md shows the stale 12-failure baseline we are about to refresh.
- reports/2026-01-test-suite-triage/phase_o/20251015T014403Z/grad_guard/summary.md confirms the guard works; we now need the suite evidence.
- docs/development/testing_strategy.md:513-523 mandates disabling torch.compile for gradchecks and recording the command + env.
How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `export PHASE_O=reports/2026-01-test-suite-triage/phase_o/$STAMP`; `mkdir -p "$PHASE_O/chunks/chunk_03" "$PHASE_O/gradients"`.
2. Move the stray grads XML into its real home: `mv reports/2026-01-test-suite-triage/phase_o/'$(date -u +%Y%m%dT%H%M%SZ)'/grad_guard/pytest.xml reports/2026-01-test-suite-triage/phase_o/20251015T014403Z/grad_guard/pytest.xml`; remove the now-empty placeholder directory with `rmdir reports/2026-01-test-suite-triage/phase_o/'$(date -u +%Y%m%dT%H%M%SZ)'/grad_guard reports/2026-01-test-suite-triage/phase_o/'$(date -u +%Y%m%dT%H%M%SZ)'`.
3. Run the chunk command from Do Now (step 2) with the guard env var already exported; capture stdout/stderr via `tee` as shown so we keep `pytest.log`, and ensure `exit_code.txt` records `$?` afterwards.
4. Summarise the run: create `$PHASE_O/gradients/summary.md` capturing collected/passed/failed/skipped counts (expected 63/63/0/0), slowest tests, and a note that C2 is cleared under guard.
5. Update `$PHASE_O/summary.md` to restate the Phase O aggregate with new totals (692 collected / 553 passed / 2 failed / 137 skipped) and reference both the original 20251015T011629Z run and this guarded chunk delta.
6. Refresh `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` (and any linked dashboard) so C2 shows RESOLVED with Attempt #70, leaving only C18 open; keep the timestamp + counts consistent with the new summary.
7. Log the work: add Attempt #70 to docs/fix_plan.md (item 8 → complete) and mark O5 state [D] + adjust O6 guidance if ledger refresh finished; update plans/active/test-suite-triage.md O5/O6 checkboxes accordingly.
8. If you touch docs, run `git status` to confirm only the expected files changed, and stage them for supervisor review.
Pitfalls To Avoid:
- Forgetting to set `NANOBRAGG_DISABLE_COMPILE=1` so gradchecks still fail.
- Writing artifacts outside the `$PHASE_O/chunks/chunk_03/` path or omitting the `gradients/summary.md` roll-up.
- Leaving the bogus `$(date -u +%Y%m%dT%H%M%SZ)` directory behind after moving `pytest.xml`.
- Skipping the summary/tracker updates; fix_plan expects counts to drop to 2 failures.
- Running the entire suite—stay on chunk 03 this loop.
- Omitting `KMP_DUPLICATE_LIB_OK=TRUE`, which can trigger MKL crashes mid-run.
- Forgetting to capture `exit_code.txt` immediately after pytest.
- Letting docs/fix_plan.md remain out of sync with the new evidence bundle.
- Mixing devices; keep CUDA disabled (command already sets `CUDA_VISIBLE_DEVICES=-1`).
Pointers:
- docs/fix_plan.md:55-57
- plans/active/test-suite-triage.md:297-305
- reports/2026-01-test-suite-triage/phase_o/20251015T011629Z/summary.md
- reports/2026-01-test-suite-triage/phase_o/20251015T014403Z/grad_guard/summary.md
- docs/development/testing_strategy.md:513-523
Next Up: 1) If chunk 03 passes and ledgers are up to date, evaluate C18 performance tolerances (tests/test_at_perf_002.py, tests/test_at_perf_006.py).
