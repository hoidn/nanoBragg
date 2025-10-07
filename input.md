Summary: Patch TRACE_PY instrumentation so the supervisor command scaling factors match C and unblock Phase L2.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — Phase L2 scaling audit
Branch: feature/spec-based-2
Mapped tests:
- tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json
- reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md
- reports/2025-10-cli-flags/phase_l/scaling_audit/compare_scaling_traces.json
- reports/2025-10-cli-flags/phase_l/scaling_audit/attempt_history.md
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_stdout.txt
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_stderr.txt
- reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot.json
- reports/2025-10-cli-flags/phase_l/scaling_audit/diff_summary.md
- tests/test_trace_pixel.py (new regression test guarding TRACE_PY values)
- scripts/validation/compare_scaling_traces.py (promote helper if reused)
- reports/2025-10-cli-flags/phase_l/scaling_audit/capture_notes.md
Do Now: CLI-FLAGS-003 Phase L2b — After updating TRACE_PY instrumentation, run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics -v`
If Blocked: Capture stdout/stderr in reports/2025-10-cli-flags/phase_l/scaling_audit/attempt_failed.log, dump `git diff > reports/.../diff_on_blocker.patch`, append blocker summary to attempt_history.md, and halt for supervisor guidance.
Context:
- Attempt #55 delivered the C scaling trace; the PyTorch side still prints placeholder values.
- Attempt #56 (evidence-only) showed `TRACE_PY: polar 1` and `TRACE_PY: capture_fraction 1` regardless of physics.
- K3g regressions are resolved; Phase L is the remaining blocker for long-term Goal #1.
- Vectorization work (Goal #2) is paused until CLI parity is unlocked.
- Plan Phase L2a is [D]; Phase L2b and L2c remain [ ].
- Protected Assets policy remains in effect; modify only scoped files.
Success Criteria:
- TRACE_PY for pixel (slow=685, fast=1039) matches C trace within ≤1e-6 relative error for all logged factors.
- New regression test in tests/test_trace_pixel.py fails if TRACE_PY reverts to placeholders.
- Updated harness produces trace_py_scaling.log, env snapshot, stdout/stderr, and comparison JSON under reports/2025-10-cli-flags/phase_l/scaling_audit/.
- docs/fix_plan.md Attempt log updated with metrics, artifact links, and Phase L2b status change to [D].
- No new regressions in existing CLI scaling tests.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:95 sets explicit steps for Phase L2b (instrumentation, regression test, harness rerun).
- docs/fix_plan.md:460 captures the refreshed next actions; staying aligned prevents plan drift.
- docs/development/testing_strategy.md:68 mandates trace parity evidence before implementation fixes.
- docs/debugging/debugging.md:24 details the parallel trace comparison workflow driving this task.
- docs/architecture/pytorch_design.md:320 documents normalization order to mirror in TRACE_PY output.
- docs/development/c_to_pytorch_config_map.md:63 highlights detector/beam scaling interplay relevant to logged fields.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log is the numeric target for parity.
- reports/2025-10-cli-flags/phase_l/scaling_audit/instrumentation_notes.md lists required TRACE keys and units.
How-To Map:
- Step 1 — Review simulator trace path (src/nanobrag_torch/simulator.py:1100-1360) and note each placeholder value in notes.md.
- Step 2 — Identify where the real tensors live: polarization tensors from `_apply_polarization`, capture fractions from `_apply_detector_absorption`, and total steps from `OversampleController` / run context.
- Step 3 — Extend Simulator to stash these tensors in `self.debug_cache` (or similar) when `trace_pixel` is requested, ensuring no gradient-detaching operations outside the trace guard.
- Step 4 — In `_apply_debug_output`, read the cached tensors, compute scalar values with `.item()` only at print time, and format `TRACE_PY: key value` with `:.15g` precision.
- Step 5 — Include additional context lines (e.g., `TRACE_PY: sources`, `TRACE_PY: mosaic_domains`) if needed to disambiguate the steps product; keep naming consistent with C logs.
- Step 6 — Construct tests/test_trace_pixel.py with deterministic config (Na=36, Nb=47, Nc=29, oversample=1, nopolar=False) that uses `capsys` to capture TRACE_PY output and asserts equality against simulator internals.
- Step 7 — Parameterise the new test over device/dtype (cpu float32, cuda float32 when available) to enforce device neutrality; guard CUDA branch with `torch.cuda.is_available()`.
- Step 8 — Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics -v` and record results in attempt_history.md; rerun with `CUDA_VISIBLE_DEVICES=0` when GPU present.
- Step 9 — Update trace_harness.py to pass `trace_pixel=[685,1039]`, reuse CLI parsing for the supervisor parameters, and stream stdout/stderr into the dedicated files under reports/…
- Step 10 — Execute `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log --config supervisor --device cpu` and capture run metadata.
- Step 11 — Compare TRACE_C and TRACE_PY via a helper script that outputs compare_scaling_traces.json summarising absolute and relative deltas for each field.
- Step 12 — Summarise findings in notes.md (commands, devices, tolerances) and update docs/fix_plan.md Attempt log with the new evidence and outcomes.
Pitfalls To Avoid:
- No placeholder constants (polar=1, capture_fraction=1) may remain once instrumentation is complete.
- Do not detach tensors prematurely; keep gradients intact by printing only inside the trace guard.
- Avoid `.cpu()` conversions when storing debug state; handle tensors on their native device.
- Keep trace logic behind `if self.trace_pixel` to prevent runtime penalties in production runs.
- Do not bypass plan sequencing by skipping the regression test or comparison JSON.
- Respect Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md) and only add files inside reports/… or scripts/validation/…
- Ensure new test cleans up temporary files (use TemporaryDirectory) to keep loops hermetic.
- Record environment snapshots (torch, python, git SHA) in trace_py_env.json for reproducibility.
- Avoid running full pytest suite; stick to targeted selectors plus the new regression test.
- Confirm `KMP_DUPLICATE_LIB_OK=TRUE` is set in any harness/test before importing torch.
Pointers:
- docs/architecture/pytorch_design.md:320 — normalization field order reference.
- docs/development/c_to_pytorch_config_map.md:63 — scaling parameter parity checklist.
- docs/debugging/debugging.md:24 — mandatory parallel trace workflow.
- docs/development/testing_strategy.md:68 — evidence-first validation rule.
- plans/active/cli-noise-pix0/plan.md:95 — Phase L2b guidance.
- docs/fix_plan.md:460 — CLI-FLAGS-003 next actions refresh.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log — C trace baseline.
- reports/2025-10-cli-flags/phase_l/scaling_audit/instrumentation_notes.md — field descriptions.
- reports/2025-10-cli-flags/phase_i/supervisor_command/summary.json — original parity failure metrics for context.
- scripts/debug_pixel_trace.py — reference for existing trace formatting conventions.
Next Up:
- Phase L2c — Diff refreshed TRACE_PY against C trace, capture compare_scaling_traces.md, and identify any remaining divergent factor (expect none once instrumentation is fixed).
Environment Prep:
- Verify editable install with `pip install -e .`; record outcome in notes.md even if already satisfied.
- Export `NB_RUN_PARALLEL=1` only when running C parity helpers; leave unset for unit tests to avoid accidental skips.
- Set `NB_C_BIN=./golden_suite_generator/nanoBragg` before invoking comparison helpers so the harness targets the instrumented binary.
- Confirm CUDA availability via `python - <<'PY'` snippet and log result (available/unavailable) in notes.md prior to running GPU variant.
- Capture `python -m nanobrag_torch --version` (or equivalent) to note CLI entry point wiring.
Command Checklist:
- `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics -v` (primary regression test)
- `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log --config supervisor --device cpu`
- `python scripts/validation/compare_scaling_traces.py --c-log reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py-log reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_audit/compare_scaling_traces.json`
- `git status -sb` before and after code changes; paste summaries into notes.md for traceability.
Logging Requirements:
- Append attempt metadata to attempt_history.md (timestamp, device, dtype, commands, pass/fail, metrics).
- Store stdout/stderr separately to keep trace_py_scaling.log clean for diffing.
- Include env snapshot (python version, torch version, git SHA) in trace_py_env.json.
- Document any deviations (e.g., missing CUDA) in notes.md so future loops understand context.
- If compare_scaling_traces.py reports deltas >1e-6, list each offending key with numeric diff in diff_summary.md.
Quality Gates:
- Regression test must pass on CPU float32; mark CUDA variant optional but encouraged when hardware is present.
- compare_scaling_traces.json should report `status: pass`; if fail, halt and escalate rather than tweaking tolerances.
- New test should fail on purpose if TRACE_PY reverts to placeholder constants (validate by temporarily forcing polar to 1 during development).
- Input.md instructions must be followed sequentially; document any intentional deviations in notes.md.
