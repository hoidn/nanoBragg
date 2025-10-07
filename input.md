Summary: Capture spindle-axis magnitude and volume evidence for the φ=0 rotation drift so Phase L3g can conclude with documented hypotheses before any simulator edits.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase L3g rotation-vector drift
Branch: feature/spec-based-2
Mapped tests: tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics (collect-only)
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/spindle_audit.log; reports/2025-10-cli-flags/phase_l/rot_vector/volume_probe.md; reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md; docs/fix_plan.md attempt update (CLI-FLAGS-003)
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics
If Blocked: Capture the failing harness stdout/stderr under reports/2025-10-cli-flags/phase_l/rot_vector/blocked.log, note the exact exception + command, and record the blocker (with artifact path) in docs/fix_plan.md Attempts before stopping.
Priorities & Rationale:
- specs/spec-a-core.md:120 — Direct↔reciprocal reconstruction mandates V_actual; the audit must quantify PyTorch vs C usage before touching the implementation.
- arch.md:170 — CrystalConfig spindle_axis contract expects unit vectors, so we confirm runtime normalization for CLI inputs (especially -spindle_axis -1 0 0).
- docs/debugging/debugging.md:15 — Parallel trace workflow is required; fresh TRACE_PY data is prerequisite to any fix.
- docs/development/testing_strategy.md:184 — Rotation pipeline details guide which tensors to log (phi→mosaic order).
- docs/architecture/c_code_overview.md:310 — Highlights where C re-normalizes spindle vectors; use it to cross-check harness outputs.
- plans/active/cli-noise-pix0/plan.md:253 — Phase L3 checklist lists rot-vector audit and hypothesis framing as blocking tasks.
- docs/fix_plan.md:460 — Next Actions already call for this probe; keeping ledger evidence up to date prevents redundant loops.
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md:1 — Existing hypotheses (spindle norm, V reuse) require confirming evidence.
How-To Map:
- Step 0 (environment prep):
  - export KMP_DUPLICATE_LIB_OK=TRUE
  - export PYTHONPATH=src
  - ls -l A.mat scaled.hkl
  - sha256sum A.mat scaled.hkl > reports/2025-10-cli-flags/phase_l/rot_vector/input_files.sha256
  - git rev-parse HEAD >> reports/2025-10-cli-flags/phase_l/rot_vector/input_files.sha256
  - date -Iseconds >> reports/2025-10-cli-flags/phase_l/rot_vector/input_files.sha256
- Step 1 (pytest guard):
  - pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics | tee reports/2025-10-cli-flags/phase_l/rot_vector/test_collect.log
  - confirm the log shows the node and exit code 0; otherwise repair collection first.
- Step 2 (refresh TRACE_PY):
  - PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
    --pixel 685 1039 --config supervisor --device cpu --dtype float32 \
    --out reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log \
    | tee reports/2025-10-cli-flags/phase_l/rot_vector/trace_run.log
  - verify the run mentions “Captured 40 TRACE_PY lines” and that per-φ JSON was written; if missing, fix harness instrumentation.
- Step 3 (spindle-axis probe):
  - Implement reports/2025-10-cli-flags/phase_l/rot_vector/spindle_probe.py (or extend harness) to parse TRACE_PY and TRACE_C spindle lines.
  - Command:
    PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/spindle_probe.py \
      --trace reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log \
      --ctrace reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log \
      --out reports/2025-10-cli-flags/phase_l/rot_vector/spindle_audit.log
  - Log raw vectors, norms, Δ(norm), Δ(component), device/dtype, and tolerance verdict (≤5e-4).
- Step 4 (volume analysis):
  - Write a python snippet to compute V_formula (reciprocal cross product) and V_actual (real vectors triple product) for both traces.
  - Save results into reports/2025-10-cli-flags/phase_l/rot_vector/volume_probe.md with sections: Inputs, PyTorch float32, PyTorch float64, C reference, delta table.
  - Run the harness again with --dtype float64 to populate the float64 section.
- Step 5 (rot-vector table refresh):
  - Update reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md with the refreshed values; highlight components exceeding tolerance and tie them to k_frac.
  - Mention per-component Δ and relative error percentages for clarity.
- Step 6 (analysis narrative):
  - Append a dated section to reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md summarizing spindle norms, volume deltas, dtype comparisons, and updated hypothesis.
  - Include a “Next diagnostic” bullet (e.g., log ap/bp before mosaic) to guide the following loop.
