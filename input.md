Summary: Port the nanoBragg.c post-rotation beam-centre recomputation so pix0 parity closes to ≤5e-5 m.
Phase: Implementation
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu|cuda]
Artifacts: reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v
If Blocked: Capture current mismatch via KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_h/trace_harness.py --mode pix0 --no-polar --outdir reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/blocked && log deltas plus traceback in reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/blocked.md, then notify supervisor.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:106 anchors Phase H4a deliverables (≤5e-5 m pix0 delta, refreshed beam centres) so implementation must satisfy those exit criteria before moving on.
- plans/active/cli-noise-pix0/plan.md:107 mandates the parity_after_lattice_fix/ trace bundle (C + PyTorch logs, diff summary) which doubles as evidence for docs/fix_plan.md Attempt #25.
- plans/active/cli-noise-pix0/plan.md:108 requires tightening the regression tolerance in tests/test_cli_flags.py alongside the targeted pytest rerun; leaving 5 mm tolerance would violate the plan.
- docs/fix_plan.md:448 keeps CLI-FLAGS-003 top priority and now lists H4a–H4c as the next actions, so closing this loop depends on updating the Attempts section with fresh metrics.
- reports/2025-10-cli-flags/phase_h/implementation/pix0_mapping_analysis.md:66 documents the 1.14 mm Y delta and will be the before/after comparison anchor once parity is restored.
- golden_suite_generator/nanoBragg.c:1822 preserves the authoritative `newvector` projection math; porting this sequence verbatim prevents the sign mistakes that caused earlier MOSFLM regressions.
- docs/development/c_to_pytorch_config_map.md:70 reiterates BEAM pivot expectations (Fbeam ← Ybeam, Sbeam ← Xbeam with offsets) which the updated code must continue to honour after recomputation.
- docs/development/testing_strategy.md:33 enforces device/dtype neutrality; the new path must keep gradients and avoid CPU-only tensors so CUDA smoke continues to pass.
How-To Map:
- Step 1: Re-read golden_suite_generator/nanoBragg.c:1822-1859 and note the order of operations (pix0 calc → Fclose/Sclose → newvector projection → updated distance) so the PyTorch port mirrors every intermediate.
- Step 2: Open src/nanobrag_torch/models/detector.py and locate `_calculate_pix0_vector`; confirm current logic stops after setting `self.pix0_vector` and `self.close_distance` without recomputing `Fbeam/Sbeam`.
- Step 3: Introduce tensor variables `close_distance_tensor = torch.dot(self.pix0_vector, self.odet_vec)` and `beam_term = (close_distance_tensor / self.r_factor) * beam_vector` immediately after pix0 assignment to mirror the C ratio update.
- Step 4: Form `newvector = beam_term - self.pix0_vector` using tensor math (no view/as_tensor shenanigans) and project onto detector axes via `Fbeam_recomputed = torch.dot(self.fdet_vec, newvector)` and the matching slow-axis projection.
- Step 5: Replace the interim Fbeam/Sbeam used earlier with the recomputed values, then update `self.beam_center_f` and `self.beam_center_s` by dividing through `self.pixel_size` and subtracting the MOSFLM 0.5 offset when the convention dictates.
- Step 6: Reset `self.distance_corrected` to `close_distance_tensor / self.r_factor`, keeping `self.close_distance = close_distance_tensor` so later obliquity math matches the C trace.
- Step 7: Ensure all newly created tensors are coerced via `.to(device=self.device, dtype=self.dtype)` to maintain device/dtype neutrality; unit-test by constructing a CUDA detector in the REPL if available.
- Step 8: Touch `_cached_pix0_vector` / `_geometry_version` only through existing helpers (call `invalidate_cache()` if necessary) to avoid desynchronising cached grids.
- Step 9: Run KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_h/trace_harness.py --mode pix0 --no-polar --outdir reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/ to refresh the PyTorch trace, metrics JSON, and default summary.md scaffold.
- Step 10: Generate the C reference via timeout 180 env NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/c_reference_runner.py --config prompts/supervisor_command.yaml --out reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/c_trace.log so the trace formats stay aligned.
- Step 11: Diff the traces with python scripts/validation/diff_traces.py --c reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/c_trace.log --py reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/py_trace.log --out reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/trace_diff.txt and verify pix0 deltas ≤5e-5 m, `F_latt` relative error <0.5%, and intensity ratio <10×; document results in summary.md.
- Step 12: Update tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot to assert ≤5e-5 m tolerance for both CPU and CUDA parametrisations, keeping existing custom/no-custom coverage intact.
- Step 13: Execute the Do Now pytest command (KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v) and watch for CUDA skip messaging; if CUDA fails unexpectedly, capture the traceback under parity_after_lattice_fix/pytest_failures/.
- Step 14: Record Attempt #25 in docs/fix_plan.md with pix0 component deltas, Fbeam/Sbeam values, regression outcome, and key artifact paths; link back to the parity_after_lattice_fix/ summary for traceability.
- Step 15: Append implementation notes (covering tensor ops, device handling, and any refactors) to reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/implementation.md so future loops understand the change rationale.
Pitfalls To Avoid:
- Do not touch files listed in docs/index.md (Protected Assets policy); no renames or deletions.
- Avoid `.item()`, `.numpy()`, or `.cpu()` on tensors that require gradients; keep all scalars as tensors.
- Preserve vectorization—never introduce Python loops over detector axes or sources in `_calculate_pix0_vector`.
- Maintain the precedence guard (`has_custom_vectors`) so pix0_override remains ignored when custom vectors are present.
- Keep MOSFLM +0.5 pixel adjustments and CUSTOM behaviour intact after updating beam centres.
- Ensure new tensors respect device/dtype neutrality; no hard-coded CPU allocations.
- Skip modifying polarization logic (Phase I) until H4 evidence is complete to prevent scope creep.
- Remember KMP_DUPLICATE_LIB_OK=TRUE on every PyTorch invocation to avoid MKL crashes.
- Archive logs under parity_after_lattice_fix/; stray temp files in repo root violate hygiene plans.
- Do not relax regression tolerances before parity proof; tighten only after confirming the Δ ≤5e-5 m.
Pointers:
- plans/active/cli-noise-pix0/plan.md:106
- plans/active/cli-noise-pix0/plan.md:107
- plans/active/cli-noise-pix0/plan.md:108
- docs/fix_plan.md:448
- reports/2025-10-cli-flags/phase_h/implementation/pix0_mapping_analysis.md:66
- golden_suite_generator/nanoBragg.c:1822
- src/nanobrag_torch/models/detector.py:326
- tests/test_cli_flags.py:439
- docs/development/c_to_pytorch_config_map.md:70
- docs/development/testing_strategy.md:33
Next Up: If H4 completes ahead of schedule, prep Phase H4b by drafting parity-after-fix metrics in reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/summary.md and stage commands for Kahn polarization analysis in Phase I.
Validation Checklist:
- Verify pix0 component deltas (X, Y, Z) all fall within ±5e-5 m when comparing C vs PyTorch traces.
- Confirm recomputed `Fbeam` and `Sbeam` values match C within ≤1e-6 m using trace_diff.txt metrics.
- Ensure `distance_corrected` equals C trace within ≤1e-6 m and note value in summary.md.
- Check that `F_latt` relative errors stay below 0.5% for the supervisor ROI; log actual percentages.
- Record the peak intensity ratio and verify it is <10×; if higher, freeze implementation and revisit calculations.
- Run pytest node on CPU and observe CUDA skip or pass result; document both outcomes in Attempt #25.
- Rerun `pytest --collect-only` for the node if the test fails to ensure no naming drift occurred post-edit.
- Inspect reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/ for stray intermediate files and remove before commit.
Reporting Requirements:
- Update reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/summary.md with a table of C vs PyTorch pix0, Fbeam, Sbeam, distance values plus percentage errors.
- Append a short narrative (3–5 sentences) to implementation.md explaining tensor operations added and how device neutrality was preserved.
- In docs/fix_plan.md Attempt #25, include command transcripts (trimmed) for trace harness, C runner, diff tool, and pytest.
- Note any skipped CUDA test in the attempt log; justify skip reason (e.g., hardware absent) per testing_strategy.md guidelines.
- Cross-link Attempt #25 entry back to pix0_mapping_analysis.md so historical context stays intact.
- Add a TODO in docs/fix_plan.md if any metrics narrowly miss targets with rationale and follow-up plan.
Metrics Targets:
- pix0_vector delta ≤5e-5 m on each axis.
- `Fbeam` and `Sbeam` absolute error ≤1e-6 m.
- `close_distance` absolute error ≤5e-6 m.
- Relative error for `F_latt_a/b/c` ≤0.5%.
- Peak intensity ratio PyTorch/C ≤10×.
- pytest node success on CPU and skip-or-pass on CUDA with no unexpected failures.
- Zero additional lint/test regressions triggered by the change.
Command Log Template:
- Record `PYTORCH_TRACE_CMD=KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_h/trace_harness.py --mode pix0 --no-polar --outdir reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/` in summary.md under a labeled code block.
- Document `timeout 180 env NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/c_reference_runner.py --config prompts/supervisor_command.yaml --out reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/c_trace.log` with runtime and exit status.
- Capture `python scripts/validation/diff_traces.py --c ... --py ... --out ...` stdout, especially the first divergence line, and paste into trace_diff.txt.
- Note pytest command output verbatim; include lines highlighting tolerance assertions to show tightened bounds.
Rollback Plan:
- If pix0 deltas remain >5e-5 m after port, revert `_calculate_pix0_vector` edits locally and stash under reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/attempt_failures/`<timestamp>`.
- Re-run trace harness against the previous commit to confirm baseline still shows 1.14 mm delta; attach evidence for comparison.
- Draft a short blocker note in docs/fix_plan.md explaining why H4 could not close and list hypotheses for next loop.
Quality Gates:
- Ensure unit tests touched by change (tests/test_cli_flags.py) preserve parameter coverage for custom/no-custom vectors.
- Update any doctstrings or inline comments to maintain ASCII only and keep them concise per repo guidelines.
- Run `python -m compileall src/nanobrag_torch/models/detector.py` if time permits to catch syntax errors before handing off.
Notes:
- The supervisor command definition lives in prompts/supervisor_command.yaml; confirm no drift before running c_reference_runner.py.
- Keep an eye on newvector projection orientation; if sign mismatches surface, re-check DetectorConvention-specific basis ordering in detector.py:560.
- Remember that CUSTOM convention removes the +0.5 pixel offset; ensure recompute path honours this by interrogating `self.config.detector_convention` after precedence guard.
- If CUDA is available, consider running torch.set_printoptions(precision=15) while debugging to inspect tensor deltas without rounding loss.
- Preserve existing logging structure in trace_harness.py; do not modify script output unless absolutely necessary for parity evidence.
- Confirm Attempt #25 references the exact git commit hash once changes are ready for review.
