Summary: Capture post-unit-fix pix0 traces so Phase K consumes fresh geometry evidence before any new code.
Phase: Evidence
Focus: CLI-FLAGS-003 Phase H5c trace refresh
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.log
Artifacts: reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.stdout
Artifacts: reports/2025-10-cli-flags/phase_h5/parity_summary.md
Do Now: CLI-FLAGS-003 Phase H5c — Capture post-unit-fix trace; run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.log`
If Blocked: Log the failure (command + stderr) to reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/attempt_log.md and halt for supervisor guidance.

Timeline:
01. Confirm `NB_C_BIN=./golden_suite_generator/nanoBragg` remains exported in the shell; note it in attempt log.
02. Ensure editable install still active; no reinstall needed unless torch import fails.
03. Create `reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/` before running harness.
04. Execute the Do Now trace harness; tee stdout to trace_py.stdout for later diffing.
05. Immediately copy `trace_py.log` to a scratch diff view against the 2025-10-22 baseline to spot unit-fix deltas.
06. Compute Δpix0, ΔFbeam, ΔSbeam manually (spreadsheet or python) and jot them into attempt log.
07. Verify the trace still reports the corrected `incident_vec` and rotated reciprocal vectors; flag any regressions.
08. Update `reports/2025-10-cli-flags/phase_h5/parity_summary.md` with the new numeric deltas and tolerance checks.
09. Note in the summary whether `F_latt` ratios now fall inside 1e-3; this informs Phase K2 readiness.
10. Stage screenshots or diff snippets only if values look suspicious; otherwise keep artifacts textual.
11. Append Attempt #35 to docs/fix_plan.md with metrics, deltas, and artifact paths.
12. Mark H5c as done in plans/active/cli-noise-pix0/plan.md once evidence is committed.
13. Leave a short README stub in the new trace directory summarising the command, git hash, and environment variables.
14. Double-check no new binary files (e.g., .npy) were produced—cleanup immediately if so.
15. Signal completion in Attempts History and pause before touching Phase K2 tasks.
16. Re-run the harness if stdout shows missing TRACE_PY lines; stale caches can drop signals.
17. Capture a quick checksum (`shasum`) of trace_py.log and add it to the attempt log for reproducibility.
18. Note current git commit (`git rev-parse HEAD`) inside the trace README.
19. Record wall-clock runtime of the harness; large drifts may hint at hidden device switches.
20. Verify locks on reports directory (no leftover write permissions issues) before proceeding.
21. Snapshot `env | sort` into the attempt log to document environment variables used.
22. After editing docs, re-open them to confirm UTF-8 encoding only—no stray BOM characters.
23. Stage files incrementally and run `git diff --cached` to ensure only evidence files appear.
24. Draft the docs/fix_plan attempt entry in a scratch buffer before committing to avoid typos.
25. Re-read the updated plan row to make sure guidance still matches the recorded artifacts.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:127 keeps H5c open; new traces are prerequisite for K2/K3.
- docs/fix_plan.md:470-517 demands refreshed pix0 evidence plus scaling reruns before normalization continues.
- reports/2025-10-cli-flags/phase_h5/parity_summary.md:6-18 now warns that current metrics predate Attempt #33.
- specs/spec-a-core.md:70-120 mandates <5e-5 m pix0 tolerance; we must document compliance.

How-To Map:
- Export `KMP_DUPLICATE_LIB_OK=TRUE` for every python invocation; without it the harness may trip MKL.
- Run the Do Now command from repo root so relative paths resolve; capture stdout with `tee` to keep a textual artifact.
- Use `python -m filecmp` or `diff -u` to compare new trace against `reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log`; record key differences.
- Update `parity_summary.md` by replacing the dated metrics table with the new numbers, noting pass/fail for pix0, F/S beams, and F_latt.
- In docs/fix_plan.md, add Attempt #35 under CLI-FLAGS-003 with metrics (Δpix0, ΔFbeam, ΔSbeam, F_latt ratio) plus artifact references.
- Stage only report/doc updates; leave git tree clean except for these evidence files.

Trace Checklist:
- pix0_vector_meters (three components) — confirm Δ < 5e-5 m vs C trace.
- Fbeam/Sbeam scalars — ensure conversion now matches C within tolerance.
- hkl_frac triplet — verify rounding to (2,2,-13) persists.
- F_latt_a/b/c and product — expect close agreement with C once K1 fix in place.
- omega_pixel_sr and polar — note values but defer detailed analysis to Phase K2.

Pitfalls To Avoid:
- Do not rerun C trace; existing 2025-10-22 artifacts remain the comparator for this loop.
- Skip pytest/nb-compare entirely—Evidence gate forbids test execution.
- Resist tweaking simulator code; today is documentation + trace capture only.
- Avoid creating new directories outside `reports/2025-10-cli-flags/phase_h5/`.
- Keep device/dtype neutral commentary; trace harness already respects configs.
- Protect docs/index.md and other protected assets per CLAUDE.md instructions.
- Document every command in attempt log to maintain reproducibility.
- If CUDA warms up unexpectedly, note it but do not debug—you’re on CPU path here.
- Leave NB_RUN_PARALLEL unset so parity pytest stays skipped.
- Don’t forget to commit/push the updated reports; supervisor automation expects clean git after run.

Data Notes:
- Baseline C trace: reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/with_override.log (use for diffing).
- Previous PyTorch trace: reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log (contains pre-unit-fix pix0 error).
- Attempt log template: reports/2025-10-cli-flags/phase_h5/py_traces/attempt_log_template.md (copy if blank).
- Target tolerances: pix0 < 5e-5 m, F_latt ratio within 1e-3, h/k/l residuals < 1e-6.
- Post-run checklist: update plan, fix_plan, parity_summary, and artifact README.

Command Log Template:
cmd01: export NB_C_BIN=./golden_suite_generator/nanoBragg
cmd02: export KMP_DUPLICATE_LIB_OK=TRUE
cmd03: mkdir -p reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24
cmd04: PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.log
cmd05: tee reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.stdout
cmd06: diff -u reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/with_override.log reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.log
cmd07: python reports/2025-10-cli-flags/phase_j/analyze_scaling.py --py reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.log --c reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/with_override.log --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/quick_ratio.md
cmd08: git status --short
cmd09: git add reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/*.log reports/2025-10-cli-flags/phase_h5/parity_summary.md docs/fix_plan.md plans/active/cli-noise-pix0/plan.md
cmd10: git commit -m "CLI-FLAGS-003 H5c trace refresh"

Post-Run Questions:
- Did Δpix0 fall below 5e-5 m on all components?
- Are F_latt ratios now within 1e-3 of C?
- Did h,k,l fractional differences stay under 1e-6?
- Any anomalies in omega or polar that require Phase K follow-up?

Telemetry Checklist:
log01: Harness wall-clock runtime (seconds).
log02: SHA of trace_py.log (shasum -a 256).
log03: Git commit hash recorded in attempt log.
log04: Environment snapshot (`env | sort > ...`).
log05: Notes on CPU vs GPU usage (should remain CPU).


Pointers:
- plans/active/cli-noise-pix0/plan.md:120-133
- docs/fix_plan.md:470-517
- reports/2025-10-cli-flags/phase_h5/parity_summary.md:6-18
- specs/spec-a-core.md:70-120

Next Up: Phase K2 scaling-chain refresh after H5c evidence lands (stay on this focus until supervisor review).
