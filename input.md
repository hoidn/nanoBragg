Summary: Land the φ-rotation duality fix so PyTorch matches nanoBragg.c on I_before_scaling for the supervisor command.
Mode: Parity
Focus: CLI-FLAGS-003 Phase M5c — φ rotation + reciprocal recompute implementation
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_cli_scaling_phi0.py; pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py (if CUDA ready)
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<ISO8601>/ (trace, per-φ JSON/log, compare_scaling_traces outputs, env, sha256, git SHA); updated lattice_hypotheses.md; refreshed docs/fix_plan.md Attempt
Do Now: CLI-FLAGS-003 Phase M5c — env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py

If Blocked: Park all evidence under reports/2025-10-cli-flags/phase_l/scaling_validation/attempt_<ISO8601>/blocking/ (commands, stderr, env.json, sha256.txt, notes.md) and log the blocker in docs/fix_plan.md before requesting guidance.

Priorities & Rationale:
- specs/spec-a-core.md:204-240 — authoritative φ/mosaic loop; current drift violates ≤1e-6 parity target and keeps VG-2 red.
- golden_suite_generator/nanoBragg.c:3042-3210 — baseline reciprocal recomputation; our implementation must mirror this to clear Hypothesis H4.
- docs/bugs/verified_c_bugs.md:166-204 — C-PARITY-001 remains C-only; regression here would undo long-term goal #1.
- rotation_fix_design.md (`fix_20251008T232018Z`) — agreed blueprint for tensor shapes, duality enforcement, and verification deliverables.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/trace_py_scaling_per_phi.json — exposes 0.5% rot_b_y drift and F_latt sign flip; use as “before” baseline.
- plans/active/cli-noise-pix0/plan.md Phase M5 — exit criteria demand first_divergence=None, rot_* parity ≤1e-6, and updated ledger artifacts.
- docs/development/c_to_pytorch_config_map.md — ensures spindle axis and unit conversions remain consistent with C CLI semantics.

