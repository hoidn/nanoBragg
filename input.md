timestamp: 2025-10-06T00:49:07Z
commit: e409734
author: galph
focus: CLI-FLAGS-003 Phase E — Parallel trace to locate first divergence
Summary: Capture and compare C vs PyTorch pixel traces for the supervisor parity run to expose the first physics mismatch.
Phase: Evidence
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_e/

Do Now: [CLI-FLAGS-003] Phase E1–E2 — instrument the C binary for pixel (1039,685) and gather matching PyTorch trace logs; authoritative commands live in ./docs/development/testing_strategy.md.
If Blocked: Capture failing commands plus stderr/stdout to reports/2025-10-cli-flags/phase_e/trace_attempt_FAIL.log, note the scenario in docs/fix_plan.md [CLI-FLAGS-003] Attempts, then pause for supervisor direction.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:80 — Phase E gate; no implementation changes allowed until trace pair exists.
- docs/fix_plan.md:664 — Next Actions explicitly demand the parallel trace before further parity work.
- docs/debugging/debugging.md:24 — SOP mandates identical trace schema; we must follow it precisely for trustworthy comparisons.
- docs/development/c_to_pytorch_config_map.md:50 — Detector and beam vectors must match C inputs; sanity-check these during trace capture.
- docs/architecture/detector.md:210 — CUSTOM convention math defines pix0 origin; interpret trace outputs against this reference.
- reports/2025-10-cli-flags/phase_d/intensity_gap.md — Phase D3 analysis identified geometry divergence; the highlighted peak pixel anchors this loop.

How-To Map:
- Pre-flight:
  * Export `AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md` at shell start so logs capture the context variable.
  * Verify git worktree clean except for temporary TRACE edits (`git status -sb`); avoid dangling instrumentation when run completes.
  * Confirm `NB_C_BIN=./golden_suite_generator/nanoBragg` is up to date (`make -C golden_suite_generator` if last build predates loop; document command if rebuilt).
- C trace instrumentation (Phase E1):
  * Add `TRACE_C:` printf statements in `golden_suite_generator/nanoBragg.c` near the pixel loop to dump: `pix0_vector`, `incident_beam_direction`, `pixel_position`, `scattering_vector`, `h,k,l`, `F_cell`, `F_latt`, `omega_pixel`, and final intensity for the sampled pixel.
  * Use consistent label ordering per docs/debugging/debugging.md (one variable per line, 12–15 significant digits, meters vs Å as documented).
  * Rebuild via `timeout 120 make -C golden_suite_generator`; stash the diff or note touched lines in reports/2025-10-cli-flags/phase_e/instrumentation_notes.md.
  * Run the supervisor parity command with `-dump_pixel 1039 685` appended:
    `NB_C_BIN=./golden_suite_generator/nanoBragg timeout 120 "$NB_C_BIN" -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -dump_pixel 1039 685 2>&1 | tee reports/2025-10-cli-flags/phase_e/c_trace.log`
  * Immediately archive the instrumented C diff (if any) to `reports/2025-10-cli-flags/phase_e/c_trace.patch` for reproducibility and rollback documentation.
- PyTorch trace capture (Phase E2):
  * Prefer the existing `scripts/debug_pixel_trace.py`; if parameters are missing, augment via CLI options or by preparing a temporary JSON config describing the supervisor command (store as `reports/2025-10-cli-flags/phase_e/supervisor_command.json`).
  * Invocation template:
    `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/debug_pixel_trace.py --mat A.mat --hkl scaled.hkl --lambda 0.976800 --oversample 1 --pix0-vector-mm -216.336293 215.205512 -230.200866 --flux 1e18 --exposure 1 --beamsize 1.0 --spindle-axis -1 0 0 --Xbeam 217.742295 --Ybeam 213.907080 --distance 231.274660 --pixel 0.172 --detpixels 2463 2527 --odet-vector -0.000088 0.004914 -0.999988 --sdet-vector -0.005998 -0.999970 -0.004913 --fdet-vector 0.999982 -0.005998 -0.000118 --beam-vector 0.00051387949 0.0 -0.99999986 --Na 36 --Nb 47 --Nc 29 --osc 0.1 --phi 0 --phisteps 10 --pixel-index 1039 685 --out reports/2025-10-cli-flags/phase_e/pytorch_trace.log`
  * Ensure the script prints variables with `TRACE_PY:` prefix matching the C labels; adjust script if necessary (log modifications in instrumentation notes, but revert code before finishing loop).
  * If script lacks features, clone it into `reports/2025-10-cli-flags/phase_e/trace_harness.py` (evidence-only) and document invocation details; use identical math paths as production code—no re-derivations.
- Trace comparison (Phase E3 prerequisites):
  * Run `diff -u reports/2025-10-cli-flags/phase_e/c_trace.log reports/2025-10-cli-flags/phase_e/pytorch_trace.log | tee reports/2025-10-cli-flags/phase_e/trace_diff.txt`.
  * Draft `reports/2025-10-cli-flags/phase_e/trace_comparison.md` summarising the first mismatched value, referencing spec/arch lines and hypothesising potential causes.
  * Update `docs/fix_plan.md` `[CLI-FLAGS-003]` Attempts with command snippets, divergence description, and next steps (E3 completion will be tracked in Phase E table).
