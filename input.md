Summary: Align scaling trace parity by forcing the supervisor harness to run PyTorch in c-parity mode and regenerate evidence for Phase M1.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: - pytest tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior::test_c_parity_mode_stale_carryover
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/summary.md; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling_cpu.log; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/metrics.json; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/commands.txt
Do Now: CLI-FLAGS-003 Phase M1 — add a phi-carryover-mode override to reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py, then rerun KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --phi-mode c-parity followed by KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling_cpu.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/summary.md --tolerance 1e-6.
If Blocked: Capture the current mismatch with compare_scaling_traces.py and write up findings in reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/summary.md, then log a new Attempt in docs/fix_plan.md explaining the blocker and attach the fresh metrics.json.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:46 emphasises Phase M’s requirement that F_cell, F_latt, and I_before_scaling match within 1e-6, so we must eliminate the 21.9% delta reported in docs/fix_plan.md:500.
- specs/spec-a-core.md:211-248 defines the φ rotation pipeline without carryover; matching the C bug therefore requires the c-parity shim described in docs/bugs/verified_c_bugs.md:166-191.
- reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T043438Z/trace_py_scaling_cpu_per_phi.log:1 shows φ₀ F_latt diverging when spec mode is used; we must re-run with c-parity so the k_frac values match the C trace at reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:264-288.
- The fresh evidence from reports/2025-10-cli-flags/phase_l/per_phi/trace_py_c_parity_per_phi.log:1 proves the shim yields the correct φ₀ lattice factor; updating the harness is the minimal fix before revisiting normalization code.
- Mapped pytest target guards against regressions in the shim after touching the harness and config plumbing.
How-To Map:
- Export env: `export KMP_DUPLICATE_LIB_OK=TRUE`
- Ensure editable install (`pip install -e .`) if dependencies missing.
- Update trace_harness.py to accept `--phi-mode {spec,c-parity}` and set `crystal_config.phi_carryover_mode` before instantiating Crystal.
- Run harness: `PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --phi-mode c-parity --out reports/2025-10-cli-flags/phase_l/scaling_validation/$ts/trace_py_scaling_cpu.log`
- Compare traces: `PYTHONPATH=src python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/$ts/trace_py_scaling_cpu.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/$ts/summary.md --tolerance 1e-6`
- Collect metrics: populate `$ts/metrics.json`, `$ts/commands.txt`, `$ts/sha256.txt`
- Pytest: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior::test_c_parity_mode_stale_carryover`
Pitfalls To Avoid:
- Do not rerun the full pytest suite; stay with the targeted selector and collect-only pass unless code paths change widely.
- Keep Device/dtype neutrality: honour CLI flag for both CPU float32/float64 if you touch CrystalConfig defaults; no hidden `.cpu()` or `.cuda()` moves.
- Respect Protected Assets—do not move or delete items referenced in docs/index.md.
- Route parity runs through c-parity mode only for the harness; leave default CLI behavior as spec-compliant.
- Preserve vectorization; no per-φ Python loops when wiring the shim flag.
- Keep artifact directories under reports/2025-10-cli-flags/phase_l/scaling_validation/ with timestamps (use `date -u +%Y%m%dT%H%M%SZ`).
- Update docs/fix_plan.md Attempt log only after new evidence is ready; avoid partial edits.
- Ensure compare_scaling_traces.py tolerances stay at 1e-6 per plan; do not relax thresholds.
Pointers:
- plans/active/cli-noise-pix0/plan.md:46-56 (Phase M tasks)
- docs/fix_plan.md:500-507 (I_before_scaling delta notes)
- specs/spec-a-core.md:211-248 (φ rotation contract)
- docs/bugs/verified_c_bugs.md:166-191 (C-PARITY-001 summary and shim guidance)
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:264-288 (C trace reference)
- reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T043438Z/trace_py_scaling_cpu_per_phi.log:1-10 (spec-mode divergence)
- reports/2025-10-cli-flags/phase_l/per_phi/trace_py_c_parity_per_phi.log:1-10 (shim match evidence)
Next Up: (1) Finish Phase M2 lattice-factor propagation fix once parity alignment is confirmed; (2) Re-run nb-compare per Phase N1–N3 after scaling metrics are green.
