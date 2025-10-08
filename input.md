Summary: Implement the Option B φ-carryover cache allocation/wiring so parity runs reach the cache path.
Mode: Parity
Focus: CLI-FLAGS-003 / plans/active/cli-noise-pix0/plan.md > Phase M2g.3–M2g.4
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/carryover_cache_plumbing/{commands.txt,env.json,pytest.log,trace_notes.md,sha256.txt}
Do Now: CLI-FLAGS-003 M2g.3/M2g.4 — implement Option B cache allocation and simulator wiring, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q`.
If Blocked: Capture the partial cache design notes plus `pytest --collect-only tests/test_cli_scaling_parity.py -q` output in the timestamped folder, log the blocker in docs/fix_plan.md Attempts, and stop without touching production tensors further.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:108 — M2g now blocks all downstream validation; cache tensors must exist before revisiting parity metrics.
- plans/active/cli-noise-pix0/plan.md:112 — M2g.1 requires re-reading the design artifacts so coding matches the approved Option B data flow.
- plans/active/cli-noise-pix0/plan.md:118 — Row-wise batch plumbing must derive `(slow_indices, fast_indices)` from ROI tensors; no Python loops allowed.
- docs/fix_plan.md:462 — Next Actions promote M2g.3 cache allocation as the immediate unblocker, followed by M2g.4 wiring to exercise the cache path.
- docs/fix_plan.md:465 — Tooling/doc updates (M2g.5/M2g.6) depend on the wiring completing cleanly; keep notes for that follow-up.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md:1 — Design memo details tensor shapes/memory budgets that the implementation must honour.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md:1 — Diagnosis log needs new entries once cache hits are observable.
- docs/bugs/verified_c_bugs.md:166 — Reminder that c-parity mode emulates the C bug only; spec mode must remain bug-free.
- specs/spec-a-core.md:205 — Spec mode requires fresh φ=0 rotations; ensure the cache is isolated behind c-parity only and guarded with tests.
- docs/development/testing_strategy.md:35 — Device/dtype neutrality is mandatory; new tensors must mirror caller device and dtype.
How-To Map:
- Create a new timestamped directory under `reports/2025-10-cli-flags/phase_l/scaling_validation/` named `carryover_cache_plumbing/<UTC timestamp>/`.
- Add `commands.txt`, `env.json`, `pytest.log`, `trace_notes.md`, and `sha256.txt` placeholders before starting to avoid forgetting artifact capture.
- Record all CLI invocations (pytest, trace harness probes, scripts) in `commands.txt`; capture `python --version`, `python -c "import torch; print(torch.__version__)"`, and `git rev-parse HEAD` into `env.json`.
- Modify `Crystal.initialize_phi_cache`, `apply_phi_carryover`, and `store_phi_final` to allocate and index cache tensors shaped `(spixels, fpixels, mosaic_domains, 3)` on the caller’s device/dtype; ensure invalidation on detector/crystal shape changes and document resets in comments referencing `nanoBragg.c:2797`.
- Add shape assertions (`assert cache.shape[-1] == 3`) guarded by `if DEBUG:` style flags (or temporary asserts removed before commit) to verify tensor layout during development.
- Thread `(slow_indices, fast_indices)` into the simulator row loop (`Simulator._compute_physics_for_position` entry path) using tensor indexing (e.g., `torch.where` on ROI masks) so φ=0 slices are swapped via `torch.where`/advanced indexing, never Python loops.
- Ensure the row batching uses the Option B granularity from the design memo: iterate slow dimension, vectorize across fast dimension slices, and reuse the cache tensor between φ steps.
- Add temporary counters or debug prints gated by an env flag (remove before commit) to confirm cache hits for φ=0 and misses elsewhere; summarize in `trace_notes.md`.
- After wiring, run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q > pytest.log` and store the log under the timestamped folder, annotating pass/fail in `commands.txt`.
- If additional sanity checks are useful, run `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --phi-mode c-parity --device cpu --dtype float64` and append observations to `trace_notes.md` (no new artifacts if unchanged).
- Generate `sha256.txt` with checksums for all files in the timestamped folder once outputs are finalized (use `sha256sum * > sha256.txt`).
- Update docs/fix_plan.md Attempts immediately after the run, referencing the timestamped folder and summarizing cache behaviours observed.
Validation Targets:
- Confirm cache tensors populate only when `phi_carryover_mode == "c-parity"`; spec mode should bypass allocation and leave caches unused.
- Verify `cache[slow_indices, fast_indices]` values differ between φ=0 and later φ steps, demonstrating proper substitution rather than stale state reuse.
- Inspect `F_latt` / `I_before_scaling` in the targeted pytest to ensure values match the C trace tolerance (≤1e-6 relative) once cache wiring is active.
- Use a temporary tensor diff (`torch.max(torch.abs(new_vec - cached_vec))`) to ensure the advanced indexing picks up the expected φ=0 vectors.
- Check gradients by back-propagating the pytest scalar (e.g., `loss = image.sum()` within the test harness) to confirm no gradient breaks arise from the cache swap.
- Log device/dtype for each cache tensor in `trace_notes.md`; both CPU float64 (test) and potential CUDA smoke must retain the caller’s dtype.
- Confirm memory footprint aligns with design memo expectations (~224 MB full-frame float32) by printing `cache.element_size() * cache.nelement()` during development (remove before commit).
- Ensure ROI masks still function: run the trace harness with a tight ROI to see cache indexing respect ROI filtering.
- Capture the per-pixel statistics from the test (if available) to compare with baseline `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T072513Z/metrics.json`.
- Validate that cache invalidation triggers when detector dimensions change (e.g., call `detector.invalidate_cache()` in a quick REPL) and note behaviour in `trace_notes.md`.
Success Criteria:
- Both `initialize_phi_cache` and `store_phi_final` raise no shape/device assertions when running the mapped pytest.
- `pytest.log` shows the targeted test passing without skips and records Option B branch coverage notes if emitted.
- `trace_notes.md` clearly documents cache hits, memory footprint checks, and any temporary instrumentation removed before commit.
- docs/fix_plan.md Attempt entry reflects the new timestamped folder, outcome (pass/fail), and highlights any remaining gaps for M2g.5/M2g.6.
- No new warnings appear in the pytest output beyond existing known notices (document any unexpected logs in `trace_notes.md`).
- Git diff limited to production code + associated documentation updates inside the CLI-FLAGS-003 scope.
- All new tensors pass `tensor.device`/`tensor.dtype` parity checks against the detector/crystal sources.
- Any temporary helper functions added to support Option B are documented with CLAUDE Rule #11 C-code citations.
- `sha256.txt` lists all artifacts with correct checksums, and files reside solely within the timestamped directory.
- Ready state for next loop: plan checklist rows M2g.3 and M2g.4 flipped to [D] once criteria satisfied, or blockers recorded if not.
Diagnostics Checklist:
- Run a quick interactive probe (`python -i`) to instantiate `Crystal`/`Detector` with a 2×2 ROI and verify cache allocation sizes before the main pytest.
- Confirm cache invalidation triggers by calling `crystal.invalidate_phi_cache()` (or equivalent) and observing zeroed tensors during the next φ loop.
- Inspect `Simulator` row batches via a temporary `print(batch_slow.size(), batch_fast.size())` (remove afterwards) to confirm Option B granularity matches design.
- Monitor memory usage with `torch.cuda.memory_allocated()` / `torch.cuda.empty_cache()` if you perform optional CUDA smoke later.
- Use `torch.testing.assert_close` inside debug blocks to compare cached vs. freshly computed vectors at φ=0 for a sample pixel.
- Verify that ROI path handles discontiguous subrectangles by simulating a small ROI mask (manually set) and ensuring indexing remains correct.
- Check that `apply_phi_carryover` returns tensors with `requires_grad=True`; log result in `trace_notes.md`.
- Ensure the simulator still honours oversample=1 (no hidden loops) by checking the shape of oversample tensors post change.
- Confirm that the Option B code path is skipped entirely when running the test with `phi_carryover_mode="spec"` (can be a quick local check documented in notes).
- Keep an eye on log noise: any new INFO/DEBUG prints should be removed or behind a flag before commit.
Documentation Updates:
- Add a new dated subsection to `reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md` summarizing the cache allocation + wiring approach.
- Update `plans/active/cli-noise-pix0/plan.md` checklist rows M2g.3/M2g.4 to [D] once artifacts and tests pass, including one-line guidance summaries.
- Append Attempt entry in `docs/fix_plan.md` with timestamp, artifacts, tests run, and whether cache hits occurred.
- If new helper functions quote C snippets, ensure docstrings include the Rule #11 template with exact line numbers from nanoBragg.c.
- Capture any adjustments required in `trace_harness.py` (even temporary) within `trace_notes.md` so M2g.5 can reuse them.
- Reflect any spec clarifications back into `specs/spec-a-core.md` annotations if the work exposes documentation gaps (supervisor approval required before editing spec).
- Propagate device/dtype learnings into `docs/development/pytorch_runtime_checklist.md` if a new edge case surfaces.
- Maintain the timestamped directory index in `reports/2025-10-cli-flags/phase_l/scaling_validation/analysis_20251119.md` to keep provenance clear.
- Note remaining work for M2h (pytest/gradcheck/trace) at the bottom of `trace_notes.md` so the next loop starts with a ready-made checklist.
- Update `galph_memory.md` expectations if substantial deviations from Option B design were necessary (flag for supervisor review).
Pitfalls To Avoid:
- Do not regress spec mode: guard Option B logic behind `phi_carryover_mode == "c-parity"`.
- No `.item()`, `.detach()`, or `.cpu()` on tensors participating in the physics path.
- Maintain `(slow, fast)` ordering when building index tensors; use `meshgrid(indexing="ij")` if needed.
- Keep cache tensors device/dtype neutral; inherit from existing detector/crystal tensors.
- Avoid reintroducing per-pixel Python loops; rely on vectorized/batched tensor ops.
- Respect Protected Assets (docs/index.md) and avoid renaming or deleting indexed files.
- Capture SHA256 checksums for produced artifacts; keep filenames ASCII.
- Limit testing to the mapped pytest selector unless the plan explicitly escalates.
- Update docs/fix_plan.md Attempts immediately after the run with artifact paths and outcomes.
- Remove any temporary debug prints or asserts before finalizing the commit.
Pointers:
- plans/active/cli-noise-pix0/plan.md:109
- plans/active/cli-noise-pix0/plan.md:115
- plans/active/cli-noise-pix0/plan.md:120
- docs/fix_plan.md:462
- docs/fix_plan.md:465
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md:1
- docs/bugs/verified_c_bugs.md:166
- docs/development/testing_strategy.md:35
- src/nanobrag_torch/models/crystal.py:1084
- src/nanobrag_torch/simulator.py:730
- docs/architecture/pytorch_design.md:68
Next Up: Phase M2g.5/M2g.6 — update trace harness + phi_carryover_diagnosis.md once cache wiring lands cleanly.
