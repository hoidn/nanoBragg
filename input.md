Summary: Finish wiring the Option B batch-indexed φ-carryover cache so c-parity runs share prior-pixel vectors without breaking vectorization or gradients.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase M2g Option B cache plumbing
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q  # should pass once cache wiring is correct; log full output under carryover_cache_validation.
- Optional CUDA probe (if available): python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --phi-mode c-parity --device cuda --dtype float64 --out trace_py_scaling_cuda.log  # archive stdout/err or note unavailability.
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/optionB_impl/{commands.txt,design_notes.md,env.json,sha256.txt}
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/carryover_cache_validation/{pytest_cpu.log,pytest_cuda.log(optional),gradcheck.log,env.json,sha256.txt}
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/carryover_probe/{trace_py_scaling.log,metrics.json,trace_diff.md,lattice_hypotheses.md.addendum,sha256.txt}
Do Now: CLI-FLAGS-003 / Phase M2g Option B cache plumbing — refactor the cache helpers and simulator path for batched `(slow_indices, fast_indices)`, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q` to validate.
If Blocked: If the batched cache introduces shape/gradient issues, capture the failure with `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --phi-mode c-parity --device cpu --dtype float64 --out trace_py_blocking.log`, archive under reports/.../scaling_validation/<timestamp>/blocking_issue/, and document hypotheses in lattice_hypotheses.md before requesting guidance.
Priorities & Rationale:
- specs/spec-a-core.md:211-233 — spec mandates fresh φ rotations; ensure spec mode remains untouched while c-parity substitutes cached vectors.
- docs/bugs/verified_c_bugs.md:166-204 — C-PARITY-001 definition; cite when updating diagnosis notes after cache wiring.
- docs/development/pytorch_runtime_checklist.md:1-40 — vectorization + device/dtype neutrality guardrails the new cache must satisfy.
- plans/active/cli-noise-pix0/plan.md:18-150 — Phase M2g tables describe Option B expectations; update M2g.3–M2g.6 states as you progress.
- docs/fix_plan.md:451-520 — Active Next Actions for CLI-FLAGS-003; append Attempt summary with new artifact paths when finished.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md §§2-3 — refreshed Option B design context; append an "Option B implemented" addendum.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/analysis.md §§2-4 — memory budget + architecture decision; confirm implementation matches the documented expectations.
- src/nanobrag_torch/models/crystal.py:195-386 — cache helpers currently single-pixel; extend signatures to accept batched index tensors and eliminate `.item()` gating.
- src/nanobrag_torch/simulator.py:730-1090 — `_compute_physics_for_position` call site and ROI batching; thread `(slow_indices, fast_indices)` here without introducing Python loops.
How-To Map:
1. Refresh design context
   - Re-read phi_carryover_diagnosis.md and 20251208 Option 1 refresh memo; jot a new dated subsection summarizing Option B decisions in optionB_impl/analysis.md before editing code.
   - Validate detector/mosaic dimensions and memory footprint for the supervisor ROI (report expected MB in design_notes.md).
2. Refactor cache allocation & API
   - Update `initialize_phi_cache` to ensure cache tensors track `(spixels, fpixels, mosaic_domains, 3)` and invalidate when dimensions change; keep allocation on `self.device/self.dtype`.
   - Change `apply_phi_carryover`/`store_phi_final` to accept batched `(slow_indices, fast_indices)` tensors (shape `(batch,)`) and operate entirely with tensor masks (`torch.where` / advanced indexing) instead of `.item()` per pixel.
   - Produce vectorized validity masks (e.g., `cache_norm.sum(dim=(-1,-2)) > 0`) so GPU runs avoid host synchronisation.
3. Thread indices through simulator
   - Build `slow_indices`/`fast_indices` tensors alongside ROI handling (`torch.where(roi_mask)` or `torch.meshgrid` with caching) and reuse them for every physics call.
   - Before `_compute_physics_for_position`, branch on `phi_carryover_mode`; when c-parity, call the updated helper to swap φ=0 slices and enqueue post-run `store_phi_final` using the same batch indices.
   - Ensure spec mode bypasses cache without extra overhead (no new allocations or device transfers).
4. Validation + evidence
   - Run the mapped pytest selector (CPU) and archive log + exit code in carryover_cache_validation.
   - If CUDA available, run trace harness and store outputs; otherwise record "CUDA unavailable" in commands.txt.
   - Execute a small gradcheck helper (2×2 ROI, float64) to prove gradients survive the cache path; document command + result.
   - Regenerate the scaling trace via trace_harness.py (CPU float64) and produce metrics.json/trace_diff.md confirming `first_divergence=None`.
   - Update lattice_hypotheses.md and phi_carryover_diagnosis.md with implementation notes + artifact links.
Pitfalls To Avoid:
- Do not introduce Python loops over pixels; rely on tensor indexing for cache reads/writes.
- Keep tensors on caller device/dtype; avoid `.cpu()` or implicit float64 promotion in cache helpers.
- Preserve autograd: no `.detach()`, `.item()`, or in-place ops that overwrite values needed for gradients.
- Never mutate spec mode behaviour; guard all cache logic behind `phi_carryover_mode == "c-parity"` checks.
- Respect Protected Assets — do not rename docs listed in docs/index.md.
- Ensure ROI handling covers full-frame default; indices must match intensity tensor shape.
- When CUDA unavailable, explicitly note it in artifacts rather than omitting expected files.
- Maintain torch.compile compatibility: avoid capturing new Python closures inside compiled regions.
- Verify cache invalidation when detector dimensions or mosaic domain counts change to prevent stale tensors.
- Capture SHA256 checksums for every artifact directory to support reproducibility.
Pointers:
- specs/spec-a-core.md:211-233 — φ rotation contract (spec baseline).
- docs/bugs/verified_c_bugs.md:166-204 — C-PARITY-001 reference text.
- docs/development/testing_strategy.md:40-120 — CLI parity testing cadence and env setup.
- plans/active/cli-noise-pix0/plan.md:90-140 — Phase M2g/M2h tables (checklist + exit criteria).
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md:160-260 — Option B callgraph + risks.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T072513Z/validation_report.md — baseline metrics to beat.
- src/nanobrag_torch/models/crystal.py:195-386 — cache helper implementations to refactor.
- src/nanobrag_torch/simulator.py:767-1090 — current detector ROI + physics batching path.
- tests/test_cli_scaling_parity.py:80-190 — targeted parity test using supervisor config.
Next Up: If cache wiring and tests pass quickly, start Phase M2h log capture (gradcheck + CUDA probe) and prep documentation updates for M2i.
