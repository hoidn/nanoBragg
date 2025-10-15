Summary: Capture chunk 03 remainder under guard-friendly selectors so the Phase O baseline reflects only C18+C19.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-001 / Next Action 9 (chunk 03 remainder ledger refresh)
Branch: feature/spec-based-2
Mapped tests: tests/test_at_cli_001.py; tests/test_at_flu_001.py; tests/test_at_io_004.py; tests/test_at_parallel_020.py; tests/test_at_perf_001.py; tests/test_at_pre_002.py; tests/test_at_sta_001.py; tests/test_configuration_consistency.py; tests/test_gradients.py (non-gradcheck subset); tests/test_show_config.py
Artifacts: reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/{pytest.log,pytest.xml,summary.md,exit_code.txt}; reports/2026-01-test-suite-triage/phase_o/${STAMP}/summary.md; reports/2026-01-test-suite-triage/remediation_tracker.md
Do Now: TEST-SUITE-TRIAGE-001 Next Action 9 — run the guard-friendly chunk 03 remainder:
  STAMP=$(date -u +%Y%m%dT%H%M%SZ);
  mkdir -p reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03 reports/2026-01-test-suite-triage/phase_o/${STAMP}/gradients;
  cp reports/2026-01-test-suite-triage/phase_o/20251015T014403Z/grad_guard/{summary.md,exit_code.txt} reports/2026-01-test-suite-triage/phase_o/${STAMP}/gradients/;
  timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors.txt -k "not gradcheck" --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest.log
If Blocked: If the remainder still hits the 600s cap, split the selector list in half (prepend `_part1`/`_part2` text files), capture both outputs under the same STAMP, and log the adjustment + timing in attempts history before syncing partial summaries.
Priorities & Rationale:
- plans/active/test-suite-triage.md:300-312 mandates the two-step O5/O6 workflow; finishing the remainder run is the gate to Sprint 1.5.
- docs/fix_plan.md:56-65 escalates Next Action 9 as partial; completing this loop unblocks the ledger refresh and C18 review.
- reports/2026-01-test-suite-triage/phase_o/20251015T030233Z/chunks/chunk_03/summary.md shows why the timeout path is insufficient; we need fresh counts without gradcheck noise.
- reports/2026-01-test-suite-triage/remediation_tracker.md documents C2 resolution but flags the outstanding ledger update; update it with the new STAMP once tests finish.
How-To Map:
1. Export STAMP (`STAMP=$(date -u +%Y%m%dT%H%M%SZ)`) and create `reports/2026-01-test-suite-triage/phase_o/${STAMP}/{chunks/chunk_03,gradients}`.
2. Copy grad suite artifacts: `cp reports/2026-01-test-suite-triage/phase_o/20251015T014403Z/grad_guard/{summary.md,exit_code.txt} reports/2026-01-test-suite-triage/phase_o/${STAMP}/gradients/`.
3. Run the remainder command from Do Now; confirm runtime <600s and that `pytest.log` records all modules except the gradchecks.
4. Generate `chunks/chunk_03/summary.md` (clone the 20251015T030233Z template; update counts, runtime, failure list — expect only C18 + C19).
5. Update `phase_o/${STAMP}/summary.md` with aggregated totals (pass/fail/skipped/xfailed, slowest tests, duration sum) and link both artifact locations.
6. Refresh `reports/2026-01-test-suite-triage/remediation_tracker.md` (C2 → 0, C18 → 2, C19 → 1) and move the stray `phase_o/$(date -u +%Y%m%dT%H%M%SZ)/grad_guard/pytest.xml` into the new STAMP bundle.
7. Update docs/fix_plan.md (Next Action 9 → ✅, add Attempt entry with STAMP) and plans/active/test-suite-triage.md (O5 → [D], O6 → [D]).
Pitfalls To Avoid:
- Do not drop `-k "not gradcheck"`; the heavy gradchecks must stay in the copied bundle.
- Keep `${STAMP}` braces in every path — prior runs failed because `$STAMP` was unset in `tee`.
- Ensure `NANOBRAGG_DISABLE_COMPILE=1` is present before importing torch; otherwise gradcheck docs become stale.
- Avoid editing production code; this is an evidence loop only.
- Capture `exit_code.txt` manually (`printf '0\n' > ...`) if pytest exits 0; missing file breaks tracker automation.
- Verify the selectors file (`reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors.txt`) before running; no ad-hoc test additions.
- Keep runtime under 600s; if close, trim the `--durations` option last — do not remove env guards.
- When cloning summary templates, update STAMP references and totals; stale counts will mislead downstream planning.
- Move, don’t copy, the stray grad_guard pytest.xml so we end with a single canonical location.
- Record Attempt details (STAMP, runtime, failures) in fix_plan attempts history immediately after the run.
Pointers:
- docs/fix_plan.md:56-65 — Next Action 9 scaffold and command snippet.
- plans/active/test-suite-triage.md:300-312 — Phase O O5/O6 instructions and exit criteria.
- reports/2026-01-test-suite-triage/phase_o/20251015T030233Z/chunks/chunk_03/summary.md — timeout context/template for the new summary.
Next Up: If this lands quickly, start drafting the C18 tolerance review summary (use reports/2026-01-test-suite-triage/phase_m3/20251015T002610Z/mixed_units/ as baseline).
