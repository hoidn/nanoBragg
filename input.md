Summary: Instrument the φ=0 trace to emit raw + normalized spindle-axis data so CLI-FLAGS-003 Phase L3g can lock hypotheses before simulator edits.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase L3g spindle normalization evidence
Branch: feature/spec-based-2
Mapped tests: tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics (collect-only)
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log; reports/2025-10-cli-flags/phase_l/rot_vector/spindle_audit.log; reports/2025-10-cli-flags/phase_l/rot_vector/volume_probe.md; reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md; docs/fix_plan.md (CLI-FLAGS-003 attempt update)
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics
If Blocked: Capture failing command + traceback to reports/2025-10-cli-flags/phase_l/rot_vector/blocked.log, note the issue in docs/fix_plan.md Attempts (CLI-FLAGS-003) with the artifact path, and stop.
Priorities & Rationale:
- specs/spec-a-cli.md:20 — CLI binding requires honoring -spindle_axis exactly; instrumentation must confirm the runtime vector before changes.
- arch.md:170 — Spindle-axis contract expects unit vectors; need evidence before adjusting normalization.
- docs/debugging/debugging.md:15 — Parallel trace SOP obligates refreshed TRACE_PY before touching production code.
- docs/development/testing_strategy.md:184 — Rotation/mosaic sequencing defines which tensors to log.
- docs/fix_plan.md:456 — Next Actions now call for spindle instrumentation and doc sync; we must deliver artifacts to close L3g.
- plans/active/cli-noise-pix0/plan.md:265 — Phase L3 checklist marks L3g [P]; spindle-axis evidence is the remaining blocker.
How-To Map:
- Prep:
  - export KMP_DUPLICATE_LIB_OK=TRUE
  - export PYTHONPATH=src
  - sha256sum A.mat scaled.hkl > reports/2025-10-cli-flags/phase_l/rot_vector/input_files.sha256
  - git rev-parse HEAD >> reports/2025-10-cli-flags/phase_l/rot_vector/input_files.sha256
  - date -Iseconds >> reports/2025-10-cli-flags/phase_l/rot_vector/input_files.sha256
- Step 1 (guard):
  - pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics | tee reports/2025-10-cli-flags/phase_l/rot_vector/test_collect.log
- Step 2 (instrumentation):
  - Extend reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py (or the TRACE_PY hooks it imports) to emit both the raw spindle axis from CLI config and the normalized axis used by Crystal/Simulator. Follow existing TRACE_PY naming (e.g., "TRACE_PY: spindle_axis_raw" / "TRACE_PY: spindle_axis_norm") and guard behind the trace flag so production runs stay untouched.
  - If simulator changes are unavoidable, keep them under debug branches only and cite the exact nanoBragg.c lines being mirrored (C logs spindle axis in the trace).
- Step 3 (refresh trace):
  - PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
      --pixel 685 1039 --config supervisor --device cpu --dtype float32 \
      --out reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log \
      | tee reports/2025-10-cli-flags/phase_l/rot_vector/trace_run.log
  - Ensure the new TRACE_PY lines appear and the run reports 40 TRACE_PY + 10 TRACE_PY_PHI entries.
- Step 4 (spindle audit):
  - Update reports/2025-10-cli-flags/phase_l/rot_vector/spindle_probe.py (or add logic) to parse the new TRACE_PY lines alongside `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`.
  - Generate reports/2025-10-cli-flags/phase_l/rot_vector/spindle_audit.log summarizing raw vs normalized vectors, norms, Δ(norm), and tolerance check (≤5e-4).
- Step 5 (volume refresh):
  - Recompute V_formula and V_actual for both implementations using the updated trace data; append the float32 table and a float64 rerun (repeat Step 3 with --dtype float64) to reports/2025-10-cli-flags/phase_l/rot_vector/volume_probe.md.
- Step 6 (analysis & ledger):
  - Append a dated section to reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md capturing the spindle results, volume deltas, dtype/device coverage, and updated hypothesis ranking.
  - Update docs/fix_plan.md Attempts (CLI-FLAGS-003) with metrics, artifacts, and the new tolerance verdict; mark hypothesis status.
  - Edit plans/active/cli-noise-pix0/plan.md Phase L3 to flip L3g to [D] if the evidence satisfies the exit criteria.
- Step 7 (optional CUDA sweep):
  - If `torch.cuda.is_available()`, rerun Step 3 with --device cuda --dtype float32 and log the device/dtype in spindle_audit.log; note results in the fix-plan attempt.
Pitfalls To Avoid:
- Skipping KMP_DUPLICATE_LIB_OK leads to MKL crashes; set it first.
- Emitting TRACE_PY lines outside the trace guard risks polluting production logs—keep instrumentation conditional.
- Forgetting to record device/dtype in spindle_audit.log weakens the evidence; print them explicitly.
- Overwriting existing logs without archiving loses historical context; append or version filenames.
- Touching simulator physics while still in evidence mode violates the doc-first mandate; focus on instrumentation only.
- Leaving docs/fix_plan.md and the plan un-updated after collecting evidence reopens the loop; sync them before ending.
- Allowing pytest collect to fail without investigation will stall downstream work; fix import issues immediately.
- Writing artifacts outside reports/2025-10-cli-flags/phase_l/rot_vector/ scatters the audit trail; keep everything in the same folder tree.
- Ignoring float64 rerun misses precision regressions; capture at least one double-precision sweep if feasible.
- Neglecting to cite the exact nanoBragg.c line numbers in new TRACE_PY comments makes parity review harder; annotate the instrumentation.
Pointers:
- specs/spec-a-cli.md:20 — CLI authority on -spindle_axis semantics.
- arch.md:170 — Spindle-axis normalization expectations.
- docs/debugging/debugging.md:15 — Required trace workflow.
- docs/development/testing_strategy.md:184 — Phi rotation ordering guidance.
- docs/development/c_to_pytorch_config_map.md:1 — Flag parity reminders.
- docs/architecture/detector.md:120 — Pivot formulas interacting with spindle axis.
- plans/active/cli-noise-pix0/plan.md:265 — Phase L3 task table and exit criteria.
- docs/fix_plan.md:456 — Next Actions referencing this evidence pass.
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md:1 — Hypotheses history to extend.
- reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md:1 — Baseline vector deltas to cite.
- reports/2025-10-cli-flags/phase_l/per_phi/trace_py_rot_vector_per_phi.json:1 — φ-wise evidence for cross-checks.
Next Up: After spindle evidence lands, draft the implementation plan for the chosen normalization fix (Phase L3h) and prepare the nb-compare rerun workflow for Phase L4 once parity metrics align.
