Summary: Capture post-pivot pix0 evidence so normalization work can safely resume.
Phase: Evidence
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_h6/post_fix/trace_py.log; reports/2025-10-cli-flags/phase_h6/post_fix/trace_diff.txt; reports/2025-10-cli-flags/phase_h6/post_fix/nb_compare_summary.md; reports/2025-10-cli-flags/phase_h6/post_fix/metadata.json; reports/2025-10-cli-flags/phase_h6/post_fix/attempt_notes.md; reports/2025-10-cli-flags/phase_h6/post_fix/nb_compare/metrics.json; reports/2025-10-cli-flags/phase_h6/post_fix/env_snapshot.txt
Do Now: CLI-FLAGS-003 Phase H6g pix0 trace verification — run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h6/post_fix/trace_py.log`
If Blocked: Capture command + stderr in `reports/2025-10-cli-flags/phase_h6/post_fix/attempt_blocked.log`, note environment (`python -c "import torch, sys; print(sys.version); print(torch.__version__); print(torch.cuda.is_available())"`), stash `git status --short` into the same log, and update docs/fix_plan.md Attempt history before pausing.

Context Recap:
- Attempt #40 confirmed SAMPLE pivot forcing when custom detector basis vectors are present (docs/fix_plan.md:448-462).
- Phase H6g remains open in plans/active/cli-noise-pix0/plan.md:131-145; |Δpix0| < 5e-5 m is the go/no-go threshold.
- Scaling-chain refresh (Phase K2) and regression test (Phase K3) are blocked until H6g artifacts land.
- Previous trace analysis (reports/2025-10-cli-flags/phase_h6/analysis.md) highlighted unit logging mismatches; ensure they do not recur.
- Pivot fix documentation (reports/2025-10-cli-flags/phase_h6/pivot_fix.md) expects runtime confirmation that pix0 now aligns with C trace values.
- Long-term goal #1 depends on executing the supervisor command parity run; we must clear this evidence gate first.

Evidence Capture Checklist:
1. Ensure working tree clean except for reports (`git status --short`).
2. Create post-fix directory: `mkdir -p reports/2025-10-cli-flags/phase_h6/post_fix`.
3. Record timestamp + commit hash: `date >> .../env_snapshot.txt` and `git rev-parse HEAD >> env_snapshot.txt`.
4. Append Python environment info to env snapshot using `python - <<'PY'` (collect `sys.version`, `torch.__version__`, `torch.cuda.is_available()`, `torch.get_default_dtype()`).
5. Document CUDA device name if available: `python - <<'PY'` printing `torch.cuda.get_device_name(0)` (guard with availability).
6. Confirm NB_C_BIN points at golden binary: `echo $NB_C_BIN >> env_snapshot.txt`; if unset note that harness relies solely on trace and not live nb-compare yet.
7. Run the Do Now harness command (ensuring `PYTHONPATH=src` comes first) and verify `TRACE_PY:detector_convention=CUSTOM` appears.
8. Immediately copy raw trace to a timestamped backup (`cp trace_py.log trace_py_$(date +%H%M%S).log`) to preserve untouched output.
9. Normalize line endings if needed using `dos2unix` (only if carriage returns appear; otherwise skip).
10. Perform diff vs C trace: `diff -u .../trace_c_pix0.log .../trace_py.log > .../trace_diff.txt` (allow non-zero exit).
11. Inspect diff for `beam_center_m` lines; they should now match numerical magnitudes (meters not millimetres).
12. Write a small python delta script to compute absolute differences for pix0 components, Fclose/Sclose, close_distance, r_factor, basis vectors; store metrics JSON.
13. Summarize numeric results in `attempt_notes.md` with bullet list (include per-axis delta in meters and micrometers).
14. If any delta exceeds 5e-5 m, rerun harness after investigating units; add failed attempt details to notes before retrying.
15. Once diff clean, run ROI nb-compare to ensure visual parity: `nb-compare --roi 1000 1100 600 700 --resample --threshold 0.995 --outdir reports/2025-10-cli-flags/phase_h6/post_fix/nb_compare -- -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0`.
16. Capture nb-compare stdout and metrics into `nb_compare_summary.md`; store JSON output in `nb_compare/metrics.json` if available.
17. Take note of correlation, sum_ratio, rmse, and peak alignment; highlight any deviations >1e-3.
18. Append ROI selection rationale (why 1000-1100,600-700) and mention that full-frame parity will follow during Phase L.
19. Update `attempt_notes.md` with references to all generated files, command strings, environment snapshot, and measured deltas.
20. Draft bullet list for docs/fix_plan Attempt #41 (Metrics, Artifacts, Observations, Next Actions) while results are fresh.
21. Review `git status --short` to confirm only reports, input.md, and docs edits appear; no source files should change in this loop.
22. If nb-compare script produced PNGs, ensure they reside inside `reports/2025-10-cli-flags/phase_h6/post_fix/nb_compare/` and are referenced in summary.
23. Verify `trace_diff.txt` is empty or only contains header lines; if not, investigate mismatched lines and annotate cause in notes.
24. Check that `metadata.json` contains all keys (timestamp, git_hash, sys_version, torch_version, cuda_available, device_name if applicable).
25. Leave TODO comment in `attempt_notes.md` specifying whether scaling-chain refresh can proceed in next loop.

Metrics to Record:
- Absolute pix0 deltas (fast, slow, close) in meters and micrometers.
- Fclose/Sclose, close_distance, and ratio differences to confirm no regression.
- nb-compare correlation, RMSE, sum_ratio, and peak distance for the ROI run.
- Execution time for trace harness (helps detect future performance regressions).
- Whether torch.cuda.is_available() and, if true, device name.
- Any warnings emitted by trace harness or nb-compare.

Pitfalls To Avoid:
- Do not edit detector/crystal code; Evidence loop should only read + record.
- Skip pytest entirely; Evidence phase forbids running unit tests.
- Ensure `nb-compare` uses ROI to avoid generating multi-hundred-MB artifacts.
- Double-check environment variables; missing `PYTHONPATH=src` will import old wheel build.
- Avoid mixing units in notes—always express deltas in meters first, with micrometer equivalents in parentheses.
- No manual edits to C trace file; treat it as read-only reference.
- Do not overwrite existing parity summaries; append new section with date 2025-10-06.
- Ensure Attempt logging happens after evidence captured, not before.
- Guard against accidentally adding binary artifacts to git (verify `.gitignore` covers outputs).
- Do not remove earlier attempt directories; future audits rely on complete history.
- Keep harness patch intact; do not disable tracing prints to shorten output.

Attempt Log Template (for docs/fix_plan.md Attempt #41):
- Date / Loop index.
- Result summary (PASS/FAIL, include |Δpix0| values).
- Metrics: pix0 deltas, nb-compare correlation/sum_ratio/RMSE/peak distance.
- Artifacts list: trace files, diff, metadata, nb-compare outputs, attempt notes.
- Observations/Hypotheses: comment on residual deltas or confirm alignment.
- Next Actions: likely K2 scaling-chain rerun, K3 pytest command, or remedial debugging if parity still off.

Reporting Reminders:
- Update `reports/2025-10-cli-flags/phase_h5/parity_summary.md` with a new section referencing post-fix deltas.
- Consider adding a short note to `reports/2025-10-cli-flags/phase_j/scaling_chain.md` indicating evidence pending H6g (if not already documented).
- Keep copy of commands in `attempt_notes.md` for reproducibility.

Pointers:
- docs/fix_plan.md:448-462 — Scope, status, and refreshed Next Actions for CLI-FLAGS-003.
- plans/active/cli-noise-pix0/plan.md:131-145 — Phase H6 table with H6g requirements and tolerance.
- reports/2025-10-cli-flags/phase_h/trace_harness.py:1-160 — Harness patching details and parameter setup.
- reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0.log — C baseline trace for diff comparison.
- reports/2025-10-cli-flags/phase_h6/analysis.md — Prior mismatch analysis; reference when summarizing improvements.
- reports/2025-10-cli-flags/phase_h6/pivot_fix.md — Implementation intent; evidence must confirm described behavior.
- docs/development/c_to_pytorch_config_map.md:1-68 — Pivot rules to cite in Attempt notes.
- docs/architecture/detector.md:1-120 — Detector pix0 computation overview.
- tests/test_cli_flags.py:677-794 — Regression tests validating pivot forcing.
- reports/2025-10-cli-flags/phase_j/scaling_chain.md — Downstream artifact awaiting refresh once H6g succeeds.

Next Up: If H6g passes quickly, begin drafting the command/script list for Phase K2 (scaling-chain regeneration) so the next loop can execute immediately; do not run until Evidence artifacts are logged.

Reference Commands:
- Inspect last Attempt log for consistency: `rg "Attempt #40" -n docs/fix_plan.md`.
- Validate harness import path: `python -c "import nanobrag_torch, inspect; print(nanobrag_torch.__file__)"` (expect src path).
- Quick sanity check of beam vectors: `python - <<'PY'` snippet printing `DetectorConfig` pivot after CLI parse (log to attempt notes).
- Confirm no leftover BEAM pivot: `python - <<'PY'` reading config and printing `detector_pivot` (should be SAMPLE).
- After nb-compare, gather metrics via `jq` if JSON produced; otherwise log manual values.

Reminder: no commits this loop—evidence only, defer code edits.
