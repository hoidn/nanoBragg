Summary: Capture fresh per-φ traces to pinpoint the F_latt drift and confirm `-nointerpolate` parity for the supervisor command.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/<timestamp>/
Do Now: CLI-FLAGS-003 Phase M5a — extend `trace_harness.py`/PyTorch trace hooks to emit `TRACE_PY_PHI` rows (k_frac, F_latt_b, F_latt) for every φ, then rerun `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/<timestamp>/` and refresh `compare_scaling_traces.py` in that folder.
If Blocked: If instrumentation changes fail, fall back to copying the existing trace harness, hard-code a new log writer under `reports/.../per_phi/debug/`, rerun the command above, and document the failure plus raw outputs in `blocked.md` inside the new folder.
Priorities & Rationale:
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/trace_py_scaling.log:15 — PyTorch `rot_b` deviates (+0.0457 along y) from C baseline, driving the F_latt delta.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log:271 — C traces show k_frac = -0.6073, vs PyTorch -0.5892, confirming φ rotation misalignment.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/trace_py_scaling.log:29 — PyTorch still uses tricubic F_cell (155.17) despite the supervisor command passing `-nointerpolate`; ensure the rerun captures whether the flag propagates.
- plans/active/cli-noise-pix0/plan.md — Phase M5 requires per-φ instrumentation before attempting the lattice fix; today’s evidence isolates the precise fields to log.
How-To Map:
- KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/<timestamp>/
- python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/<timestamp>/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/<timestamp>/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/<timestamp>/summary.md
- KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py > reports/2025-10-cli-flags/phase_l/scaling_validation/per_phi/<timestamp>/collect.log
Pitfalls To Avoid:
- Do not reintroduce the φ carryover shim; keep rotations spec-compliant unless the plan explicitly says otherwise.
- Preserve vectorization when adding trace taps; avoid per-φ Python loops inside the simulator.
- Respect Protected Assets in docs/index.md when staging artifacts.
- Keep device/dtype neutrality—update hooks to work on CPU and CUDA without `.cpu()` conversions.
- Ensure `-nointerpolate` flag flows through config rather than hard-coding interpolation mode.
Pointers:
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/trace_py_scaling.log:15
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log:271
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json
- plans/active/cli-noise-pix0/plan.md
Next Up: Re-run the same harness on CUDA once per-φ traces match, then pivot to verifying the `-nointerpolate` path in `Crystal.lookup_structure_factor`.
