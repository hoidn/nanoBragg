Summary: Confirm spindle-axis parity for CLI-FLAGS-003 before re-running supervisor command.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c; tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/vg1_phi_grid_py.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/vg1_phi_grid_c.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/pytest_phi0.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/pytest_collect.log
Artifacts: docs/fix_plan.md
Artifacts: plans/active/cli-noise-pix0/plan.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md
Do Now: CLI-FLAGS-003 Phase L3k.3 — align the φ=0 lattice-vector test with the supervisor command by wiring spindle_axis = (-1, 0, 0), rerunning the targeted pytest selector (`KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c`), and capturing the updated failure output under reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/ before refreshing the VG-1 checklist.
If Blocked: If pytest setup keeps tripping on missing context, run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --pixel 685 1039 --device cpu --dtype float32 --out reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/vg1_phi_grid_py.log` and document the numeric gap in `vg1_phi_grid_py.log` / `vg1_phi_grid_c.log` so we can revisit the pytest wiring next loop.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:276-309 keeps Phase L3k.3 gates open until φ=0 evidence lands with supervisor-axis parity.
- docs/fix_plan.md:450-520 records VG-1.4 (k_frac drift 1.8e-2) as the current blocker; today’s run validates whether the spindle axis mismatch is the culprit.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:266-277 is our authoritative C trace for rot_b_y and k_frac; the pytest selector must reference these numbers with the correct axis.
- docs/development/c_to_pytorch_config_map.md:42 maps `-spindle_axis` → `CrystalConfig.spindle_axis`; confirming parity ensures we honour the CLI flag in both code and tests.
- specs/spec-a-cli.md:90-110 documents φ/osc semantics; matching them avoids off-by-one errors when the harness sweeps φ_tic.
How-To Map:
- `pytest --collect-only tests/test_cli_scaling_phi0.py -q | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/pytest_collect.log`
- `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/pytest_phi0.log`
- `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c | tee -a reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/pytest_phi0.log`
- If pytest still fails before the axis change, rerun the PyTorch trace harness with the supervisor flags and archive both `vg1_phi_grid_py.log` and the matching C snippet (`sed -n '260,280p' reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log > .../vg1_phi_grid_c.log`).
- Update `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md` (VG-1 rows) and log Attempt details in docs/fix_plan.md once the spindle-axis alignment evidence is captured.
Pitfalls To Avoid:
- Do not leave `spindle_axis` at the default (0,1,0); that contradicts the supervisor command and invalidates VG-1.
- No `.cpu()`/`.item()` on tensors that feed gradients (CLAUDE Rule #9) when adjusting tests.
- Keep per-φ traces under `reports/.../rot_vector/base_vector_debug/`—Protected Assets rule forbids relocating entries from docs/index.md.
- Maintain vectorization in `Crystal.get_rotated_real_vectors`; avoid introducing Python loops when adjusting tests or harnesses.
- Use `KMP_DUPLICATE_LIB_OK=TRUE` on every torch invocation; missing it causes MKL crashes.
- Do not run the full pytest suite; stick to the targeted selectors listed above until parity is restored.
- Preserve device neutrality: any temporary tensors introduced for debugging must live on `crystal.device`/`detector.device`.
- Keep `mosflm_matrix_correction.md` and fix_checklist in sync; log new artifacts in both plan and fix_plan.
- Avoid modifying `docs/index.md` or other Protected Assets.
- No ad-hoc scripts under repo root; reuse existing harnesses or place helpers under `scripts/`.
Pointers:
- specs/spec-a-cli.md:88-116 (φ/osc and spindle axis semantics)
- docs/development/c_to_pytorch_config_map.md:38-54 (CLI flag → CrystalConfig mapping)
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:260-277 (C ground truth for rot_b, k_frac)
- reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md:187-297 (Phase L3k implementation memo)
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md (VG-1 status table)
Next Up: If spindle-axis parity holds, return to Phase L3k.3 VG-3 by re-running nb-compare with the supervisor command and archiving the refreshed summary.json.
