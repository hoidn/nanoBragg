Timestamp: 2025-10-06T04:55:24Z
Commit: 6a0d252
Author: galph
Active Focus: [CLI-FLAGS-003] Phase G3 trace verification + parity rerun

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm (Phase G3) — env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_e/trace_harness.py > reports/2025-10-cli-flags/phase_g/traces/trace_py.log

If Blocked: Capture PyTorch detector/crystal dumps via `python scripts/debug_pixel_trace.py --pixel 1039 685 --config reports/2025-10-cli-flags/phase_e/trace_config.yaml > reports/2025-10-cli-flags/phase_g/traces/trace_py_blocked.log` and log the failure mode in docs/fix_plan.md Attempts before exiting.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:80 — Phase G requires fresh TRACE_C/TRACE_PY logs plus parity rerun before we can declare geometry parity.
- docs/fix_plan.md:454 — Current Next Actions emphasise executing Phase G3 and refreshing parity artifacts under `reports/2025-10-cli-flags/phase_g/`.
- reports/2025-10-cli-flags/phase_e/trace_harness.py#L20 — Harness must now consume MOSFLM A* tensors to mirror the CLI pipeline implemented in Phase G2.
- reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/metrics.json — Previous parity metrics (corr≈−5e-06) establish the regression we must improve.
- docs/debugging/debugging.md:32 — SOP mandates parallel trace comparison before implementing further fixes; adhere strictly to the trace workflow.
- specs/spec-a-cli.md:70 — Defines semantics for `-mat`, `-pix0_vector_mm`, and `-beam_vector`; parity proves we honour the spec.
- docs/architecture/detector.md:118 — CUSTOM pivot math drives pix0 reconstruction; verifying it via traces guards against regressions.
- docs/architecture/pytorch_design.md:186 — Core Rules 12–13 summarised; G3 must show these remain intact with MOSFLM orientation.
- docs/development/c_to_pytorch_config_map.md:34 — Confirms CLI→config threading for MOSFLM matrices and pix0 overrides; treat as authoritative mapping while auditing traces.
- reports/2025-10-cli-flags/phase_g/design/orientation_notes.md — Keep this file updated so future loops can see what changed between Phase E and Phase G.

How-To Map:
- `export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md`
- `export KMP_DUPLICATE_LIB_OK=TRUE`
- `export NB_C_BIN=./golden_suite_generator/nanoBragg`
- `mkdir -p reports/2025-10-cli-flags/phase_g/design`
- `mkdir -p reports/2025-10-cli-flags/phase_g/traces`
- `mkdir -p reports/2025-10-cli-flags/phase_g/parity`
- `mkdir -p reports/2025-10-cli-flags/phase_g/pytest`
- Re-read `reports/2025-10-cli-flags/phase_e/trace_summary.md` to recall the pix0 divergence history.
- Append updated context to `reports/2025-10-cli-flags/phase_g/design/orientation_notes.md` (include why MOSFLM tensors fix the earlier fallback).
- Edit `reports/2025-10-cli-flags/phase_e/trace_harness.py`:
-  • Add `mosflm_a_star`, `mosflm_b_star`, `mosflm_c_star` fields when constructing `CrystalConfig`.
-  • Ensure the harness still converts mm→m for pix0 overrides exactly once.
-  • Confirm Device/dtype arguments use float64 for traces, matching Phase E precision.
-  • Thread `DetectorConvention.CUSTOM` and pivot selection exactly as CLI does after Phase F2.
- Record edits and reasoning in `reports/2025-10-cli-flags/phase_g/design/harness_delta.md` (line numbers and tensor-handling notes).
- If the instrumented binary changed, reapply `reports/2025-10-cli-flags/phase_e/c_trace.patch` and run `make -C golden_suite_generator`.
- Capture build output in `reports/2025-10-cli-flags/phase_g/design/c_trace_build.log` for audit.
- Generate PyTorch trace:
-  • `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_e/trace_harness.py > reports/2025-10-cli-flags/phase_g/traces/trace_py.log`
-  • Redirect stderr to `trace_py.stderr` to retain warnings; note any warnings in design notes.
- Generate C trace:
-  • `$NB_C_BIN -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -dump_pixel 1039 685 2>&1 | tee reports/2025-10-cli-flags/phase_g/traces/trace_c.log`
- Verify both logs contain 40 trace lines; if counts differ log the discrepancy in the summary file.
- Diff traces:
-  • `diff -u reports/2025-10-cli-flags/phase_g/traces/trace_c.log reports/2025-10-cli-flags/phase_g/traces/trace_py.log > reports/2025-10-cli-flags/phase_g/traces/trace_diff.log`
-  • Capture the index of the first mismatch (if any) and the corresponding variable name.
- Document outcomes in `reports/2025-10-cli-flags/phase_g/trace_summary_orientation.md` (sections: Overview, Metrics, Divergence, Next Steps).
- Run parity comparison:
-  • `nb-compare --outdir reports/2025-10-cli-flags/phase_g/parity --resample --threshold 0.995 -- -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0`
-  • Preserve the generated PNGs and metrics.json; add commentary (corr, RMSE, max diff, mean diff) to `parity/README.md`.
- Verify PyTorch CLI produced `img.bin` without noise image when `-nonoise` is present; log observation in summary.
- Run regression tests sequentially:
-  • `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py -k pix0 -v | tee reports/2025-10-cli-flags/phase_g/pytest/test_cli_flags.log`
-  • `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_geo_003.py::TestATGEO003RFactorAndBeamCenter::test_r_factor_calculation -v | tee -a reports/2025-10-cli-flags/phase_g/pytest/test_at_geo_003.log`
-  • If CUDA available: `CUDA_VISIBLE_DEVICES=0 env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py -k pix0 --maxfail=1 -v | tee reports/2025-10-cli-flags/phase_g/pytest/test_cli_flags_cuda.log`
- Review pytest outputs for new warnings; document any in design notes.
- Update `docs/fix_plan.md` `[CLI-FLAGS-003]` Attempts with Attempt #18 (include metrics, artifact paths, notable observations, next steps for Phase H).
- Append a short polarization TODO (current C vs PyTorch Kahn factor) to `trace_summary_orientation.md` to seed Phase H.
- Ensure all artifacts are referenced in the summary and staged later for supervisor review.
- Inspect `reports/2025-10-cli-flags/phase_g/parity/metrics.json` with `jq '.'` and copy headline numbers into the summary file.
- Capture a thumbnail of the nb-compare diff PNG (e.g., via `open` or `imgcat`) and describe visual cues in the parity README.
- Cross-check that PyTorch CLI still emits stdout banner lines introducing configs; note any changes for future regression tests.
- Re-run the PyTorch CLI with `--help` to confirm new flags remain documented; log the command output under `reports/2025-10-cli-flags/phase_g/design/help_output.txt`.
- After tests, run `git status --short` and `git diff` to audit changes before requesting supervisor review.

