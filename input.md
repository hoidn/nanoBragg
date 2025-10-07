Summary: Replace placeholder TRACE_PY scaling log generation with the live simulator output so Phase L2b evidence can proceed.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase L2b instrumentation)
Branch: feature/spec-based-2
Mapped tests: tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics (collect-only OK in evidence mode)
Mapped tests: tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_with_absorption (collect-only)
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/harness_run.log
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_stdout.txt (should capture live TRACE_PY once fixed)
Artifacts: reports/2025-10-cli-flags/phase_j/trace_c_scaling.log
Do Now: CLI-FLAGS-003 Phase L2b — update reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py to capture the simulator’s TRACE_PY stdout/stderr for pixel (685,1039), then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics`
If Blocked: Snapshot the failing harness attempt via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_audit/blocked_trace_py_scaling.log --device cpu --dtype float32` and log blockers in scaling_audit_summary.md before touching simulator code.
Priorities & Rationale:
- docs/fix_plan.md:448-467 identifies Phase L2b trace instrumentation as the gating task before normalization analysis.
- plans/active/cli-noise-pix0/plan.md Phase L2b notes TRACE_PY still prints `I_before_scaling NOT_EXTRACTED` and must emit real tensors.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log currently shows placeholders (`polar 0`, `I_pixel_final 0`).
- reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md documents the expectation to reuse live simulator output rather than harness constants.
- reports/2025-10-cli-flags/phase_j/trace_c_scaling.log lines 180-212 remain the C reference that the new PyTorch trace must mirror.
How-To Map:
- Modify trace_harness.py to spawn the CLI (`nanoBragg` or `PYTHONPATH=src python -m nanobrag_torch`) with `-trace_pixel 685 1039` and redirect stdout to trace_py_stdout.txt before post-processing.
- After capturing stdout, parse the TRACE_PY lines to rebuild trace_py_scaling.log verbatim (preserve ordering and precision).
- Refresh harness_run.log with command + env; update scaling_audit_summary.md with key deltas (polarization, capture_fraction, steps, I_before_scaling, I_pixel_final).
- Validate selectors with `pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics` before execution if new parametrisation is added.
- Once harness emits live numbers, diff against C via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_j/trace_c_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md`.
Pitfalls To Avoid:
- Do not regenerate trace lines from config constants; rely on simulator stdout so updates track future physics fixes.
- Keep harness evidence-only (no simulator code edits) unless a subsequent plan phase authorises changes.
- Respect Protected Assets: leave docs/index.md references untouched and avoid deleting listed files.
- Preserve device/dtype neutrality when invoking harness—surface `--device`/`--dtype` options instead of hardcoding CPU/float64.
- Do not expand scope into Phase L3 normalization fixes until live trace data is captured and logged.
- Ensure `KMP_DUPLICATE_LIB_OK=TRUE` is exported for every PyTorch invocation to avoid MKL crashes.
- Avoid `.item()` on tensors in any future simulator changes; trace collection should stay non-destructive.
Pointers:
- plans/active/cli-noise-pix0/plan.md (Phase L2b table)
- docs/fix_plan.md:448-520 (CLI-FLAGS-003 attempts + next actions)
- docs/development/testing_strategy.md §2 (parity evidence expectations)
- docs/development/c_to_pytorch_config_map.md (pivot and scaling parameter mapping)
- reports/2025-10-cli-flags/phase_l/scaling_audit/instrumentation_notes.md (harness assumptions)
Next Up: Phase L2c trace comparison once live PyTorch values are recorded.
