Summary: Drive φ=0 parity deltas down to ≤1e-6 while documenting the spec-vs-parity stance so CLI-FLAGS-003 can advance toward the supervisor command goal.
Mode: Docs
Focus: CLI-FLAGS-003 L3k.3c.3 — φ=0 parity delta
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c -v ; pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c -v
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<TAG>/trace_py_rot_vector.log ; reports/2025-10-cli-flags/phase_l/per_phi/<TAG>/trace_py_rot_vector_per_phi.json ; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<TAG>/comparison_summary.md ; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<TAG>/delta_metrics.json ; reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md
Do Now: CLI-FLAGS-003 L3k.3c.3 — refine the φ=0 carryover handling until the new per-φ traces meet Δk, Δb_y ≤ 1e-6 (CPU and optional CUDA), capture the evidence, and rerun the mapped pytest selectors.
If Blocked: If the harness crashes or the new metrics still exceed thresholds after one carefully documented refinement, archive stderr/stdout under reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<TAG>/blockers/, log an Attempt in docs/fix_plan.md explaining the obstruction, and stop without guessing.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:309 — L3k.3c.3 remains [ ] until Δk and Δb_y are ≤1e-6.
- plans/active/cli-noise-pix0/plan.md:310 — L3k.3c.4 demands an explicit spec vs parity memo before moving on.
- docs/fix_plan.md:460 — Next Actions gate downstream phases (L3k.3d/L3k.3e) on this tighter parity.
- specs/spec-a-core.md:211 — Normative φ sampling is `phi = phi0 + phistep * tic` with no carryover; match this in the memo.
- docs/bugs/verified_c_bugs.md:166 — C-PARITY-001 documents the legacy bug; cite it when describing the parity shim.
- docs/fix_plan.md:2050 — Attempt #114 documents why Δk=2.845e-05 is insufficient; reference it when logging the new attempt.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/comparison_summary.md:1 — Use the previous “success” metrics as the baseline to beat.

How-To Map:
- Environment setup line 1: `export KMP_DUPLICATE_LIB_OK=TRUE` (must precede any torch import).
- Environment setup line 2: `export NB_C_BIN=./golden_suite_generator/nanoBragg` to keep supervisor parity reproducible.
- Environment setup line 3: ensure `PYTHONPATH=src` is in the environment before running harness scripts.
- Tag definition: `export TRACE_TAG=$(date +%Y%m%dT%H%M%S)` to isolate each evidence capture.
- Directory prep step 1: `mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TRACE_TAG`.
- Directory prep step 2: `mkdir -p reports/2025-10-cli-flags/phase_l/per_phi/$TRACE_TAG` to hold the JSON output.
- Harness command (CPU float64):
  `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py \
   --pixel 685 1039 \
   --config supervisor \
   --dtype float64 \
   --device cpu \
   --out reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TRACE_TAG/trace_py_rot_vector.log`
- Harness command (optional CUDA float32 if available):
  `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py \
   --pixel 685 1039 \
   --config supervisor \
   --dtype float32 \
   --device cuda \
   --out reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/${TRACE_TAG}_cuda/trace_py_rot_vector.log`
- JSON relocation: move or symlink the generated per-φ JSON from the harness into `reports/2025-10-cli-flags/phase_l/per_phi/$TRACE_TAG/` to avoid nested `/reports/` directories (e.g., `mv reports/.../per_phi/trace_py_rot_vector_per_phi.json reports/2025-10-cli-flags/phase_l/per_phi/$TRACE_TAG/`).
- Comparison command (CPU trace):
  `python scripts/compare_per_phi_traces.py \
   reports/2025-10-cli-flags/phase_l/per_phi/$TRACE_TAG/trace_py_rot_vector_per_phi.json \
   reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log \
   | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TRACE_TAG/compare_latest.txt`
- Comparison command (CUDA trace, optional):
  `python scripts/compare_per_phi_traces.py \
   reports/2025-10-cli-flags/phase_l/per_phi/${TRACE_TAG}_cuda/trace_py_rot_vector_per_phi.json \
   reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log \
   | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/${TRACE_TAG}_cuda/compare_latest.txt`
