Summary: Quantify float32 vs float64 impact on the CLI scaling chain before touching normalization code.
Phase: Evidence
Focus: CLI-FLAGS-003 — Phase K3d dtype-sensitivity sweep
Branch: main
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/dtype_sweep/
Do Now: CLI-FLAGS-003 K3d dtype sensitivity; NB_PYTORCH_DTYPE=float64 PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/f_latt_fix/analyze_scaling.py
If Blocked: If the float64 run crashes, capture stdout/stderr to dtype_sweep/attempt_failed.log, rerun once at default dtype for comparison, and log config + traceback in Attempt History.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:173 — K3d demands dtype evidence before we reopen implementation work on normalization.
- docs/fix_plan.md:448 — New Next Actions gate K3a/K3c on confirming whether rounding causes the 21.6% F_latt drift.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md — Current float32 ratios show F_latt_b≈46.98 vs C 38.63, so we need a dtype control run.
- reports/2025-10-cli-flags/phase_j/trace_c_scaling.log — C baseline keeps h=2.0012, so compare PyTorch float64 traces against this reference.
- src/nanobrag_torch/simulator.py:250 — sincg inputs depend on precise h/k/l; confirming dtype sensitivity de-risks code changes here.
How-To Map:
- Ensure editable install is active and NB_C_BIN remains pointed at golden_suite_generator/nanoBragg.
- From repo root run:
  1) `NB_PYTORCH_DTYPE=float64 PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/f_latt_fix/analyze_scaling.py`.
  2) Move generated logs/JSON into `reports/2025-10-cli-flags/phase_k/f_latt_fix/dtype_sweep/` (stamp subdir).
  3) Record key deltas (hkl_frac, F_latt_*, polar) comparing float32 vs float64 in `dtype_sweep/dtype_sensitivity.md`.
- Note the environment snapshot (commit hash, torch version) alongside results.
Pitfalls To Avoid:
- Do not edit source this loop; gather evidence only.
- No pytest runs while Phase=Evidence.
- Keep Protected Assets untouched (docs/index.md references).
- Avoid clobbering existing reports—create timestamped subdirectories.
- Ensure NB_PYTORCH_DTYPE override is cleared afterward.
- Respect device/dtype neutrality—no hard-coded `.cpu()`/`.cuda()` in probes.
- Capture stdout/stderr for reproducibility; don’t rely on scrollback.
- Do not delete prior scaling artifacts; we still need baseline comparisons.
- Refrain from pushing until supervisor review closes the loop.
Pointers:
- plans/active/cli-noise-pix0/plan.md:173
- reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log
- reports/2025-10-cli-flags/phase_j/trace_c_scaling.log
- src/nanobrag_torch/models/crystal.py:681
- src/nanobrag_torch/simulator.py:250
- docs/development/c_to_pytorch_config_map.md
- specs/spec-a-core.md
Next Up:
1. If dtype drift is confirmed, tackle K3a (mosflm rescale guard) with post-fix orientation traces.
2. If float64 matches C, proceed to K3c regression/docs updates after implementing the needed float32 fix.
