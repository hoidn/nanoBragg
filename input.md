Summary: Capture fresh C traces to prove pix0 override precedence before touching PyTorch scaling.
Phase: Evidence
Focus: CLI-FLAGS-003 / -nonoise & -pix0_vector_mm parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/, reports/2025-10-cli-flags/phase_h5/c_precedence.md
Artifacts note: store raw stdout with TRACE_C lines intact; do not trim progress banners or warnings.
Artifacts note: ensure the precedence memo records timestamp, git SHA, and NB_C_BIN path for reproducibility.
Artifacts note: attach a brief summary of observed deltas (pix0, Fbeam, Sbeam) at the top of the memo for quick reference.
Do Now: CLI-FLAGS-003 H5a — run `NB_C_BIN=./golden_suite_generator/nanoBragg` with the supervisor command (first WITH, then WITHOUT `-pix0_vector_mm`) and tee stdout to `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/{with_override,without_override}.log`; refresh `c_precedence.md` with the new dot-product derivation.
Do Now note: after both runs, jot down immediate observations (match vs mismatch) before diving into diff analysis.
Do Now note: keep terminal scrollback until logs are verified on disk in case tee fails.
If Blocked: Capture at least the WITH-override run to `reports/.../c_traces/2025-10-22/with_override_attempt.log`, log the failure cause plus environment in c_precedence.md under a new "Attempts" heading, and stop.
If Blocked note: mention whether the failure occurred before or after command launch (e.g., missing NB_C_BIN vs runtime crash).
If Blocked note: record stdout tail (~20 lines) in the memo so the supervisor can triage remotely.

Priorities & Rationale:
- docs/fix_plan.md:508-570 — Next actions demand H5a evidence before Phase K resumes.
  Reasserts that normalization work is paused until pix0 override parity is proven with new traces.
- plans/active/cli-noise-pix0/plan.md:1-35 — Plan context flags the 1.14 mm pix0 delta blocking normalization.
  Highlights the new 2025-10-22 bullet noting stale C evidence and the need for refreshed logs.
- reports/2025-10-cli-flags/phase_j/trace_c_scaling.log:164-202 — Baseline C values (`F_latt` 3.56e4, polar 0.9126) to match against future PyTorch traces.
  Use these numbers as the acceptance target when comparing PyTorch outputs in H5c.
- docs/architecture/detector.md — Details pix0 projection math for custom vectors so the dot-product derivation is documented verbatim.
  Cite the BEAM pivot equations when updating c_precedence.md to keep derivations authoritative.
- specs/spec-a-cli.md — Canonical CLI semantics for `-pix0_vector_mm`, including unit expectations for the override flag.
  Restate the spec text in the precedence memo to show compliance with the external contract.
- docs/debugging/detector_geometry_checklist.md — Required checklist before claiming detector parity; note the expectation on meter vs millimetre conversions.
  Reference its guidance on verifying Fbeam/Sbeam signs when you summarise the traces.

How-To Map:
1. Prep instrumentation
   - Run `export NB_C_BIN=./golden_suite_generator/nanoBragg` from repo root to select the instrumented binary.
   - Ensure the binary still contains the TRACE_C printf hooks for pix0/Fbeam/Sbeam; rebuild if needed before running the command.
2. Create output directories
   - Execute `mkdir -p reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22` to keep artifacts segregated by date.
   - Confirm the directory exists so later tee commands do not fail silently.
3. WITH override run
   - Invoke the supervisor command exactly as documented, including `-pix0_vector_mm -216.336293 215.205512 -230.200866`.
   - Command template:
     `"$NB_C_BIN" -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 2>&1 | tee reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/with_override.log`.
   - Let the run complete; confirm the log contains TRACE_C lines for pix0, Fbeam, Sbeam, hkl, and F_latt.
   - After the run, quickly `grep TRACE_C: pix0` to verify instrumentation fired before moving on.
   - Note any warnings or error messages emitted; copy them into the memo verbatim.
