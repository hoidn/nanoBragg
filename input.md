Summary: Restore φ=0 parity between PyTorch and C so CLI-FLAGS-003 can progress beyond L3k.3.
Mode: Parity
Focus: CLI-FLAGS-003 L3k.3c φ=0 initialization parity
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c; tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/<timestamp>/; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<timestamp>/comparison_summary.md; reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md
Do Now: CLI-FLAGS-003 — execute L3k.3c φ=0 parity fix and then run `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling_phi0.py -k "phi0" -vv`
If Blocked: Capture fresh φ=0 base-vector dumps (Py + C) into `base_vector_debug/<timestamp>/`, update diagnosis.md with hypotheses, and log the attempt in docs/fix_plan.md before touching simulator code.

Priorities & Rationale:
- specs/spec-a-cli.md:55-66 — supervisor command relies on custom detector/spindle vectors; φ rotation must follow CUSTOM precedence and spindle axis mapping.
- docs/development/c_to_pytorch_config_map.md:54-77 — documents spindle axis translation and twotheta defaults; φ=0 drift violates this mapping.
- plans/active/cli-noise-pix0/plan.md:1-18 — latest gap snapshot highlights φ_tic=0 Δk≈1.81e-2 as the gating issue before ROI parity work.
- plans/active/cli-noise-pix0/plan.md:292-296 — L3k.3b is done; L3k.3c requires a φ=0 fix plus refreshed comparison narrative.
- docs/fix_plan.md:552-578 — Attempts #100-101 captured failing φ0 metrics; plan expects this loop to turn them green.

