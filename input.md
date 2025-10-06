Summary: Confirm the MOSFLM rescale fix by rerunning the scaling parity workflow and refreshing every dependent artifact so Phase K3g can close cleanly.
- Phase: Validation
- Mode: Parity
- Focus: CLI-FLAGS-003
- Branch: feature/spec-based-2
- Mapped tests: tests/test_cli_scaling.py::test_f_latt_square_matches_c
- Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/, reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/
Do Now: CLI-FLAGS-003 — run `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v`
If Blocked: Capture a fresh Phase K3f trace (`trace_py.log`) and log the failure context under `reports/2025-10-cli-flags/phase_k/f_latt_fix/attempts.md` so we can diagnose before touching code.
Priorities & Rationale:
1. plans/active/cli-noise-pix0/plan.md Phase K3g lists the scaling parity rerun as the only remaining gate after K3g1/K3g2 went green.
2. docs/fix_plan.md (Attempt #47) records MOSFLM validation and explicitly calls for K3g3 before Phase L.
3. specs/spec-a-cli.md §Interpolation/Normalization still defines Δh/Δk/Δl tolerances and intensity sum ratios; we must show compliance.
4. reports/2025-10-cli-flags/phase_k/base_lattice/summary.md now documents the placeholder-volume root cause as resolved, but it also asks for regenerated traces and scaling metrics.
5. Long-term goal #1 (full parallel parity command) is blocked until CLI-FLAGS-003 closes; this loop removes the last evidence gap.
How-To Map:
1. Environment prep:
   - `export NB_C_BIN=./golden_suite_generator/nanoBragg`
   - `export KMP_DUPLICATE_LIB_OK=TRUE`
   - `export NB_RUN_PARALLEL=1` when running pytest.
2. Pytest execution:
   - Navigate to repo root.
   - Run `pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v` with env above.
   - Capture stdout/stderr to `reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest_post_fix.log`.
3. Metrics update:
   - Open `reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md`.
   - Append a new section dated today with correlation, RMSE, Δh, Δk, Δl, sum ratio, peak match counts.
   - Note whether tolerances (Δ ≤ 5e-4, correlation ≥ 0.999, sum ratio in 0.99–1.01) are met.
4. nb-compare rerun:
   - Command (single line):
     `nb-compare --c-bin $NB_C_BIN -- -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0`
   - Store outputs under `reports/2025-10-cli-flags/phase_k/f_latt_fix/nb_compare_post_fix/`.
   - Record metrics (correlation, RMSE, peak distances) in a short README inside that directory.
5. Trace refresh:
   - Run `PYTHONPATH=src python reports/2025-10-cli-flags/phase_k/base_lattice/trace_harness.py --out reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py.log` (env still has KMP_DUPLICATE_LIB_OK).
   - Use `python reports/2025-10-cli-flags/phase_k/base_lattice/compare_traces.py --c reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt --py reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py.log > reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_diff.txt`.
   - Confirm Δh, Δk, Δl in the diff shrink below 5e-4; summarize in `summary.md` under a new dated bullet.
6. Documentation sync:
   - Update `reports/2025-10-cli-flags/phase_k/base_lattice/summary.md` with a bullet citing the regenerated trace results.
   - Add a note to `reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md` referencing the nb-compare directory.
   - Append a short paragraph to `docs/fix_plan.md` Attempt #47 (sub-bullet) capturing the parity metrics.
7. Optional closure prep:
   - If everything passes, draft a note in plan Phase L (not executing yet) summarizing readiness for the supervisor command rerun.
Pitfalls To Avoid:
1. Skipping `KMP_DUPLICATE_LIB_OK=TRUE` will trigger libomp errors before tests run.
2. Do not modify production code this loop; we are collecting evidence.
3. Keep vectorization intact—no introducing Python loops into scaling paths while debugging.
4. Maintain device/dtype neutrality when logging tensors; avoid `tensor.cpu()` unless copying for numpy output.
5. Place all generated files under the documented `reports/` hierarchy; no stray /tmp artifacts.
6. Leave `input.md` untouched after reading it.
7. Respect Protected Assets listed in docs/index.md (loop.sh, supervisor.sh, input.md, etc.).
8. Run only the mapped pytest selector; skip full-suite runs until implementation work resumes.
9. Annotate any nb-compare deviations immediately; do not rely on memory.
10. When editing markdown summaries, keep ASCII formatting and follow existing section conventions.
Pointers:
1. plans/active/cli-noise-pix0/plan.md — Phase K3f/K3g tables outline completion criteria and checklist expectations.
2. docs/fix_plan.md — CLI-FLAGS-003 Attempts #46–47 document prior evidence and the newly added regression test.
3. reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/cell_tensors_py.txt — Confirms the MOSFLM real vectors now match C.
4. reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md — Needs the latest Δh/Δk/Δl, correlation, and sum ratio numbers.
5. reports/2025-10-cli-flags/phase_k/base_lattice/trace_harness.py — Script to regenerate PyTorch traces post-fix.
6. reports/2025-10-cli-flags/phase_k/base_lattice/compare_traces.py — Automates C vs PyTorch trace diffs; use it after re-running harness.
7. tests/test_cli_scaling.py::TestFlattSquareMatchesC — Target pytest selector for K3g3.
8. tests/test_cli_scaling.py::TestMOSFLMCellVectors::test_mosflm_cell_vectors — Regression that must stay green while updating artifacts.
9. specs/spec-a-cli.md §§Interpolation & Normalization — Ground truth for acceptance tolerances.
10. docs/debugging/debugging.md Parallel Trace SOP — Reference for regenerating trace evidence without diverging from production code.
Next Up: If scaling parity is green and artifacts are refreshed, queue Phase L1 nb-compare for the full supervisor command so we can close CLI-FLAGS-003 on the next loop.
Verification Checklist:
1. Confirm pytest log shows `tests/test_cli_scaling.py::test_f_latt_square_matches_c` PASSED with no skips and NB_RUN_PARALLEL banner printed.
2. Verify scaling_chain.md new section includes timestamp, command, correlation, RMSE, Δh, Δk, Δl, sum ratio, and explicit pass/fail statements.
3. Ensure nb-compare output directory contains `metrics.json`, `difference.png`, and a short README summarising thresholds.
4. Double-check `trace_diff.txt` reports Δh/Δk/Δl below 5e-4 before noting success.
5. Update docs/fix_plan.md Attempt #47 with a sub-bullet referencing both the pytest log and nb-compare metrics.
6. Stage all modified artifacts (`reports/...`, plan updates) so the supervisor can review diffs without fishing for untracked files.
7. Note any anomalies (e.g., lingering Δk spikes) in galph_memory during handoff; silence implies success.
Context Recap:
1. Attempt #46 captured the 40× reciprocal vector mismatch; those artifacts remain under `phase_k/base_lattice/` for reference.
2. Commit 46ba36b introduced the MOSFLM rescale branch and regression test; Attempt #47 documented the new evidence but deferred scaling rerun.
3. The plan now marks K3g1 and K3g2 complete, setting the stage for K3g3; this loop provides the necessary parity proof.
4. No production code changes are expected; success depends on evidence capture and documentation updates.
Data Management Notes:
1. Keep raw nb-compare outputs in the dedicated `nb_compare_post_fix/` folder; do not mix with previous attempts to preserve chronology.
2. When editing markdown summaries, maintain chronological order (oldest to newest) and include UTC timestamp if possible.
3. If any command fails, record the exact stderr in a `*_failure.log` file alongside the attempted command.
4. Use ASCII tables in summaries to keep reports diff-friendly; avoid embedding large binary blobs or images directly in git.
5. Ensure every new artifact path is relative to repo root so future automation can find it.
Communication Reminders:
1. Document any deviations from the prescribed commands in `reports/2025-10-cli-flags/phase_k/f_latt_fix/logbook.md` for traceability.
2. If tolerances are still missed, flag the exact metric (Δh, Δk, Δl, sum ratio, or peak count) and propose a hypothesis before ending the loop.
3. Mention in galph_memory whether nb-compare visuals show residual artifacts so we know if Phase L needs extra scrutiny.
Timeboxing:
1. Target ≤20 minutes for the pytest + metrics update sequence; note overruns and their causes.
2. Allocate another ≤20 minutes for nb-compare generation and diff capture.
3. Reserve the final 10 minutes for documentation updates and git status review.
Exit Signals:
1. Scaling parity metrics fall within spec tolerances and are documented in scaling_chain.md.
2. Trace diff shows Δh/Δk/Δl below thresholds and is cross-referenced in summary.md.
3. docs/fix_plan.md updated with Attempt #47 sub-bullet summarising the rerun results.
4. git status clean except for intentional report/document updates staged for review.
5. galph_memory entry drafted to brief the next supervisor loop on outcomes and next steps.
End of memo.
