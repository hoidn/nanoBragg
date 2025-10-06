Summary: Finish Phase K3 so MOSFLM scaling matches C before rerunning the supervisor command.
Phase: Implementation
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::test_f_latt_square_matches_c
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/orientation_delta_post_fix.md; reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain_post_fix.md; reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest_post_fix.log
Do Now: CLI-FLAGS-003 Phase K3a–K3c — env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v
If Blocked: Capture current mosflm_rescale.py output to reports/2025-10-cli-flags/phase_k/f_latt_fix/blocker.log and log the obstacle in docs/fix_plan.md Attempts before changing code.
Priorities & Rationale:
- src/nanobrag_torch/models/crystal.py:681 still rescales cross products even when MOSFLM matrices are supplied, so F_latt_b stays 21.6% high.
- src/nanobrag_torch/config.py:504 leaves polarization_factor at 1.0; C resets polar to 0.0 each pixel so the dynamic factor is recomputed (≈0.9126) and parity fails until we match it.
- plans/active/cli-noise-pix0/plan.md:173-185 spells out K3a–K3c deliverables we just updated; stay within that guidance.
- docs/fix_plan.md:448-461 now calls for MOSFLM rescale gating, polarization realignment, and the targeted scaling pytest before returning to Phase L.
- specs/spec-a-cli.md:1-120 documents the implicit MOSFLM pivot rules we must preserve while changing normalization.
How-To Map:
- PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/f_latt_fix/mosflm_rescale.py > reports/2025-10-cli-flags/phase_k/f_latt_fix/orientation_delta_post_fix.md
- PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_post_fix.log (reuse the supervisor command inputs baked into the harness)
- PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_j/analyze_scaling.py --c-log reports/2025-10-cli-flags/phase_j/trace_c_scaling.log --py-log reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_post_fix.log --out reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain_post_fix.md
- env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v | tee reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest_post_fix.log
Pitfalls To Avoid:
- Do not reintroduce the cross-product rescale for MOSFLM orientations; gate it strictly per plan.
- Keep device/dtype neutrality—no hard-coded .cpu()/.cuda(), and avoid creating new CPU tensors mid-path.
- Preserve differentiability (no .item(), no detaching) when adjusting polarization defaults.
- Obey the Protected Assets rule; avoid touching files listed in docs/index.md.
- Keep parity scripts under reports/…; do not drop new artifacts in repo root.
- When updating BeamConfig defaults, ensure CLI flags still override correctly (respect config map precedence).
- Record new evidence in docs/fix_plan.md Attempts once tasks finish; avoid silent progress.
- Maintain vectorization discipline—no scalar loops when editing cell tensors or scaling paths.
- Run only the targeted pytest listed; full suite waits until parity closes.
Pointers:
- src/nanobrag_torch/models/crystal.py:681
- src/nanobrag_torch/config.py:504
- plans/active/cli-noise-pix0/plan.md:173
- docs/fix_plan.md:448
- specs/spec-a-cli.md:1
Next Up: Phase L — rerun the supervisor nb-compare command once K3 artifacts are archived.