How-To Map:
- Step 1: Review `comparison_summary.md` and `diagnosis.md` under `base_vector_debug/202510070839/` to internalize the current φ_tic behavior before touching code.
- Step 2: Inspect `Crystal.get_rotated_real_vectors` to confirm whether φ=0 uses the same rotation matrix as φ>0; log findings in `analysis_notes.md` before edits.
- Step 3: If C instrumentation changed since last loop, rebuild via `make -C golden_suite_generator` to keep TRACE_C_PHI aligned.
- Step 4: Reproduce C trace when needed with the supervisor command plus `-trace_pixel 685 1039` to refresh `c_trace_phi_<timestamp>.log`.
- Step 5: Implement the minimal φ=0 fix (likely ensuring base lattice vectors are recomputed from instrumented reciprocal vectors before applying φ rotation).
- Step 6: Rerun the Py harness: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --out trace_py_rot_vector_<timestamp>.log --device cpu --dtype float64`.
- Step 7: Store outputs under `per_phi_postfix/<timestamp>/` and copy the comparison summary template there.
- Step 8: Compare traces with `python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/<timestamp>/trace_py_rot_vector_<timestamp>_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/c_trace_phi_202510070839.log` (or newer C trace if regenerated).
- Step 9: Update `comparison_summary.md` narrative so it reflects that only φ_tic=0 diverged previously; ensure new run shows Δk ≤ 1e-6 for all tics.
- Step 10: Record SHA256 of the new JSON/log files in `per_phi_postfix/<timestamp>/sha256.txt` for auditability.
- Step 11: Run targeted pytest command: `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling_phi0.py -k "phi0" -vv`.
- Step 12: If tests now pass, capture stdout to `base_vector_debug/<timestamp>/pytest_phi0.log` and stash the command plus outcome in `summary.txt`.
- Step 13: Update `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md` VG-1.4 row to ✅ and log new Δk maxima and rot_b deltas.
- Step 14: Append Attempt #102 (or next number) to `docs/fix_plan.md` with metrics: Δk_max, rot_b error, pytest outcome, trace paths.
- Step 15: Note in `plans/active/cli-noise-pix0/plan.md` if any new prerequisites emerge for L3k.3d.

Detailed Actions:
1. Open current φ=0 traces and read the exact Δk/rot_b deltas to confirm the target thresholds.
2. Validate that the PyTorch path feeds `spindle_axis=[-1,0,0]` through every call chain; if not, capture call sites before editing.
3. Audit `Crystal.compute_cell_tensors` to ensure reciprocal→real recomputation uses V_actual prior to φ rotation.
4. Verify the misset + φ pipeline order matches CLAUDE Rule #12 before making changes.
5. Implement the minimal fix; avoid broad refactors in this loop.
6. After implementation, run the trace harness and confirm each φ_tic matches C to ≤1e-6.
7. Run the targeted pytest selector; confirm both φ0 tests pass.
8. Update all artefacts and documentation tracked in plan/fix_plan/checklist.
9. If parity still fails, capture the new Δk table and clearly state the remaining gap in diagnosis.md.
10. Only after evidence is saved should you consider additional code adjustments.

Pitfalls To Avoid:
- Do not touch docs/index.md or move protected artefacts.
- Keep vectorized tensor math; adding per-pixel loops violates PyTorch runtime guardrails.
- Maintain device neutrality by constructing temporaries with `type_as` or `device` from inputs.
- Avoid `.item()` on tensors that participate in gradients; use tensor math end-to-end.
- Preserve TRACE_C/TRACE_PY key names to keep comparison tooling stable.
- Do not relax pytest tolerances; the goal is to hit ≤1e-6, not to redefine success.
- Do not regenerate golden C data without explicit plan approval.
- Ensure `comparison_summary.md` text mirrors the table (no statements about "all φ" once fixed).
- Capture new artefacts under timestamped directories; never overwrite prior evidence.
- Keep per-φ JSON precision (float64) to avoid numerical noise hiding regressions.

Pointers:
- specs/spec-a-cli.md:55-66
- docs/development/c_to_pytorch_config_map.md:54-77
- plans/active/cli-noise-pix0/plan.md:292-296
- docs/fix_plan.md:552-578
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/diagnosis.md

Next Up:
1. L3k.3d — fix nb-compare ROI zero-sum issue once φ=0 is resolved.
2. L3k.3e — finalize documentation and checklist updates to close VG-5.

Additional Diagnostics Checklist:
A. Confirm `rot_b[0,0,1]` matches 0.6715882339 within tolerance after fix; record absolute and relative errors.
B. Confirm `k_frac` at φ=0 equals -0.6072558396 within absolute tolerance 1e-6; log the delta in summary.txt.
C. Verify φ_tic table remains monotonic and matches C at every step; include the table in comparison_summary.md.
D. Check that `trace_py_env.json` records the new git SHA and timestamp; update it if the harness regenerates traces.
E. Capture `sha256.txt` for both JSON and log outputs in the new per_phi_postfix directory.
F. Ensure `fix_checklist.md` VG-1.4 row cites the new timestamp and links to artefacts.
G. When editing docs/fix_plan.md, state whether φ=0 tests were previously expected to fail and are now green.
H. If any tolerances need justification, document them inside the test file docstring rather than silence the assertion.
I. Keep `tests/test_cli_scaling_phi0.py` docstrings updated with the new C reference if values change slightly.
J. Update `summary.txt` with commands executed, git SHA, and outcomes for quick auditing.

Trace Validation Steps:
- Re-run `python scripts/compare_per_phi_traces.py --help` if the CLI changed, to confirm arguments remain valid.
- Inspect `comparison_stdout.txt` to ensure no WARN/ERROR messages remain; if they do, capture them in diagnosis.md.
- Verify that the comparison script reports "All entries within tolerance" after the fix; screenshot or copy the console snippet into diagnosis.md.
- Confirm that per-φ JSON includes 10 entries with `phi_tick` 0..9; if not, stop and diagnose before proceeding.
- After the fix, rerun `pytest --collect-only -q` to ensure test suite still collects 655 tests; store log under base_vector_debug/.

Documentation Updates:
- Summarize the φ=0 fix in `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<timestamp>/diagnosis.md`.
- Add a bullet to `plans/active/cli-noise-pix0/plan.md` context noting the new timestamp and Δk results.
- Cross-link the new attempt from `plans/active/vectorization.md` only if vectorization code paths were touched; otherwise leave untouched.
- Mention in docs/fix_plan.md whether nb-compare still needs attention so future loops pick up L3k.3d quickly.

Quality Gates:
- Do not mark VG-1.4 complete until both comparison script and pytest tests pass.
- If Δk creeps above 1e-6, halt and diagnose before pushing changes downstream.
- Ensure CUDA smoke coverage remains possible; do not add CPU-only guards unless absolutely necessary.
- Re-run `pytest --collect-only -q` for confirmation even if no new tests were added.
- Keep HPC guard rails (vectorization + device neutrality) in place while debugging.

