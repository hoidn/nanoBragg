Summary: Chase the 2.85 µm pix0_z mismatch so φ=0 c-parity traces drop below the 1e-6 gate.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c, tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c, tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior::test_c_parity_mode_stale_carryover
Artifacts: reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023956Z/
Do Now: CLI-FLAGS-003 Phase L3k.3c.4 — PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/parity_shim/$TS/trace_py_c_parity.log --config supervisor --device cpu --dtype float64 --phi-mode c-parity && NB_C_BIN=./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg -mat A.mat -floatfile /tmp/c_float.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -trace_pixel 685 1039 > reports/2025-10-cli-flags/phase_l/parity_shim/$TS/c_trace_phi.log && KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/parity_shim/$TS/trace_py_c_parity_per_phi.json reports/2025-10-cli-flags/phase_l/parity_shim/$TS/c_trace_phi.log
If Blocked: Capture fresh pix0/scattering vectors with KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/debug_pixel_trace.py --pixel-s 685 --pixel-f 1039 and document the delta under reports/2025-10-cli-flags/phase_l/parity_shim/$TS-blocked/ before touching code.
Priorities & Rationale:
- docs/fix_plan.md:458-480 — Next action now singles out pix0_z drift (Attempt #128 evidence) so Phase L3k.3c.4 must remove it before any other tweaks.
- reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023956Z/diff_summary.md — New comparison pinpoints pix0 as the first >1e-6 divergence.
- plans/active/cli-phi-parity-shim/plan.md:70-112 — Phase C4 still [P]; requires per-φ traces with ≤1e-6 deltas before moving to documentation (Phase D).
- specs/spec-a-core.md:211-224 — Normative φ rotation uses fresh vectors each step; parity shim must only introduce carryover, not geometry drift.
- docs/bugs/verified_c_bugs.md:166-204 — C bug description; confirms we should quarantine carryover while keeping spec mode clean.
How-To Map:
- Regenerate PyTorch per-φ traces: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/parity_shim/$TS/trace_py_c_parity.log --config supervisor --device cpu --dtype float64 --phi-mode c-parity` (main trace in parity_shim/$TS, per-φ JSON under `reports/2025-10-cli-flags/phase_l/per_phi/...$TS/`).
- Compare traces: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/parity_shim/$TS/trace_py_c_parity_per_phi.json reports/2025-10-cli-flags/phase_l/parity_shim/$TS/c_trace_phi.log > reports/2025-10-cli-flags/phase_l/parity_shim/$TS/compare_stdout.txt`.
- Validate targeted tests on CPU (and CUDA if available): `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c -v` and `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior::test_c_parity_mode_stale_carryover -v`.
- Archive SHA256 + env: reuse `scripts/tools/capture_env.py` (or copy template from `reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/env.json`) into the new `$TS` directory.
- When parity passes, update `reports/2025-10-cli-flags/phase_l/parity_shim/$TS/diff_summary.md` with the compare output and log metrics into docs/fix_plan.md.
Pitfalls To Avoid:
- Do not relax VG-1 tolerances; the goal is Δk ≤ 1e-6, not another shim fudge.
- Keep spec mode untouched — only the opt-in c-parity path may change.
- Preserve vectorization; no Python loops when adjusting pix0 math.
- Maintain device/dtype neutrality (no hard-coded `.cpu()`/`.double()`); reuse detectors’ existing conversions.
- Set `KMP_DUPLICATE_LIB_OK=TRUE` for every run involving torch to avoid MKL crashes.
- Don’t overwrite existing evidence directories; use a new `$TS` folder per run.
- Avoid editing files listed in docs/index.md (Protected Assets rule).
- Skip full pytest suite until targeted parity selectors and trace scripts pass.
- Document commands in `commands.txt` under the new report directory so the supervisor ledger stays reproducible.
- Leave `_phi_last_cache` behavior untouched until pix0 is corrected (no premature refactors).
Pointers:
- docs/fix_plan.md:458-480
- plans/active/cli-phi-parity-shim/plan.md:70-112
- reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023956Z/diff_summary.md
- specs/spec-a-core.md:211-224
- docs/bugs/verified_c_bugs.md:166-204
Next Up: After pix0 parity lands, close Phase C5 documentation and prep L3k.3d nb-compare per plan.
