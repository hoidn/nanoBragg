Summary: Implement the φ-rotation duality fix and capture fresh parity evidence so I_before_scaling matches the C trace.
Mode: Parity
Focus: CLI-FLAGS-003 Phase M5c — φ rotation + reciprocal recompute implementation
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_cli_scaling_phi0.py; pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py (run second only if CUDA is available)
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<ISO8601>/ (trace, per-φ JSON/log, compare_scaling_traces outputs, env.json, sha256.txt, git_sha.txt); reports/2025-10-cli-flags/phase_l/per_phi/rot_star_<ISO8601>.{log,json}; reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md (update); docs/fix_plan.md Attempt log
Do Now: CLI-FLAGS-003 Phase M5c — env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py

If Blocked: Park outputs under reports/2025-10-cli-flags/phase_l/scaling_validation/attempt_<ISO8601>/blocking/ (include commands.txt, stderr, env.json, sha256.txt, notes.md) and log the blocker plus hypothesis in docs/fix_plan.md before requesting guidance.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:108-140 — Phase M5 checklist keeps M5c next; clearing it unblocks parity closure.
- specs/spec-a-core.md:204-240 — φ/mosaic loop requires fresh rotations every tick; current drift violates spec tolerances.
- golden_suite_generator/nanoBragg.c:3042-3210 — authoritative reciprocal recompute cycle we must mirror (Rules #12/#13).
- docs/bugs/verified_c_bugs.md:166-204 — C-PARITY-001 remains C-only; ensure fix does not reintroduce carryover semantics.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/trace_py_scaling_per_phi.json — “before” evidence showing rot_b_y drift and F_latt sign flip; use for comparison.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T234304Z/compare_scaling_traces.md — latest post-normalization divergence notes; parity must flip first_divergence to None.

How-To Map:
1. Ensure editable install is current and export KMP_DUPLICATE_LIB_OK=TRUE; reuse the supervisor command ROI (pixel 685,1039).
2. Re-read rotation_fix_design.md (fix_20251008T232018Z) and the nanoBragg.c snippet to confirm tensor pipeline requirements and docstring text.
3. In src/nanobrag_torch/models/crystal.py, build Rodrigues matrices for every φ tick (shape (φ,3,3)) on the caller’s device/dtype; broadcast mosaic rotations to (φ,mos,3,3).
4. Rotate base real vectors (`self.a/b/c`) and reciprocal vectors (`self.a_star/b_star/c_star`) with batched matmul; avoid Python loops and keep broadcasts explicit.
5. Compute `V_star_actual = dot(a*_rot, cross(b*_rot, c*_rot))`, clamp to ≥1e-18, invert to `V_actual`; document guard rationale in a brief comment.
6. Reconstruct real vectors from rotated reciprocals (`cross(b*_rot, c*_rot) * V_actual`) to satisfy Rule #12, then rebuild reciprocal vectors from those real vectors divided by `V_actual` (Rule #13).
7. Mirror the helper inside `get_rotated_real_vectors_for_batch`; refresh docstrings with the nanoBragg.c excerpt (Rule #11) and strip any leftover carryover references.
8. Regenerate traces with `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/trace_harness.py --emit-rot-stars --out ${FIX_DIR}` (set FIX_DIR to the new fix_<ISO8601> path); capture main trace, per-φ log, per-φ JSON, commands.txt, env.json, git_sha.txt, sha256.txt.
9. Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log --py ${FIX_DIR}/trace_py_scaling.log --out ${FIX_DIR}/compare_scaling_traces.md`; archive stdout, metrics.json, compare_scaling_traces.txt.
10. Execute `env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py`; if CUDA is present, follow with `env KMP_DUPLICATE_LIB_OK=TRUE pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py` and save both logs in the fix directory.
11. Update reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md closing H4/H5 with parity deltas; note any GPU observations.
12. Record Attempt details (artifacts, metrics, pytest status, compare-trace outcome, rot_* delta summary) in docs/fix_plan.md; mention whether duplicate per_phi/report trees were consolidated or deferred.

Verification Checklist:
- Confirm `trace_py_scaling.log` matches C on `rot_a_star`, `rot_b_star`, `rot_c_star`, `k_frac`, `F_latt_b`, and `F_latt` within ≤1e-6 relative error for every φ tick.
- Ensure `compare_scaling_traces.md` reports `first_divergence=None`; inspect metrics.json to verify all factors meet the ≤1e-6 tolerance gate.
- Validate PyTorch `V_actual` equals the C baseline (24682.2566301114 Å³) for each φ/mosaic tile; log discrepancies in summary if encountered.
- Check per-φ JSON for monotonic drift; rot_b_y should remain stable and F_latt should stay negative post-fix.
- Review pytest output for skips/failures; annotate reasons (e.g., CUDA unavailable) in docs/fix_plan.md Attempt entry.
- Run `pytest --collect-only -q` if time allows to confirm suite health after code edits.

Reporting & Handoff:
- Populate ${FIX_DIR}/summary.md with command list, durations, parity outcomes, pytest status, and any residual TODOs (e.g., per_phi cleanup).
- Update docs/fix_plan.md with Attempt #195 (artifacts, parity metrics, pytest results, CUDA notes) and link the fix_<ISO8601> directory.
- Refresh galph_memory findings if new hypotheses arise (e.g., mosaic-domain quirks) so the supervisor log stays current.
- If CUDA run skipped or fails, schedule follow-up under Phase M5e in docs/fix_plan.md Attempt notes.

Pitfalls To Avoid:
- Reintroducing φ carryover caches or conditionals; keep implementation spec-only.
- Breaking vectorization with Python loops; rely on broadcasting/matmul and keep shapes (φ,mos,3).
- Allocating tensors on CPU when device is CUDA (and vice versa); always use self.device/self.dtype.
- Calling .item()/.detach()/.numpy() on tensors that must stay differentiable.
- Skipping the duality cycle (real-from-rec, then rec-from-real); doing so preserves the drift we are fixing.
- Forgetting to clamp V_star_actual before inversion, leading to NaNs or massive spikes.
- Leaving docstrings or summaries mentioning carryover mode; keep documentation synced with spec.
- Omitting trace or compare outputs from the artifact directory; reviewers need the evidence bundle.
- Touching Protected Assets listed in docs/index.md without updating the index/plan.
- Ignoring the duplicated `reports/.../per_phi/reports/...` tree; at minimum call it out in summary if cleanup is deferred.

Pointers:
- src/nanobrag_torch/models/crystal.py:960-1185 — primary rotation helpers to refactor.
- plans/active/cli-noise-pix0/plan.md:108-140 — Phase M5 task definitions and exit criteria.
- specs/spec-a-core.md:204-240 — normative φ rotation loop contract.
- golden_suite_generator/nanoBragg.c:3042-3210 — reciprocal recomputation reference block.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T232018Z/rotation_fix_design.md — detailed tensor/duality blueprint.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/summary.md — “before” rot_* drift metrics to beat.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T234304Z/blocker_analysis.md — latest divergence analysis to retire.
- docs/bugs/verified_c_bugs.md:166-204 — reminder that carryover stays a documented C-only defect.
- scripts/validation/compare_scaling_traces.py — parity script; see usage block at top of file.

Next Up (optional):
1. Phase M5d — once parity is green, regenerate compare_scaling_traces bundle for closure and tidy duplicate per-φ directories.
2. Phase M5e — rerun targeted tests on CPU+CUDA post-fix and queue CUDA/gradcheck prep for Phase M6.

Risk Log:
- Rotation matrices built at float32 could accumulate drift; mitigate by using self.dtype (float64 for trace runs) and confirming per-φ parity.
- Mosaic_domains >1 may expose broadcast bugs; test with a 2-domain configuration in a quick notebook before running full harness if time permits.
- CUDA kernels may produce small numeric differences; capture GPU trace metrics and flag deviations >1e-6.
- compare_scaling_traces exits non-zero on missing inputs; ensure script stdout/stderr captured in summary.md.
- Duplicate report trees inflate repo size; document consolidation plan during M5d if not addressed this loop.

Monitoring:
- Track git diff for crystal.py (and batch helper) only; flag any accidental edits elsewhere.
- Note trace harness runtime; if it grows >10% from pre-fix attempt, record explanation in summary.
- Watch gradcheck coverage expectations for Phase M6; jot down any new gradient-risk areas discovered during the refactor.

Definitions:
- V_actual: Reciprocal volume inverse (expected 24682.2566301114 Å³ for supervisor ROI); used to enforce metric duality per slice.
- first_divergence: Field emitted by compare_scaling_traces; target value `None` after parity fix.
- rot_*: Rotated reciprocal vectors returned by get_rotated_real_vectors; parity goal ≤1e-6 relative error per component across all φ ticks.

Evidence Naming:
- Use FIX_DIR=reports/2025-10-cli-flags/phase_l/scaling_validation/fix_$(date -u +%Y%m%dT%H%M%SZ) before running commands; reuse the same env var for every artifact path.
- Name per-φ files `rot_star_${TS}.log/json` and list them in sha256.txt to avoid duplicate trees.
- Record pytest logs as `pytest_cpu.log` / `pytest_cuda.log` inside FIX_DIR for consistency with prior bundles.

Validation Notes:
- Keep a scratch diff (`diff -u` between new and baseline per-φ JSON) in FIX_DIR/diff_per_phi.log for reviewers.
- Note any tolerances temporarily widened during debugging; reset them before final artifact capture.
- Capture torch.dtype/device info in summary.md so future CUDA runs know the baseline context.
- If mosaic_domains>1 testing uncovers drift, log it as Hypothesis H6 with evidence.
- For reproducibility, record random seeds (if any) in run_metadata.json.
- Double-check that git status is clean before staging artifacts to avoid mixing evidence and code diffs.
