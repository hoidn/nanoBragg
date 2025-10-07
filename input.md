Summary: Capture a PyTorch scaling trace for the supervisor command so Phase L normalization parity can proceed without touching production code.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — Phase L2 scaling audit
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling.py::test_f_latt_square_matches_c (selector check only)
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log — primary TRACE_PY output
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json — environment snapshot
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md — timestamped command log
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_stdout.txt — stdout capture
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_stderr.txt — stderr capture
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/attempt_history.md — per-run summary
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot.json — CLI arg/param dump
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/readme.md — optional overview once trace succeeds
Do Now: CLI-FLAGS-003 Phase L2b — KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log --config supervisor
If Blocked: If the harness raises during config or execution, capture stdout/stderr plus traceback into reports/2025-10-cli-flags/phase_l/scaling_audit/attempt_failed.log, append a blocker note to attempt_history.md, and pause for supervisor guidance.
Context: Phase L2a (C trace) is complete and logged as Attempt #55; L2b is now the gating deliverable for long-term Goal #1.
Context: Evidence-only loop — no production code edits, no nb-compare, no full pytest runs beyond selector validation.
Context: Maintain Protected Assets policy; all new files must stay under reports/2025-10-cli-flags/phase_l/scaling_audit/.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md Phase L2 marks L2a [D]; L2b must deliver the PyTorch trace before diffing.
  context: Updating the plan to [D] for L2b depends on producing trace_py_scaling.log with matching fields.
- docs/fix_plan.md#cli-flags-003 lists L2b/L2c as next actions after Attempt #55.
  context: Staying aligned with the fix plan ledger keeps long-term Goal #1 on schedule.
- docs/architecture/pytorch_design.md §§3.5–3.6 define normalization order (steps → omega → absorption → r_e² → fluence).
  context: Recording variables in that order simplifies parity comparisons with the C trace.
- docs/development/testing_strategy.md §2.5 mandates trace-driven debugging before implementation work.
  context: Evidence-first approach prevents repeating the earlier F_latt misdiagnosis.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log already captures the C-side values for pixel (685,1039).
  context: Mirroring these fields enables immediate Phase L2c diffing without additional C instrumentation.
- Phase J highlighted I_before_scaling as the first divergent factor.
  context: Fresh Py traces confirm whether normalization drift remains after K3g fixes.
- Long-term Goal #2 (vectorization) remains blocked until CLI parity succeeds.
  context: Completing L2b removes a critical dependency before redirecting effort toward vectorization.

How-To Map:
- Step 0 — Verify editable install: run `pip install -e .` (if needed) and log the command plus outcome in notes.md.
  detail: even "Requirement already satisfied" should be recorded for future provenance.
- Step 1 — Review instrumentation guidance: read instrumentation_notes.md and list expected TRACE keys in notes.md.
  detail: include I_before_scaling, omega_pixel_sr, capture_fraction, polarization, r_e_sqr, fluence, steps, and final intensity.
- Step 2 — Prepare harness skeleton at reports/.../trace_harness.py.
  detail: add argparse flags for `--pixel`, `--out`, `--config`, `--device`, and `--dtype` (default float32).
- Step 3 — Load supervisor parameters: import CLI parser with `PYTHONPATH=src`; recreate the command from reports/.../supervisor_command/README.md.
  detail: store parameters in config_snapshot.json for reproducibility.
- Step 4 — Instantiate Detector/Crystal/Beam without noise.
  detail: ensure `-nonoise` is honoured so intensity values match the noiseless C run.
- Step 5 — Run simulator to obtain intensities for full detector.
  detail: keep tensors on selected device; avoid `.cpu()` conversions until logging stage.
- Step 6 — Extract scaling quantities for pixel (slow=685, fast=1039).
  detail: note exact indexing used (e.g., `[685, 1039]`) for each tensor in notes.md.
- Step 7 — Format TRACE lines as `TRACE_PY: key value` with `:.15g` precision and consistent key casing.
  detail: store units in comments if helpful but keep TRACE line pure numeric for diffing.
- Step 8 — Write trace to trace_py_scaling.log and capture stdout/stderr to dedicated files.
  detail: use shell redirection or Python logging to avoid mixing outputs.
- Step 9 — Capture environment via inline Python snippet (sys.version, torch version, cuda availability, git SHA).
  detail: include `platform.platform()` and request device info via torch to aid future comparisons.
- Step 10 — Document workflow in notes.md with ISO timestamps and command list; summarize outcomes per command.
  detail: include elapsed time if easily measured for transparency.
