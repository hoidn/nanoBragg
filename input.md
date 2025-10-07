Summary: Close the φ-rotation parity gap so the supervisor CLI command stops diverging and Phase L3k can move forward.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestCLIScaling::test_f_latt_square_matches_c
Mapped tests: tests/test_cli_scaling.py::TestCLIScaling::test_per_phi_trace_alignment
Mapped tests: tests/test_cli_scaling.py::TestCLIPivotSelection::test_sample_pivot_custom_vectors
Mapped tests: tests/test_cli_scaling.py::TestCLIScaling::test_nb_compare_supervisor_roi
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/per_phi/
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/scaling_delta/
Artifacts: reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md
Artifacts: docs/fix_plan.md (CLI-FLAGS-003 section)
Artifacts: scripts/validation/compare_scaling_traces.py outputs (post-fix)
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/archive/ (superseded traces)
Do Now: Step 1 — Review the Phase L3k memo (`reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md`) to refresh the intended change set, thresholds, and verification requirements.
Note: Pay attention to the Post-Implementation checklist inside the memo (VG mapping) so no verification gate is missed later.
Do Now: Step 2 — Insert the nanoBragg.c φ-loop excerpt (lines 3006-3098) into the `get_rotated_real_vectors` docstring before any code edits to comply with CLAUDE Rule #11.
Note: Copy the C code exactly (no paraphrasing) and keep indentation consistent with existing docstring formatting.
Do Now: Step 3 — Modify `src/nanobrag_torch/models/crystal.py` so φ rotation applies only to real-space vectors (a, b, c); remove direct rotation of a*, b*, c*; afterwards recompute reciprocal vectors from the rotated real basis using cross products and `V_actual` per CLAUDE Rule #13.
Note: Preserve vectorization by keeping tensors shaped `(phi_steps, mosaic_domains, 3)` and reusing `rotate_axis` and `rotate_umat` broadcasting helpers.
Note: Ensure `V_actual` uses dot product between the rotated real vectors (`torch.dot(a_vec, b_cross_c)`) to maintain metric duality.
Do Now: Step 4 — Regenerate per-φ traces via `python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --phi-seq "0.0,0.05,0.1" --outdir reports/2025-10-cli-flags/phase_l/rot_vector/per_phi/`; capture logs (`trace_py_phi_0.00.log`, `trace_py_phi_0.05.log`, `trace_py_phi_0.10.log`) plus JSON.
Note: Compare new traces with `reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/per_phi_c_20251006-151228.log` using the existing comparison script; record deltas in a `per_phi/comparison_postfix.md` summary.
Do Now: Step 5 — Run `python scripts/validation/compare_scaling_traces.py --c-trace reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py-trace reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_postfix.log --outdir reports/2025-10-cli-flags/phase_l/rot_vector/scaling_delta/` to quantify I_before_scaling, k_frac, b_Y deltas.
Note: Confirm the JSON output shows I_before_scaling ratio within 0.99–1.01 and k_frac delta ≤ 1e-6; include the markdown summary in the Attempt entry.
Do Now: Step 6 — Execute `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py -k lattice -v` for CPU; if CUDA is available, rerun with the same selector on GPU.
Note: Save logs as `pytest_lattice_$(date +%Y%m%d)_cpu.log` and `pytest_lattice_$(date +%Y%m%d)_cuda.log` inside `reports/2025-10-cli-flags/phase_l/rot_vector/` for VG-2 evidence.
Do Now: Step 7 — Run `nb-compare --roi 100 156 100 156 --resample --outdir reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/ -- -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0` for VG-3.
Note: Inspect `summary.json` for correlation ≥ 0.9995, sum_ratio between 0.99 and 1.01, and mean peak distance ≤ 1 pixel; record metrics in fix_plan Attempt.
Do Now: Step 8 — Update `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md` by marking VG-1..VG-5 rows with PASS/metrics and note artifacts for each subgate.
Note: Include specific file paths for per-φ logs, pytest logs, nb-compare summaries, and scaling delta outputs.
Do Now: Step 9 — Append a detailed Attempt entry to `docs/fix_plan.md` (CLI-FLAGS-003) summarizing code changes, metrics, artifacts, and next actions (Phase L4), referencing all VG evidence.
Note: Mention correlation, sum_ratio, k_frac delta, b_Y delta, I_before_scaling ratio, and any residual risks.
Do Now: Step 10 — Archive superseded traces (pre-fix per-φ logs, old scaling trace) into `reports/2025-10-cli-flags/phase_l/rot_vector/archive/$(date +%Y%m%d)_pre_fix/` to keep evidence tidy.
Note: Update `mosflm_matrix_correction.md` with a Post-Implementation section citing new code lines, metrics table, and archived artifact locations.
If Blocked: Gather fresh evidence (per-φ logs, scaling trace, pytest --collect-only) under a timestamped attempt folder, record deviations vs C baseline, update docs/fix_plan.md Attempt notes with hypotheses, and hold further code edits until root cause is clear.
Priorities & Rationale:
- PyTorch rotates reciprocal vectors during φ, breaking metric duality and shifting k_frac (Phase L3k memo, per-φ logs) leading to F_latt sign flip and 1.2e5 intensity mismatch.
- Latest scaling trace (`trace_py_scaling_20251117.log`) shows F_latt mismatch despite HKL device fix; Phase L3k fix targets this discrepancy.
- Plan `fix_checklist.md` enforces per-φ, scaling, pytest, nb-compare, and documentation gates; compliance verifies parity restoration before Phase L4.
- specs/spec-a-core.md §4 and docs/development/c_to_pytorch_config_map.md demand correct rotation order, pivot handling, and unit conversions; modifications must respect these contracts.
- CLAUDE.md Rules #11 and #13 are mandatory: docstring references must precede implementation changes, and reciprocal vectors must be recomputed from rotated real vectors using actual volume.
How-To Map:
- Implementation: Use `rotate_axis` on real vectors only; compute `rotated_real = rotate_umat(...)`; afterwards derive reciprocal vectors with cross products and `1 / V_actual` scaling; maintain tensor batching and differentiability.
- Per-φ verification: Run harness, compare with C log, ensure k_frac, F_latt_b, F_latt align; capture results in markdown summary for VG-1 evidence.
- Scaling delta: Use `compare_scaling_traces.py` to produce JSON/markdown verifying I_before_scaling ratio near 1, k_frac delta ≤ 1e-6, b_Y delta ≤ 1e-6, F_latt sign alignment; include outputs in fix_plan Attempt.
- Targeted tests: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py -k lattice -v` (CPU/GPU), logs stored in reports directory for VG-2.
- nb-compare: Use command above; ensure NB_C_BIN points to golden suite binary; store summary/diff images for VG-3.
- Documentation: Update `mosflm_matrix_correction.md` and `fix_checklist.md` with metrics and status; log Attempt in docs/fix_plan.md; archive outdated logs.
Pitfalls To Avoid:
- Skipping docstring C-code snippet — violates CLAUDE Rule #11.
- Leaving reciprocal vectors rotated without recomputation — breaks Rule #13 and parity.
- Introducing Python loops or CPU-only tensors — undermines vectorization and device neutrality.
- Forgetting `KMP_DUPLICATE_LIB_OK=TRUE` — triggers libomp crash.
- Deviating from supervisor command parameters — parity metrics become meaningless.
- Neglecting docs/fix_plan updates — supervision loses traceability.
- Running unnecessary full pytest sweeps — wastes time and muddies evidence.
- Overwriting traces without archival — future audits lose baseline comparisons.
- Breaking gradient flow — avoid `.item()`/`.detach()` on tensors needed for autograd.
Pointers:
- src/nanobrag_torch/models/crystal.py:1000-1080 — φ rotation implementation to adjust.
- golden_suite_generator/nanoBragg.c:3006-3098 — C reference for φ rotation order.
- golden_suite_generator/nanoBragg.c:2050-2199 — Reciprocal reconstruction sequence to mirror.
- reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md:187-297 — Implementation memo with thresholds.
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:20-160 — VG-1..VG-5 definitions.
- reports/2025-10-cli-flags/phase_l/per_phi/per_phi_py_20251007.json — Pre-fix per-φ data to replace.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/per_phi_c_20251006-151228.log — C per-φ baseline.
- reports/2025-10-cli-flags/phase_l/scaling_validation/metrics.json — Current scaling metrics; update post-fix.
- docs/development/testing_strategy.md:164 — Canonical parity command mapping.
- docs/debugging/debugging.md:34 — Trace SOP instructions.
- specs/spec-a-cli.md:112-158 — CLI flag semantics for φ, oscillation, nonoise, pix0.
- docs/architecture/pytorch_design.md:142-210 — Rotation pipeline expectations and vectorization rules.
- scripts/validation/compare_scaling_traces.py — Scaling delta tool for VG-4.
Next Up: After VG-1..VG-5 pass, execute Phase L4 (full supervisor command without ROI) to capture full-frame nb-compare metrics, then re-evaluate remaining CLI parity tasks or oversample_thick plan per docs/fix_plan prioritization.

Environment Prep:
- Ensure `NB_C_BIN=./golden_suite_generator/nanoBragg` is exported before nb-compare.
- Confirm `KMP_DUPLICATE_LIB_OK=TRUE` is set for all PyTorch invocations (pytest, harness, nb-compare wrappers).
- Verify CUDA availability with `python - <<'PY'` snippet if planning GPU run; otherwise skip with log note.

Gate Threshold Recap:
- VG-1: k_frac absolute error ≤ 1e-6, F_latt sign matches C, b_Y relative error ≤ 1e-6 across φ samples.
- VG-2: Targeted pytest (lattice selector) passes on CPU (and CUDA if available) without skips.
- VG-3: nb-compare ROI correlation ≥ 0.9995, sum_ratio within [0.99, 1.01], mean peak distance ≤ 1 px.
- VG-4: Scaling delta JSON shows I_before_scaling ratio 0.99–1.01, k_frac delta ≤ 1e-6, b_Y delta ≤ 1e-6, F_latt signs consistent.
- VG-5: Documentation updated (mosflm memo, fix_checklist, fix_plan) with code refs and metrics; superseded traces archived.

Metrics To Capture in Attempt Entry:
- Correlation, sum_ratio, peak distance from nb-compare summary.
- k_frac delta, b_Y delta, I_before_scaling ratio from scaling_delta metrics.json.
- Pass/fail outcome of pytest lattice selector (CPU/CUDA) with log file paths.
- Paths to new per-φ logs and comparison markdown summary.
- Confirmation that docstring include of nanoBragg.c snippet is present with line numbers.

Fallback Decision Tree:
- If per-φ traces still diverge, re-run harness at φ=0 only to ensure baseline remains aligned; inspect rotated vectors in trace logs.
- If nb-compare misses correlation threshold, inspect scaling delta output to check remaining factors (polarization, capture_fraction) and backtrack before further code edits.
- If pytest lattice fails, capture failure tracebacks, revert code edits temporarily, and log blocked state in fix_plan.

Communication Notes:
- Record any deviations, partial passes, or open questions in docs/fix_plan.md Attempt entry for supervisor visibility.
- When closing the loop, mention whether GPU parity was exercised; if skipped, document rationale (no GPU available).
- Keep timestamps for all newly generated artifacts to maintain chronological audit trail.

