Summary: Fix the Phase L2b scaling harness so it passes each MOSFLM reciprocal vector individually, captures a live TRACE_PY log, and unlocks the normalization diff.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase L2b)
Branch: feature/spec-based-2
Mapped tests: tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log, reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json, reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md, reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_fullrun.log
Do Now: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase L2b) → KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log --config supervisor (after patching the harness so `mosflm_a_star`, `mosflm_b_star`, `mosflm_c_star` each receive the correct tensor)
If Blocked: Record the failing stdout/stderr in reports/2025-10-cli-flags/phase_l/scaling_audit/attempts/<timestamp>/, log the blocker under CLI-FLAGS-003 Attempt History, and park the diff in notes.md before touching normalization.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:239 — L2b guidance now calls out the MOSFLM vector bug; harness must mirror CLI orientation before L2c resumes.
- docs/fix_plan.md:464-472 — Next Actions #1 explicitly require the harness orientation fix; without it F_cell stays 0 and parity analysis is meaningless.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log — Current trace shows F_cell=0 despite scaled.hkl having hkl (1,12,3); fixing the harness should populate real values.
- docs/development/c_to_pytorch_config_map.md:55-88 — Confirms MOSFLM orientation must be honoured for matrix inputs; use it as the contract while wiring the harness.
- tests/test_trace_pixel.py:22-243 — Regression guard that expects TRACE_PY to emit live physics scalars; keep it green after refactor.

How-To Map:
- Step 1: Edit reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py so lines 157-161 assign `mosflm_a_star=torch.tensor(a_star, ...)`, `mosflm_b_star=torch.tensor(b_star, ...)`, `mosflm_c_star=torch.tensor(c_star, ...)` instead of packing a list. Leave the tensors on the requested device/dtype.
- Step 2: Keep the HKL loader using `F_grid, metadata = read_hkl_file(...)`; after the tweak, re-run the script path to ensure metadata is threaded through without tuple unpack errors.
- Step 3: Execute `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log --config supervisor` from repo root. Confirm the log prints non-zero `F_cell`, `I_before_scaling`, and `I_pixel_final`.
- Step 4: Archive updated env + notes (overwrite trace_py_env.json, refresh notes.md with observed deltas) and stash the pre-fix log under a timestamped subdir before replacing trace_py_scaling.log.
- Step 5: Validate selector discovery with `pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics`, then rerun `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c-log reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py-log reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md` to re-establish Phase L2c evidence.

Pitfalls To Avoid:
- Don’t leave `mosflm_b_star`/`mosflm_c_star` as None; Crystal falls back to default orientation and zeros F_cell.
- Keep tensors on the requested device and dtype; avoid implicit `.cpu()` conversions inside the harness.
- Preserve KMP_DUPLICATE_LIB_OK before every torch import to prevent MKL crashes.
- Do not overwrite trace_py_fullrun.log; keep it as evidence of the regression.
- Avoid editing production simulator paths this loop—the task is harness-only.
- Respect Protected Assets policy; never move or delete files listed in docs/index.md.
- Keep ROI pixel (685,1039) unchanged so comparison tooling lines up with C trace.
- Refrain from running full pytest; stick to targeted selector discovery per supervisor evidence gate.
- No ad-hoc scripts in repo root—use existing validation tooling paths.
- Ensure HKL metadata is pulled from the dict; do not resurrect legacy tuple unpacking.

Pointers:
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:150-167 — Harness MOSFLM injection that needs correction.
- docs/fix_plan.md:464-470 — CLI-FLAGS-003 Next Actions detailing the orientation fix requirement.
- plans/active/cli-noise-pix0/plan.md:239-243 — Phase L2b checklist updated with MOSFLM guidance.
- scripts/validation/compare_scaling_traces.py:1-200 — Tool to rerun once the Py trace is live again.
- docs/development/c_to_pytorch_config_map.md:55-88 — Orientation parity rules to verify before rerun.

Next Up: If this passes quickly, proceed to Phase L2c by rerunning compare_scaling_traces.py and updating scaling_audit_summary.md with the new first divergence.
