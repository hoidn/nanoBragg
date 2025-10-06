Summary: Generate definitive nb-compare evidence for the supervisor CLI command (Phase I3) and package it for plan closure review.
Summary: Confirm polarization parity, pix0 alignment, and noise suppression while keeping artifacts organized under reports/.
Phase: Validation
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm (Phase I3 final parity)
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_flags.py::TestCLIPolarization::test_default_polarization_parity
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-10-cli-flags/phase_i/supervisor_command/
Artifacts: reports/2025-10-cli-flags/phase_i/supervisor_command/logs/
Artifacts: reports/2025-10-cli-flags/phase_i/supervisor_command/artifacts/
Do Now: [CLI-FLAGS-003] Phase I3 final parity — run `KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg nb-compare --outdir reports/2025-10-cli-flags/phase_i/supervisor_command --save-diff --threshold 0.999 -- -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0`)
Do Now: Store stdout/stderr produced by nb-compare inside reports/2025-10-cli-flags/phase_i/supervisor_command/logs/ for later reference.
If Blocked: Capture separate PyTorch and C invocations (same args) into reports/2025-10-cli-flags/phase_i/supervisor_command/blocked/, annotate failure cause, and stop for supervisor input.
If Blocked: Record exact command, return code, and stderr snippet in Attempt #27 draft section of docs/fix_plan.md before escalating.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:110 spells out Phase I goals (polarization parity) and expects supervisor command evidence before closure.
- plans/active/cli-noise-pix0/plan.md:114 lists I3 exit criteria requiring archived logs and metrics for this exact command.
- docs/fix_plan.md:448 still lists CLI-FLAGS-003 as in_progress; Attempt #27 must reference nb-compare metrics to justify completion.
- docs/fix_plan.md:454 (Attempt #26) already notes remaining work; update there with parity results to complete the narrative.
- specs/spec-a-cli.md:120 captures precedence between custom vectors and pix0 overrides; parity evidence confirms we now match C behavior.
- specs/spec-a-cli.md:152-189 enumerates CLI acceptance tests; reproducing the supervisor command aligns with AT-CLI-006/-007 expectations.
- docs/architecture/detector.md:70 highlights post-rotation beam-centre recompute; verifying this command proves H4 work under real geometry.
- docs/development/testing_strategy.md:90 mandates authoritative commands and artifact storage; nb-compare logs satisfy Tier 1 evidence.
- docs/architecture/c_parameter_dictionary.md:95 defines the -nonoise and pix0 flag mappings; use it while reviewing stdout to ensure no silent divergence.
- README_PYTORCH.md:180-198 provides nb-compare usage notes and output expectations (correlation, RMSE, PNG previews).
- galph_memory.md latest entry flagged Phase I3 parity as outstanding; delivering evidence resolves the documented blocker.
How-To Map:
- Activate editable install if needed: `pip install -e .` (run once) and note version in logs/README.md.
- Export authoritative doc env var for provenance logging: `export AUTHORITATIVE_CMDS_DOC=docs/development/testing_strategy.md`.
- Create directories: `mkdir -p reports/2025-10-cli-flags/phase_i/supervisor_command/{logs,artifacts,roi}` before executing commands.
- Run nb-compare per Do Now; keep terminal output for the supervisor memo (copy into logs/nb_compare_stdout.txt).
- After run, move `summary.json`, `c_stdout.txt`, `c_stderr.txt`, `py_stdout.txt`, `py_stderr.txt`, `c_float.bin`, `py_float.bin`, `c.png`, `py.png`, `diff.png`, `diff.bin` into artifacts/.
- Inspect `summary.json` to confirm correlation ≥0.999, RMSE near zero, sum_ratio within 1±0.01, peak distances ≤1 pixel.
- Parse stdout logs to find polarization factor lines; record both C and PyTorch values in README.md.
- Run targeted pytest: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPolarization::test_default_polarization_parity -v | tee reports/2025-10-cli-flags/phase_i/supervisor_command/logs/pytest_cli_polarization.txt`.
- Run `pytest --collect-only -q | tee reports/2025-10-cli-flags/phase_i/supervisor_command/logs/pytest_collect.txt` to log module import status.
- Document the workflow in `reports/2025-10-cli-flags/phase_i/supervisor_command/README.md` (command snippet, metrics table, stdout highlights, pointer to plan lines).
- Update docs/fix_plan.md Attempts section with Attempt #27 summary referencing README path and metrics (correlation, RMSE, polarization delta, nb-compare threshold).
- Snapshot file list using `ls -R reports/2025-10-cli-flags/phase_i/supervisor_command > reports/.../logs/file_tree.txt` for audit trail.
- Leave binaries untracked (reports/ is gitignored) but ensure README enumerates file names for reviewers.
Pitfalls To Avoid:
- No code edits this loop; parity failure should result in documented findings, not hotfixes.
- Forgetting `KMP_DUPLICATE_LIB_OK=TRUE` in environment will crash PyTorch/nb-compare; keep it in Do Now command.
- Do not modify A.mat or scaled.hkl; they are protected assets referenced in docs/index.md.
- Avoid manual renaming of nb-compare outputs before copying; keep canonical filenames for reviewer clarity.
- Keep the command arguments identical to the supervisor specification; small deviations (pixel size, beam center) break parity.
- Do not delete previous Phase H artifacts; they remain part of the parity narrative.
- Ensure ROI-specific follow-up runs (if any) use new outdir to avoid overwriting baseline evidence.
- Skip CUDA for now; mixing devices mid-loop complicates evidence and is off-plan.
- Do not relax nb-compare threshold; failing correlation means parity is still broken.
- Capture actual runtime logs; summary without stdout/stderr is insufficient for plan closure.
Pointers:
- plans/active/cli-noise-pix0/plan.md:110
- plans/active/cli-noise-pix0/plan.md:114
- docs/fix_plan.md:448
- docs/fix_plan.md:454
- specs/spec-a-cli.md:120
- specs/spec-a-cli.md:152
- docs/architecture/detector.md:70
- docs/development/testing_strategy.md:90
- docs/architecture/c_parameter_dictionary.md:95
- README_PYTORCH.md:180
- galph_memory.md:1
Next Up: If correlation ≥0.999 and polarization matches, run `nb-compare --roi 100 356 100 356 --outdir reports/2025-10-cli-flags/phase_i/supervisor_command/roi --save-diff --threshold 0.999 -- [same args]` to validate local alignment, then brief supervisor before touching vectorization Phase A.
Priorities & Rationale:
- docs/debugging/detector_geometry_checklist.md:12 reminds us to validate units (meters) when reviewing pix0 output; include this check in README.
- docs/architecture/pytorch_design.md:45 emphasizes device-neutral tensor handling; confirm nb-compare logs show no implicit CPU/GPU transfers.
- docs/development/c_to_pytorch_config_map.md:40 maps CLI flags to config fields; cross-reference when interpreting stdout warnings.
How-To Map:
- Verify Kahn factor computation manually: after nb-compare, run `python scripts/check_polarization.py --config reports/2025-10-cli-flags/phase_i/supervisor_command/summary.json` if divergence suspected (script optional, log decision).
- Store SHA256 hashes (`shasum -a 256`) of c_float.bin and py_float.bin in logs/hashes.txt for reproducibility.
- Capture `env | sort > reports/.../logs/environment.txt` prior to running commands to document environment variables (especially NB_C_BIN, AUTHORITATIVE_CMDS_DOC).
- Take note of nb-compare speedup; comment in README whether PyTorch is faster or slower than C for this scenario.
- For ROI follow-up, note ROI bounds origin (slow,fast) to confirm orientation matches spec.
Pitfalls To Avoid:
- Avoid mixing relative/absolute paths when referencing artifacts; stick to repo-relative paths for traceability.
- Be cautious about shell history expansions (e.g., `!`); include commands exactly as executed in README to aid reproduction.
- Do not re-run nb-compare with the same outdir unless intentionally overwriting; use unique subdirectories per attempt.
- Remember that -nonoise suppresses noiseimage output; confirm there is no stray noise file produced and note that in README.
- Watch for warnings about custom vectors being re-normalized; if seen, include them in Attempt #27 notes.
- Keep `scaled.hkl` untouched; do not open in editors that might modify newline encoding (Protected Asset).
Pointers:
- docs/debugging/detector_geometry_checklist.md:12
- docs/architecture/pytorch_design.md:45
- docs/development/c_to_pytorch_config_map.md:40
Next Up: Document whether further polarization-specific pytest coverage is needed (e.g., multi-source case) once parity evidence is reviewed.
Next Up: Prepare to switch supervision to plans/active/vectorization.md Phase A once CLI parity item closes.
Evidence Checklist:
- ✔ nb-compare summary.json archived with correlation, RMSE, peak metrics.
- ✔ stdout/stderr captured for both C and PyTorch runs.
- ✔ README.md summarises command, environment, metrics, polarization numbers, pix0 deltas.
- ✔ pytest targeted node executed and log saved under logs/.
- ✔ pytest --collect-only log saved to confirm import health.
- ✔ hashes.txt records SHA256 of float outputs.
- ✔ environment.txt captures NB_C_BIN, NB_PY_BIN resolution, AUTHORITATIVE_CMDS_DOC.
- ✔ Attempt #27 entry drafted with metrics, artifact paths, command snippet, and pass/fail verdict.
- ✔ ROI follow-up decision recorded (even if deferred) with rationale.
- ✔ No stray noiseimage/img artifacts present; README notes confirmation.
- ✔ Beam center comparison documented (C vs PyTorch) to prove H4 results persist under this geometry.
- ✔ Mention in README whether nb-compare speedup meets expectations or if further perf work needed.
- ✔ Cite relevant spec lines (specs/spec-a-cli.md:120, docs/architecture/detector.md:70) in README for reviewer convenience.
- ✔ Append `ls -R` output to file_tree.txt so reviewers can browse artifact structure without local listing.
- ✔ screenshot/diff PNG preview (if needed) described; actual PNG kept for review.
- ✔ Document any warnings emitted by nb-compare (none expected) and note resolution if they appear.
- ✔ Confirm that -nonoise suppressed noise image by checking absence of noiseimage.img; log observation.
- ✔ Confirm pix0 vector printed in stdout matches C to within 1e-8 m and note delta magnitude.
- ✔ Confirm polarization factor exactly matches C; include direct numeric copy in README.
- ✔ Add section in README summarising follow-up tasks (e.g., vectorization) so context is carried forward.
Observation Tasks:
- Note whether nb-compare indicates resampling (should be false); if true, investigate and log cause.
- Observe runtime difference; if PyTorch slower, flag for PERF-PYTORCH-004 plan notes.
- Observe sum_ratio; ensure within 1 ± 0.01; if outside, treat as failure and update fix_plan accordingly.
- Observe mean/max peak distances; if >1 pixel, parity not acceptable; log issue.
- Observe any CLI warnings (e.g., custom vectors re-normalized) and interpret using c_parameter_dictionary references.
Communication Notes:
- When updating docs/fix_plan.md, include correlation value to six decimals and reference README path.
- Mention in Attempt #27 whether additional tests (e.g., ROI-specific) were executed or deferred.
- Flag in README if command produced large output size (float bin) and confirm storage path (reports/...).
- Provide guidance on re-running command (copy/paste ready) for reviewers within README.
- Record command start/end timestamps to estimate runtime for future scheduling.
- Mention in README that this evidence is prerequisite for moving to plans/active/vectorization.md Phase A.
- Note any environment anomalies (e.g., warnings about MKL, fallback to python -m) and include them in logs.
- Confirm that nb-compare auto-selected PyTorch runner (`nanoBragg` or `python -m nanobrag_torch`) and record the exact command path.
- If nb-compare fails, capture exit code and reason in README and fix_plan attempt before halting.
Closing Actions:
- After evidence review, notify supervisor (via Attempt #27 summary) that CLI parity is ready for final decision.
- Prepare short bullet list in README of checks performed so future audits can scan quickly.
- Clean workspace only after supervisor sign-off; do not delete artifacts pre-review.
- Keep this input.md untouched; engineer must not edit it per SOP.
- Ensure git status remains clean (reports/ ignored) before handing work back.
- Document any deviations from plan (e.g., additional ROI run) in README and fix_plan to avoid ambiguity.
- Capture any manual calculations (e.g., delta pix0) in README with explicit numeric values.
- Optionally add note about machine specs (CPU model) to help interpret runtimes.
- Reconfirm nb-compare threshold used (0.999) in README to show compliance.
- Save command history snippet (`history | tail -n 20`) into logs/history_tail.txt for traceability.
- If you create helper notebooks/scripts, store them under reports/ with explanatory note; do not leave stray files in repo root.
- Remember to include note in README that noiseimage.img is intentionally absent due to -nonoise.
- Validate oversample parameter (1) matches expectation; mention in README as part of command summary.
- Document spool of NB_C_BIN resolution order (found path) in README for reproducibility.
- Confirm py_stdout does not contain warnings about missing HKL entries; if it does, note default_F usage.
- Mention in README whether custom spindle axis was accepted (should match -1 0 0) per stdout.
- Ensure controlling branch (feature/spec-based-2) remains unchanged after evidence loop.
- Provide concluding statement in README and Attempt #27 that CLI parity requirement is met pending supervisor approval.
