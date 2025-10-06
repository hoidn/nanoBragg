Summary: Capture fresh C traces proving how pix0 overrides interact with custom vectors before altering PyTorch geometry.
Phase: Evidence
Focus: CLI-FLAGS-003 / Phase H5 pix0 override
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_h5/c_traces/, reports/2025-10-cli-flags/phase_h5/c_precedence.md, reports/2025-10-cli-flags/phase_h5/attempts/
Do Now: CLI-FLAGS-003 Phase H5a — export NB_C_BIN=./golden_suite_generator/nanoBragg && "$NB_C_BIN" -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 2>&1 | tee reports/2025-10-cli-flags/phase_h5/c_traces/with_override.log; repeat without -pix0_vector_mm to capture without_override.log.
If Blocked: If TRACE_C lines disappear, rebuild instrumentation via reports/2025-10-cli-flags/phase_e/c_trace.patch (make -C golden_suite_generator) and log the failed attempt under reports/2025-10-cli-flags/phase_h5/attempts/ before retrying.
Priorities & Rationale:
- docs/fix_plan.md:448 — Next actions require H5 traces first; no PyTorch edits until we know C’s precedence.
- docs/fix_plan.md:512 — Attempt #28 already ties scaling mismatch to F_latt; confirming pix0 override keeps that diagnosis grounded.
- plans/active/cli-noise-pix0/plan.md:111 — H5 exit criteria explicitly hinge on new C evidence with both override states.
- plans/active/cli-noise-pix0/plan.md:118 — H5b guidance depends on projection maths; we must verify source data before coding.
- docs/architecture/detector.md:51 — BEAM pivot formula defines the relationship between pix0, Fbeam, and Sbeam; confirm C still honours it with overrides.
- docs/development/c_to_pytorch_config_map.md:35 — Detector flag mapping notes mm↔m conversions; ensure trace logs reflect those conversions accurately.
- specs/spec-a-cli.md:57 — CLI precedence rules for custom vectors vs pix0 flags must be respected; evidence informs spec compliance notes.
- reports/2025-10-cli-flags/phase_j/scaling_chain.md:30 — Scaling chain identified F_latt mismatch; updated C traces show whether the override actually shifts Fbeam/Sbeam.
- reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/summary.md — Previous parity run had pix0 deltas <2e-8 m; use as comparison baseline.
- CLAUDE.md:80 — Protected Assets rule reminds us not to touch docs/index.md-linked files while gathering evidence.
How-To Map:
- Set export NB_C_BIN=./golden_suite_generator/nanoBragg for reproducibility before running any commands.
- mkdir -p reports/2025-10-cli-flags/phase_h5/c_traces/ reports/2025-10-cli-flags/phase_h5/attempts/ to keep artefacts organized.
- Ensure the instrumented C binary is up to date; `make -C golden_suite_generator nanoBragg` if TRACE_C macros were modified.
- For the with_override run, pipe stdout/stderr through tee so TRACE_C entries and summary remain in with_override.log.
- After the first run, immediately extract pix0_vector, Fbeam, and Sbeam lines using `rg` and jot results in c_precedence.md with clear formatting.
- Repeat command without the -pix0_vector_mm flag to produce without_override.log; capture the command variant explicitly in the memo.
- Diff the two logs via `diff -u with_override.log without_override.log > reports/.../c_traces/diff.log` to highlight any differences automatically.
- If TRACE_C ordering differs from prior harnesses, note the deviation; do not reformat logs this loop.
- In c_precedence.md, include a short derivation showing pix0_override_m converted to meters and projected onto fdet/sdet vectors, referencing detector equations.
- Summarize findings with a table (override state vs pix0/Fbeam/Sbeam) so Phase H5b implementation has instant reference.
- Keep raw logs intact for nb-compare or future trace scripts; store derived tables separately within the markdown memo.
- Update reports/2025-10-cli-flags/phase_h5/c_precedence.md with timestamp, commands, binary hash (from `$NB_C_BIN --version` if available), and environment notes.
- If instrumentation rebuild was required, capture `git diff` of golden_suite_generator/nanoBragg.c and stash patch under reports/.../attempts/ before reverting.
Pitfalls To Avoid:
- Do not edit Detector._calculate_pix0_vector yet; Evidence phase only.
- Avoid running pytest or nb-compare; Phase=Evidence prohibits test execution.
- Do not delete or overwrite prior Phase H traces; keep new logs alongside older ones for comparison.
- Ensure the command uses -nointerpolate and -nonoise exactly as specified; deviations invalidate parity analysis.
- Verify NB_C_BIN points to the instrumented binary; using the frozen root binary skips TRACE_C output.
- Keep environment variable KMP_DUPLICATE_LIB_OK=TRUE set when invoking any Python helpers (trace harness, analysis scripts).
- Watch for line-ending differences when diffing logs; use `diff -u` rather than GUI tools to keep outputs text-friendly.
- Don’t rerun PyTorch CLI yet; that belongs to H5c/H5d after implementation work.
- Avoid editing docs/fix_plan.md mid-loop unless H5a data is ready; partial updates confuse traceability.
- Refrain from compressing logs; raw text is required for later tooling comparisons.
- Stay off GPU runners for this C evidence; CPU parity suffices for H5a.
- Record any anomalies (e.g., TRACE_C missing F_latt) in the attempts log even if run succeeds.
Pointers:
- plans/active/cli-noise-pix0/plan.md:111
- plans/active/cli-noise-pix0/plan.md:140
- docs/fix_plan.md:448
- docs/architecture/detector.md:51
- specs/spec-a-cli.md:57
- docs/development/c_to_pytorch_config_map.md:35
- reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/summary.md
- reports/2025-10-cli-flags/phase_j/scaling_chain.md:30
- reports/2025-10-cli-flags/phase_e/trace_comparison.md
- docs/development/testing_strategy.md:45
Next Up: H5b — once C evidence proves override application, update Detector._calculate_pix0_vector to reuse projection logic on the custom-vector path and capture PyTorch traces (Phase H5c).
