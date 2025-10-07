Summary: Implement the φ-rotation fix so CLI parity metrics can advance to Phase L3k verification.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestCLIScaling::test_f_latt_square_matches_c
Mapped tests: tests/test_cli_scaling.py -k lattice -v
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/
Artifacts: reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md
Artifacts: plans/active/cli-noise-pix0/plan.md
Artifacts: docs/fix_plan.md
Do Now: CLI-FLAGS-003 Phase L3k.2 φ-rotation fix — env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py -k lattice -v (VG-2) after implementing per plan.
If Blocked: Capture fresh per-φ traces via trace_harness.py and log deltas under reports/2025-10-cli-flags/phase_l/rot_vector/blockers/ before revisiting the memo.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:276 locks L3k.2 as the gate before parity rerun; finishing it unblocks VG-1..VG-5.
- docs/fix_plan.md:458 now targets L3k.2–L3k.4 explicitly; clearing them retires the outstanding Next Actions for long-term goal #1.
- reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md documents the required physics change and tolerances, so implementation must trace to it.
- specs/spec-a-cli.md:34 ensures pix0 overrides remain aligned with CUSTOM convention; φ rotation must respect that contract.
- docs/architecture/detector.md:80 highlights pivot handling; verifying after the fix confirms pix0 stays stable.
How-To Map:
- env KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --phi-seq "0.0,0.05,0.1" --outdir reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix
- env KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c-trace reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py-trace reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/trace_py_phi_0.00.log --outdir reports/2025-10-cli-flags/phase_l/rot_vector/scaling_delta
- nb-compare --roi 100 156 100 156 --resample --outdir reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/ -- -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0
Pitfalls To Avoid:
- Do not edit reciprocal vectors directly after the fix; recompute via cross products to preserve metric duality.
- Keep tensors differentiable; avoid `.detach()`/`.item()` in Crystal paths.
- Maintain vectorization (no Python loops over φ or mosaic indices).
- Respect device neutrality—use existing tensor devices/dtypes, no hard-coded `.cpu()`.
- Insert the nanoBragg.c snippet into the docstring before code edits to satisfy CLAUDE Rule #11.
- Run commands with KMP_DUPLICATE_LIB_OK=TRUE to prevent MKL crashes.
- Do not skip nb-compare; VG-3 metrics must reach the thresholds before moving on.
- Update fix_checklist.md immediately after each gate to avoid losing traceability.
- Avoid overwriting prior artifacts; use new timestamped folders under reports/.
- Confirm CUSTOM convention still forces SAMPLE pivot (trace per plan) so pix0 parity holds.
Pointers:
- plans/active/cli-noise-pix0/plan.md:276
- docs/fix_plan.md:458
- reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md:187
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:1
- specs/spec-a-cli.md:34
Next Up: Execute Phase L3k.3 verification gates once code lands and artifacts are seeded.
