Summary: Restore Option B batch cache plumbing by reversing the scalar regression in the c-parity helpers so VG-2 parity work can resume.
Mode: Parity
Focus: CLI-FLAGS-003 / plans/active/cli-noise-pix0/plan.md › Phase M2g.2b
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/carryover_cache_plumbing/
Do Now: CLI-FLAGS-003 M2g.2b — restore batched cache signatures, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q`
If Blocked: Capture the failure log under `reports/.../carryover_cache_plumbing/<timestamp>/pytest_blocked.log`, update docs/fix_plan.md Attempts with blockers, and rerun `pytest --collect-only tests/test_cli_scaling_parity.py` to document collection status in `attempts_history.md`.
Priorities & Rationale:
- docs/fix_plan.md:451 — Next Actions front-load undoing commit f84fd5e before wiring Option B.
- plans/active/cli-noise-pix0/plan.md:27 — Status snapshot records the scalar regression and mandates tensor signatures.
- plans/active/cli-noise-pix0/plan.md:103 — Phase M2g.2b checklist requires batched `(slow_indices, fast_indices)` and tensor-native validity checks.
- plans/active/cli-noise-pix0/plan.md:104 — Phase M2g.3 depends on tensor caches, so M2g.2b is foundational.
- plans/active/cli-phi-parity-shim/plan.md:32 — Documentation Phase D assumes the shim stays opt-in; wiring must keep spec mode untouched.
- specs/spec-a-core.md:204 — Normative φ rotation forbids carryover, guiding how spec mode should behave.
- docs/bugs/verified_c_bugs.md:166 — C-PARITY-001 write-up frames what the shim is emulating and why the bug must remain isolated.
- docs/development/pytorch_runtime_checklist.md:5 — Vectorization guardrail blocks the scalar API from persisting.
- docs/development/testing_strategy.md:44 — Device/dtype discipline requires CPU smoke for every parity touchpoint.
- src/nanobrag_torch/models/crystal.py:245 — Current implementation shows the exact regression we must reverse.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/analysis.md — Captures the previous scaling divergence to compare against after the fix.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T100653Z/carryover_probe/analysis.md — Documents cross-pixel behaviour that must change once cache plumbing works.
- docs/architecture/detector.md:312 — Pixel indexing conventions ensure `(slow, fast)` ordering stays consistent when threading indices.
- docs/architecture/pytorch_design.md:118 — Broadcast shape guidance to follow when reintroducing tensor indices.
- docs/index.md:15 — Protected Assets list reminder (loop.sh, supervisor.sh) before editing automation scripts referenced by plan.
- docs/bugs/verified_c_bugs.md:180 — Details on tolerance split (spec vs c-parity) to respect in regression tests.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T072513Z/run_metadata.json — Baseline environment snapshot for comparison with new env.json.
- docs/fix_plan.md:919 — Prior attempt entries on cache gradients; read to avoid repeating abandoned approaches.
- docs/development/pytorch_runtime_checklist.md:16 — Reminder to cite runtime checklist in plan updates and commit messages.
- CLAUDE.md:190 — Implementation rules reiterating no `.item()` on differentiable tensors, relevant when revising cache gates.
How-To Map:
- Restore `apply_phi_carryover` and `store_phi_final` to accept tensor `(slow_indices, fast_indices)` arguments; rename variables accordingly for clarity.
- Remove the `.item()` validity branch and replace it with tensor-based checks such as `cache_real_a.abs().sum(dim=(-1, -2)) > 0` applied per batch.
- Ensure cache lookups use advanced indexing (`cache[slow_indices, fast_indices]`) that broadcasts correctly without Python loops.
- Preserve device/dtype neutrality by allocating caches via detector tensors (`torch.zeros_like`) rather than default CPU factories.
- Confirm `_phi_cache_initialized` logic and invalidation behaviour survive the signature change.
- Thread tensor indices back through the simulator hot path (`_render_roi_pixels`, `_compute_physics_for_position`) without resurrecting `_run_sequential_c_parity()`.
- Audit docstrings to retain the nanoBragg.c citation per CLAUDE Rule #11 and adjust wording to reflect batched semantics.
- Re-run `black`/`ruff` if needed so signature changes keep formatting consistent (no manual loops introduced).
- Execute `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q` and capture stdout/stderr in `pytest_cpu.log` plus command listing.
- Record environment details (`python --version`, `torch.__version__`) into `env.json` inside the new artifact directory.
- Summarise changes, tensor shapes, and outstanding tasks in `reports/.../carryover_cache_plumbing/<timestamp>/analysis.md` for plan cross-linking.
- Update `reports/.../phi_carryover_diagnosis.md` with a dated subsection referencing hash f84fd5e and the restored tensor API.
- Log the work in docs/fix_plan.md Attempts once test output is archived, including exit codes and artifact paths.
- Run `pytest --collect-only tests/test_cli_scaling_parity.py` before edits to document baseline behaviour in `collect_before.log`.
- Optionally add a temporary tensor assert (e.g., check batch dims) under a debug flag to validate shapes during development; remove before committing.
- Verify that gradients still flow by running a quick `torch.autograd.grad` probe on cached tensors in an interactive notebook (log output to `grad_probe.txt`).
- After pytest, run `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --phi-mode c-parity --dry-run` to ensure tooling still imports with the new signatures.
- Update `plans/active/cli-noise-pix0/plan.md` checklist states (flip M2g.2b to [P] or [D]) immediately after pushing code.
- Add a TODO comment in code if further wiring (M2g.3+) is pending so reviewers track follow-up items (remove once resolved).
- Record git hash snapshots in `analysis.md` (before/after) to simplify future regressions.
- If CUDA is unavailable, note that explicitly in `analysis.md` so the next loop can schedule GPU validation.
- Cross-check the restored signature against existing traces (`trace_py_scaling.log`) to ensure logging still matches expected variable names.
- After code edits, run `python -m compileall src/nanobrag_torch/models/crystal.py` to catch syntax errors early and log output.
- Verify mypy/ruff status if the repo mandates them; capture any static-analysis deltas in `analysis.md`.
- Prepare a short diff summary (paths + intent) inside the artifact folder to ease review for the next loop.
- Tag TODOs in the code with `# TODO(galph-M2g)` so they are discoverable via `rg` until cleared.
- Double-check that config dataclasses still serialise correctly if signatures changed (run `python -m scripts.debug_pixel_trace --help` to ensure CLI still constructs configs).
Pitfalls To Avoid:
- Do not retain scalar `slow_index`/`fast_index` parameters; commit f84fd5e must be superseded.
- Avoid `.item()` on cache tensors; use tensor reductions that keep gradients intact.
- No Python loops over pixels or φ—vectorization is mandatory.
- Ensure spec mode pathways bypass the cache entirely; only c-parity should touch the stored tensors.
- Maintain gradient flow; no `.detach()` or `.clone()` guardrails should reappear.
- Keep caches on the caller’s device/dtype; no implicit `.cpu()` or new CPU tensors inside the loop.
- Preserve Protected Assets referenced in docs/index.md; do not relocate loop.sh or supervisor scripts.
- Run commands from repo root with documented env vars; include `KMP_DUPLICATE_LIB_OK=TRUE` explicitly.
- Watch for shape mismatches when broadcasting cache tensors; add asserts if necessary for debugging.
- Update plan tables after work; leaving M2g.2b unchecked stalls downstream phases.
- Do not silently change tolerance thresholds; any adjustment must be justified in docs/fix_plan.md.
- Avoid touching unrelated files (`vectorization.md`, `docs/bugs/...`) during this focused loop to keep review surface small.
- Do not rerun the full pytest suite yet; targeted parity test is sufficient until wiring completes.
- Refrain from editing `supervisor.sh` or automation harnesses unless explicitly coordinated.
- Resist the temptation to add ad-hoc debug prints; use existing tracing scripts and remove temporary asserts before commit.
- Do not forget to clean up temporary validation files; every artifact must sit under the timestamped directory.
- Avoid editing docs outside the scope of M2g.2b unless cross-referenced in the plan.
- Keep commit messages explicit (reference Phase M2g.2b) to simplify future archaeology.
Pointers:
- src/nanobrag_torch/models/crystal.py:245 — Scalar signature to replace with tensor indices.
- src/nanobrag_torch/models/crystal.py:297 — `.item()` validity gate to rewrite.
- src/nanobrag_torch/models/crystal.py:381 — Cache write sites needing batched indexing.
- docs/fix_plan.md:451 — CLI-FLAGS-003 ledger entry for attempts and metrics logging.
- plans/active/cli-noise-pix0/plan.md:24 — Status snapshot listing outstanding parity blockers.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T072513Z/metrics.json — Baseline metrics to beat once cache wiring works.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — Central diagnosis doc to update.
- docs/development/testing_strategy.md:90 — Guidance on capturing targeted pytest logs and env snapshots.
- docs/bugs/verified_c_bugs.md:173 — Notes on opt-in shim tolerances (≤5e-5) for regression acceptance.
- docs/development/pytorch_runtime_checklist.md:8 — Device/dtype checklist for referencing in commit notes.
- docs/development/implementation_plan.md:142 — Historical notes on batching strategy to mirror when finalising tensor flow.
- docs/architecture/undocumented_conventions.md:210 — Recap of detector pivot caveats relevant when threading indices.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/analysis.md — Latest Option B design recap.
- tests/test_phi_carryover_mode.py — Companion tests to monitor once cache is wired (ensure selectors still pass).
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T102155Z/parity_test_failure/pytest.log — Reference failure signature that should disappear after fixes.
- scripts/validation/compare_scaling_traces.py — Tool that must continue to handle the new cache outputs; rerun as needed.
- docs/architecture/detector.md:522 — Notes on ROI indexing that help validate `(slow, fast)` orientation.
- src/nanobrag_torch/simulator.py:720 — Entry point expected to thread indices; review before wiring changes.
- tests/test_cli_scaling_phi0.py — Regression coverage to rerun once the parity shim is stable.
Next Up:
- Progress through M2g.3–M2g.6 (cache allocation, simulator wiring, tooling updates, documentation) once signatures compile cleanly.
- Execute the M2h validation bundle (pytest CPU + optional CUDA, gradcheck) to demonstrate cache parity stability.
- Prepare for M2i trace regeneration so VG-2 metrics can flip to green and unblock nb-compare (Phase N).
