Summary: Reconfirm HKL coverage for the supervisor command so the scaling trace stops zeroing F_cell.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling.py
Artifacts: reports/2025-10-cli-flags/phase_l/structure_factor/probe_20251117.log, reports/2025-10-cli-flags/phase_l/structure_factor/analysis_20251117.md, reports/2025-10-cli-flags/phase_l/scaling_audit/harness_hkl_state_20251117.txt
Do Now: CLI-FLAGS-003 Phase L3a — `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/structure_factor/probe.py --pixel 685 1039 --hkl scaled.hkl --fdump reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_20251006175946.bin --dtype float32 --device cpu`
If Blocked: Copy the probe stdout/stderr to `reports/2025-10-cli-flags/phase_l/structure_factor/probe_blocker_20251117.log`, record the failure context in docs/fix_plan.md Attempt history for CLI-FLAGS-003, and halt before editing any source files.
Priorities & Rationale:
- docs/fix_plan.md:448 pinpoints F_cell=0 as the gating blocker for CLI-FLAGS-003 and now requires a fresh Phase L3a rerun.
- plans/active/cli-noise-pix0/plan.md:248 spells out the Phase L3a/L3b evidence steps that must precede any simulator edits.
- specs/spec-a-cli.md:1 keeps the -hkl/-nonoise flag contract authoritative while we debug ingestion.
- docs/development/c_to_pytorch_config_map.md:1 reminds us of C↔Py HKL parity rules that the probe must satisfy.
- reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md:1 documents the I_before_scaling divergence we are trying to clear.
How-To Map:
- Back up existing artifacts first: `cp reports/2025-10-cli-flags/phase_l/structure_factor/probe.log reports/2025-10-cli-flags/phase_l/structure_factor/probe_20251007.log` (same for analysis.md) so the rerun has a clean diff trail.
- Run the probe command from repo root (see Do Now) and let it regenerate probe.log/analysis.md with current data.
- Immediately copy the fresh outputs to timestamped filenames listed under Artifacts (`cp probe.log probe_20251117.log`, etc.) before any additional runs overwrite them.
- Capture the HKL metadata snapshot by dumping the relevant keys from `trace_harness.py` (e.g., rerun harness or use a short Python snippet) and store results in `harness_hkl_state_20251117.txt`.
- Validate the pytest selector without executing tests: `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py > reports/2025-10-cli-flags/phase_l/structure_factor/collect_cli_scaling_20251117.log`.
- Diff `probe_20251117.log` against `config_snapshot.json` to identify mismatched h/k/l ranges, then summarize the findings in `analysis_20251117.md`.
Pitfalls To Avoid:
- Do not overwrite archived evidence without copying it to a datestamped filename first.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` set for every Python/PyTorch invocation to avoid MKL crashes.
- Stay in evidence mode only; no edits to simulator, harness, or CLI code this loop.
- Respect Protected Assets in docs/index.md; avoid renaming or deleting indexed files.
- Do not run the full pytest suite; stick to the collect-only selector listed above.
- Avoid changing device/dtype defaults in scripts—leave probe on CPU/float32 unless a later plan says otherwise.
Pointers:
- plans/active/cli-noise-pix0/plan.md:248
- docs/fix_plan.md:448
- reports/2025-10-cli-flags/phase_l/structure_factor/analysis.md:1
- reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot.json:1
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log:20
Next Up: 1. CLI-FLAGS-003 Phase L3c harness audit (ensure trace_harness attaches HKL metadata correctly); 2. CLI-FLAGS-003 Phase L3d regression (add structure-factor lookup assertions in tests/test_cli_scaling.py).
