Summary: Implement the Option B pixel-cache pathway so c-parity φ=0 reuses prior-pixel vectors while staying vectorized and gradient-safe.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase M2g Option B cache plumbing
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q
  Expectation: passes once Option B cache plumbing is correct; failure output must be captured under the new timestamped validation folder.
- Optional follow-up (record availability): python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --phi-mode c-parity --device cuda --dtype float64 --out trace_py_scaling_cuda.log
  Expectation: only run when CUDA is accessible; archive stdout/err even if CUDA is unavailable, noting the reason in commands.txt.
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/optionB_impl/
  • commands.txt — chronicle implementation commands, including git diff view and helper scripts run.
  • env.json — capture `python -m nanobrag_torch --version` style metadata, CUDA availability, git SHA.
  • sha256.txt — list checksums for every artifact placed in this directory.
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/carryover_cache_validation/
  • pytest_cpu.log — output from targeted parity test.
  • pytest_cuda.log — optional CUDA parity probe (mark N/A if skipped).
  • gradcheck.log — results from the small-ROI gradcheck harness.
  • env.json, sha256.txt — mirror environment + checksum capture.
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/carryover_probe/
  • trace_py_scaling.log — ROI trace rerun with new cache.
  • metrics.json, trace_diff.md — diff vs previous baseline showing `first_divergence=None`.
  • lattice_hypotheses.md addendum — note the closure of the F_latt hypothesis.
Do Now: CLI-FLAGS-003 / Phase M2g Option B cache plumbing — implement the batch-indexed cache pathway and then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q`.
If Blocked: If plumbing the cache stalls (shape errors, gradient breaks, etc.), immediately rerun `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --phi-mode c-parity --device cpu --dtype float64 --out trace_py_blocking.log`, store logs under `reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/blocking_issue/`, and document the blocker plus hypothesis in lattice_hypotheses.md before requesting guidance.
Priorities & Rationale:
- specs/spec-a-core.md:211-213 — spec requires each φ step to rotate the reference lattice anew; Option B must keep spec mode unaffected while reproducing the C bug only in `c-parity` mode.
- docs/bugs/verified_c_bugs.md:166-204 — summarises C-PARITY-001 and ensures we emulate the bug intentionally; cite this entry when updating diagnosis notes.
- docs/development/pytorch_runtime_checklist.md:1-35 — mandates vectorization and device neutrality; Option B must satisfy these guardrails (no Python loops, no device forks).
- plans/active/cli-noise-pix0/plan.md:18-140 — Phase M2g checklist now reflects Option B; keep the state table up to date (mark M2g.3–M2g.6 as they complete).
- docs/fix_plan.md:451-520 — Next Actions align with Option B; update Attempt history with new timestamps and evidence paths after the loop.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — central narrative for the cache design; append an "Option B implemented" section describing tensor shapes and helper entry points.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/analysis.md — documents the decision matrix and the Option B rationale; use this to verify memory budgets and helper API expectations.
- src/nanobrag_torch/models/crystal.py:120-360 — existing cache fields, `initialize_phi_cache`, `apply_phi_carryover`, and `store_phi_final` currently clone single-pixel tensors; refactor here to support batched `(slow_indices, fast_indices)` indexing without detaching.
- src/nanobrag_torch/simulator.py:730-880 — surface pixel indices into `_compute_physics_for_position`, ensure vectorized execution remains intact, and hook the crystal helpers appropriately.
How-To Map:
1. Refresh context
   - Read phi_carryover_diagnosis.md and 20251208 Option 1 refresh memo; jot new notes under a fresh timestamp subsection before touching code.
   - Skim `torch.take_along_dim` / `torch.index_put` docs if needed for batched indexing semantics.
2. Refactor crystal cache helpers
   - Extend `initialize_phi_cache` to allocate `(spixels, fpixels, mosaic_domains, 3)` tensors lazily; validate device/dtype using existing crystal attributes.
   - Modify `apply_phi_carryover` to accept `(slow_indices, fast_indices)` lists; use advanced indexing (`cache[slow_indices, fast_indices]`) and conditional `where` masks to swap φ=0 slices without `.clone()`.
   - Update `store_phi_final` to write `phi_final_idx=-1` slices back into the cache via `index_put_` (no detach, no clone) and guard spec mode early.
3. Thread indices through the simulator
   - Ensure `_compute_physics_for_position` (and any wrappers) receives `(slow_indices, fast_indices)` for the pixels in the current batch; avoid per-pixel Python loops by reusing existing tensor batches.
   - Invoke the crystal helper only when `phi_carryover_mode == "c-parity"`; bail immediately for spec mode to preserve normative behaviour.
4. Update tooling & docs
   - Adjust `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py` and any parity harness wrappers to call the new helper signature.
   - Append an "Option B implementation" section to `phi_carryover_diagnosis.md` summarising tensor flow, gradients, and references to `nanoBragg.c:2797,3044-3095`.
   - Note the decision and timestamp in `reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/analysis.md` if additional conclusions arise.
5. Validation bundle
   - Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q` (CPU float64) and store output under `carryover_cache_validation/pytest_cpu.log`.
   - If CUDA exists, run the trace harness with `--device cuda --dtype float64` to prove device neutrality; otherwise log the absence explicitly.
   - Execute the 2×2 ROI gradcheck harness (update or create script) and capture `gradcheck.log` showing successful gradients with the cache engaged.
