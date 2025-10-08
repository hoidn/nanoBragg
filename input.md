Summary: Wire the Option B pixel cache through the vectorised simulator so VG-2 parity work can resume.
Mode: Parity
Focus: CLI-FLAGS-003 / plans/active/cli-noise-pix0/plan.md > Phase M2g (tasks M2g.3-M2g.4)
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/carryover_cache_plumbing/
Do Now: CLI-FLAGS-003 M2g.3-M2g.4 - allocate the per-pixel cache tensors and thread `(slow_indices, fast_indices)` through `_compute_physics_for_position`, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q`.
If Blocked: If wiring stalls, capture the current diff plus a failing `pytest --collect-only tests/test_cli_scaling_parity.py` log in the new artifact folder, note blockers in docs/fix_plan.md, and stop before altering production code further.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:102 - Phase M2g remains open; cache tensors must exist before validation can proceed.
- plans/active/cli-noise-pix0/plan.md:112 - Checklist item M2g.3 spells out the required `(S,F,N_mos,3)` buffers and device/dtype neutrality.
- plans/active/cli-noise-pix0/plan.md:113 - M2g.4 mandates applying cached phi vectors inside the vectorised physics path without Python loops.
- docs/fix_plan.md:3383 - Next Actions already highlight continuing Option B cache plumbing now that commit 678cbf4 restored tensor signatures.
- docs/bugs/verified_c_bugs.md:166 - C-PARITY-001 reminder: this shim emulates a C-side bug; spec mode must remain untouched.
- specs/spec-a-core.md:204 - Normative phi pipeline requires fresh rotations, so ensure the shim only runs when `phi_carryover_mode="c-parity"`.
How-To Map:
- Start from `src/nanobrag_torch/models/crystal.py`; add `_phi_cache_*` tensors sized `(detector.spixels, detector.fpixels, mosaic_domains, 3)` in `initialize_phi_cache`, respecting detector device/dtype.
- Ensure cache invalidation happens whenever detector dimensions or mosaic domains change (reuse existing invalidation hooks).
- In `Simulator.run()` (and helpers), derive `(slow_indices, fast_indices)` tensors from the ROI grid using tensor operations (`torch.where` or meshgrid) and pass them to `apply_phi_carryover` / `store_phi_final`.
- Inside `_compute_physics_for_position`, insert the Option B substitution by indexing tensors (`cache[slow_indices, fast_indices]`) and using tensor-friendly guards (`torch.where`, boolean masks) to replace only phi=0 slices.
- Keep spec mode fast-path unchanged by guarding the new code with `if crystal.phi_carryover_mode == "c-parity"` checks that avoid `.item()`; use tensor comparisons.
- Update docstrings to reflect batched semantics while retaining the nanoBragg.c reference per CLAUDE Rule #11.
- After wiring, run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q` and store stdout/stderr as `pytest_cpu.log` in the artifact folder.
- Record `python --version`, `python -c "import torch; print(torch.__version__)"`, and git SHA into `env.json` / `git_sha.txt` alongside `commands.txt` and `sha256.txt`.
- Summarise behaviour changes (tensor shapes, cache hit evidence) in `analysis.md`, and drop any updated trace harness commands into `commands.txt`.
Pitfalls To Avoid:
- Do not reintroduce `_run_sequential_c_parity()` or any per-pixel Python loops.
- Avoid `.item()`, `.detach()`, or `.clone()` on differentiable tensors inside the cache path.
- Keep all new tensors on the caller's device/dtype; no hard-coded `.cpu()` or `.cuda()` moves.
- Respect `(slow, fast)` ordering when building pixel indices; match detector conventions.
- Do not edit spec mode tolerances or documentation while focusing on Option B wiring.
- Leave Protected Assets (loop.sh, supervisor.sh) untouched.
- Don't run the full pytest suite; limit execution to the mapped selector unless instructed otherwise.
- Keep vectorisation intact; use broadcasting instead of expanding Python loops across phi or mosaic domains.
- Ensure traces remain opt-in via debug_config so production paths stay clean.
Pointers:
- plans/active/cli-noise-pix0/plan.md:112
- plans/active/cli-noise-pix0/plan.md:113
- docs/fix_plan.md:3383
- src/nanobrag_torch/models/crystal.py:244
- src/nanobrag_torch/simulator.py:718
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md
- specs/spec-a-core.md:204
- docs/bugs/verified_c_bugs.md:166
Next Up: If the cache wiring lands quickly, move to M2g.5 trace/tooling updates before attempting validation.