- Step 11 — Update attempt_history.md with the attempt number, artifacts produced, and status (success/blocked).
  detail: note whether all TRACE keys were emitted and any observed anomalies.
- Step 12 — Validate selector only: `pytest --collect-only -q tests/test_cli_scaling.py::test_f_latt_square_matches_c`, append console output to notes.md.
  detail: confirm test collection count matches historical values to catch import regressions.
- Step 13 — Manually review trace_py_scaling.log versus the C trace for sanity (e.g., steps=10, fluence≈1e24).
  detail: record any deviations >5% in notes.md to accelerate Phase L2c diffing.
- Step 14 — Ensure git tree remains clean except for new report artifacts.
  detail: run `git status --short` and list expected files in notes.md.

Pitfalls To Avoid:
- Do not modify src/nanobrag_torch or docs outside the scoped report directory.
  note: any accidental edit should be reverted immediately to keep evidence isolated.
- Avoid `.item()` on tensors that might ever require gradients; prefer `.detach()` before conversion.
  note: this preserves differentiability expectations recorded in docs/architecture/pytorch_design.md.
- Keep device/dtype neutrality; allow optional CUDA execution later by honouring `--device` flag.
  note: default to CPU but log fallback behaviour if CUDA requested and unavailable.
- Obey Protected Assets rule (docs/index.md); do not move or delete loop.sh, supervisor.sh, input.md, etc.
  note: Protected Assets violations are plan blockers.
- No nb-compare or full pytest runs; evidence gate restricts this loop to instrumentation and selector checks.
  note: Phase L4 will handle full parity reruns once scaling aligns.
- Set KMP_DUPLICATE_LIB_OK=TRUE for every torch process to avoid MKL duplication errors.
  note: log env var usage in notes.md so future loops can replicate the environment.
- Include `-nonoise` and `-pix0_vector_mm` when constructing the CLI config.
  note: missing either flag invalidates parity with the supervisor command.
- Preserve TRACE formatting exactly; deviations complicate planned compare_scaling_traces tooling.
  note: use lowercase snake_case keys matching the C log.
- Handle missing CUDA gracefully by falling back to CPU with a logged warning.
  note: capture warning in trace_py_stderr.txt for transparency.
- Keep artifacts within reports/2025-10-cli-flags/phase_l/scaling_audit/ to maintain plan cross-reference integrity.
  note: organize additional files in subdirectories if necessary but stay under this root.

Pointers:
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log — authoritative C reference trace.
  usage: match each TRACE_PY key against these values during Phase L2c.
- reports/2025-10-cli-flags/phase_l/scaling_audit/instrumentation_notes.md — expected fields and precision.
  usage: replicate formatting guidance before running the harness.
- plans/active/cli-noise-pix0/plan.md — Phase L2 table updated this loop.
  usage: mark L2b [D] and add Attempt reference once artifacts exist.
- docs/fix_plan.md — Next Actions list now targets L2b/L2c.
  usage: update Attempts history after trace capture to keep ledger synchronized.
- docs/development/testing_strategy.md — parity-first workflow and environment requirements.
  usage: cite §2.5 in notes.md to justify evidence-only cadence.
- docs/architecture/pytorch_design.md — normalization order and scaling semantics.
  usage: reference section numbers when annotating future scaling_audit_summary.md.
- src/nanobrag_torch/simulator.py — source for variables such as normalized_intensity and self.fluence.
  usage: confirm attribute names before accessing them in the harness.
- reports/2025-10-cli-flags/phase_i/supervisor_command/README.md — canonical parameter list.
  usage: copy parameter values into config_snapshot.json verbatim.
- scripts/validation/analyze_scaling.py — prior art for factor comparisons.
  usage: reuse parsing patterns when building compare_scaling_traces.py.
- docs/debugging/debugging.md — reinforces TRACE schema expectations.
  usage: follow SOP to capture first divergence precisely.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/trace_py_after.log — example TRACE formatting.
  usage: mimic spacing and precision for consistency.

Reference Reminders:
- Attempt #55 already archived C trace metrics; Py trace must reference the same pixel and configuration.
- Store command history chronologically in notes.md with ISO timestamps for auditability.
- Capture git SHA via `git rev-parse HEAD` in config_snapshot.json to tag evidence to a commit.
- Record any optional flags (device, dtype) used during harness execution in attempt_history.md.
- Leave TODO placeholder in readme.md if summary pending; mark it complete when Phase L2c closes.

Next Up: Phase L2c comparison (build compare_scaling_traces.py and summarize deltas) once the PyTorch scaling trace is archived.