- Step 7 (plan + ledger sync):
  - Add an Attempt entry to docs/fix_plan.md under CLI-FLAGS-003 capturing metrics, artifacts, thresholds, and hypothesis outcome.
  - If Phase L3 text needs refinement (e.g., new spindle normalization task), update plans/active/cli-noise-pix0/plan.md lines 265-267 accordingly.
- Step 8 (optional cross-check):
  - If CUDA is available, repeat Step 2 with --device cuda --dtype float32; append the results to spindle_audit.log and document them in fix_plan.
  - If CUDA is unavailable or fails, log the reason in blocked.log and fix_plan attempt.
- Step 9 (per-φ verification):
  - Ensure the per-φ JSON under reports/2025-10-cli-flags/phase_l/per_phi/ includes k_frac entries; reference it in analysis.md to show φ dependence (or lack thereof).
- Step 10 (cleanup):
  - Keep new files under reports/2025-10-cli-flags/phase_l/rot_vector/; avoid temporary directories.
  - Run git status to confirm only intended files changed; no simulator sources touched.
- Step 11 (documentation proof):
  - Cross-reference new artifacts in docs/fix_plan.md (list paths in the attempt entry).
  - State tolerance thresholds (norm ≤5e-4, volume ≤1e-6) so future comparisons are deterministic.
  - Mention any dtype/device coverage in the attempt summary.
Pitfalls To Avoid:
- Forgetting to export KMP_DUPLICATE_LIB_OK causes MKL failures; set it before every harness run.
- Hard-coding .cpu()/.cuda() in probes breaks device neutrality; keep probes parameterized.
- Overwriting trace files without preserving older copies will erase evidence; archive first.
- Writing artifacts outside reports/2025-10-cli-flags/phase_l/rot_vector/ fragments audit history; stay within that directory tree.
- Editing simulator/crystal code during this evidence pass is off-limits; gather data only.
- Skipping timestamps and git SHA in new artifacts impairs reproducibility; include them explicitly.
- Ignoring float64 probes risks missing dtype regressions; capture at least one double-precision run if possible.
- Leaving pytest output in the terminal history risks loss; tee logs into the reports directory.
- Failing to document tolerance thresholds makes later comparisons ambiguous; write them next to the numbers.
- Neglecting to update docs/fix_plan.md and plan.md leaves the ledger stale after evidence capture.
- Using relative imports without PYTHONPATH=src may import stale modules; set the env var first.
- Assuming A.mat/scaled.hkl integrity without checksums can mislead if files change; record sha256 upfront.
- Forgetting to note device/dtype in spindle_audit.log reduces its diagnostic value; print both explicitly.
- Removing existing analysis context instead of appending will lose historical rationale; always append.
- Failing to mention per-φ findings in analysis.md leaves Phase L3e context unclear; reference the JSON explicitly.
- Skipping CUDA note when unavailable can waste future time; document availability status.
Pointers:
- specs/spec-a-core.md:120 — Reciprocal→real reconstruction / V_actual rule.
- arch.md:170 — CrystalConfig spindle-axis expectation (unit vector contract).
- docs/debugging/debugging.md:15 — Parallel trace SOP (C vs Py traces first).
- docs/development/testing_strategy.md:184 — Phi rotation workflow relevant to the audit.
- docs/architecture/c_code_overview.md:310 — C spindle normalization notes.
- docs/development/c_to_pytorch_config_map.md:1 — Parameter parity reminders for CLI flags.
- plans/active/cli-noise-pix0/plan.md:260 — Phase L3 checklist and deliverables.
- docs/fix_plan.md:460 — CLI-FLAGS-003 Next Actions tied to this audit.
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md:1 — Existing hypothesis log to extend.
- reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md:1 — Baseline table for update.
- reports/2025-10-cli-flags/phase_l/per_phi/trace_py_rot_vector_per_phi.log:1 — Current per-φ evidence to cite.
- reports/2025-10-cli-flags/phase_l/rot_vector/spindle_audit.log:1 — New log location to populate.
- reports/2025-10-cli-flags/phase_l/rot_vector/volume_probe.md:1 — Markdown summary to extend.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:1 — C reference trace for comparison.
Next Up: 1) Refresh per-φ scaling validation (Phase L3e artifacts) with the new spindle/volume metrics to confirm k_frac impact across phi steps; 2) Draft the implementation strategy for the normalization correction (Phase L3h) once evidence isolates the precise mismatch; 3) After L3h delivers matching scalings, schedule the nb-compare rerun and sum-ratio analysis required to close CLI-FLAGS-003; 4) Only then revisit long-term Goal #1 full command execution.
