Summary: Capture φ=0 lattice-vector parity evidence for CLI-FLAGS-003 before re-running the supervisor command.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/phi0_trace_py.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/phi0_trace_py64.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/phi0_trace_c.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/phi0_diff.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/pytest_phi0.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/pytest_collect.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/sha256.txt
Artifacts: reports/2025-10-cli-flags/nb_compare_phi_fix/summary.json
Artifacts: docs/fix_plan.md
Artifacts: plans/active/cli-noise-pix0/plan.md
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251119.log
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md
Do Now: CLI-FLAGS-003 Phase L3k.3 — author a focused pytest (`tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c`) that loads the supervisor configuration, captures the φ=0 rotated vectors, and asserts both `rot_b[0,0,1]` and the φ=0 `k_frac` match the C trace values from reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:266-277. Once authored, run `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c` and archive the failure output (red test expected) under base_vector_debug/pytest_phi0.log.
If Blocked: If pytest scaffolding is slow, fall back to `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --out reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/phi0_trace_py.log`, plus a float64 rerun, capture the matching C snippet (`sed -n '260,288p' ... > phi0_trace_c.log`), and document the deltas in phi0_diff.md so the pytest can be codified next loop.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:276 flags Phase L3k verification gates as the current blocker before Phase L4 parity.
- docs/fix_plan.md:529 records Attempt #99 with VG-1 k_frac span 0.018088 and mandates supervisor escalation; we must now quantify the base-vector drift.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251119.log:15 shows `rot_b` slow component 0.7173197865, deviating from C.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251119.log:20 logs φ=0 `k_frac=-0.5891416`, well off the C value.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:266-277 anchors the C expectations (rot_b_y=0.6715882339, k_frac=-0.6072558396).
- specs/spec-a-cli.md:30-44 describe φ/osc/step semantics that the test must respect to avoid false positives.
- docs/development/c_to_pytorch_config_map.md:42 binds CLI φ parameters to simulator fields, ensuring parity reproduction.
- reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/summary.json shows sum_ratio≈1.16×10⁵; resolving the φ=0 mismatch is prerequisite to trusting nb-compare metrics.
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:21 keeps VG-1.4 flagged ⚠️; today’s evidence should flip it to ✅ once parity is demonstrated.
How-To Map:
- `mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug`
- `export PYTHONPATH=src`
- In the new test, import `load_cli_config` or reuse existing helpers from tests/test_cli_scaling.py to instantiate Simulator with the supervisor command set (see prompts/supervisor.md for args).
- Seed the test with `device='cpu', dtype=torch.float32`, call `simulator.crystal.get_rotated_real_vectors(simulator.crystal.config)` and capture `(rot_a, rot_b, rot_c)` before any mosaic broadcasting.
- Assert φ count is 10; guard with `assert rot_b.shape[0] == simulator.crystal.config.phi_steps` so config drift is surfaced immediately.
- Compare `rot_b[0,0,1]` against 0.6715882339 with `pytest.approx` (abs tol 5e-4). Document the failing observed value in the assertion message for clarity.
- Compute φ=0 Miller indices using existing helpers (`dot_product(scattering, rot_b[0,0])`) so the test can assert `k_frac` matches the C trace.
- Until the fix lands, leave the test hard-failing (no xfail) to keep the gap visible.
- Capture pytest collection output with `pytest --collect-only tests/test_cli_scaling_phi0.py -q | tee reports/.../pytest_collect.log` to document discovery.
- After test run, use `tail -n +1 reports/.../pytest_phi0.log >> docs/fix_plan.md` when logging Attempt notes (manual step later).
- Re-run `trace_harness.py` twice: float32 (phi0_trace_py.log) and float64 (phi0_trace_py64.log) to identify dtype sensitivity; pass `--dtype float64` on the second invocation.
- Extract C reference lines: `nl -ba reports/.../c_trace_scaling.log | sed -n '260,288p' > reports/.../base_vector_debug/phi0_trace_c.log` to include line numbers for documentation.
- Generate a quick diff table: `python - <<'PY' ...` to load both traces and compute Δb_Y, Δk_frac, ΔF_latt_b, writing to phi0_diff.md.
- Update `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/sha256.txt` with checksums of all new artifacts for reproducibility.
- Append the observed deltas (Py vs C) to `reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md` so future loops see the numeric context.
- Refresh `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md` VG-1 annotations to reference base_vector_debug/ artifacts; status stays ⚠️ until fix passes.
- Log findings in docs/fix_plan.md under CLI-FLAGS-003 Attempts (include failing test name, deltas, artefact paths, and proposed follow-up).
- Optional sanity: `python - <<'PY'` script to recompute cross products from post-misset reciprocal vectors and check if Py real vectors diverge at that stage; add results to phi0_diff.md.
Pitfalls To Avoid:
- Do NOT edit simulator/crystal implementation under this memo; we’re gathering evidence only.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` set for every Python/pytest invocation to avoid MKL crashes.
- Use the supervisor command exactly; altering HKL or detector flags invalidates parity comparisons.
- Ensure NB_C_BIN points at golden_suite_generator/nanoBragg when running pytest; mixing binaries invalidates expectations.
- Avoid using GPU tensors; stay on CPU float32/float64 to match stored traces.
- Don’t overwrite historical per_phi artefacts—create new files under base_vector_debug/.
- Remember to commit the new pytest file but NOT any fixes; the red test documents the bug for TDD.
- Keep assertion tolerances tight (≤5e-4) so passing the test demands real parity.
- Capture complete pytest output; partial logs make fix_plan updates ambiguous.
- Double-check the test imports no heavy modules (torch.compile etc.) to keep turnaround fast.
- Maintain consistent environment variables in phi0_trace_py*.log headers; record them in the log preamble.
- Avoid detaching tensors inside the test; use pure tensor operations to keep gradients intact for future checks.
- When comparing float64 probes, note any improved alignment—it might hint at precision issues.
- Archive nb-compare outcomes if you touch the directory; stale metrics can mislead later analyses.
- Verify the test fails for the expected reason (k_frac mismatch) and not unrelated config errors.
- When updating fix_plan, include exact Δb_Y and Δk_frac figures to aid future debugging.
Pointers:
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251119.log:15
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251119.log:20
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:266
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:271
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:21
- plans/active/cli-noise-pix0/plan.md:278
- docs/fix_plan.md:529
- specs/spec-a-core.md:120
- specs/spec-a-cli.md:30
- docs/development/c_to_pytorch_config_map.md:42
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md:302
- reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/summary.json:1
Next Up: With the failing test and quantitative diffs captured, isolate the real-vector reconstruction stage (b*×c* scaling) to confirm whether the drift originates before or after V_actual is applied, then plan the corrective patch.
Additional Data Capture:
- `python - <<'PY'` snippet to load `A.mat` with numpy, reconstruct real vectors independently, and confirm whether PyTorch’s Stage 3 values match the analytical result; append output to phi0_diff.md.
- `python - <<'PY'` to compute `torch.cross(rot_b[0,0], rot_c[0,0])` directly inside the test (guarded by `if False`) so you can quickly toggle diagnostics without affecting runtime.
- Generate a quick plot (optional) with matplotlib saving to `base_vector_debug/phi0_kfrac.png` showing `k_frac` vs φ for Py vs C using existing JSON/trace data to visualise the drift; link the PNG in phi0_diff.md.
- Run `nb-compare` once more with `--outdir reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/debug_phi0/` after the evidence capture to confirm metrics still match the stored summary; if they differ, document in phi0_diff.md and halt before fix attempts.
- Capture environment snapshot via `python - <<'PY'` printing torch.version, numpy.version, and git SHA; append to base_vector_debug/phi0_diff.md for traceability.
- If time allows, dump `Simulator.crystal.a/b/c` directly to `base_vector_debug/crystal_vectors_before_phi.json` (use `tensor.tolist()` with high precision) so future loops can diff without rerunning the harness.
Extended Pitfalls:
- Don’t clean the repo (e.g., git clean) until all base_vector_debug artefacts are committed; we rely on them for fix_plan logging.
- Ensure pytest import paths use the editable install; running the CLI entry point inside the test can discard recent code changes.
- When copying trace snippets, avoid truncating scientific notation; small differences matter.
- Remember that the supervisor command sets `-oversample 1`; altering oversample accidentally will change k_frac values.
- Avoid mixing relative and absolute tolerances in asserts—stick to abs tol so sign flips stay visible.
- Keep phi indexing zero-based in the test; off-by-one errors can mask the φ=0 anomaly.
- When running float64 probes, beware of casting results back to float32 before comparison; inspect both values.
- Document any warnings emitted by the harness (e.g., `UserWarning`) in phi0_diff.md; unacknowledged warnings can hide config drift.
- If the new test impacts test discovery time significantly, note the delta in fix_plan so we can budget for future parametrisations.
- Commit the test with clear naming (e.g., `TestPhiZeroParity`) so future search results find it quickly.
- Validate that the test tears down cleanly (no temp files left in repo root); otherwise list unexplained artefacts in phi0_diff.md.
