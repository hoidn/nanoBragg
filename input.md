Summary: Update the pix0 trace harness so PyTorch emits SAMPLE-pivot TRACE_PY lines that mirror the new C instrumentation, proving whether the remaining Δpix0 is real or just a stale harness artifact.
Phase: Implementation
Focus: CLI-FLAGS-003 — Phase H6b (PyTorch pix0 trace harness)
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log; reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.stderr; reports/2025-10-cli-flags/phase_h6/py_trace/env_snapshot.txt; reports/2025-10-cli-flags/phase_h6/py_trace/git_context.txt
Do Now: CLI-FLAGS-003 / Phase H6b — instrument the Py trace harness, then run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log 2> reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.stderr`
If Blocked: If the harness still imports the site-packages build or exits before printing TRACE_PY, capture the failing command and `PYTHONPATH=src python -c "import nanobrag_torch, pathlib; print(nanobrag_torch.__file__); print(pathlib.Path().resolve())"` to reports/2025-10-cli-flags/phase_h6/py_trace/attempts.md, then pause.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:130 — Phase H6b explicitly calls for a SAMPLE-pivot TRACE_PY log under phase_h6; no Py trace artifacts exist yet.
- docs/fix_plan.md:448 — Attempt #35 documents the 1.14 mm ΔF; Next Actions now insist on editable imports and proper pivot selection before revisiting scaling.
- reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log:1 — Provides the exact TRACE_C ordering/precision we must mirror for a meaningful diff.
- docs/architecture/detector.md:107 — Pivot precedence table shows custom detector vectors imply SAMPLE pivot regardless of -distance, matching the C trace observation.
How-To Map:
1. Edit reports/2025-10-cli-flags/phase_h/trace_harness.py: remove the hard-coded `DetectorPivot.BEAM`, let DetectorConfig choose SAMPLE, and keep beam-center inputs in millimetres.
2. Monkey-patch or wrap Detector._calculate_pix0_vector inside the harness so, after calling the real method, it prints TRACE_PY lines matching the C log (detector_convention, angles, beam_center_m, Fclose/Sclose/close_distance/ratio/distance, term_fast/slow/close, pix0 before/after rotations, post-rotation basis vectors).
3. Run the Do Now command (PYTHONPATH=src, KMP_DUPLICATE_LIB_OK=TRUE). Capture stdout/stderr to the designated files; the STDERR should include the `# Tracing pixel …` banner for trace provenance.
4. Record reproducibility metadata: `env | sort > env_snapshot.txt`, `git rev-parse HEAD > git_context.txt`, and optional SHA256 of the log.
5. After verifying TRACE_PY alignment, append a short note to reports/2025-10-cli-flags/phase_h5/parity_summary.md summarizing whether Δpix0 persists.
Pitfalls To Avoid:
- Leaving `detector_pivot=DetectorPivot.BEAM`; C is clearly using SAMPLE here.
- Running without `PYTHONPATH=src` and accidentally exercising the stale site-package build.
- Forgetting to print TRACE_PY with `.15g` precision and identical token names.
- Omitting env/git context alongside the new log (breaks reproducibility expectations).
- Accidentally editing core simulator/detector code instead of monkey-patching via the harness.
- Overwriting the existing C trace artifacts in reports/2025-10-cli-flags/phase_h6/c_trace/.
- Running pytest (Evidence phase guard) — this loop is trace-only.
- Dropping the stderr log; we need both stdout and stderr for diffing/timestamps.
- Skipping `Detector.apply_custom_vectors` inputs (beam_vector, pix0_override) that keep parity with the supervisor command.
Pointers:
- plans/active/cli-noise-pix0/plan.md:130
- docs/fix_plan.md:448
- reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log:1
- reports/2025-10-cli-flags/phase_h/trace_harness.py:1
- docs/architecture/detector.md:107
- docs/development/testing_strategy.md:51
Next Up: Phase H6c — diff C/Py traces and document the first divergence once the new TRACE_PY lands.
