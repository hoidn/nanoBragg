Summary: Enforce the gradcheck compile guard in tests/test_gradients.py and prove the targeted grad suite passes cleanly.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage — Apply gradcheck compile guard (C2)
Branch: main
Mapped tests: tests/test_gradients.py -k "gradcheck"
Artifacts: reports/2026-01-test-suite-triage/phase_o/$STAMP/grad_guard/
Do Now: [TEST-SUITE-TRIAGE-001] Apply gradcheck compile guard — set a fresh STAMP/PHASE_O directory, add the module-level `os.environ["NANOBRAGG_DISABLE_COMPILE"] = "1"` before importing torch in tests/test_gradients.py, then run `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_gradients.py -k "gradcheck" --maxfail=0 --durations=25 --junitxml "$PHASE_O/grad_guard/pytest.xml" 2>&1 | tee "$PHASE_O/grad_guard/pytest.log"` and record the exit code.
If Blocked: Capture the failing command output in `$PHASE_O/grad_guard/blocked.log`, note the exit code, and log the blocking detail in docs/fix_plan.md Attempts before stopping.
Priorities & Rationale:
- Fix-plan next action #7 (docs/fix_plan.md:45) now targets the gradcheck compile guard; closing it keeps Phase O momentum.
- Phase O table (plans/active/test-suite-triage.md:302) is marked [D] for O2/O3; the guard unlocks the post-guard baseline refresh.
- Attempt #48 summary (reports/2026-01-test-suite-triage/phase_o/20251015T011629Z/summary.md) shows remaining failures isolated to C2/C18.
- Testing strategy §4.1 (docs/development/testing_strategy.md:514) mandates in-test `NANOBRAGG_DISABLE_COMPILE` for gradchecks.
How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `export PHASE_O=reports/2026-01-test-suite-triage/phase_o/$STAMP`; `mkdir -p "$PHASE_O/grad_guard"`.
2. Edit tests/test_gradients.py: import os if needed and set `os.environ["NANOBRAGG_DISABLE_COMPILE"] = "1"` before the first torch import.
3. Run `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_gradients.py -k "gradcheck" --maxfail=0 --durations=25 --junitxml "$PHASE_O/grad_guard/pytest.xml" 2>&1 | tee "$PHASE_O/grad_guard/pytest.log"`.
4. Immediately capture the exit status with `echo $? > "$PHASE_O/grad_guard/exit_code.txt"`.
5. If the suite passes, note total duration and counts in a brief `$PHASE_O/grad_guard/summary.md` for follow-up Phase O aggregation.
Pitfalls To Avoid:
- Do not run the full chunk ladder this loop; keep scope to gradcheck validation.
- Insert the env guard before importing torch and without breaking existing module imports.
- Retain ASCII formatting; no smart quotes in the test file.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` in every pytest command to avoid MKL crashes.
- No `.item()` or dtype/device assumptions while touching tests.
Pointers:
- docs/fix_plan.md:45
- plans/active/test-suite-triage.md:302
- docs/development/testing_strategy.md:514
- reports/2026-01-test-suite-triage/phase_o/20251015T011629Z/summary.md
Next Up: Rerun chunk 03 with `NANOBRAGG_DISABLE_COMPILE=1` after the guard lands to refresh Phase O counts.
