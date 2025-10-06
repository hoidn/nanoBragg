Summary: Restore pix0 override precedence with custom detector vectors so F_latt parity recovers before normalization fixes.
Phase: Implementation
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -q
Artifacts: reports/2025-10-cli-flags/phase_h5/
Do Now: CLI-FLAGS-003 H5b — Restore pix0 override in custom-vector path; env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -q
If Blocked: If override logic still fails parity, capture fresh C/PyTorch traces into reports/2025-10-cli-flags/phase_h5/debug_attempt/ and log the issue in docs/fix_plan.md Attempts History before pausing.
Priorities & Rationale:
- reports/2025-10-cli-flags/phase_j/scaling_chain.md shows pix0-driven F_latt mismatch causing the 3.6e-7 intensity ratio; resolving override precedence is prerequisite to Phase K.
- plans/active/cli-noise-pix0/plan.md Phase H5 lays out the required evidence, implementation, and documentation steps; stay inside that checklist this loop.
- docs/architecture/detector.md §5 documents the BEAM pivot formula `pix0 = -Fbeam*fdet - Sbeam*sdet + distance*beam_vector`; restored override must follow it exactly.
- specs/spec-a-cli.md mandates CLI parity for `-pix0_vector_mm` even with custom detector vectors; no shortcuts allowed.
- docs/development/c_to_pytorch_config_map.md clarifies MOSFLM beam-center mappings used to derive Fbeam/Sbeam from overrides; double-check before adjusting tests.
How-To Map:
- Reproduce C behavior: `NB_C_BIN=./golden_suite_generator/nanoBragg timeout 120 $NB_C_BIN -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0` (store stdout under `reports/2025-10-cli-flags/phase_h5/c_traces/with_override.log`). Repeat without `-pix0_vector_mm` for comparison.
- After patching Detector, rerun the PyTorch CLI: `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat A.mat -floatfile torch_img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0` and pipe trace output to `reports/2025-10-cli-flags/phase_h5/py_traces/with_override.log` via the existing trace harness.
- Use the harness at `reports/2025-10-cli-flags/phase_h/trace_harness.py` (extend if needed) to extract `pix0_vector`, `Fbeam`, `Sbeam`, fractional h/k/l, and `F_latt` components into `phase_h5/parity_summary.md`.
- Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -q` to confirm regression coverage, then update docs/fix_plan.md with Attempt #29 summary.
Pitfalls To Avoid:
- Do not drop `KMP_DUPLICATE_LIB_OK=TRUE`; every PyTorch CLI/test run must set it.
- Keep Detector changes vectorized and device/dtype neutral—no `.cpu()` casts or tensor detaches.
- Preserve Protected Assets (`loop.sh`, `input.md`, entries listed in docs/index.md); never rename or delete them.
- Avoid editing plan status markers unless evidence is captured and cross-referenced in reports/.
- Ensure trace logs differentiate "with" vs "without" override; ambiguous filenames slow parity review.
- Do not rerun full pytest; stick to targeted nodes unless you finish implementation changes.
- Retain existing pix0 tests; update tolerances only if parity artifacts justify the change.
- No ad-hoc scripts outside `scripts/`—extend existing harnesses instead.
- Keep commits clean; include rationale and tests in message per supervisor SOP.
Pointers:
- plans/active/cli-noise-pix0/plan.md
- docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm
- docs/architecture/detector.md
- specs/spec-a-cli.md
- reports/2025-10-cli-flags/phase_j/scaling_chain.md
Next Up: Phase H5c trace comparison & Attempt #29 logging (if code lands cleanly).
