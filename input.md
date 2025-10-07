Summary: Attach scaled.hkl into the scaling trace harness so TRACE_PY reports F_cell=190.27 for the supervisor pixel and the harness evidence matches the new probe run.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling.py
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/collect_cli_scaling_20251117.log, reports/2025-10-cli-flags/phase_l/scaling_audit/harness_hkl_state_20251117.txt, reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251117.log, reports/2025-10-cli-flags/phase_l/structure_factor/analysis.md
Do Now: CLI-FLAGS-003 Phase L3c harness audit — KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float32 --out trace_py_scaling.log
If Blocked: Capture stdout/stderr to reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness_failure_20251117.log, note the exception (command + stack) in docs/fix_plan.md Attempt history for CLI-FLAGS-003, and stop before editing simulator or CLI code.
Priorities & Rationale:
- docs/fix_plan.md:448-463 records the refreshed next actions; L3c harness audit is explicitly the first todo after the probe success.
- plans/active/cli-noise-pix0/plan.md:249-261 promotes L3a to [D] and keeps L3c/L3d open until scaled.hkl is threaded through harness + CLI.
- specs/spec-a-cli.md:60-120 defines the -hkl / Fdump precedence and -pix0_vector semantics that must remain correct when we change ingestion.
- docs/development/c_to_pytorch_config_map.md:1-40 reiterates that HKL tensors must stay on the caller device/dtype; the harness should respect that contract.
- reports/2025-10-cli-flags/phase_l/structure_factor/probe_20251117.log:1 proves F_cell=190.270004 already lives in scaled.hkl, so the harness must surface it without fallback hacks.
- reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md:1 pinpoints `I_before_scaling` (F_cell=0) as the first divergence, so today’s evidence should replace that zero.
How-To Map:
- Ensure env vars are in place: export KMP_DUPLICATE_LIB_OK=TRUE and confirm NB_C_BIN still points at golden_suite_generator/nanoBragg for later comparisons.
- Snapshot existing artifacts so the rerun diff is clean: cp reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_pre_L3c.log; cp reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot.json reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot_pre_L3c.json; cp reports/2025-10-cli-flags/phase_l/scaling_audit/harness_hkl_state_fixed.txt reports/2025-10-cli-flags/phase_l/scaling_audit/harness_hkl_state_pre_L3c.txt (if the file exists).
- Run the harness command from repo root (see Do Now). Expect the run to emit TRACE_PY lines, config snapshot, env snapshot, and the final pixel intensity summary.
- Immediately promote the refreshed outputs to timestamped names so earlier evidence is preserved:
  - cp reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251117.log
  - cp reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot.json reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot_20251117.json
  - cp reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env_20251117.json
- Dump the HKL metadata actually attached by the harness so we can compare ranges against the earlier probe: PYTHONPATH=src python - <<'PY' > reports/2025-10-cli-flags/phase_l/scaling_audit/harness_hkl_state_20251117.txt
from nanobrag_torch.io.hkl import read_hkl_file
F, meta = read_hkl_file('scaled.hkl', default_F=0.0)
for key in sorted(meta):
    print(f"{key}: {meta[key]}")
PY
- Inspect the new trace to ensure F_cell now matches: grep 'TRACE_PY: F_cell' reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251117.log
- Update reports/2025-10-cli-flags/phase_l/structure_factor/analysis.md with two short bullet sections: (1) probe summary (grid ranges, F_cell), (2) harness confirmation (metadata snapshot path, F_cell match, remaining deltas if any).
- Re-run the mapped selector to confirm tests still collect: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py > reports/2025-10-cli-flags/phase_l/scaling_audit/collect_cli_scaling_20251117.log
- Record a short diff note under docs/fix_plan.md Attempt history describing the harness rerun, file names, and whether F_cell still needs work.
- Stage but do not commit until supervisor loop ends; keep notes about any harness edits you make so we can document them explicitly.
Pitfalls To Avoid:
- Do not touch simulator scaling code or CLI parser yet; L3c is about evidence and harness parity only.
- No new ad-hoc scripts in repo root—keep tooling under reports/… per SOP.
- Avoid `.item()` on tensors destined for gradients; if you need scalar logging, use `.detach().cpu().item()` in test-only code paths.
- Keep harness device/dtype neutral; never hard-code CPU tensors when running on CUDA.
- Do not delete prior evidence logs; copy-before-overwrite is mandatory for reproducibility.
- Stay on the supervisor branch; no rebases or merges mid-loop.
- Resist rerunning the full parity command until plan Phase L3 closes; nb-compare waits for L4.
- Maintain Protected Assets (`docs/index.md` list) untouched.
- Keep Mode Parity focus—avoid perf tweaks or vectorization work in this loop.
- Capture all new files with descriptive timestamps to simplify archive later.
Pointers:
- docs/fix_plan.md:448
- plans/active/cli-noise-pix0/plan.md:249
- specs/spec-a-cli.md:60
- docs/development/c_to_pytorch_config_map.md:1
- docs/development/testing_strategy.md:1
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1
- reports/2025-10-cli-flags/phase_l/structure_factor/probe_20251117.log:1
- reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md:1
Next Up: 1. Audit src/nanobrag_torch/__main__.py HKL loading to mirror the harness attachment pattern; 2. Add a structure-factor + intensity regression in tests/test_cli_scaling.py once HKL ingestion is fixed.