Pitfalls To Avoid:
- No fallback to canonical reciprocal vectors when MOSFLM tensors are provided; confirm by logging `crystal.config.mosflm_a_star` after construction.
- Avoid `.item()` on tensors like `close_distance`, `distance_corrected`, or volumes; keep them differentiable.
- Do not mix devices—ensure all tensors stay on CPU float64 for traces; PyTorch + CUDA mismatches will skew comparisons.
- Keep `(slow, fast)` indexing consistent; swapping axes recreates 90° rotations and invalidates metrics.
- Retain CUSTOM pivot logic exactly as in Phase F2; do not reintroduce the pre-transform pix0 override.
- Do not overwrite the frozen root `./nanoBragg` binary; instrumentation belongs under `golden_suite_generator/`.
- Store every artifact under `reports/2025-10-cli-flags/phase_g/`; stray files violate hygiene SOP.
- Run `nb-compare` with `--resample`; skipping it causes false mismatches due to shape differences.
- Commit summary updates only after verifying metrics; premature updates cause fix_plan drift.
- Keep worktree clean; note any unavoidable leftovers in docs/fix_plan.md.
- When editing harnesses/tests, avoid introducing new imports under `reports/` that shadow src modules; keep sys.path modifications minimal and documented.
- Double-check `Simulator.incident_beam_direction` is set exactly once; duplicate assignments can mask orientation bugs.

Pointers:
- plans/active/cli-noise-pix0/plan.md#L86 — G3 checklist and exit criteria.
- docs/fix_plan.md:452 — Current status plus previous attempts for `[CLI-FLAGS-003]`.
- reports/2025-10-cli-flags/phase_e/trace_harness.py#L55 — Injection point for MOSFLM vectors.
- docs/debugging/debugging.md:29 — Trace SOP reference.
- specs/spec-a-cli.md:82 — Flag semantics governing parity command.
- docs/architecture/detector.md:146 — CUSTOM pix0 and close_distance formulas.
- docs/architecture/pytorch_design.md:186 — Core Rule 13 recap.
- reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/metrics.json — Prior parity baseline for comparison.
- plans/active/vectorization.md#L15 — Upcoming initiative slated once parity succeeds.
- docs/development/testing_strategy.md:30 — Tier 1 parity expectations to keep in mind when reviewing nb-compare output.
- reports/2025-10-cli-flags/phase_e/trace_diff.txt — Refer back to the prior diff for context on expected variable order and formatting.
- reports/2025-10-cli-flags/phase_e/pytorch_instrumentation_notes.md — Contains exact TRACE_PY printing conventions to reuse.
- docs/development/pytorch_runtime_checklist.md:12 — Device/dtype neutrality reminders relevant when adjusting harness tensors.
- reports/2025-10-cli-flags/phase_a/README.md — Original semantics capture; revisit to confirm new evidence remains consistent.

Next Up: [VECTOR-TRICUBIC-001] Phase A baseline capture after CLI parity artifacts are refreshed and logged.
