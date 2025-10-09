Summary: Implement the φ rotation duality fix so PyTorch matches nanoBragg’s per-step lattice pipeline.
Mode: Parity
Focus: CLI-FLAGS-003 Phase M5c — φ rotation duality
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/
Do Now: CLI-FLAGS-003 Phase M5c — implement φ rotation duality, then run `pytest -v tests/test_cli_scaling_phi0.py` (CPU).
If Blocked: Capture a fresh per-φ trace with the existing harness and log it under `reports/.../fix_<timestamp>/`; note findings in docs/fix_plan.md Attempts.

Priorities & Rationale:
- specs/spec-a-core.md:204 — mandates fresh φ rotations with reciprocal regeneration; current PyTorch drift violates this.
- docs/fix_plan.md:451 — CLI-FLAGS-003 gating task remains M5c; parity progress is blocked until duality is fixed.
- plans/active/cli-noise-pix0/plan.md M5c row — now cites the captured nanoBragg snippet you must port verbatim.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/trace_py_scaling_per_phi.log — shows b_star_y drift that the fix must eliminate.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251009T005448Z/summary.md — highlights scale factors and volume ordering to preserve during implementation.

How-To Map:
- Regenerate PyTorch trace after the fix: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/trace_py_scaling.log`.
- Compare against the C baseline: `python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/compare_scaling_traces.txt`.
- Emit per-φ JSON/MD summaries mirroring M5a; reuse the harness flag for `--per-phi-log` if needed.
- Run targeted regression: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` (CPU) and, if CUDA is available, `KMP_DUPLICATE_LIB_OK=TRUE pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py`.
- Archive artifacts (`summary.md`, `metrics.json`, `run_metadata.json`, `sha256.txt`) under the new timestamp and record Attempt in docs/fix_plan.md.

Pitfalls To Avoid:
- Do not skip the Rule #11 docstring; cite `c_phi_rotation_reference.md` line ranges exactly.
- Preserve vectorization; no Python for-loops over φ or mosaic domains.
- Keep tensors on caller device/dtype—no implicit `.cpu()` or dtype casts.
- Reuse the actual volume from the misset stage (`V_cell = 1/V_star`); do not recompute via formula volume.
- Ensure reciprocal regeneration uses the `1e20/V_cell` scale factor mirroring nanoBragg.c.
- Avoid `.item()` on tensors that will participate in gradients.
- Maintain Protected Assets; do not touch files listed in docs/index.md.
- Update lattice_hypotheses.md once parity is green; leave breadcrumbs in docs/fix_plan.md Attempts.
- Capture new per-φ traces post-fix—missing evidence will block closure of Phase M5d.

Pointers:
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251009T005448Z/c_phi_rotation_reference.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251009T005448Z/summary.md
- specs/spec-a-core.md:204
- plans/active/cli-noise-pix0/plan.md
- docs/fix_plan.md:451

Next Up: Phase M5d — rerun compare_scaling_traces and close H4 once the implementation lands.
