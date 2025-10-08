Summary: Implement the Option B φ-cache so F_latt/I_before_scaling match C for the supervisor ROI and capture fresh parity evidence.
Mode: Parity
Focus: CLI-FLAGS-003 Phase M2g Option B φ-cache parity
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py; NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/20251214_optionB_patch/ (CPU traces, metrics, commands); reports/2025-10-cli-flags/phase_l/scaling_validation/20251214_optionB_patch_cuda/ (CUDA parity + gradcheck, optional)
Do Now: CLI-FLAGS-003 Phase M2g Option B cache fix — KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_cli_scaling.py -k TestFlattSquareMatchesC::test_f_latt_square_matches_c
If Blocked: Capture fresh CPU + CUDA trace harness runs (spec mode) under reports/2025-10-cli-flags/phase_l/scaling_validation/ATTEMPT_BLOCKED_<timestamp>/, drop ATTEMPT_BLOCKED.md summarising the issue, and stop without touching src/.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:101 keeps M2g/M2h open; clearing the Option B cache work unblocks all downstream parity phases.
- docs/fix_plan.md:451 lists Phase M2g/M2h as the top Next Actions, so progress here is the critical-path deliverable.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T174753Z/metrics.json documents the current `first_divergence="I_before_scaling"` failure; new evidence must replace this red bundle.
- specs/spec-a-core.md:211-228 fixes the physics contract (fresh φ rotation, sincg(π·h)); Option B must honor this spec while reproducing the C bug only in the shim path.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md captures the approved tensor shapes and lifecycle—follow it verbatim.

How-To Map:
Step 1: Re-read plans/active/cli-noise-pix0/plan.md Phase M2g table (lines 101-121) plus the Option B memo at reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md to refresh the required tensor flow.
Step 2: Collect baseline evidence by running `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --device cpu --mode spec` and, if CUDA is available, rerun with `--device cuda`; stash logs + env.json in the new 20251214_optionB_patch directories.
Step 3: Inspect current cache helpers in src/nanobrag_torch/models/crystal.py and simulator.py; note where `(slow_indices, fast_indices)` need to flow without `.item()`, `.clone()`, or `.detach()`.
Step 4: Implement the Option B cache updates (Crystal.initialize_phi_cache/apply_phi_carryover/store_phi_final and the simulator batch plumbing) keeping the spec path untouched and citing the nanoBragg.c lines in docstrings per CLAUDE Rule #11.
Step 5: Run `pytest -v tests/test_cli_scaling_phi0.py` (spec regression) and the Do Now parity command to verify no regressions; expect the parity test to fail until the cache is correct.
Step 6: Re-run the trace harness command(s) from Step 2; confirm `metrics.json` now reports `first_divergence=None` and that F_latt, polar, omega deltas fall ≤1e-6 relative.
Step 7: Execute the grad/device validation set: CPU + CUDA trace harness, `pytest -v tests/test_cli_scaling_phi0.py`, and (optional) `python reports/2025-10-cli-flags/phase_l/scaling_validation/gradcheck_probe.py --device cpu --dtype float64` to ensure gradients survive.
Step 8: Update reports/2025-10-cli-flags/phase_l/scaling_validation/20251214_optionB_patch/ with commands.txt, env.json, metrics.json, trace logs, summary.md, dir listing, and sha256.txt; mirror CUDA artifacts if run.
Step 9: Append Attempt # (next) in docs/fix_plan.md under [CLI-FLAGS-003] summarising the Option B fix, metrics, artifacts, and command list; mark M2g or M2h checklist rows [D] if exit criteria are met.
Step 10: Note outcomes and artifact paths in galph_memory.md’s next supervisor entry to keep the handoff trail intact before staging changes.

Pitfalls To Avoid:
- Do not resurrect the phi_carryover shim or reintroduce sequential fallbacks—keep loops fully vectorised.
- Avoid `.clone()`, `.detach()`, or `.item()` on tensors participating in gradients; maintain device/dtype neutrality.
- Spec path must remain deterministic; guard shim-specific logic so spec mode stays untouched.
- Keep cache tensors on the caller’s device; never hard-code `.cpu()`/`.cuda()` allocations.
- Always capture KMP_DUPLICATE_LIB_OK=TRUE and NB_RUN_PARALLEL env vars in commands.txt for reproducibility.
- Do not overwrite existing red evidence bundles; create new timestamped directories and leave prior artifacts intact.
- Respect Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md) and avoid renaming listed files.
- Remember to rerun pytest after edits; parity evidence without tests is not acceptable.
- Ensure trace harness uses the spec-only flag; do not flip back to the deprecated c-parity path.
- Keep code comments concise and only where the control flow is non-obvious.

Pointers:
- plans/active/cli-noise-pix0/plan.md:101 (M2g Option B cache guidance + subtasks)
- docs/fix_plan.md:451 (Next Actions now pointing to M2g/M2h)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T174753Z/metrics.json (current failing metrics reference)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md (approved batch design)
- specs/spec-a-core.md:211-228 (normative φ rotation + sincg definition for parity checks)

Next Up: If Option B closes with green metrics, proceed to plans/active/cli-noise-pix0/plan.md Phase M2h validation (CUDA parity + gradcheck sign-off).