4. WITHOUT override run
   - Repeat the command verbatim but remove the `-pix0_vector_mm` triplet (keep every other flag identical).
   - Tee output to `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/without_override.log` for side-by-side comparison.
   - Verify the log still reports TRACE_C values; you should see geometry differences if the override is applied.
   - Use `grep TRACE_C: F_latt` on both logs to sanity-check magnitude (expect ~3.56e4 vs ~3.56e4 once fixed).
   - If the values remain identical, flag it immediately in the memo and halt further implementation work.
5. Diff and annotate
   - Run `diff -u reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/with_override.log reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/without_override.log > reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/diff.log`.
   - Inspect the diff to ensure Fbeam, Sbeam, pix0_vector, and hkl values differ; record precise deltas in the memo.
6. Update precedence memo
   - Append a new section to `reports/2025-10-cli-flags/phase_h5/c_precedence.md` summarising the two runs.
   - Include a table with pix0, Fbeam, Sbeam, F_latt, and hkl values plus the computed dot products (pix0 delta projected on fdet/sdet).
   - Document any surprises (e.g., if values still match identically) and flag for supervisor review before moving forward.
7. Housekeeping
   - Keep raw logs unedited; if redaction is necessary, duplicate the file first.
   - Preserve file permissions (644) so later tooling can read them without sudo.
   - Note the git status after updates so the supervisor can diff the memo changes easily next loop.

Pitfalls To Avoid:
- Don't skip `NB_C_BIN`; the root binary lacks TRACE_C outputs needed for precedence analysis.
  Using the wrong binary forces another evidence loop and wastes time.
- No pytest runs this loop (Evidence gate).
  Tests violate the Evidence-phase rule; stick to command-line traces only.
- Keep outputs under `reports/2025-10-cli-flags/phase_h5/`; Protected Assets forbid ad-hoc directories.
  Ensure nested directories use the 2025-10-22 stamp to avoid clobbering prior evidence.
- Retain the original CLI flag order; reordering may change precedence checks in nanoBragg.c.
  The goal is a faithful reproduction of the supervisor command, not experimentation.
- Ensure logs capture full stdout/stderr via `tee`; partial logs invalidate the evidence and make diffs useless.
  Double-check file sizes after each run.
- Avoid editing pix0 math or Detector code yet—this loop is evidence gathering only.
  Implementation changes belong to a later plan phase.
- Do not delete previous 2025-10-21 traces; archive new ones alongside them for comparison.
  Historical context is needed to explain the change in conclusions.
- Confirm commands run from repo root; relative paths assume cwd=/Users/ollie/Documents/nanoBragg3.
  Running elsewhere will break path resolution for A.mat and scaled.hkl.
- Respect device neutrality when reporting later—no hard-coded CPU assumptions in notes.
  Mention device/dtype explicitly if relevant in observations.
- Document units (meters vs mm) explicitly in c_precedence.md updates.
  The spec expects clarity on unit conversions, especially for `_mm` overrides.

Pointers:
- plans/active/cli-noise-pix0/plan.md:7-121 — Phase H5 goal, exit criteria, and post-update guidance describing the stale C evidence.
  Follow the checklist so H5a is satisfied before PyTorch work resumes.
- docs/fix_plan.md:520-570 — Attempt #29 status plus supervisor note correcting the earlier "override ignored" assumption.
  Reference this when writing the precedence summary to show the misinterpretation was resolved.
- reports/2025-10-cli-flags/phase_j/scaling_chain.md — Factor-by-factor breakdown identifying `F_latt` as the first divergence.
  Use its values to cross-check the C trace numbers you capture.
- docs/architecture/detector.md — BEAM pivot equations and projection rules for pix0 and beam center handling.
  Quote the relevant equation in your memo to tie the dot-product math back to the spec.
- docs/debugging/detector_geometry_checklist.md — Mandatory detector debugging checklist to confirm geometry evidence quality.
  Tick through its steps (units, axis orientation, pivot) while reviewing the new C logs.
- specs/spec-a-cli.md — CLI flag reference ensuring behaviour matches the normative spec.
  Point to the `pix0_vector_mm` paragraph when you justify the observed precedence.

Next Up: Phase H5c PyTorch trace capture and comparison once the C precedence evidence is logged and reviewed.
Next Up note: prepare to mirror the C trace structure so diffing is one-to-one (ensure TRACE_PY lines include pix0/Fbeam/Sbeam/F_latt).
