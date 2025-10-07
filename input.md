Summary: Implement spec-compliant φ rotation so VG-1 passes before adding the parity shim
Mode: Parity
Focus: CLI-FLAGS-003 / Phase L3k.3c.3
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::test_k_frac_phi0_matches_c -v
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/trace_py_rot_vector_per_phi.json; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/comparison_summary.md; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/delta_metrics.json; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/pytest_phi0.log
Do Now: CLI-FLAGS-003 Phase L3k.3c.3 — remove `_phi_last_cache` default carryover, regenerate per-φ traces, then run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::test_k_frac_phi0_matches_c -v`
If Blocked: Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/collect_only.log`, capture Δk/Δb_y from the last good traces, and log hypotheses in diagnosis.md before touching code

Priorities & Rationale:
- specs/spec-a-core.md:211-214 — spec mandates fresh rotation each φ step; default behavior must agree before parity work
- docs/bugs/verified_c_bugs.md:166-204 — C-PARITY-001 documents the carryover bug we only emulate behind a shim
- plans/active/cli-noise-pix0/plan.md:303-311 — Phase L3k.3c.3/3c.4/3c.5 tasks define the gating work
- docs/fix_plan.md:450-464 — Next Actions call for spec-compliant rotation, then parity shim design, then doc/test refresh
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:116-353 — Current analysis memo establishes verification thresholds and logging expectations

How-To Map:
- Update `src/nanobrag_torch/models/crystal.py` to drop `_phi_last_cache` from the default path while keeping instrumentation on `phi = phi_start + (osc/phisteps)*tic`
- Rebuild per-φ traces: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/trace_py_rot_vector_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/c_trace_phi_20251123.log > reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/comparison_stdout.txt`
- After code edits run targeted pytest: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::test_k_frac_phi0_matches_c -v | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/pytest_phi0.log`
- Record Δk/Δb_y ≤1e-6 in `delta_metrics.json` and update VG-1 rows in `fix_checklist.md`

Pitfalls To Avoid:
- Do not reintroduce carryover in default flow; parity shim is deferred to L3k.3c.4
- Preserve vectorization—no Python loops per docs/architecture/pytorch_design.md
- Maintain device/dtype neutrality; avoid `.cpu()`, `.item()`, or tensor detaches in differentiable paths
- Keep tracing tensor-based; instrumentation must mirror production helpers per debugging SOP
- Respect Protected Assets and existing artifacts; write new evidence under timestamped `reports/2025-10-cli-flags/...` directories only
- Ensure φ sampling uses `osc/phisteps` (not `phisteps-1`); fix tests if they rely on old value
- Do not relax VG-1 thresholds; target ≤1e-6 per fix_checklist.md
- Keep parity tests referencing C trace values distinct from spec tests to avoid masking regressions
- Coordinate with future parity shim work—leave clear TODO noting follow-up flag addition after spec path passes
- Remove temporary scripts/logs outside the reports directory before finishing the loop

Pointers:
- specs/spec-a-core.md:211-214
- docs/bugs/verified_c_bugs.md:166-204
- plans/active/cli-noise-pix0/plan.md:303-311
- docs/fix_plan.md:460-464
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:116-353

Next Up:
1. Phase L3k.3c.4 — design the opt-in C carryover shim and associated tests once VG-1 is green
2. Phase L3k.3c.5 — refresh docs/tests to cover dual-mode behavior after shim landing
