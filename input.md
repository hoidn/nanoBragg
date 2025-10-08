Summary: Harden CLI-FLAGS-003 tricubic debug instrumentation before continuing Phase M scaling parity.
Mode: Parity
Focus: CLI-FLAGS-003 Phase M0 instrumentation hygiene
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only tests/test_cli_scaling_phi0.py
- pytest --collect-only tests/test_phi_carryover_mode.py
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/instrumentation_audit.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/commands.txt
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/env.json
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling_spec.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling_per_phi.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/sha256.txt
Do Now: CLI-FLAGS-003 Phase M0a–M0c instrumentation hygiene; run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling.log --device cpu --dtype float64`, guard `_last_tricubic_neighborhood`, verify device/dtype neutrality, and update plan plus fix_plan with the new findings.
If Blocked: If the harness or simulator crashes, capture stdout/stderr plus traceback into instrumentation_audit.md, note the failing command and exit code in commands.txt, stop before production edits, and alert supervisor with the log path once documented.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:88-118 — Phase M0 is now gating Phase M1; must close to resume scaling parity.
- docs/development/testing_strategy.md:35-120 — Device/dtype discipline applies even to debug instrumentation.
- docs/bugs/verified_c_bugs.md:166-204 — Parity shim context; instrumentation must respect spec mode defaults.
- docs/fix_plan.md:451-520 — Ledger next actions now include instrumentation hygiene Attempt logging.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py — Harness API controlling trace capture.
- specs/spec-a-core.md:200-320 — Tricubic interpolation contract to keep intact.
- docs/architecture/pytorch_design.md:1-120 — Vectorization/branching guidance relevant to guard placement.
- plans/active/cli-phi-parity-shim/plan.md:1-160 — Shim API ensures spec vs c-parity toggles remain explicit.
- docs/development/pytorch_runtime_checklist.md:1-180 — Debug code must still pass runtime guardrails.
- reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023140Z/summary.md — Existing trace baseline for comparison.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/manual_summary.md — Last metrics showing 0.2086% drift.
How-To Map:
- Step 1: Generate UTC timestamp `ts=$(date -u +%Y%m%dT%H%M%SZ)` and make directory `reports/2025-10-cli-flags/phase_l/scaling_validation/$ts` with `mkdir -p`.
- Step 2: Seed instrumentation_audit.md with heading, objective, and checklist referencing plan IDs.
- Step 3: Log initial git state by running `git status --short` and `git rev-parse HEAD`; append outputs to commands.txt.
- Step 4: Export env vars `export KMP_DUPLICATE_LIB_OK=TRUE` and `export PYTHONPATH=src`; record both lines in commands.txt.
- Step 5: Confirm editable install by noting `pip show nanobragg-torch` or `pip list | grep nanobragg`; jot the command/result in commands.txt.
- Step 6: Validate pytest selectors with `pytest --collect-only tests/test_cli_scaling_phi0.py`; append command and excerpt of collection output to commands.txt.
- Step 7: Repeat collection for `pytest --collect-only tests/test_phi_carryover_mode.py`; capture runtime and exit status.
- Step 8: Execute trace harness for c-parity per Do Now command, redirecting stdout to trace_py_scaling.log and capturing stderr separately if emitted.
- Step 9: Immediately re-run harness with `--phi-mode spec` writing to trace_py_scaling_spec.log to ensure instrumentation stays opt-in.
- Step 10: Optionally run harness with `--dtype float32` for parity with production defaults; document any differences.
- Step 11: Inspect trace logs for presence of `TRACE_PY_TRICUBIC_*` lines, noting which mode emitted them in instrumentation_audit.md.
- Step 12: Drop into a Python REPL (e.g., `python - <<'PY'`) to query simulator.crystal._last_tricubic_neighborhood after a non-debug run; confirm it is falsy or cleared.
- Step 13: If guard adjustments are needed, edit simulator/crystal accordingly, ensuring changes stay behind debug checks; describe modifications in audit file.
- Step 14: Re-run Steps 6–9 after edits to verify no regressions introduced by the guard logic.
- Step 15: For CUDA coverage, if available, execute harness with `--device cuda --dtype float32` and confirm no device mismatch occurs; log results.
- Step 16: Collect environment metadata (python version, torch version, CUDA availability, git SHA, timestamp) into env.json via a short Python script; cite the script in commands.txt.
- Step 17: Compute SHA256 checksums across produced artifacts using `shasum -a 256 *.log *.md *.json > sha256.txt`; store command and output snippet.
- Step 18: Summarize findings in instrumentation_audit.md including action items, whether `_last_tricubic_neighborhood` is scoped, device/dtype observations, and any follow-ups.
- Step 19: Update plans/active/cli-noise-pix0/plan.md to flip M0a/M0b/M0c states as appropriate with brief inline notes referencing $ts.
- Step 20: Append docs/fix_plan.md Attempt describing the instrumentation hygiene work, linking to the new timestamp directory and noting pass/fail status for each M0 subtask.
- Step 21: Stage modifications to plan/fix_plan (and code if changed) without committing yet; verify `git diff` shows only intended files.
- Step 22: Review logs to confirm spec mode traces remain free of tricubic dumps; add explicit statement to audit file.
- Step 23: If instrumentation introduces new CLI options or debug flags, document them in commands.txt and mention whether scripts need updates.
- Step 24: Before ending loop, ensure commands.txt includes reproducible sequences for CPU and CUDA runs plus SHA output lines.
- Step 25: Backfill instrumentation_audit.md with a short risk assessment (memory retention, gradient graph impact) and mitigation notes.
Evidence Targets:
- TRACE_PY logs showing tricubic grid present only in c-parity debug runs.
- Confirmation snippet demonstrating `_last_tricubic_neighborhood` absence during production runs.
- Device/dtype matrix summarizing CPU float64, CPU float32, and CUDA float32 outcomes.
- SHA256 manifest referencing all generated artifacts for reproducibility.
- Plan checklist snippet proving M0 tasks updated with timestamp.
Pitfalls To Avoid:
- Leaving `_last_tricubic_neighborhood` populated after production runs; guard or clear before return.
- Creating CPU-only tensors inside simulator trace path during CUDA runs; use caller device/dtype.
- Reordering or deleting existing TRACE_PY lines needed for diffing against C.
- Introducing Python loops in hot interpolation paths instead of restricting them to trace-only contexts.
- Forgetting to restore `self.crystal.interpolate` back to its saved value on every path.
- Editing Protected Assets listed in docs/index.md beyond necessary plan fixes.
- Skipping SHA256 generation; parity audits rely on checksum history.
- Omitting commands from commands.txt; future repro depends on full command trail.
- Allowing trace-only instrumentation to execute during nb-compare or supervisor runs.
- Requesting GPU runs without checking torch.cuda.is_available(); always note availability in env.json.
Pointers:
- plans/active/cli-noise-pix0/plan.md:88-118 — Phase M0 instrumentation hygiene tasks.
- docs/fix_plan.md:451-520 — CLI-FLAGS-003 ledger with new instrumentation next action.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1-210 — Harness CLI and trace flow.
- docs/development/testing_strategy.md:35-120 — Device/dtype enforcement guidance.
- docs/bugs/verified_c_bugs.md:166-204 — φ carryover bug documentation.
- docs/architecture/pytorch_design.md:1-120 — Vectorization considerations for guard placement.
- specs/spec-a-core.md:200-320 — Tricubic interpolation contract reference.
- plans/active/cli-phi-parity-shim/plan.md:1-160 — Shim behavior for spec vs c-parity.
- docs/development/pytorch_runtime_checklist.md:1-180 — Runtime guardrails to cite in audit.
- reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023140Z/summary.md — Prior trace comparison baseline.
Context Reminders:
- Attempt #142 introduced the tricubic instrumentation; verify its behavior matches assumptions recorded there.
- Prior scaling traces showed 0.2086% I_before_scaling drift; ensure new guard does not change numeric results.
- Ensure new artifacts stay within reports/ timestamped folder to keep git clean.
Next Up:
- Phase M1 HKL lookup parity rerun using refreshed harness after instrumentation hygiene completes.
Checklist Updates:
- Mark plan tasks M0a, M0b, M0c with detailed notes referencing new timestamp once evidence collected.
- Add docs/fix_plan.md Attempt entry (#143 if next) summarizing instrumentation guard findings and linking artifacts.
- Record whether CUDA harness executed; if skipped, justify in instrumentation_audit.md and plan next attempt.
- Note any required follow-up code review (e.g., if guard changes touch simulator) so supervisor can schedule review loop.
Documentation Notes:
- Update instrumentation_audit.md with cross-links to docs/development/pytorch_runtime_checklist.md and specs/spec-a-core.md citations.
- Mention in audit whether additional trace variables are desired for Phase M1 (so supervisor can plan next loop).
- If guard logic reveals new spec gap, note it for potential specs/spec-a update (do not edit spec yet).
Communication:
- Post instrumentation summary and artifact path in docs/fix_plan.md Attempts log plus galph_memory on next supervisor loop.
- Flag any unexpected performance impact so we can adjust Phase M benchmarks accordingly.
