Summary: Replace the sequential c-parity fallback with the planned vectorised carryover cache so VG-2 parity work can resume.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<new_ts>/{carryover_cache_validation,carryover_probe}/
Do Now: docs/fix_plan.md › [CLI-FLAGS-003] M2g — remove `_run_sequential_c_parity`, implement the pixel-indexed carryover cache, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q`.
If Blocked: Capture the current failing test log (`pytest --collect-only` + `-q`) under `reports/.../attempts_blocked/<ts>/` and note the blocker in docs/fix_plan.md Attempt history before stopping.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:17 — Plan now mandates removing the sequential fallback (M2g.2) before wiring Option 1 caches.
- docs/fix_plan.md:451 — Fix plan next actions call for restoring vectorisation and delivering the cache with validation artifacts.
- docs/development/pytorch_runtime_checklist.md:6 — Vectorisation rule forbids per-pixel Python loops; sequential path violates this.
- docs/bugs/verified_c_bugs.md:166 — c-parity bug description requires emulation via carryover without breaking differentiability.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — Option 1 design notes define tensor shapes and lifecycle you must implement.
- src/nanobrag_torch/simulator.py — Current `_run_sequential_c_parity` branch must be excised while keeping spec mode untouched.
How-To Map:
- Remove sequential branch: edit src/nanobrag_torch/simulator.py to drop `_run_sequential_c_parity()` and restore unified vectorised flow; keep spec mode behaviour identical.
- Implement cache: in src/nanobrag_torch/models/crystal.py allocate `(S,F,N_mos,3)` caches on detector-sized tensors, add `apply_phi_carryover` helper invoked from `_compute_physics_for_position` when `phi_carryover_mode=="c-parity"`.
- Update instrumentation: mirror helper usage in reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py so traces exercise the cache.
- Documentation: append a new dated subsection to reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md explaining removal of the sequential fallback and the cache tensor pathway.
- Testing: run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q`; if CUDA available, queue the trace harness command for M2h.2 (`python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --phi-mode c-parity --device cuda --dtype float64`).
- Artifact capture: stash pytest log, commands.txt, env.json, updated diagnosis notes, and any trace outputs under `reports/2025-10-cli-flags/phase_l/scaling_validation/<new_ts>/carryover_cache_validation/` and `.../carryover_probe/`.
Pitfalls To Avoid:
- Do not leave any per-pixel Python loops in production paths; maintain fully batched tensor ops.
- No `.detach()`, `.clone()` hacks, or in-place writes that sever gradients inside the carryover helper.
- Keep spec mode behaviour unchanged; only c-parity should engage the cache.
- Maintain device/dtype neutrality; allocate caches on the caller’s device/dtype without implicit `.cpu()`.
- Preserve debug instrumentation gating; new trace taps must stay behind debug_config checks.
- Include CLAUDE Rule #11 C-code snippets for any new helper implementations.
- Update docs/fix_plan.md Attempt history after work; don’t silently change plan state.
- Avoid touching Protected Assets listed in docs/index.md (e.g., loop.sh, supervisor.sh, input.md).
- Run only the mapped pytest selector; defer full suite until closing loop.
- Keep git history clean; no stray debug prints or commented-out code in final diff.
Pointers:
- plans/active/cli-noise-pix0/plan.md:17
- docs/fix_plan.md:451
- docs/development/pytorch_runtime_checklist.md:6
- docs/bugs/verified_c_bugs.md:166
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md
- src/nanobrag_torch/models/crystal.py:1000
- src/nanobrag_torch/simulator.py:720
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:50
Next Up: 1) Finish M2h validation bundle (CPU+CUDA traces, gradcheck); 2) Regenerate M2i cross-pixel traces and metrics once cache passes targeted tests.
