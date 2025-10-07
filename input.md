Summary: Capture MOSFLM matrix evidence to unblock the scaling parity fix.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_probe.log; reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_probe.md; reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md (draft skeleton); reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md
Do Now: CLI-FLAGS-003 Phase L3h MOSFLM probe — `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --out reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_probe.log`
If Blocked: Capture the blocking reason in `reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_probe.md` (Attempts section) and run `pytest --collect-only -q` to validate the environment before pinging supervisor.
Context Reminders:
- Long-term goal #1 hinges on this parity work; no nb-compare rerun until L3h–L3j close.
- Supervisor command parameters are recorded in prompts/supervisor.md; replicate them verbatim.
- Attempt #91 established spindle parity; reuse its formatting when adding new TRACE lines.
- All new evidence must live under `reports/2025-10-cli-flags/phase_l/rot_vector/` so the plan references stay valid.
- Current first divergence: `I_before_scaling` because PyTorch reports `F_cell=0` for hkl=(-7,-1,-14).
- The probe should reveal where MOSFLM real-vector reconstruction diverges from nanoBragg.c.
Priorities & Rationale:
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md: Append MOSFLM probe metrics to maintain a single source of truth for L3 evidence.
- reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_validation_summary.md: Keep the ≤1e-6 tolerance context visible while analysing new numbers.
- docs/architecture/detector.md:50: Re-read BEAM pivot math before interpreting pix0 outputs.
- docs/architecture/detector.md:118: Revisit SAMPLE pivot semantics in case traces reveal implicit pivot flips.
- specs/spec-a-cli.md:30: Confirm CLI precedence (custom vectors > pix0 override) when auditing harness inputs.
- docs/development/c_to_pytorch_config_map.md:40: Ensure HKL tensors respect device/dtype expectations during the run.
- docs/debugging/detector_geometry_checklist.md:60: Follow the parallel trace SOP verbatim to avoid process drift.
- arch.md:520: Core Rule #13 (metric duality) frames the volume reconciliation we need to document.
- plans/active/cli-noise-pix0/plan.md:120: Execute the new L3h–L3j tasks exactly and update checklist states in the plan.
- docs/development/testing_strategy.md:86: Tier 1 parity guidance restricts us to targeted pytest commands; stay within scope.
- golden_suite_generator/nanoBragg.c:2135: Reference the reciprocal→real reconstruction logic in the corrective memo.
- arch.md:200: Rotation ADR recap ensures trace observations align with design intent.
How-To Map:
- 1. Export `NB_C_BIN=./golden_suite_generator/nanoBragg` before any harness commands.
- 2. Confirm `trace_harness.py` in `reports/2025-10-cli-flags/phase_l/rot_vector/` already ingests HKL tensors and spindle data (Phase L2/L3 updates).
- 3. Execute `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --out reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_probe.log`.
-    • Expected output: ≥43 TRACE_PY lines (original 40 + spindle + MOSFLM dumps).
-    • Capture stdout/stderr to `mosflm_matrix_probe.log` or adjacent text files.
- 4. If supported, add `--emit-c-trace reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_probe_c.log`; otherwise cite prior Attempt #71 C traces in the markdown.
- 5. Immediately record git SHA, torch/cuda versions, device, and dtype in the markdown header (match Phase L3e metadata style).
- 6. Run `pytest --collect-only -q` and redirect output to `reports/2025-10-cli-flags/phase_l/rot_vector/test_collect_latest.log` to confirm collection stability.
- 7. Build `mosflm_matrix_probe.md` with sections: Inputs, MOSFLM Reciprocals, Post-misset Reciprocals, Reconstructed Real Vectors, Re-derived Reciprocals, Volume Metrics, Summary.
-    • Provide per-component absolute and relative deltas; emphasise Y-component drift.
-    • Include volume comparisons: V_star, V_cell, V_actual (precision ≥1e-6 Å³).
- 8. Paste key TRACE excerpts (C and PyTorch) into the markdown for each divergent vector component.
- 9. Record SHA256 hashes for `A.mat` and `scaled.hkl` in the markdown (reuse existing `input_files.sha256` format).
- 10. If harness code changed, annotate the diff in an `Implementation Notes` section and reset modifications before ending the loop.
- 11. Draft `mosflm_matrix_correction.md` with outline headings (Summary, Evidence, C references, Proposed PyTorch changes, Validation Plan) ready for Phase L3i.
- 12. Update `docs/fix_plan.md` Attempt history with a new entry summarising commands run, key deltas, and artifact paths.
- 13. Leave production code untouched; only commit documentation, reports, and plan updates per supervisor instructions.
- 14. Snapshot `git status --short` and paste into the markdown so future loops know the working tree state during evidence capture.
Pitfalls To Avoid:
- Do not modify simulator/crystal modules; this iteration is documentation + evidence only.
- Avoid `.cpu()`, `.numpy()`, or `.item()` on tensors coming from differentiable paths.
- Preserve TRACE_PY ordering; append MOSFLM lines after the existing spindle outputs.
- Do not overwrite previous artifacts; append new sections or create timestamped files.
- Leave `docs/index.md` alone per Protected Assets rule.
- Skip nb-compare until L3j checklist exists; we’re still diagnosing root cause.
- Seed any RNG (mosaic generators) and log the seed so traces stay deterministic.
- Ensure harness CLI arguments exactly match the supervisor command; no shortcuts.
- Keep harness edits minimal and well-commented; avoid broad refactors.
- Do not regenerate golden C data; rely on existing Fdump/bin files unless explicitly instructed otherwise.
- Retain older probe outputs; they provide historical comparisons.
- Check device/dtype on HKL tensors before running the simulator; mismatch will zero F_cell again.
- Always prefix Python commands with `KMP_DUPLICATE_LIB_OK=TRUE` to avoid MKL collisions.
- Avoid editing prompt or SOP files; limit changes to plan/report artifacts.
- Keep new TRACE lines consistent in precision (≥12 significant digits).
- Don’t forget to restore harness script to clean state after capturing evidence if you made temporary edits.
- Document any divergence >1e-6 explicitly in the markdown; note whether it violates spec or architecture rules.
- No full pytest runs; testing strategy restricts this loop to collect-only confirmation.
Guardrails & Checklist Hooks:
- Link the work back to plan task IDs L3h/L3i/L3j in `plans/active/cli-noise-pix0/plan.md` (update State column as you progress).
- Ensure the markdown includes timestamps, git SHA, command list, and environment snapshot (torch, CUDA, Python).
- Capture any observed V_formula vs V_actual discrepancy; flag it if relative error exceeds 1e-6.
- Confirm the harness still emits 10 `TRACE_PY_PHI` entries; if that count changes, log why.
- After documentation, run `git status --short` and include the output in the markdown so next loops know which files changed.
- Update docs/fix_plan.md Attempt history immediately after writing the probe summary so parity backlog stays current.
Verification Notes:
- Compare PyTorch vs C reciprocal vectors before and after applying misset; expect ≤1e-9 Å⁻¹ deltas.
- Examine real-vector Y-components; previous drift was +6.8% on b_y. Quantify new values precisely.
- Record spindle axis vector and magnitude even if unchanged; redundancy is better than missing data.
- Verify `steps` remains 10 and `fluence` matches the C trace; note any accidental regression.
- Confirm `F_cell` now reads 190.27 in the harness once MOSFLM matrix handling is corrected (if still 0, highlight in summary).
- Ensure structure factor lookup uses device-aware tensors; log tensor `.device` in the markdown to prove it.
Documentation Checklist:
- `mosflm_matrix_probe.md`: include Overview, Commands, Environment, Raw Data tables, Analysis, Next Steps.
- `mosflm_matrix_correction.md` (draft): outline Summary, C references, PyTorch targets, Validation plan, Open questions.
- `fix_checklist.md`: list validation steps (trace, pytest selector, nb-compare) with expected thresholds and owners.
- Update `analysis.md` with a short paragraph referencing the new probe artifact and takeaways.
- Append Attempt entry in docs/fix_plan.md summarising results and linking to new artifacts.
Pointers:
- docs/architecture/detector.md:74: BEAM pivot pix0 formula for interpreting TRACE_C.
- docs/architecture/detector.md:150: SAMPLE pivot pivot formula in case of pivot switching.
- docs/debugging/detector_geometry_checklist.md:94: Diff snippets for pix0/basis traces.
- docs/development/testing_strategy.md:86: Parity artefact reporting requirements.
- reports/2025-10-cli-flags/phase_l/rot_vector/spindle_audit.log: Formatting reference for probe output.
- reports/2025-10-cli-flags/phase_l/rot_vector/invariant_probe.md: Metric duality baseline numbers.
- reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log: Baseline ordering of TRACE lines.
- docs/architecture/pytorch_design.md:220: Rotation pipeline design to cite when drafting corrective memo.
- arch.md:520: Core Rule #13 explanation (reciprocal↔real consistency).
- golden_suite_generator/nanoBragg.c:3004: Phi rotation loop showing how MOSFLM vectors are used in C.
- plans/active/vectorization.md:40: Broadcasting guidance in case harness needs tensorized data capture.
Next Up:
- Phase L3i: draft `mosflm_matrix_correction.md` summarising the fix plan, citing nanoBragg.c lines and PyTorch call sites.
- Phase L3j: build `fix_checklist.md` so the implementation loop has deterministic exit criteria and mapped validations.
