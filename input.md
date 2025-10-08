Summary: Repair the scaling comparison script so Phase M parity evidence flows through scripted outputs instead of manual summaries.
Mode: Parity
Focus: CLI-FLAGS-003 Phase M1 instrumentation follow-up
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only tests/test_cli_scaling_phi0.py
- pytest --collect-only tests/test_phi_carryover_mode.py
- pytest -xvs tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/commands.txt
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling_spec.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling_per_phi.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/scaling_validation_summary.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/metrics.json
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/run_metadata.json
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/env.json
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/sha256.txt
- plans/active/cli-noise-pix0/plan.md (Phase M1 updated with timestamp & notes)
- docs/fix_plan.md (Attempt capturing tooling fix and residual metrics)
Do Now: CLI-FLAGS-003 Phase M1 — repair scripts/validation/compare_scaling_traces.py and rerun `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/scaling_validation_summary.md`
If Blocked: Halt immediately once the script still crashes; capture full stdout/stderr plus exit code in <timestamp>/commands.txt, stash any partial outputs, update instrumentation_audit.md with the new failure, and page galph rather than attempting alternate fixes.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:64 — Phase M1 checklist explicitly cites the crashing compare_scaling_traces.py; resolving it is the gate to HKL parity work.
- docs/fix_plan.md:461 — Next Actions start with “Stabilise scaling comparison tooling,” so this iteration focuses there.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/commands.txt — Historical SIGKILL repro; new evidence must supersede it with a clean run.
- scripts/validation/compare_scaling_traces.py:1 — Script must continue emitting markdown and metrics.json for audit; fixes must retain CLI semantics.
- docs/development/testing_strategy.md:35 — Device/dtype neutrality extends to tooling; avoid CPU-only assumptions.
- docs/bugs/verified_c_bugs.md:166 — φ carryover context; script needs to read both spec and c-parity traces faithfully.
- plans/active/cli-phi-parity-shim/plan.md:76 — Phase C5/D3 documentation depends on refreshed scaling outputs once the script works.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/instrumentation_audit.md:1 — Confirms `_enable_trace` guard; tooling changes must respect trace-only capture.
- docs/architecture/pytorch_design.md:80 — Vectorization narrative; avoid slipping back to scalar loops while patching tooling.
Verification Checklist:
- Confirm the repaired script exits 0 and produces summary + metrics files.
- Validate metrics.json `first_divergence` remains `I_before_scaling`.
- Ensure summary shows relative delta ≈ −2.086e-03 (current parity gap) for continuity.
- Make sure targeted pytest run passes on CPU; optionally include CUDA if available.
- Check plan + fix_plan updates include timestamp and artifact paths.
- Verify sha256.txt covers all generated artifacts (no omissions).
How-To Map:
1. `ts=$(date -u +%Y%m%dT%H%M%SZ)`; note this value in commands.txt for traceability.
2. `RUN_DIR=reports/2025-10-cli-flags/phase_l/scaling_validation/$ts` to scope outputs.
3. `mkdir -p "$RUN_DIR"` ensuring parent directories exist; verify with `ls "$RUN_DIR"`.
4. Append `git rev-parse HEAD` and `git status -sb` to `$RUN_DIR/commands.txt` for pre-work provenance.
5. Log runtime exports: echo `export KMP_DUPLICATE_LIB_OK=TRUE` and `export PYTHONPATH=src` into commands.txt.
6. Capture editable install metadata via `pip show nanobragg-torch >> "$RUN_DIR/commands.txt"` (or log failure if not installed).
7. Generate c-parity trace: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --device cpu --dtype float64 --out "$RUN_DIR/trace_py_scaling.log" | tee -a "$RUN_DIR/commands.txt"`.
8. Optionally run spec-mode trace to confirm divergence expectations: repeat Step 7 with `--phi-mode spec --out "$RUN_DIR/trace_py_scaling_spec.log"`.
9. Convert per-φ JSON: if harness supports `--dump-per-phi`, enable it so `$RUN_DIR/trace_py_scaling_per_phi.log/json` capture references.
10. Build env.json snapshot using a short python script capturing python version, OS, torch version, CUDA availability, git sha, and timestamp.
11. Inspect the trace file headers to ensure TRACE_PY labels align with script expectations (pre/post polar present exactly once).
12. Edit `scripts/validation/compare_scaling_traces.py`; focus on robust parsing (no `split()` assumptions beyond two columns), guard against `ValueError`, and ensure `I_before_scaling_pre_polar` mapping remains.
13. Add inline comments if new logic references C behavior; cite nanoBragg.c lines to satisfy CLAUDE Rule #11 when needed.
14. Run `python scripts/validation/compare_scaling_traces.py --help` and append output to commands.txt.
15. Execute the Do Now command referencing the new trace; tee stdout into commands.txt for audit.
16. Confirm `scaling_validation_summary.md`, `metrics.json`, `run_metadata.json` appear in RUN_DIR; list them in commands.txt.
17. Review summary content, ensuring Markdown tables render properly and note the absolute & relative deltas for I_before_scaling.
18. Check metrics.json structure: `tolerance_rel`, `first_divergence`, `num_divergent`, `factors` keys should populate.
19. Optionally run script with spec-mode trace to confirm it reports expected large divergence; record results if executed.
20. Run collect-only selectors:
    - `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_cli_scaling_phi0.py | tee -a "$RUN_DIR/commands.txt"`
    - `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_phi_carryover_mode.py | tee -a "$RUN_DIR/commands.txt"`
21. Execute targeted parity tests on CPU: `KMP_DUPLICATE_LIB_OK=TRUE pytest -xvs tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py | tee -a "$RUN_DIR/commands.txt"`.
22. If CUDA is available, optionally run `KMP_DUPLICATE_LIB_OK=TRUE pytest -xvs tests/test_phi_carryover_mode.py -k cuda` and record pass/skip.
23. Compute checksums: `(cd "$RUN_DIR" && shasum -a 256 * > sha256.txt)`; append file list + sha output to commands.txt.
24. Update `plans/active/cli-noise-pix0/plan.md` Phase M1 How/Why column with the new timestamp and tooling fix summary.
25. Add a detailed Attempt entry under `docs/fix_plan.md` CLI-FLAGS-003 noting the script repair, tests, artifacts, and residual ΔI_before_scaling.
26. Document any follow-up hypotheses (e.g., need to log 4×4×4 weights) at the bottom of `scaling_validation_summary.md` to guide Phase M2.
27. Record final `git status -sb` in commands.txt to show clean state after work.
28. Stage modified files and prepare for supervisor commit (galph handles final commit but staging should be ready).
29. Keep RUN_DIR tree intact; do not prune intermediate logs.
30. If additional diagnostics were run (spec trace, CUDA run), mention them in fix_plan Attempt to avoid losing context.
Pitfalls To Avoid:
- Do not revert `_enable_trace` guard; Phase M0 hygiene must persist.
- Avoid hard-coded `.cpu()` calls in tooling; maintain device neutrality.
- Do not overwrite previous report directories; new timestamp every run.
- No tolerance downgrades—stick with ≤1e-6 relative thresholds.
- Do not skip targeted pytest runs or the collect-only validation.
- Leave Protected Assets untouched (input.md, docs/index.md, loop.sh, supervisor.sh).
- Maintain ASCII-only edits; no Unicode or fancy formatting.
- Avoid introducing sleeps or long-running loops in scripts.
- Keep compare_scaling_traces.py backwards compatible with prior CLI options.
- Prefix every torch command with `KMP_DUPLICATE_LIB_OK=TRUE` to avoid MKL issues.
- Scope code edits to tooling/docs only; no physics changes this loop.
- Ensure commands.txt records every command chronologically; missing provenance blocks plan closure.
- Do not run full pytest suite; evidence gate forbids it.
- Guard against accidental deletion of c_trace_scaling.log; treat it as canonical C reference.
- Remember to update plan and fix_plan exactly once with clear timestamps.
Pointers:
- docs/fix_plan.md:461
- plans/active/cli-noise-pix0/plan.md:64
- scripts/validation/compare_scaling_traces.py:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/instrumentation_audit.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/commands.txt:1
- docs/development/testing_strategy.md:35
- docs/bugs/verified_c_bugs.md:166
- docs/architecture/pytorch_design.md:80
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1
Next Up: Once the tooling is stable, proceed to Phase M2 to chase the φ₀ F_latt drift and close the ≤1e-6 I_before_scaling parity gap.
Alternative: schedule Phase C5 documentation sync once Phase M2 evidence lands.
