Summary: Capture the guarded chunk-03 rerun under the new 905 s ceiling and package the evidence bundle for Phase R.
Mode: Perf
Focus: [TEST-SUITE-TRIAGE-001] Phase R chunk 03 rerun (R3)
Branch: feature/spec-based-2
Mapped tests: timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part1.txt --maxfail=0 --durations=25; timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part2.txt --maxfail=0 --durations=25; timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part3a.txt --maxfail=0 --durations=25; timeout 2400 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part3b.txt --maxfail=0 --durations=25
Artifacts: reports/2026-01-test-suite-triage/phase_r/$STAMP/{commands.txt,summary.md,timing_summary.md,env/python.txt,env/torch.txt,chunks/chunk_03/pytest_part{1,2,3a,3b}.log,chunks/chunk_03/pytest_part{1,2,3a,3b}.xml,chunks/chunk_03/exit_code.txt}
Do Now: Next Action 17 — Phase R chunk 03 rerun (R3); recreate `commands.txt`, then execute the four guarded chunk commands so `@pytest.mark.timeout(905)` is validated in situ and every log lands under `reports/2026-01-test-suite-triage/phase_r/$STAMP/`.
If Blocked: Stop after the failing command, capture stdout/stderr + `exit_code.txt` in `reports/2026-01-test-suite-triage/phase_r/$STAMP/chunks/chunk_03/attempt_blocked/`, and log the blocker in docs/fix_plan.md Attempts History before exiting the loop.
Priorities & Rationale:
- plans/active/test-suite-triage.md:374-386 — Phase R now hinges on R3 to confirm the ladder passes with the 905 s guard.
- docs/fix_plan.md:783-799 — Attempt #83 closed R2; Next Action 17 is the current blocker for initiative closure.
- reports/2026-01-test-suite-triage/phase_r/20251015T091543Z/chunks/chunk_03/summary.md — Documents the 900.02 s breach we must replace with a passing 905 s run.
- reports/2026-01-test-suite-triage/phase_r/20251015T100100Z/tolerance_update/design.md — Authorization packet for the new ceiling; cite it when drafting summary.md.
- reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/commands.txt — Canonical command roster to clone for the new STAMP.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2026-01-test-suite-triage/phase_r/$STAMP/{chunks/chunk_03,env}` before any `tee` pipes.
- Copy `reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/commands.txt` to `reports/2026-01-test-suite-triage/phase_r/$STAMP/commands.txt` and edit it to reflect the new STAMP plus 905 s expectation.
- Run part 1:
  `timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part1.txt --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_r/$STAMP/chunks/chunk_03/pytest_part1.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_r/$STAMP/chunks/chunk_03/pytest_part1.log`
- Run part 2 (same pattern, swap selector file and suffix `part2`).
- Run part 3a (same pattern, suffix `part3a`).
- Run part 3b with the extended ceiling:
  `timeout 2400 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part3b.txt --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_r/$STAMP/chunks/chunk_03/pytest_part3b.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_r/$STAMP/chunks/chunk_03/pytest_part3b.log`
- Record exit code (`echo $? > .../exit_code.txt`) after the final command and capture env info (`python -VV > .../env/python.txt`, `python - <<'PY'` snippet for torch version → `env/torch.txt`).
- Draft `summary.md` noting pass/fail counts per chunk and explicitly call out observed runtime vs 905 s ceiling for `test_property_gradient_stability`; place timing stats in `timing_summary.md`.
- Update docs/fix_plan.md Attempts History once results are known (PASS vs residual failures) — include STAMP + runtime highlights.
Pitfalls To Avoid:
- Do not forget `mkdir -p` before piping to `tee`; missing dirs drop logs.
- Keep `CUDA_VISIBLE_DEVICES=-1` and `NANOBRAGG_DISABLE_COMPILE=1`; the compile guard is required for C2 stability.
- Leave selectors untouched; no ad-hoc test lists.
- Monitor runtime during part3b; abort only if >905 s indicates a real regression.
- Stay on-branch `feature/spec-based-2`; no rebases mid-run.
- Document the STAMP consistently across commands, logs, and summaries.
- Avoid editing production code—this loop is test execution only.
- Do not delete prior `phase_r/20251015T09*` artifacts; we need the comparison history.
- Capture exit codes even on success; we need proof of the guarded ladder result.
Pointers:
- plans/active/test-suite-triage.md:374-386
- docs/fix_plan.md:783-799
- reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/commands.txt
- reports/2026-01-test-suite-triage/phase_r/20251015T091543Z/chunks/chunk_03/summary.md
- reports/2026-01-test-suite-triage/phase_r/20251015T100100Z/tolerance_update/design.md
Next Up: If chunk 03 passes cleanly, proceed to Phase R4 — aggregate the ladder results, refresh remediation_tracker.md, and prep the final full-suite guard run.
