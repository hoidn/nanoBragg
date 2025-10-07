Summary: Wire the scaling harness into the HKL grid so TRACE_PY sees real structure factors and rerun the L2b comparison.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase L2b)
Branch: feature/spec-based-2
Mapped tests: tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log, reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md, reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json, reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md, reports/2025-10-cli-flags/phase_l/scaling_audit/harness_hkl_state.txt
Do Now: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase L2b) → KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log --config supervisor (after updating the harness to attach `crystal.hkl_data` / `crystal.hkl_metadata` before constructing Simulator)
If Blocked: Capture stdout/stderr to reports/2025-10-cli-flags/phase_l/scaling_audit/attempts/<timestamp>/, log the blocker under CLI-FLAGS-003 Attempt History, and stash the latest harness snapshot in notes.md before touching normalization code.

Priorities & Rationale:
- docs/fix_plan.md:458-476,482-492 — Phase L2b remains open because the harness never sets `Crystal.hkl_data`; fix_plan now cites harness_hkl_state.txt as proof.
- plans/active/cli-noise-pix0/plan.md:12-20,243 — L2b guidance updated today: consume `(F_grid, metadata)` and attach them directly to the Crystal before rerunning the trace.
- reports/2025-10-cli-flags/phase_l/scaling_audit/harness_hkl_state.txt — Evidence that `crystal.hkl_data is None` after the current harness path.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log:1-35 — Shows `F_cell=0`/`I_before_scaling=0` despite hkl=(1,12,3), confirming the metadata bug.
- docs/development/c_to_pytorch_config_map.md:55-88 — Reference for MOSFLM orientation semantics you must preserve while touching the harness.

How-To Map:
- Patch reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py so the HKL read writes `crystal.hkl_data = F_grid_tensor` and `crystal.hkl_metadata = hkl_metadata` (alternatively call `crystal.load_hkl(...)` on the same path); ensure metadata dict stays on the correct device/dtype.
- Keep the MOSFLM vector assignments introduced last loop and re-run the harness via `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log --config supervisor` from the repo root.
- Update reports/…/harness_hkl_state.txt with a quick post-fix probe (reuse the python snippet but now expect `hkl_data is None? False`).
- Archive refreshed env + notes: overwrite trace_py_env.json and append key observations to notes.md; stash the old trace under a timestamped subdir if you want to diff later.
- Validate selector discovery via `pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics`, then run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c-log reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py-log reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md` to refresh L2c.

Pitfalls To Avoid:
- Do not leave `crystal.hkl_data` unset; structure factors will revert to default_F=0.
- Keep tensors device/dtype-neutral—no `.cpu()` or implicit host copies in the harness.
- Preserve MOSFLM vector assignments and the SAMPLE pivot; orientation regression will break pix0 parity.
- Always set `KMP_DUPLICATE_LIB_OK=TRUE` before importing torch or running harness/test commands.
- Do not overwrite trace_py_fullrun.log; it remains the pre-fix regression artifact.
- No production simulator edits this loop—focus on harness wiring only.
- Avoid running the entire pytest suite; stick to the targeted selector after verifying collection.
- Respect Protected Assets (docs/index.md) when moving or deleting files.
- Keep ROI pixel (685,1039) unchanged so comparison tooling aligns with the C trace.
- Update notes.md with context; future audits rely on that log.

Pointers:
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:170-250 — HKL load + Simulator wiring that needs the metadata assignment.
- docs/fix_plan.md:458-494 — CLI-FLAGS-003 Next Actions and fresh Attempt #73 summary.
- plans/active/cli-noise-pix0/plan.md:15-20,243 — L2b checklist reflecting today’s blocker.
- scripts/validation/compare_scaling_traces.py:1-200 — Tool you must rerun after the harness fix.
- src/nanobrag_torch/models/crystal.py:98-210 — Shows `hkl_data`/`hkl_metadata` fields consulted by `get_structure_factor`.

Next Up: If everything passes quickly, move to Phase L3 prep by documenting the first non-zero divergence from the refreshed scaling audit.
