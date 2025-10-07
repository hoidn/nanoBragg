Summary: Kick off tricubic vectorization by completing Phase C1’s batched neighbor gather with thorough evidence for VECTOR-TRICUBIC-001.
Mode: Perf
Focus: VECTOR-TRICUBIC-001 – Vectorize tricubic interpolation and detector absorption
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only tests/test_at_str_002.py -q
- tests/test_at_str_002.py::test_tricubic_interpolation_enabled
- tests/test_tricubic_interpolation.py::test_auto_enable_interpolation (sanity sweep after gather change)
- tests/test_at_str_002.py::test_tricubic_out_of_bounds_fallback (ensures single-warning semantics are intact)
- tests/test_gradients.py::TestCrystal::test_tricubic_gradient (sanity check that gradients survive gather change)
Artifacts:
- reports/2025-10-vectorization/phase_c/gather_notes.md
- reports/2025-10-vectorization/phase_c/collect_log.txt
- reports/2025-10-vectorization/phase_c/test_tricubic_interpolation_enabled.log
- reports/2025-10-vectorization/phase_c/test_tricubic_out_of_bounds_fallback.log
- reports/2025-10-vectorization/phase_c/diff_snapshot.json
- reports/2025-10-vectorization/phase_c/runtime_probe.json
- reports/2025-10-vectorization/phase_c/gradient_smoke.log
- reports/2025-10-vectorization/phase_c/cuda_collect_log.txt
- docs/fix_plan.md Attempt update for VECTOR-TRICUBIC-001
Do Now: VECTOR-TRICUBIC-001 – Phase C1 batched gather; run pytest --collect-only tests/test_at_str_002.py -q, then env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py::test_tricubic_interpolation_enabled -v
If Blocked: Record the failing selector output in collect_log.txt + gather_notes.md, capture the offending tensor shapes, and stop before touching Phase C2; flag the blockage at docs/fix_plan.md:1811 with a succinct Attempt entry referencing the artifacts.
Priorities & Rationale:
- docs/fix_plan.md:1796-1810 elevates Phase C1 as the next executable task for VECTOR-TRICUBIC-001 and requires artifact links under reports/2025-10-vectorization/phase_c/.
- plans/active/vectorization.md:1-120 now prescribes gather_notes.md, collect logs, runtime probes, and pytest selectors to unblock implementation—follow it verbatim to avoid plan drift.
- specs/spec-a-core.md:470-488 mandates that tricubic out-of-range lookups revert to default_F and emit only a single warning; vectorization must retain that contract.
- docs/development/testing_strategy.md:18-57 reinforces device/dtype discipline and the collect-first test cadence used in this loop, matching the `pytest --collect-only` requirement in Do Now.
- reports/2025-10-vectorization/phase_a/tricubic_baseline.md documents scalar runtimes; use these numbers as the baseline in gather_notes.md for quick before/after comparisons and to flag regressions.
- reports/2025-10-vectorization/phase_b/design_notes.md §2 diagrams the `(B,4,4,4)` gather layout—treat this as authoritative for shaping the batched tensor and index order.
- archive/fix_plan_archive.md:62 shows prior failures when gather fell back to scalar loops; avoid repeating those mistakes by validating masks early and logging results.
- src/nanobrag_torch/models/crystal.py:272-410 is the implementation surface—keep diffs focused there so review stays surgical and cache invalidation logic remains localised.
- docs/architecture/pytorch_design.md:5-12 captures the differentiability vs performance balance; vectorization must respect these guardrails.
- docs/development/pytorch_runtime_checklist.md:12-68 reiterates GPU/CPU parity expectations relevant to the new batched path.
How-To Map:
- Step 0: Ensure editable install remains active (`pip install -e .` already done previously) and export `KMP_DUPLICATE_LIB_OK=TRUE` for every PyTorch command.
- Step 1: `pytest --collect-only tests/test_at_str_002.py -q | tee reports/2025-10-vectorization/phase_c/collect_log.txt` to confirm new tests register; note any warnings in gather_notes.md.
- Step 2: Snapshot the current scalar gather logic (copy/paste pseudocode) into gather_notes.md for reference before edits.
- Step 3: Implement the batched `(S,F,4,4,4)` gather using torch indexing/broadcasting per design_notes §2—support arbitrary leading batch dims (oversample, phisteps, mosaic, sources, ROI).
- Step 4: During implementation, drop temporary assertions comparing scalar vs batched values for a small ROI; log the diff/ratio into diff_snapshot.json (use `torch.max(abs(diff))`).
- Step 5: Double-check fallback logic (`needs_default_F`) still masks OOB neighborhoods and triggers the `disable_tricubic` flag exactly once.
- Step 6: After edits, rerun `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py::test_tricubic_interpolation_enabled -v | tee reports/2025-10-vectorization/phase_c/test_tricubic_interpolation_enabled.log`.
- Step 7: Re-run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_interpolation.py::test_auto_enable_interpolation -v` to ensure auto-enable heuristics remain intact; append the exit status to gather_notes.md.
- Step 8: Summarize before/after runtimes, numerical diffs, and warning counts in gather_notes.md; reference any new helper functions introduced.
- Step 9: Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py::test_tricubic_out_of_bounds_fallback -v | tee reports/2025-10-vectorization/phase_c/test_tricubic_out_of_bounds_fallback.log` to demonstrate the single-warning behavior survived vectorization.
- Step 10: Optionally execute `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 50 --device cpu --mode compare --outdir reports/2025-10-vectorization/phase_c` if runtime regressions appear; note results in runtime_probe.json.
- Step 11: Summarize before/after runtimes, numerical diffs, and warning counts in gather_notes.md; reference any new helper functions introduced.
- Step 12: Update docs/fix_plan.md Attempt history with metrics (max delta, runtime delta, warning count) and cross-link the artifacts created in reports/2025-10-vectorization/phase_c/.
- Step 13: Stage changes but do not commit; stop for supervisor review once artifacts and Attempt entry are in place.
- Step 14: Execute `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_gradients.py::TestCrystal::test_tricubic_gradient -v | tee reports/2025-10-vectorization/phase_c/gradient_smoke.log` to confirm autograd remains intact.
- Step 15: If CUDA is available, repeat Steps 1, 6, 7, 9 on GPU by prefixing commands with `CUDA_VISIBLE_DEVICES=0`; archive the collect output as cuda_collect_log.txt and note any device-specific warnings.
- Step 16: Document any skipped CUDA runs (with reason) inside gather_notes.md to maintain auditability per testing_strategy.md.
- Step 17: Capture `git diff --stat` and `pytest --version` outputs at loop end, append both to gather_notes.md for traceability.
- Step 18: Snapshot modified file list with `git status -sb > reports/2025-10-vectorization/phase_c/status_snapshot.txt` before staging.
- Step 19: Add a “Next questions” subsection to gather_notes.md enumerating follow-ups for Phase C2/C3 so context is preserved across loops.
Pitfalls To Avoid:
- No `.cpu()`/`.cuda()` shims inside the gather—use `.type_as` or `device = lattice_values.device` patterns when coercion is necessary.
- Do not mutate cached tensors in-place; create new tensors or clone before modification to preserve autograd and caching semantics.
- Keep broadcasting explicit; avoid implicit expansion via mismatched shapes that could hide bugs on CUDA.
- Retain the one-time warning behavior for interpolation disablement; multiple emissions indicate regression.
- Ensure OOB masking clamps the exact 64 neighbors needed by polin3 and does not request 3×3×3 subsets.
- Guard against negative indices by clamping before gather; do not rely on PyTorch wraparound semantics.
- Preserve dtype neutrality—no hard-coded float64 when the caller provides float32; mirror the input tensor dtype everywhere.
- Do not edit polynomial helpers (`polint`, `polin2`, `polin3`) in this loop; they belong to Phase D and require separate evidence.
- Avoid adding logging prints in hot paths; use notes in gather_notes.md instead of stdout.
- Keep new tests lean (<1s) so the suite remains quick for iterative work; rely on existing fixtures.
- Remember to clear cached tensors or call `invalidate_cache()` if cache keys change; stale caches will hide correctness bugs.
- Verify gradients still propagate by spot-checking `.requires_grad` on outputs when running the targeted tests; document observations.
- If CUDA is unavailable, note it explicitly in gather_notes.md; otherwise run tests on both CPU and CUDA before closing the loop.
- Maintain Protected Assets discipline—do not relocate scripts/benchmarks or reports directories.
- Capture hash of modified files (`git diff --stat`) in gather_notes.md for future reference.
- Leave TODOs out of production code; use gather_notes.md for residual questions.
- Keep default_F pathways untouched; altering initialization risks diverging from spec.
- Do not downcast to half precision during experiments—stick to float32/float64 until vectorization is validated.
- Avoid pushing commits mid-loop; supervisor will consolidate once Phase C1 evidence is reviewed.
- Make sure new tensors inherit `device` and `dtype` from `self.hkl_data` rather than global defaults.
- Resist adding temporary global flags; confine experimentation to local scope and remove debug hooks before final diff.
- Confirm that the gathered tensor ordering matches C polin3 expectations (fast axis first); mismatched ordering silently corrupts interpolation.
- Keep report filenames ASCII; supervisor automation depends on predictable names.
- Do not touch docs/index.md—Protected Assets rule prohibits accidental edits while focusing on vectorization.
- Avoid editing unrelated modules; restrict diff to `crystal.py`, tests, and documentation updates linked to plan outputs.
- Ensure new tensors use `contiguous()` only when necessary; superfluous calls can hurt perf.
- Remember to un-pin any temporary environment variables (e.g., ROI overrides) before running final tests.
- Check for accidental `torch.stack([...], dim=-1)` vs `dim=-2` mismatches; highlight chosen order in gather_notes.md.
- Keep assertions behind `if debug:` style guards temporary; remove them before staging to avoid runtime overhead.
Pointers:
- docs/fix_plan.md:1796-1810
- plans/active/vectorization.md:1-160
- specs/spec-a-core.md:470-488
- docs/development/testing_strategy.md:18-57
- reports/2025-10-vectorization/phase_b/design_notes.md
- reports/2025-10-vectorization/phase_a/tricubic_baseline.md
- scripts/benchmarks/tricubic_baseline.py
- src/nanobrag_torch/models/crystal.py:272
- archive/fix_plan_archive.md:62
- docs/architecture/pytorch_design.md:5
- docs/development/pytorch_runtime_checklist.md:12
- reports/2025-10-vectorization/phase_c/ (directory overview)
- docs/development/testing_strategy.md:90
- reports/2025-10-vectorization/phase_c/gather_notes.md (living log for this loop)
- src/nanobrag_torch/models/crystal.py:310 (fallback disablement logic)
Next Up: Phase C2 – implement and run `tests/test_tricubic_vectorized.py::test_oob_warning_single_fire`, archive the `pytest -k oob_warning -v` log to reports/2025-10-vectorization/phase_c/test_tricubic_vectorized.log, and then progress to C3 device-aware caching notes.