How-To Map:
- Step 1: Refresh environment (pip editable install, export KMP_DUPLICATE_LIB_OK=TRUE) so tooling runs with current sources.
- Step 2: In `crystal.py`, introduce Rodrigues rotation matrices for φ steps (tensor shape `(N_phi,3,3)`), using design memo pseudocode; keep them differentiable.
- Step 3: Load or synthesise mosaic rotation matrices (`(N_mos,3,3)`), convert identity case to shared tensor to avoid reallocations.
- Step 4: Compose rotations: `R_total = R_phi.unsqueeze(1) @ U_mos.unsqueeze(0)` to produce `(N_phi,N_mos,3,3)` broadcasted transforms.
- Step 5: Rotate base real vectors (`self.a`, `self.b`, `self.c`) to Angstrom outputs using `torch.matmul`; store as `(N_phi,N_mos,3)`.
- Step 6: Rotate base reciprocal vectors similarly; treat outputs as provisional until duality is enforced.
- Step 7: Compute cross products `b_star_rot × c_star_rot`, etc., derive `V_star_actual`, clamp to 1e-18, invert to `V_actual`, and document numeric guard in comments.
- Step 8: Recompute real vectors from rotated reciprocal vectors (`a_real = cross(b*_rot, c*_rot) * V_actual`) to satisfy Rule #12; verify shapes align via broadcasting.
- Step 9: Recalculate reciprocal vectors from refreshed real vectors (`a_star_final = cross(b_real, c_real) / V_actual`) to satisfy Rule #13; confirm `dot(a_star_final, cross(b_star_final, c_star_final))` ≈ `1/V_actual` for sanity (optional assert in trace/debug mode only).
- Step 10: Mirror logic in `get_rotated_real_vectors_for_batch` so batch path reuses new helper without redundant computation.
- Step 11: Remove any vestigial comments referencing carryover caches or static-only reciprocal reuse; refresh docstrings with updated C snippet (Rule #11).
- Step 12: Run targeted CPU trace harness (`trace_harness.py --emit-rot-stars`) storing outputs at `fix_<ISO8601>/`; ensure per-φ JSON/log files exist and note timestamp in commands.txt.
- Step 13: Execute `compare_scaling_traces.py` pointing at new PyTorch trace vs the `spec_baseline` C trace; inspect stdout for `first_divergence=None` and archive `.txt`/`.md` results in the fix directory.
- Step 14: Run CPU pytest (`pytest -v tests/test_cli_scaling_phi0.py`); capture log. If CUDA accessible, repeat with `-m gpu_smoke` to certify GPU parity.
- Step 15: Update `lattice_hypotheses.md` (close H4/H5, document parity numbers, note clean rot_* deltas) and append Attempt entry in docs/fix_plan.md with metrics + artifact paths.
- Step 16: Refresh `sha256.txt`, `env.json`, and `git_sha.txt` in the fix directory; double-check no artifacts are left unstaged.
- Step 17: Leave a note (or perform cleanup if time allows) regarding the duplicated `reports/2025-10-cli-flags/phase_l/per_phi/reports/...` subtree so M5d can consolidate it.

Verification Checklist:
- Confirm `trace_py_scaling.log` aligns with C trace on `rot_a_star`, `rot_b_star`, `rot_c_star`, `k_frac`, `F_latt_b`, `F_latt` to ≤1e-6 relative error for every φ tick.
- Ensure `compare_scaling_traces.txt` reports `first_divergence=None` and that all downstream factors stay ≤1e-6 delta.
- Validate PyTorch trace `V_actual` remains constant and matches C volume (24682.2566301114 Å³ for supervisor case).
- Inspect per-φ JSON to verify rot_b_y convergence (no monotonic drift) and F_latt stays negative, mirroring C.
- Review pytest logs for skipped tests; annotate reasons (e.g., CUDA unavailable) in docs/fix_plan.md Attempt.
- After code changes, run `pytest --collect-only -q` if time allows to ensure suite imports remain healthy.

Reporting & Handoff:
- Populate `fix_<ISO8601>/summary.md` summarising delta metrics, commands, env, and outcome (parity achieved or blockers).
- Update docs/fix_plan.md with Attempt #195 (include trace parity numbers, pytest status, compare_scaling_traces outcome, notes on per_phi cleanup).
- Append closure paragraph to `galph_memory.md` if additional findings arise (e.g., new hypotheses, residual drift).
- If CUDA run skipped or fails, state so explicitly and schedule follow-up under Phase M5e.

Pitfalls To Avoid:
- Reintroducing φ carryover caches or conditionals; keep implementation spec-only.
- Breaking vectorization by looping in Python; rely on tensor broadcasting and batched matmul.
- Creating tensors on CPU while running on CUDA (or vice versa); always use `self.device`/`self.dtype`.
- Using `.item()`, `.detach()`, or NumPy conversions inside differentiable paths; maintain autograd compatibility.
- Forgetting duality cycle (real-from-rec, rec-from-real); skipping either step reproduces the drift we are eliminating.
- Neglecting clamp guards on `V_star_actual`; avoid division-by-zero or negative volumes.
- Leaving stale docstrings/summaries that reference carryover mode; keep documentation synchronized.
- Ignoring artifact manifests; update `sha256.txt` and note new timestamps in summary files.
- Touching files listed in docs/index.md without plan update (Protected Assets rule).
- Dropping empirical evidence for parity — reviewers need traces, compare outputs, pytest logs, and env metadata consolidated.

Pointers:
- src/nanobrag_torch/models/crystal.py:990-1180 — target functions to refactor (real + batch variants).
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T232018Z/rotation_fix_design.md — authoritative design memo for this fix.
- golden_suite_generator/nanoBragg.c:3042-3210 — C reference for reciprocal recomputation and integral_form guard.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log#L270-L320 — expected C trace values per φ tick.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/summary.md — baseline drift metrics to ensure we have resolved.
- docs/bugs/verified_c_bugs.md:166-204 — reminder of C-only carryover defect.
- plans/active/cli-noise-pix0/plan.md:103-140 — Phase M5 checklist (current task + downstream M5d/M5e).
- docs/development/c_to_pytorch_config_map.md §Crystal — ensure spindle axis / cell handling remain spec-aligned.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md — update with closure notes.

Next Up (optional):
- Phase M5d — once parity is green, regenerate compare_scaling_traces bundle, close H5, and prep for nb-compare.
- Phase M5e — rerun targeted tests on CPU+CUDA post-fix, capture evidence bundle, and ready plan for Phase M6 ledger sync.

Risk Log:
- Risk: Rotation matrices built with single precision could accumulate drift; Mitigation: use self.dtype (float64 for traces) and verify per-φ parity.
- Risk: Mosaic domains >1 may expose broadcasting bugs; Mitigation: add quick unit test with mosaic_domains=2 before running full harness.
- Risk: CUDA path might diverge if torch.matmul chooses different kernels; Mitigation: run gpu_smoke pytest and compare rot_* deltas on GPU trace if available.
- Risk: compare_scaling_traces fails silently if outputs missing; Mitigation: check exit code and capture stdout/stderr in summary.md.
- Risk: Duplicate reports tree bloats repo; Mitigation: document cleanup plan in fix summary so Phase M5d addresses it explicitly.

Monitoring:
- Track git diff for `crystal.py` only; no other production files should change this loop.
- Record execution time for trace harness; note regressions >10% in summary for future perf passes.
- Watch gradcheck coverage (Phase M6) — note in docs/fix_plan if additional grad tests seem necessary after this change.

Definitions:
- V_actual: 1 / dot(a_star, cross(b_star, c_star)); expected constant 24682.2566301114 Å³ for supervisor ROI.
- first_divergence: field reported by compare_scaling_traces; must flip from `I_before_scaling` to `None`.
- rot_*: rotated reciprocal vectors returned by `get_rotated_real_vectors`; parity target ≤1e-6 relative error per component.

