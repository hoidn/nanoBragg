Summary: Restore the fully vectorised c-parity pipeline using the pixel-indexed carryover cache so VG-2 scaling parity can advance without regressions.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<new_ts>/carryover_cache_validation/
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<new_ts>/carryover_probe/
Do Now: docs/fix_plan.md › [CLI-FLAGS-003] M2g — delete `_run_sequential_c_parity`, implement the Option 1 pixel-indexed carryover cache, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q`.
If Blocked: Capture `pytest --collect-only -q` plus the mapped selector under `reports/.../attempts_blocked/<timestamp>/` (commands.txt, env.json, collect.log, sha256.txt); log the blocker in docs/fix_plan.md Attempts and stop.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md — Phase M2g explicitly demands removal of the sequential fallback; Option 1 cache work must follow immediately.
- plans/active/cli-noise-pix0/plan.md — Status snapshot (2025-12-08) shows sequential branch is the last regression before cache wiring.
- plans/active/cli-noise-pix0/plan.md — Checklists M2g.1–M2g.3 describe the cache design, validation taps, and expected artifacts; align implementation to these tables.
- docs/fix_plan.md:451 — Next actions list “restore vectorisation → Option 1 cache → targeted pytest,” matching today’s objective.
- docs/fix_plan.md Attempts #152-154 — Evidence clarifies current cache never fires within a run and sequential execution breaks the vectorisation mandate.
- docs/development/pytorch_runtime_checklist.md:1-10 — Reiterates no Python loops in compiled paths and immediate CPU/CUDA parity once code changes.
- specs/spec-a-core.md:205-233 — Normative φ pipeline: rotate from reference each step; spec mode must stay untouched by the cache.
- docs/bugs/verified_c_bugs.md:166-204 — C-PARITY-001 context ensures the shim remains opt-in and default behaviour stays spec-compliant.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — Option 1 architecture note defines tensor shapes, caches per domain, and memory budgets; use it as the blueprint.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — Existing attempt logs explain failure signatures; replicate final metrics to prove success.
- src/nanobrag_torch/simulator.py — Sequential helper is the regression and must be removed; run() should stay batch-oriented.
- src/nanobrag_torch/models/crystal.py — Houses cache scaffolding requiring conversion to per-pixel tensors on the correct device/dtype.
- tests/test_cli_scaling_parity.py — Acceptance test gating VG-2; once cache works, this test must pass at ≤1e-6 relative error.
How-To Map:
- Step 1: Remove `_run_sequential_c_parity` and its invocation from `Simulator.run()`.
- Step 1a: After removal, confirm `run()` still starts by clearing caches and normalising oversample parameters.
- Step 1b: Ensure ROI masks, debug hooks, and tensor allocations continue to work unchanged.
- Step 1c: Reroute c-parity mode to share the vectorised path; no conditional early return should remain.
- Step 2: Implement Option 1 caches inside `Crystal`.
- Step 2a: Create member tensors for rotated real vectors (ap, bp, cp) and reciprocal vectors (a*, b*, c*) sized `(spixels, fpixels, mosaic_domains, 3)`.
- Step 2b: Expose helper `_ensure_phi_carryover_cache(device, dtype, shape)` that lazily allocates or resizes caches using `torch.zeros` on the correct device/dtype.
- Step 2c: Expose helper `_reset_phi_carryover_cache()` invoked at run start to zero cached tensors.
- Step 2d: Expose helper `_record_phi_carryover(rotated_real, rotated_reciprocal, pixel_mask)` to stash φ=final vectors before leaving each φ iteration.
- Step 2e: Expose helper `_apply_phi_carryover(rotated_real, rotated_reciprocal, pixel_mask)` that swaps φ=0 vectors with cached φ=final tensors when mode == c-parity.
- Step 2f: Use tensor indexing and broadcasting (no loops) to write/ read caches per pixel and mosaic domain; respect ROI if present.
- Step 2g: Keep gradient flow intact by avoiding `.detach()`, `.clone()`, `.item()`, or in-place modifications.
- Step 3: Amend `_compute_physics_for_position` to interact with the cache.
- Step 3a: Determine φ step indices using existing vectorised tensors and boolean masks (e.g., `phi_index == 0`).
- Step 3b: Apply cached tensors before computing Miller fractions when φ index is zero in c-parity mode.
- Step 3c: Record φ=final tensors for each pixel batch at the end of the φ loop.
- Step 3d: Ensure mosaic domain axis is preserved; caches should store [pixel, domain, vector_component].
- Step 3e: Guard code so spec mode bypasses caches entirely to preserve normative behaviour.
- Step 3f: Validate that caches stay on the same device as rotated vectors; reuse `.to()` with `device=` only when outside hot loops.
- Step 3g: Confirm oversample dimensions remain broadcast-friendly; new tensors should match existing shapes.
- Step 4: Instrumentation updates (if needed).
- Step 4a: Keep debug taps behind `if self.debug_config` checks; new taps should match naming in trace harness docs.
- Step 4b: If new tap points are added, document them under `reports/.../trace_harness.py` README and commands list.
- Step 4c: Run `pytest --collect-only` to ensure trace harness imports succeed if modifications occur.
- Step 5: Documentation updates.
- Step 5a: Append a dated subsection to `phi_carryover_diagnosis.md` describing the cache architecture, removal of sequential fallback, and validation evidence.
- Step 5b: Mention memory impact (≈224 MB @ float32) and rationale for acceptance.
- Step 5c: Cite nanoBragg.c lines 2797-3095 in new helper docstrings per CLAUDE Rule #11 to maintain traceability.
- Step 5d: Update any relevant comments in code to note spec vs c-parity pathways.
- Step 5e: Cross-reference the new subsection from `reports/2025-10-cli-flags/phase_l/scaling_validation/README.md` if present.
- Step 6: Fix-plan bookkeeping.
- Step 6a: Add an Attempt entry to docs/fix_plan.md with command log, artifacts, metrics, and git SHA.
- Step 6b: Update plan checklist items (M2g tasks) to `[D]` once evidence is archived.
- Step 6c: Note any follow-up requirements for M2h (e.g., gradcheck scope) inside the Attempt entry.
- Step 7: Testing and validation.
- Step 7a: Run the mapped pytest selector (CPU mandatory) and capture full log, env.json, collect.log, sha256.txt under `carryover_cache_validation/`.
- Step 7b: If CUDA is available, queue `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --phi-mode c-parity --device cuda --dtype float64`; record decision (run or defer) in artifacts.
- Step 7c: Verify pytest output shows relative error ≤1e-6; note metrics in Attempt log.
- Step 7d: If failure persists, capture logs and revert partial code before ending loop.
- Step 7e: For manual diagnosis, rerun trace harness for consecutive pixels (684,1039 → 685,1039) to confirm carryover effect.
- Step 8: Artifact organisation.
- Step 8a: Store `commands.txt`, `env.json`, `pytest.log`, `collect.log`, `sha256.txt` under `carryover_cache_validation/<timestamp>/`.
- Step 8b: Store updated trace outputs or diagnostic notes under `carryover_probe/<timestamp>/`.
- Step 8c: Include `analysis.md` or update `phi_carryover_diagnosis.md` with summary tables comparing C vs PyTorch metrics.
- Step 8d: Ensure artifacts mention device/dtype used (cpu/cuda, float32/float64) and pixel indices examined.
- Step 8e: Add checksum file (sha256.txt) covering new artifacts for reproducibility.
- Step 9: Git hygiene.
- Step 9a: Before committing, run `git diff` to ensure only intended files changed (Crystal, Simulator, docs, plan updates).
- Step 9b: Remove temporary debug prints, scaffolding, or commented code before staging.
- Step 9c: Commit with message referencing CLI-FLAGS-003 M2g; note `tests: pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q` if passing.
- Step 9d: Push after commit; if rejected, pull with `timeout 30 git pull --rebase`, resolve conflicts, update galph_memory, and re-push.
- Step 9e: Ensure workspace ends clean; document if any intentional leftovers remain.
Pitfalls To Avoid:
- No per-pixel or per-phi Python loops — vectorisation is mandatory.
- No `.detach()`, `.clone()`, `.cpu()`, `.cuda()`, or `.numpy()` inside differentiable paths.
- No cache allocations on the wrong device/dtype; use helper functions to match caller configuration.
- No forgetting to clear caches between runs; stale data corrupts subsequent simulations.
- No overlooking mosaic domain axis; each domain requires distinct cached vectors.
- No changing spec mode behaviour; default run must remain spec-compliant.
- No enabling debug traces by default; keep instrumentation gated.
- No modifying Protected Assets listed in docs/index.md.
- No skipping docs/fix_plan.md updates; supervisor relies on accurate ledger entries.
- No running the full pytest suite this loop; stick to the mapped selector unless instructed.
- No leaving commented-out code or placeholder warnings in final diff.
- No forgetting to set `KMP_DUPLICATE_LIB_OK=TRUE` in test commands.
- No silent dtype changes; maintain float32 default unless gradcheck requires float64.
Pointers:
- plans/active/cli-noise-pix0/plan.md — Phase M2 checklist, Option 1 diagrams, status snapshot.
- docs/fix_plan.md:451-3450 — CLI-FLAGS-003 history, attempts, next actions.
- docs/development/pytorch_runtime_checklist.md — Vectorisation/device guardrails.
- specs/spec-a-core.md:205-233 — Normative φ rotation spec.
- docs/bugs/verified_c_bugs.md:166-204 — Bug description, tolerances, acceptance notes.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — Architecture notes & Option 1 tables.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py — Trace command reference and ROI guidance.
- src/nanobrag_torch/models/crystal.py:1000-1200 — Existing φ handling and cache scaffolding.
- src/nanobrag_torch/simulator.py:720-1280 — Run pipeline, oversample logic, debug integration points.
- tests/test_cli_scaling_parity.py:92-140 — Acceptance test definitions and tolerances.
- docs/development/testing_strategy.md:1.4-2.3 — Device/dtype cadence and parallel validation mandates.
Next Up:
- Phase M2h validation bundle — targeted pytest (CPU+CUDA), gradcheck probes, updated traces once cache lands.
- Phase M2i cross-pixel trace diff — regenerate metrics.json to confirm φ=0 now mirrors φ=final for consecutive pixels and document results.
- Phase N nb-compare run — once scaling is green, rerun ROI nb-compare to confirm image parity metrics hit thresholds.
