Summary: Capture Phase L3k.3c.4 parity evidence—per-φ traces and targeted pytest logs for spec vs c-parity modes—so CLI-FLAGS-003 can advance to nb-compare.
Mode: Parity
Focus: CLI-FLAGS-003 — Phase L3k.3c.4 parity shim evidence capture
Branch: feature/spec-based-2
Mapped tests: tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior; tests/test_cli_scaling_phi0.py::TestPhiZeroParity
Artifacts: reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/trace_py_spec.log; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/trace_py_c_parity.log; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/c_trace_phi.log; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/per_phi_summary_spec.txt; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/per_phi_summary_c_parity.txt; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/delta_metrics.json
Do Now: CLI-FLAGS-003 Phase L3k.3c.4 – run the parity trace harness twice (spec + c-parity) via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --dtype float64 --device cpu --phi-mode <mode> --out reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/trace_py_<mode>.log`, then collect a fresh C reference (`NB_C_BIN=./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg ... -trace_pixel 685 1039`) and compare with `KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py <py_json> <c_log> | tee reports/.../per_phi_summary_<mode>.txt`.
If Blocked: Capture the failing command + stderr to `reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/attempt_fail.log`, note whether the harness needs refactoring (e.g., add `--phi-mode` plumbing), and log an Attempt under CLI-FLAGS-003 before pausing.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:306-314 marks L3k.3c.4 as [D] except for Phase C4 evidence; completing these traces unblocks Phase L3k.3c.5 docs/tests.
- plans/active/cli-phi-parity-shim/plan.md:47-55 requires per-φ comparisons for both modes plus Δk/Δb tolerances ≤1e-6.
- docs/fix_plan.md:450-470 now calls for parity shim evidence capture ahead of documentation updates.
- docs/bugs/verified_c_bugs.md:166-204 describes the C-PARITY-001 baseline the parity mode must reproduce.
- tests/test_cli_scaling_phi0.py:1-120 keeps spec-mode assertions locked; we must prove parity mode matches C without regressing spec.
How-To Map:
- Prep directory: `timestamp=$(date -u +%Y%m%dT%H%M%SZ); outdir=reports/2025-10-cli-flags/phase_l/parity_shim/$timestamp; mkdir -p "$outdir"`.
- Harness (add `--phi-mode` if missing by threading a new argparse choice into trace_harness.py that injects `phi_carryover_mode` into `params['crystal']`):
  - Spec run: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --dtype float64 --device cpu --phi-mode spec --out "$outdir/trace_py_spec.log"`.
  - Parity run: same command with `--phi-mode c-parity` and output to `trace_py_c_parity.log`.
  - Each invocation should emit a per-φ JSON (e.g., trace_py_per_phi.json) and env/config snapshots; copy them into `$outdir`.
- C trace: `NB_C_BIN=./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg -mat A.mat -floatfile c_phi.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -trace_pixel 685 1039 > "$outdir/c_trace_phi.log" 2>&1`.
- Per-φ comparisons: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py "$outdir/trace_py_spec_per_phi.json" "$outdir/c_trace_phi.log" | tee "$outdir/per_phi_summary_spec.txt"` and repeat for the parity JSON (`trace_py_c_parity_per_phi.json`). Record Δk/Δb_y, ensure parity mode ≤1e-6; include final metrics in `delta_metrics.json`.
- Tests: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior -v > "$outdir/pytest_phi_carryover.log"` and `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity -v > "$outdir/pytest_phi0.log"`.
- Update plan/fix_plan: mark `plans/active/cli-phi-parity-shim/plan.md` C4/C5 accordingly, append Attempt in docs/fix_plan.md with artifact paths, and refresh `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` with the new parity numbers.
Pitfalls To Avoid:
- Keep spec mode untouched as default; do not flip defaults while adding harness options.
- Use `PYTHONPATH=src` so the harness exercises the editable install, not site-packages copies.
- Preserve tensor device/dtype neutrality—ensure harness indices and overrides stay on the chosen device.
- Capture SHA256 hashes for every generated file in `$outdir/sha256.txt` (use `shasum -a 256`); parity review depends on reproducibility.
- Do not overwrite historic traces; use the new timestamped folder every run.
- Respect Protected Assets (docs/index.md) when editing harness or logging outputs.
- If CUDA is available, note whether traces/tests were CPU-only and document rationale (parity gating is CPU baseline, but mention GPU status).
- Avoid running nb-compare yet; stay scoped to per-φ validation until VG-1 thresholds confirmed.
- Ensure C trace build uses the instrumented binary (`NB_C_BIN=./golden_suite_generator/nanoBragg`); do not rebuild the frozen root binary.
Pointers:
- plans/active/cli-phi-parity-shim/plan.md:47-55 — Phase C4 expectations and tolerance thresholds.
- plans/active/cli-noise-pix0/plan.md:300-315 — L3k.3c subphase checklist and evidence routing.
- docs/fix_plan.md:450-470 — Updated Next Actions emphasizing parity evidence capture.
- specs/spec-a-core.md:211-214 — Spec φ rotation rule (identity at φ=0).
- docs/bugs/verified_c_bugs.md:166-204 — C-PARITY-001 reference values for φ=0 carryover.
- tests/test_phi_carryover_mode.py:1-200 — Existing parity-mode tests you must keep green.
Next Up: (1) Phase L3k.3c.5 doc updates once traces are archived; (2) Prepare nb-compare rerun (Phase L3k.3d) with `--py-args "--phi-carryover-mode c-parity"` after VG-1 passes.
