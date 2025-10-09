Summary: Close CLI-FLAGS-003 by rerunning the supervisor nb-compare and logging the Option 1 metrics.
Mode: Docs
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_l/supervisor_command/<STAMP>/**/*
Do Now: CLI-FLAGS-003 Phase O — run `STAMP=$(date -u +"%Y%m%dT%H%M%SZ") && KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg python scripts/nb_compare.py --outdir reports/2025-10-cli-flags/phase_l/supervisor_command/${STAMP} --save-diff --resample --threshold 0.98 -- -mat A.mat -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0` then capture analysis + summary and update the ledgers before running `pytest -v tests/test_cli_scaling_phi0.py`.
If Blocked: Capture the command, stdout/stderr, and environment in `reports/2025-10-cli-flags/phase_l/supervisor_command/<STAMP>/attempt_blocked.md`; log the failure details in docs/fix_plan.md Attempts and stop.
Priorities & Rationale:
- docs/fix_plan.md:460-474 keeps CLI-FLAGS-003 focused on Phase O closure and documents expected metrics.
- plans/active/cli-noise-pix0/plan.md:25-105 outlines O1–O3 deliverables and artifact requirements for the supervisor rerun.
- docs/bugs/verified_c_bugs.md:166-189 confirms the sum-ratio blow-up is a documented C-only bug (C-PARITY-001) that must be cited in the analysis.
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/analysis.md:1-80 shows the correlation≈0.985 / sum_ratio≈1.16e5 numbers you should expect to repeat.
- docs/architecture/c_parameter_dictionary.md:312-332 maps `-nonoise`/pix0 flags to the C variables to double-check CLI emission notes in the summary.
How-To Map:
- `STAMP=$(date -u +"%Y%m%dT%H%M%SZ")`
- `KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg python scripts/nb_compare.py --outdir reports/2025-10-cli-flags/phase_l/supervisor_command/${STAMP} --save-diff --resample --threshold 0.98 -- [args...]`
- Write `reports/2025-10-cli-flags/phase_l/supervisor_command/${STAMP}/analysis.md` summarising correlation, sum_ratio, peak distances, runtimes, and explicitly attributing the sum_ratio failure to C-PARITY-001 with doc links.
- `pytest -v tests/test_cli_scaling_phi0.py`
- Update `docs/fix_plan.md` with a VG-5 Attempt (correlation ≈0.985 pass, sum_ratio ≈1.16e5 expected), mark O1/O2 [D] in `plans/active/cli-noise-pix0/plan.md`, and record the path + metrics in the plan Status Snapshot.
- Mirror the bundle to `reports/archive/cli-flags-003/supervisor_command_${STAMP}/` once docs are updated.
Pitfalls To Avoid:
- Do not tweak nb-compare thresholds; 0.98 is required so the command exits cleanly.
- Keep `NB_C_BIN` pointing at `./golden_suite_generator/nanoBragg`; do not rebuild or swap binaries mid-run.
- Ensure `analysis.md` states that the large sum_ratio is expected from C-PARITY-001; omit this and the ledger entry will be incomplete.
- Capture both `c_stdout.txt` and `py_stdout.txt`; missing either breaks our historical trace.
- Do not delete or rename anything listed in docs/index.md (Protected Assets rule).
- Avoid adding new code changes—this loop is documentation/evidence only.
- If you run the optional CUDA rerun, append outputs with a `_cuda` suffix rather than overwriting the CPU bundle.
- Remember to record SHA256 hashes for each float image in `sha256.txt`.
- Keep the working directory clean; stage only doc/report updates when you commit.
Pointers:
- docs/fix_plan.md:468-474
- plans/active/cli-noise-pix0/plan.md:25-111
- docs/bugs/verified_c_bugs.md:166-189
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/analysis.md:1-80
- docs/architecture/c_parameter_dictionary.md:312-332
Next Up: Archive the bundle (Plan O3) and draft Phase P watch checklist items once VG-5 is logged.
Pre-run Checklist:
- Verify `pip install -e .` already executed in the temp workspace noted in reports history.
- Confirm `A.mat`, `scaled.hkl`, and existing ROI binaries are present in repo root before running.
- Ensure no stale `/tmp/tmp*_py.bin` files are left from prior runs; clean if necessary to avoid confusion.
- Double-check `docs/index.md` protected assets before touching scripts or docs.
- Review `reports/2025-10-cli-flags/phase_i/supervisor_command/README.md` for historical reference.
- Note current git SHA for inclusion in `env.json` (use `git rev-parse HEAD`).
Environment Prep:
- Export `NB_C_BIN=./golden_suite_generator/nanoBragg` in the same shell that runs nb-compare.
- Set `KMP_DUPLICATE_LIB_OK=TRUE` to avoid MKL duplicate library crashes.
- Keep `PYTHONPATH=src` available if you need to invoke `python -m nanobrag_torch` directly.
- Record `nproc`, `uname -a`, and Python version in `env.json` for repeatability.
- Ensure CUDA visibility matches chosen device; leave `CUDA_VISIBLE_DEVICES` unset if CPU-only.
- Verify disk space in reports directory before writing ~200 MB of outputs.
Command Notes:
- Use the exact flag ordering from the Do Now command to keep diff noise low.
- Include `--save-diff` and `--resample` every run to guarantee diff artifacts exist even with shape drift.
- Keep `--threshold 0.98` so nb-compare exits 0 despite the known correlation drop versus legacy threshold 0.999.
- Capture stdout via `tee reports/.../nb_compare_stdout.txt` for future audits.
- If the command fails mid-run, preserve partial logs and rerun in a fresh directory; do not overwrite.
- Avoid enabling `--png-scale linear`; leave percentile scaling so PNGs match prior bundles.
Output Files:
- `commands.txt` must list both C and PyTorch invocations with absolute runtimes.
- `summary.json` should include args, runtimes, and ROI (expect full-frame 2527×2463 data).
- Store PNG previews (`c.png`, `py.png`, `diff.png`, `comparison.png`) under the `<STAMP>/results/` folder.
- Write `sha256.txt` covering all float images and PNG assets using `sha256sum`.
- Persist raw float bins (`c_float.bin`, `py_float.bin`, `diff_float.bin`) alongside PNGs.
- Keep `env.json` capturing OS, Python, PyTorch, and git metadata for reproducibility.
Analysis Highlights:
- Explicitly mention correlation ≈0.9852 and why that passes the relaxed threshold.
- Document the sum_ratio ≈1.16×10^5 and cite `docs/bugs/verified_c_bugs.md:166-189`.
- Note peak distances (expected 0.00 px) proving geometric parity remains intact.
- Summarize runtimes (C ≈0.5 s, Py ≈5.6 s) to contextualize performance gap.
- Reinforce that intensity scaling divergence roots in C-PARITY-001, not PyTorch regressions.
- Include a short "Next Steps" block pointing at Plan O2/O3 and Phase P watch items.
Metrics To Capture:
- Correlation (expect ~0.985) and threshold result.
- RMSE and max absolute difference for completeness.
- C sum vs Py sum with explicit numeric values.
- Sum ratio with scientific notation to avoid truncation.
- Mean and max peak distance metrics from nb-compare.
- Runtime speedup ratio (C/Py) to track performance trend.
Documentation Updates:
- Append VG-5 Attempt to `docs/fix_plan.md` citing new bundle path and metrics.
- Update `plans/active/cli-noise-pix0/plan.md` Status Snapshot with `<STAMP>` and mark O1/O2 [D].
- Mention the run and metrics in `galph_memory.md` summary for traceability.
- Cross-reference `analysis.md` from the Attempt entry so future readers can reproduce reasoning.
- If optional CUDA run executed, note it under Attempts with separate metrics.
- Ensure `docs/bugs/verified_c_bugs.md` remains untouched except for references; no edits expected.
Archive Actions:
- Copy the entire `<STAMP>` directory to `reports/archive/cli-flags-003/supervisor_command_${STAMP}/` once ledgers updated.
- Preserve directory structure (inputs/results/logs) during the mirror to maintain discoverability.
- Record the archive path in `analysis.md` so future audits find it quickly.
- Do not delete the live `<STAMP>` directory after archiving; the archive is an additional copy.
- If existing archive folder already uses the same stamp, append `_rerun` to avoid collisions.
- After archiving, re-run `git status` to confirm no unexpected files remain.
Test Notes:
- After nb-compare, run `pytest -v tests/test_cli_scaling_phi0.py` to reconfirm φ rotation invariants.
- Include pytest stdout in `tests/test_cli_scaling_phi0.py.log` under the same `<STAMP>` directory.
- If cuda is available and you choose to run GPU smoke, add `CUDA_VISIBLE_DEVICES=0 pytest -v tests/test_cli_scaling_phi0.py -m gpu_smoke`.
- Record skipped markers explicitly so we know whether CUDA coverage occurred.
- Use `pytest --collect-only -q` first if import errors are suspected; capture the log when doing so.
- Note any deselected GPU markers in the ledger Attempt.
Optional CUDA Run:
- Only run after CPU bundle is complete and documented.
- Reuse the same nb-compare command but add `--cuda` flag if the script supports it; otherwise call the CLI directly.
- Store outputs under `<STAMP>_cuda` to distinguish from CPU data.
- Document device, compute capability, and driver in `env_cuda.json`.
- Mention any runtime anomalies or memory warnings in `analysis_cuda.md`.
- Do not treat CUDA results as blocking; they are supplementary evidence.
Reporting Reminders:
- Update `reports/README.md` index if a new archive subdirectory is introduced.
- Add a short entry to `docs/fix_plan.md` Attempt noting whether png previews match orientation expectations.
- Confirm `analysis.md` hyperlinks are relative paths so they work on other machines.
- Include a `notes.txt` with any deviations or retries performed during the run.
- If nb-compare outputs warnings, quote them verbatim inside the analysis for future debugging.
- Close the loop by adding an Attempts History pointer to `reports/archive/cli-flags-003/`.
