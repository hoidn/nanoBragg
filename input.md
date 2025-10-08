Summary: Bring the c-parity shim within VG-1 by eliminating the 2.845e-05 residual Δk drift vs the C trace.
Mode: Parity
Focus: CLI-FLAGS-003 — Phase L3k.3c.4 parity shim evidence capture
Branch: feature/spec-based-2
Mapped tests: tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior; tests/test_cli_scaling_phi0.py::TestPhiZeroParity
Artifacts: reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/trace_py_spec*.{log,json}; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/trace_py_c_parity*.{log,json}; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/c_trace_phi.log; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/delta_metrics.json; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/pytest_phi*.log; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/sha256.txt
Do Now: CLI-FLAGS-003 Phase L3k.3c.4 — after fixing the φ carryover logic, rerun the parity trace harness for both modes via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --dtype float64 --device cpu --phi-mode <mode> --out reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/trace_py_<mode>.log` and regenerate the matching `TRACE_C_PHI` log, then recompute `delta_metrics.json`.
If Blocked: Capture failing command + stderr to `<outdir>/attempt_fail.log`, keep the tree untouched, and document the blocker + hypothesis in docs/fix_plan.md Attempt history before stopping.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:309 marks L3k.3c.4 as [P]; VG-1 requires Δk, ΔF_latt_b ≤1e-6/1e-4 before we can advance to documentation and nb-compare phases.
- plans/active/cli-phi-parity-shim/plan.md:47-55 calls for ≤1e-6 parity in c-parity mode; today’s run (20251008T011326Z) still sits at 2.845e-05, so shim logic needs refinement.
- docs/fix_plan.md Attempt #122 records the regression and the missing TRACE_C_PHI instrumentation; resolving both is prerequisite for credible parity evidence.
- docs/bugs/verified_c_bugs.md:166-204 defines the C reference behavior—use it to ensure the optional shim matches the bug without altering the spec-default path.
- specs/spec-a-core.md:211-214 keep the primary contract (identity rotation at φ=0); any fix must leave spec mode untouched while tightening the parity mode.
How-To Map:
- Restore TRACE_C instrumentation if needed: `pushd golden_suite_generator && patch -p1 < ../c_instrumentation.patch && make && popd` (or re-apply the existing TRACE_C_PHI edits manually, then rebuild). Confirm `TRACE_C_PHI` appears before re-running comparisons.
- Prepare outdir: `timestamp=$(date -u +%Y%m%dT%H%M%SZ); outdir=reports/2025-10-cli-flags/phase_l/parity_shim/$timestamp; mkdir -p "$outdir"`.
- Spec run: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --dtype float64 --device cpu --phi-mode spec --out "$outdir/trace_py_spec.log"`.
- C-parity run: same command with `--phi-mode c-parity` and output `trace_py_c_parity.log`.
- Copy per-φ JSON/log/env/config into `$outdir` (rename with `_spec` / `_c_parity` suffixes) before the second run overwrites them.
- Fresh C trace: `NB_C_BIN=./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg ... -trace_pixel 685 1039 > "$outdir/c_trace_phi.log" 2>&1` (use the supervisor command arguments exactly as in docs/fix_plan.md).
- Comparisons: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py "$outdir/trace_py_<mode>_per_phi.json" "$outdir/c_trace_phi.log" | tee "$outdir/per_phi_summary_<mode>.txt"` for both modes; follow with a small Python snippet to rebuild `$outdir/delta_metrics.json` capturing max deltas.
- Tests: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior -v > "$outdir/pytest_phi_carryover.log"` and `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity -v > "$outdir/pytest_phi0.log"`.
- Hashes: `(cd "$outdir" && shasum -a 256 *.log *.json *.txt > sha256.txt)`.
Pitfalls To Avoid:
- Do not loosen VG-1 tolerances; fixing the shim must hit ≤1e-6 without altering the spec-default branch.
- Keep spec mode untouched; any quick fix that regresses TestPhiZeroParity will be backed out.
- Ensure all tensors stay device/dtype neutral—no hard-coded `.cpu()` / `.double()` calls when adjusting phi rotation.
- Don’t rely on the stale 20251008T005247Z C log; regenerate TRACE_C_PHI so evidence reflects the current binary.
- Avoid deleting or renaming protected assets referenced in docs/index.md (trace harness, reports directories, loop scripts).
- Preserve vectorization inside `Crystal.get_rotated_real_vectors`; no per-φ Python loops to patch the carryover path.
- Re-run only the mapped targeted tests; defer nb-compare until VG-1 tolerances pass.
- Document any shim adjustments with updated CLAUDE Rule #11 citations if you touch the core function.
- Capture both CPU and (if available) CUDA behavior when adding diagnostics; note skips explicitly in logs.
- Keep the worktree clean; log intermediate artifacts under `reports/` rather than leaving temp files elsewhere.
Pointers:
- docs/fix_plan.md:450-574 — CLI-FLAGS-003 context + latest Attempt #122 notes.
- plans/active/cli-phi-parity-shim/plan.md:39-55 — Phase C4 requirements and tolerances.
- plans/active/cli-noise-pix0/plan.md:306-314 — L3k.3c sub-phase checklist (now [P]).
- docs/bugs/verified_c_bugs.md:166-204 — Definition of C-PARITY-001 bug to reproduce.
- src/nanobrag_torch/models/crystal.py:1070-1175 — Current φ rotation + carryover shim implementation.
Next Up: 1) Update docs (`docs/bugs/verified_c_bugs.md`, diagnosis) once VG-1 passes; 2) Proceed to L3k.3d nb-compare ROI analysis with `--phi-carryover-mode c-parity`.