- Metrics logging step 1: update `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TRACE_TAG/comparison_summary.md` with Δk, Δb_y, ΔF_latt, and git SHA.
- Metrics logging step 2: update `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TRACE_TAG/delta_metrics.json` (write CPU + CUDA entries, include units).
- Metrics logging step 3: append the matching row in `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md`, marking VG-1.4 as pending or done depending on results.
- Memo update step 1: open `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` and add a subsection summarizing the new metrics.
- Memo update step 2: within that subsection, cite `specs/spec-a-core.md:211` (no carryover) and `docs/bugs/verified_c_bugs.md:166` (carryover bug) to clarify normative vs parity expectations.
- Memo update step 3: outline the action plan (e.g., spec-compliant default, optional parity shim flag, how to stage implementation) and reference the new TRACE_TAG directory.
- Memo update step 4: summarize CPU vs CUDA results in a small table (Δk, Δb_y, pass/fail) to keep VG-1 evidence audit-friendly.
- Memo update step 5: note whether additional instrumentation (e.g., logging spindle axis norms) was required so the next loop knows the exact code changes.
- Pytest command 1: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c -v` should pass once Δk ≤ 1e-6.
- Pytest command 2: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c -v` should also pass; if it fails, include failure text in the Attempt note.
- Optional collect command (before modifications): `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_cli_scaling_phi0.py -q` to ensure selectors remain valid.
- Fix-plan logging: add Attempt entry referencing TRACE_TAG, Δk, Δb_y, CPU/CUDA coverage, and the memo location.
- Plan sync: flip L3k.3c.3 (and L3k.3c.4 if memo completed) to [D] in plans/active/cli-noise-pix0/plan.md once evidence is in place.
- Clean-up: ensure new artifacts are listed in `.gitignore` if large, otherwise stage them alongside doc updates.
- Sanity check: rerun `python scripts/compare_per_phi_traces.py ... --summary-only` if available to double-check metrics before logging.
- Verification log: store SHA256 checksums of the new trace outputs in `reports/.../input_files.sha256` alongside existing entries.
- Diagnostic snapshot: capture `python -m torch.utils.collect_env` output under `reports/.../base_vector_debug/$TRACE_TAG/env.txt` to record library versions.
- Gradient audit: rerun `pytest tests/test_suite.py::TestTier2GradientCorrectness::test_gradcheck_phi_rotation -v` if the cache logic changes; log the result in diagnosis.md even if it remains green.
- Notebook flag: if you open any notebooks for quick checks, park them under `scratch/` or exclude them before commit.

Verification Checklist:
- [ ] Δk ≤ 1e-6 on CPU trace (compare_per_phi_traces output).
- [ ] Δb_y ≤ 1e-6 Å on CPU trace (delta_metrics.json).
- [ ] Optional CUDA trace either captured with ≤ 1e-6 deltas or explicitly documented as unavailable.
- [ ] Guard tests (`test_rot_b_matches_c`, `test_k_frac_phi0_matches_c`) both pass.
- [ ] diagnosis.md updated with spec citation and parity shim plan.
- [ ] docs/fix_plan.md attempt logged with TRACE_TAG, metrics, memo path, and CUDA note.
- [ ] plans/active/cli-noise-pix0/plan.md rows L3k.3c.3/L3k.3c.4 updated to [D] only after evidence is in place.
- [ ] comparison_summary.md lists git SHA, env snapshot reference, and both Δk/Δb_y values.
- [ ] delta_metrics.json clearly distinguishes CPU vs CUDA entries via keys.
- [ ] fix_checklist.md VG-1.4 row flipped to ✅ with reference to TRACE_TAG.

Pitfalls To Avoid:
- Do not treat Δk=2.845e-05 as success; VG-1 threshold is ≤1e-6 per fix_checklist.md.
- Avoid generating directories like `per_phi/reports/...`; keep the hierarchy flat (`.../per_phi/<TAG>/`).
- Preserve differentiability: no `.item()`, `.numpy()`, `.detach()`, or ad-hoc `torch.tensor(...)` conversions inside the core φ loop.
- Maintain device/dtype neutrality: migrate or invalidate `_phi_last_cache` during `Crystal.to()` before reuse.
- Keep the guard tests untouched; they must fail until evidence proves the fix.
- Respect Protected Assets (docs/index.md) during any cleanup.
- Document CUDA availability explicitly in diagnosis.md (present vs absent) to avoid ambiguity later.
- Capture git SHA and environment metadata in `comparison_summary.md` for reproducibility.
- Update docs/fix_plan.md immediately after evidence capture; stale guidance blocks automation.
- If per-φ traces fail to include TRACE_PY_PHI lines, fix instrumentation first before tweaking physics.
- When adjusting cache logic, ensure mosaic domains >1 still behave (run a quick spot check if time permits and note results).
- Do not downgrade tolerances in the guard tests; the spec requires the stricter threshold.
- Avoid overwriting the 20251123 C trace; treat it as read-only ground truth.

Pointers:
- plans/active/cli-noise-pix0/plan.md:309
- plans/active/cli-noise-pix0/plan.md:310
- docs/fix_plan.md:460
- specs/spec-a-core.md:211
- docs/bugs/verified_c_bugs.md:166
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:1
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/comparison_summary.md:1
- tests/test_cli_scaling_phi0.py:1
- docs/fix_plan.md:2050
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_metrics.json:1

Next Up: 1) CLI-FLAGS-003 L3k.3d — rerun nb-compare ROI parity once VG-1 turns green; 2) CLI-FLAGS-003 L3k.3e — finalize checklist/docs and log the Attempt before moving to the supervisor command rerun.