6. Cross-pixel rerun
   - Re-run the ROI trace (`--roi 684 686 1039 1040`) to confirm φ=0 values propagate between consecutive pixels; update `metrics.json` and `lattice_hypotheses.md` to declare the hypothesis closed.
7. Ledger updates
   - Mark relevant M2g checklist items [D] in the plan, log Attempt in docs/fix_plan.md with new artifact paths, and summarise findings in `scaling_validation_summary.md`.

Implementation Checklist (tie to plan IDs):
- [ ] M2g.1 — annotate `phi_carryover_diagnosis.md` with today's timestamp summarising Option B intent before coding.
- [ ] M2g.3 — confirm cache tensors allocate once per detector geometry; record tensor shapes in commands.txt.
- [ ] M2g.4 — verify `apply_phi_carryover` handles arbitrary batch sizes (1, ROI, full frame); add quick unit test snippet if helpful.
- [ ] M2g.5 — update `trace_harness.py` and ensure new helper is import-safe; rerun with `--dry-run` flag if available to sanity-check.
- [ ] M2g.6 — extend diagnosis memo with C snippet citations plus memory footprint recap.
- [ ] M2h.1 — store pytest CPU log; include summary line in fix_plan Attempt.
- [ ] M2h.2 — document CUDA availability status (present/absent) explicitly.
- [ ] M2h.3 — attach gradcheck result and note any tolerance adjustments.
- [ ] M2h.4 — update docs/fix_plan.md with Attempt number, git SHA, and artifact paths.
- [ ] M2i.1–M2i.3 — archive ROI traces, metrics, and laced documentation updates.

Reporting Requirements:
- Update `reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md` with a new subsection summarising Option B metrics, including correlation, relative error, and cache hit statistics if instrumented.
- Record `git status` snapshot and the exact `pytest` command in `commands.txt` for each artifact directory.
- Append a short "Implementation notes" paragraph to `reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/optionB_impl/notes.md` (create if absent) describing tensor shapes, memory consumption, and any helper signatures introduced.
- Mention the updated files (`crystal.py`, `simulator.py`, `trace_harness.py`, diagnosis memo) in docs/fix_plan Attempt entry along with line references.
- If any temporary instrumentation was added, note how it was removed prior to final testing.

Regression Guards:
- Run `pytest --collect-only -q` after refactoring to ensure selector stability, especially if helper signatures impact imports.
- If failures persist after Option B implementation, capture stack traces and partial outputs before reverting anything; do not roll back helper changes without documenting the issue.
- Keep `trace_harness.py` compatibility with spec mode by executing a quick spec-mode sanity trace (no need to archive unless divergent).
- Confirm no new warnings from torch.compile or Dynamo appear; note any such warnings in commands.txt.

Pitfalls To Avoid:
- Reintroducing any per-pixel Python loop or sequential fallback; the simulator must stay batched per Core Rule #16.
- Using `.detach()`, `.clone()`, or in-place writes that sever autograd links; rely on functional tensor ops instead.
- Allocating cache tensors repeatedly per pixel; initialise once per run (or when detector dims change) and reuse.
- Neglecting spec mode: ensure helpers early-return when `phi_carryover_mode="spec"` so normative behaviour is unchanged.
- Forgetting to update trace harness / parity scripts to the new helper signature; stale tooling will fail evidence generation.
- Ignoring device/dtype neutrality; caches must live on the caller's device and dtype.
- Skipping documentation updates in `phi_carryover_diagnosis.md`; the design history needs the new Option B notes.
- Leaving artifacts without SHA256 manifests or missing commands.txt; reproducibility is mandatory.
- Omitting CLAUDE Rule #11 C-code snippets in new helper docstrings/comments.
- Leaving gradcheck disabled or XFAILed; the cache must pass gradcheck to confirm differentiability.
- Forgetting to update `_enable_trace` toggles if additional instrumentation is required.

Pointers:
- specs/spec-a-core.md:205-233 — φ rotation contract.
- docs/bugs/verified_c_bugs.md:166-204 — carryover bug reference.
- docs/development/pytorch_runtime_checklist.md — vectorization & device guardrails.
- plans/active/cli-noise-pix0/plan.md:18-140 — updated M2g/M2h checklist.
- docs/fix_plan.md:451-520 — Next Actions + Attempt log guidance.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — diagnosis narrative to extend.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/analysis.md — architecture decision record.
- src/nanobrag_torch/models/crystal.py:120-360 — cache helper implementation sites.
- src/nanobrag_torch/simulator.py:730-880 — simulator integration points.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py — tooling needing updates.
- tests/test_cli_scaling_parity.py:1-150 — targeted parity regression; ensures new cache wiring is exercised.
- tests/test_phi_carryover_mode.py — dual-mode guard to confirm spec vs c-parity pathways remain intact.
Next Up: Phase M2h validation bundle (pytest + gradcheck + CUDA trace) once Option B cache is in place.
