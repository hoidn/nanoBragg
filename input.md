Summary: Refresh TRACE_PY harness to capture real scaling factors for supervisor pixel.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase L2b)
Branch: feature/spec-based-2
Mapped tests: tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics (validated with --collect-only)
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/{trace_py_scaling.log,trace_py_env.json,notes.md}
Do Now: CLI-FLAGS-003 Phase L2b — refresh trace harness; run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --out trace_py_scaling.log --device cpu --dtype float32` then `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics -v`
If Blocked: Capture stdout/stderr from the harness run into `trace_py_stdout_cli.txt` and log the failure cause in `notes.md` with timestamp; do not patch simulator again—pause and notify galph in Attempts History.
Priorities & Rationale:
- docs/fix_plan.md:448-474 — current CLI-FLAGS-003 next actions demand a live TRACE_PY harness before normalization fixes.
- plans/active/cli-noise-pix0/plan.md:241-243 — Phase L2b/L2c guidance calls for replacing placeholder trace data and rerunning the comparison script.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log — shows placeholders; verifying replacement confirms progress.
- specs/spec-a-cli.md:1-120 — ensures CLI flag semantics (-nonoise, flux/beamsize) remain aligned while updating harness inputs.
- docs/debugging/debugging.md:1-120 — parallel trace SOP requires authentic logs for first-divergence analysis.
How-To Map:
- Fix harness: modify `trace_harness.py` so it instantiates `Simulator(..., debug_config={'trace_pixel': [685, 1039]})` and streams stdout into `trace_py_scaling.log`; prefer contextlib.redirect_stdout.
- Rerun harness: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --out trace_py_scaling.log --device cpu --dtype float32` (writes log + env snapshot); capture stderr separately if needed.
- Validate instrumentation: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics -v` (CPU/GPU parametrised); attach log to Attempts History.
- Prepare for comparison: once log is live, stage `trace_py_scaling.log`, `trace_py_env.json`, and update `notes.md` highlighting polar/omega/steps values.
Pitfalls To Avoid:
- Do not reintroduce manual TRACE_PY formatting; rely on simulator stdout to keep physics consistent.
- No `.cpu()` / `.numpy()` conversions when handling tensors; maintain device neutrality per runtime checklist.
- Keep Protected Assets intact (docs/index.md references); avoid moving files listed there.
- Do not rerun full pytest; stick to targeted selector above until code changes land.
- Avoid editing production physics while adjusting harness; this loop is evidence-only for CLI parity.
- Ensure harness uses supervisor flag set (beam_vector, flux, beamsize) to prevent automatic oversample changes.
- Capture environment metadata via existing JSON writer; do not introduce ad-hoc logging destinations.
- Maintain reproducibility: set `KMP_DUPLICATE_LIB_OK=TRUE` on every run interacting with torch.
- Archive outputs under the specified reports directory; no stray artifacts in repo root.
- Update Attempts History in docs/fix_plan.md after runs with metrics (steps, fluence, polar, I_before, final intensity).
Pointers:
- docs/fix_plan.md:448-461 — authoritative next steps for CLI-FLAGS-003.
- plans/active/cli-noise-pix0/plan.md:241-243 — detailed Phase L2 guidance.
- reports/2025-10-cli-flags/phase_l/scaling_audit/instrumentation_notes.md — harness expectations and required metadata snapshots.
- scripts/validation/compare_scaling_traces.py — ready for rerun once new TRACE_PY log exists.
- docs/development/testing_strategy.md:1-120 — reminder on targeted testing cadence and device checks.
Next Up:
- Rerun `scripts/validation/compare_scaling_traces.py` with refreshed logs to populate `scaling_audit_summary.md`.
- Outline polarization fix scope in simulator once first divergence is confirmed.