- Trace variable checklist (reference while capturing logs):
  * Detector origins: `pix0_vector`, `fdet_vector`, `sdet_vector`, `odet_vector` (meters).
  * Beam geometry: `incident_beam_direction`, `beam_vector`, `distance_corrected`.
  * Pixel position & scattering: `pixel_pos_meters`, `diffracted_vec`, `scattering_vec_A_inv`.
  * Reciprocal space: `h`, `k`, `l`, `stol`, `twotheta`.
  * Intensity path: `F_cell`, `F_latt`, `omega_pixel`, `polar`, `intensity`.
  * Normalization scalars: `steps`, `fluence`, `r_e_sqr`, `source_weight` (if present).
- Post-run hygiene:
  * Remove any temporary TRACE prints from C source; re-run `make -C golden_suite_generator` to restore pristine binary (log deletion command in instrumentation notes).
  * Ensure reports directory contains: `c_trace.log`, `pytorch_trace.log`, `trace_diff.txt`, `trace_comparison.md`, `instrumentation_notes.md`, and any auxiliary configs.
  * Leave a succinct Attempt entry in docs/fix_plan.md capturing metrics, divergence, and recommendations before closing the loop.
- Instrumentation notes template (capture in reports/2025-10-cli-flags/phase_e/instrumentation_notes.md):
  * Header with timestamp, git commit hash, and NB_C_BIN path used for the run.
  * List of source files touched (e.g., nanoBragg.c line ranges) and the exact TRACE labels added.
  * Build commands executed (include timeout wrapper) and whether recompilation was necessary.
  * Runtime command(s) with full argument list and wall-clock durations.
  * Observed warnings or anomalies during execution (e.g., OpenMP thread counts, floatfile writes).
  * Post-run clean-up actions (TRACE removal commands, `git checkout --` usage if applied).
  * Checklist tick-boxes: `[ ] C trace captured`, `[ ] PyTorch trace captured`, `[ ] diff archived`, `[ ] fix_plan updated`.
- Trace log formatting reminders:
  * Prefix C lines with `TRACE_C:` and PyTorch lines with `TRACE_PY:` to simplify diffing.
  * Maintain consistent variable order across both traces to minimize diff noise.
  * Use scientific notation with fixed precision (e.g., `%.15g`) so trailing zeros do not obscure differences.
  * Include units in comments once per section if helpful (e.g., `# meters`) rather than per line.
  * Separate logical groups (geometry, beam, scattering, intensity) with blank lines for readability.

Pitfalls To Avoid:
- Do not touch simulator/detector production code—this loop is for evidence gathering only.
- Keep CUSTOM convention inputs verbatim; avoid reordering vector components or unit scaling outside documented conversions.
- Respect instrumentation rule: reuse production helpers rather than recomputing variables in trace scripts.
- Avoid torch.compile, Dynamo caching tweaks, or manual GPU/CPU transfers that could skew trace output.
- Protected Assets Rule: never delete or rename artifacts listed in docs/index.md (loop.sh, supervisor.sh, input.md, A.mat, etc.).
- Always set `KMP_DUPLICATE_LIB_OK=TRUE` before importing torch in any Python harness.
- Treat `scaled.hkl` and `A.mat` as read-only; copy if you need variants.
- Capture failures immediately—no reruns without new instrumentation notes.
- Keep trace precision high (15 significant digits) and align units with spec (meters for detector geometry, Å/Å⁻¹ for physics).
- Remove TRACE diffs before ending loop; document clean-up in instrumentation notes to prevent accidental commits.

Pointers:
- docs/development/testing_strategy.md#21-ground-truth-parallel-trace-driven-validation — Canonical trace workflow.
- docs/debugging/debugging.md:40 — Variable naming schema and precision requirements for trace logs.
- docs/architecture/c_parameter_dictionary.md#pix0_vector_mm — Flag semantics; confirm conversions reflect this entry.
- docs/architecture/detector.md:255 — CUSTOM basis construction; compare with trace outputs.
- src/nanobrag_torch/models/detector.py:360 — Pix0 override assignment path to validate against C trace results.
- src/nanobrag_torch/simulator.py:820 — Steps/normalization path; note values once divergence pinpointed.
- reports/2025-10-cli-flags/phase_c/parity/c_cli.log — Baseline C run (without TRACE) for cross-checking derived values.

Next Up:
- If traces align quickly and first divergence is recorded, outline remediation hypotheses in `reports/2025-10-cli-flags/phase_e/trace_comparison.md` and queue Phase C3 doc updates for the following loop.
- Otherwise, if trace capture hits tooling gaps (e.g., debug script lacking arguments), document blockers clearly in instrumentation_notes.md and propose one lightweight helper script for next loop.
- Maintain the evidence-only stance: defer any code fix sketches until the divergence is documented and linked to spec/arch citations.
- Prepare a short bullet summary for the next Attempts History entry so future loops can fast-forward into implementation once the trace is in hand.
- Note any environmental anomalies (CPU/GPU availability, OpenMP thread differences) so they can be ruled out quickly in subsequent analysis loops.
- Keep the reports directory tidy—each artifact should include a short README block explaining how to regenerate it.
- Double-check that `input.md` remains unedited by Ralph; any adjustments must flow through supervisor loops only.
- Sync the new artifacts with `git add` next supervisor pass to prevent accidental loss.
