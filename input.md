Summary: Recreate nanoBragg.c's post-rotation beam-centre recompute so pix0/Fbeam/Sbeam match C within 5e-5 m.
Phase: Implementation
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu|cuda]
Artifacts: reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v
If Blocked: Run KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_h/trace_harness.py --mode pix0 --no-polar --outdir reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/blocked && document deltas plus stack traces in reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/blocked.md before paging supervisor.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:94 spells out Phase H4a–H4c requirements; H4a specifically demands mirroring nanoBragg.c lines 1846-1860 and logging notes in parity_after_lattice_fix/implementation.md.
- docs/fix_plan.md:448 keeps CLI-FLAGS-003 top priority and lists H4a/H4b/H4c as next actions; the Attempt #25 entry must cite new metrics once traces land.
- reports/2025-10-cli-flags/phase_h/implementation/pix0_mapping_analysis.md captures the current 3.9 mm Y delta; use it as the before/after reference in parity_after_lattice_fix/summary.md.
- docs/development/c_to_pytorch_config_map.md:70 reiterates BEAM pivot mappings (Fbeam←Ybeam, Sbeam←Xbeam with MOSFLM +0.5) that must still hold after recomputation.
- golden_suite_generator/nanoBragg.c:1822-1859 is the authoritative sequence (newvector projection + updated distance); keep ordering identical to avoid sign or offset drift.
- docs/architecture/detector.md:210 describes pix0, r-factor, and close-distance relationships; the PyTorch update should satisfy those invariants and log them in traces.
How-To Map:
- Export KMP_DUPLICATE_LIB_OK=TRUE for every Python/pytest run; set NB_C_BIN=./golden_suite_generator/nanoBragg when capturing C traces.
- Study nanoBragg.c:1822-1859 to note how `newvector = close_distance/ratio * beam - pix0` is formed before projecting to F/S axes.
- Edit src/nanobrag_torch/models/detector.py around lines 520-620; after computing `self.pix0_vector`, recompute `close_distance_tensor = torch.dot(self.pix0_vector, self.odet_vec)` and `beam_term = close_distance_tensor / self.r_factor * beam_vector` using tensor ops on the detector device/dtype.
- Form `newvector = beam_term - self.pix0_vector`, set `Fbeam_recomputed = -torch.dot(newvector, self.fdet_vec)` and `Sbeam_recomputed = -torch.dot(newvector, self.sdet_vec)`, then refresh `self.beam_center_f/s` respecting MOSFLM's ±0.5 pixel offset.
- Update `self.distance_corrected = close_distance_tensor / self.r_factor` and keep `self.close_distance = close_distance_tensor`; invalidate cached geometry if these tensors change.
- Capture PyTorch trace via KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_h/trace_harness.py --mode pix0 --no-polar --outdir reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/.
- Generate matching C trace using timeout 180 env NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/c_reference_runner.py --config prompts/supervisor_command.yaml --out reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/c_trace.log.
- Diff traces with PYTHONPATH=src python scripts/validation/diff_traces.py --c reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/c_trace.log --py reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/py_trace.log --out reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/trace_diff.txt and confirm pix0/Fbeam/Sbeam deltas ≤5e-5 m.
- Tighten tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot tolerance to 5e-5 m (CPU & CUDA) before running the targeted pytest command in Do Now; archive the pytest log beside the traces.
- Update reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/summary.md with before/after metrics (pix0 components, beam centers, F_latt snippet) and cross-link to Attempt #25 in docs/fix_plan.md.
Pitfalls To Avoid:
- Do not short-circuit pix0 recompute when custom vectors or overrides are present; recompute newvector in all BEAM pivot cases as C does.
- Avoid creating CPU tensors (torch.tensor([...])) without .to(self.device, self.dtype); keep device/dtype neutrality for CUDA runs.
- Do not reintroduce `.item()` or detach when logging metrics; maintain differentiability through pix0 calculations.
- Keep MOSFLM +0.5 offsets intact when updating beam_center_f/s; CUSTOM should remain offset-free.
- Do not delete or rename any file listed in docs/index.md (Protected Assets rule).
- Resist adjusting plan tolerances without updating docs/fix_plan.md and plan tables; tolerances must reflect evidence.
- Do not run full pytest; stick to the targeted node plus trace scripts for this loop.
- Ensure cached pixel grids are invalidated if pix0 changes; otherwise stale coords will poison parity runs.
- Maintain consistent trace formatting (TRACE_PY keys) to keep diff tool useful.
- Keep `authoritative_cmds_doc` mapping in mind: tests/testing_strategy.md is the source for allowed pytest selectors.
Pointers:
- src/nanobrag_torch/models/detector.py:540 — current pix0 override and BEAM pivot logic needing recompute.
- golden_suite_generator/nanoBragg.c:1822 — reference newvector projection and F/S recomputation.
- docs/architecture/detector.md:205 — description of pix0_vector, beam centres, and r-factor relationships.
- docs/development/c_to_pytorch_config_map.md:70 — BEAM pivot beam-centre mapping requirements.
- reports/2025-10-cli-flags/phase_h/implementation/pix0_mapping_analysis.md — baseline evidence showing 3.9 mm Y delta.
Next Up: Execute Phase H4b evidence capture if implementation finishes early; otherwise prep Phase I polarization audit checklist for next loop.
