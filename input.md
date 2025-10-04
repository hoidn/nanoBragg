Header: 2025-10-04 01:16:02Z | Commit d8dbf96 | Author galph | Active Focus: [CLI-FLAGS-003] Phase A parity capture for -nonoise & pix0 overrides
Context: Phase A must bank C-side evidence (noise skip + pix0 vectors) before code changes; plan refreshed with explicit override wiring gaps.
Reminder: Keep reports under reports/2025-10-cli-flags/ with dated subfolders; trace logs belong in phase_a/ until promoted.
Environment Baseline: Work from repo root /Users/ollie/Documents/nanoBragg3 with approvals=never and sandbox=danger-full-access; respect automation guard scopes.
Coordination: Update docs/fix_plan.md Attempts immediately after each major action to keep supervisor visibility high.
 Communication: Ping supervisor via docs/fix_plan.md note if any anomaly deviates from spec expectations before proceeding.

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_entrypoint.py -q after capturing C traces and memo.
Execution Notes: Complete plan tasks A1–A3 sequentially, then update docs/fix_plan.md Attempts before touching implementation.
Trace Policy: Record every command (stdout/stderr) alongside environment variables in README.md for reproducibility.
 Artifact Checklist: Ensure c_with_nonoise.log, c_with_noise.log, and pix0_trace/trace.log exist before closing Phase A.
 Validation Reminder: Confirm img.bin is generated in both runs and note presence/absence of noise images in logs.

If Blocked: If NB_C_BIN command fails, capture stderr to reports/2025-10-cli-flags/attempt_fail/c_run.log and note exit code.
If Blocked: Should instrumentation patch introduce compilation errors, revert the patch, document the diff, and proceed with uninstrumented logs, marking plan task as deferred.
If Blocked: If pytest CLI smoke fails baseline, capture pytest output, open docs/fix_plan.md entry with failure signature, and pause further actions pending supervisor review.
If Blocked: When external dependencies (scaled.hkl, A.mat) are missing, document missing asset under reports/2025-10-cli-flags/attempt_fail/assets.md and notify in docs/fix_plan.md.
 If Blocked: For permission issues writing to reports/, verify directory exists and log the mkdir command plus permissions fix in README.md before re-running.
 If Blocked: For timeouts, rerun command with `time` prefix to capture duration and note whether failure is reproducible.

Priorities & Rationale:
- Priority 1: specs/spec-a-core.md:520 forbids writing noise when -nonoise is supplied; C evidence is prerequisite to mirror semantics in PyTorch.
  Rationale: Without a parity log, any PyTorch toggle risks misinterpreting spec (e.g., silent noisefile writes) and failing acceptance tests.
- Priority 2: specs/spec-a-cli.md:60 documents -pix0_vector units (meters) and CUSTOM switch; verifying C trace ensures mm alias converts correctly.
  Rationale: A measured pix0 vector anchors future DetectorConfig override logic and prevents regressing CUSTOM behaviour.
- Priority 3: docs/architecture/detector.md:188 explains pix0 caching; confirm override impact before bypassing `_calculate_pix0_vector()`.
  Rationale: Detector cache invalidation must stay correlated with overrides to avoid stale coordinates during parallel tests.
- Priority 4: src/nanobrag_torch/__main__.py:542 currently stores `custom_pix0_vector` but Detector ignores it; documenting this gap drives plan Phase B updates.
  Rationale: Highlighting unused config prevents duplicate work and clarifies why mm alias must map to a new override field.
- Priority 5: plans/active/cli-noise-pix0/plan.md tasks A1–A3 gate all implementation; finishing artifacts unlocks B-phase coding safely.
  Rationale: The plan is the coordination spine—keeping it updated ensures Ralph’s loop stays aligned with long-term goal.

How-To Map:
Step 1: Export NB_C_BIN=./nanoBragg in the shell to stay consistent with comparison SOP before every command.
Reason: All parity tooling respects NB_C_BIN precedence; exporting once avoids path confusion mid-loop.
Step 2: Execute the full supervisor configuration with -nonoise and capture stdout/stderr.
Reason: This isolates the effect of -nonoise while keeping every other parameter identical for diffing.
Command:
NB_C_BIN=./nanoBragg \
  nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 \
  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 \
  -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -nonoise \
  > reports/2025-10-cli-flags/phase_a/c_with_nonoise.log 2>&1
Step 3: Repeat command without -nonoise and capture output to reports/2025-10-cli-flags/phase_a/c_with_noise.log for direct comparison.
Reason: This reference run confirms that noisefile generation remains active when flag is absent, providing a diff baseline.
Step 4: Insert temporary TRACE_C instrumentation in golden_suite_generator/nanoBragg.c around pix0 calculation (matching spec units) and rebuild via make -C golden_suite_generator.
Reason: Direct C trace ensures we know the exact vector and units before wiring PyTorch overrides.
Step 5: Rerun the command (choose -nonoise variant for clarity) and redirect trace lines to reports/2025-10-cli-flags/phase_a/pix0_trace/trace.log.
Reason: Capturing trace under the same configuration avoids drift due to stochastic noise.
Step 6: Remove or guard instrumentation once logs are captured to avoid contaminating future runs, documenting the diff in README.md.
Reason: Clean binaries keep subsequent parity runs noise-free and prevent stray TRACE_C lines from polluting logs.
Step 7: Summarise findings in reports/2025-10-cli-flags/phase_a/README.md including measured pix0 vector (meters), whether noisefile was skipped, and any warnings emitted.
Reason: README summary becomes the canonical artifact for Phase A exit criteria and future reference.
Step 8: Run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_entrypoint.py -q to validate baseline CLI parsing remains green post-data collection.
Reason: Smoke test guards against unintended CLI regressions introduced during instrumentation or cleanup.
Step 9: Append Attempt entry under docs/fix_plan.md `[CLI-FLAGS-003]` capturing command lines, artifacts, and conclusions for A1–A3.
Reason: Fix plan ledger must record evidence to prevent duplication and to brief future loops.
Step 10: Stage artifacts under git for visibility but coordinate with supervisor before committing (per automation guard policy).
Reason: Supervisor must review before pushing to ensure guard plans remain satisfied; follow automation SOP.

Pitfalls To Avoid:
- Pitfall: Forgetting NB_C_BIN environment; this breaks parity logs—always export before running nanoBragg.
- Pitfall: Writing logs outside reports/ hierarchy; violates documentation SOP and complicates traceability.
- Pitfall: Failing to revert instrumentation; leaves C binary noisier and risks confusing later comparisons.
- Pitfall: Mixing units when transcribing pix0 vectors; keep metres vs millimetres explicit in README.md.
- Pitfall: Ignoring CUSTOM convention triggers; providing pix0 overrides auto-selects CUSTOM per CLI spec.
- Pitfall: Attempting PyTorch implementation before Phase A evidence; respect plan gating to avoid rework.
- Pitfall: Omitting KMP_DUPLICATE_LIB_OK for pytest; could trigger MKL duplicate errors mid-run.
- Pitfall: Forgetting to record RNG seeds when running noise-enabled scenario; include seed in log headers for reproducibility.
- Pitfall: Altering docs/index.md listing; Protected Assets rule forbids unsanctioned edits.
- Pitfall: Leaving instrumentation prints active inside golden_suite_generator when committing; ensure the repo returns to parity-friendly state.
- Pitfall: Editing pix0 vectors without normalising; always confirm vector length matches C trace before storing in config.
- Pitfall: Skipping ROI mask checks in logs; document ROI assumptions so later tests know which pixels were evaluated.

Pointers:
- specs/spec-a-core.md:520 — authoritative -nonoise behaviour (skip noise image even when -noisefile present).
- specs/spec-a-cli.md:60 — -pix0_vector input units and CUSTOM convention side effects.
- docs/development/c_to_pytorch_config_map.md:35 — pivot/convention precedence mapping relevant to pix0 handling.
- docs/architecture/detector.md:188 — pix0 caching expectations and override implications.
- plans/active/cli-noise-pix0/plan.md — refreshed tasks (note B3/B4/B5 require the evidence you collect now).
- docs/fix_plan.md:630 — `[CLI-FLAGS-003]` status, attempts, and exit criteria summary.
- src/nanobrag_torch/__main__.py:542 — current CLI storage of `custom_pix0_vector` (unused path to fix later).
- src/nanobrag_torch/__main__.py:1152 — noise writer lacking -nonoise guard; evidence feeds future change.
- golden_suite_generator/nanoBragg.c:730 — location of pix0 computation for instrumentation (verify after pulling).
- reports/2025-10-cli-flags/phase_a/README.md — create/update summary per task A3 requirement.
- docs/debugging/debugging.md:25 — parallel trace SOP reminder when comparing C vs PyTorch outputs.
- docs/development/testing_strategy.md:78 — Tier 1 trace-driven validation expectations backing this evidence-gathering loop.
- docs/architecture/c_parameter_dictionary.md:118 — reference entry for -nonoise and pix0 flags to cross-check naming.
- prompts/supervisor.md:7 — authoritative parallel command we must reproduce.

Next Up:
- After Phase A artifacts are archived, proceed to plan Phase B1/B2 (argparse additions + noise suppression flag wiring) and prepare corresponding unit tests.
- Queue Phase B3-B5 work once override wiring design is agreed; ensure Device/DType parity remains central.
- Begin drafting documentation updates (specs/spec-a-cli.md & docs/architecture/detector.md) concurrently so Phase C runs smoothly once implementation lands.
- Anticipate adding regression coverage in tests/test_cli_flags.py to assert both meter and millimetre inputs map to identical DetectorConfig tensors.
- Plan for adding NoiseConfig.generate_noise_image flag once implementation begins; capture acceptance tests to back behaviour change.
- Schedule follow-up to rerun NB-compare parity command after implementation to confirm pix0 override and noise suppression behave end-to-end.
- Consider prepping a short write-up for reports/2025-10-cli-flags/phase_d/ outlining residual risks (e.g., interactions with -noisefile) ahead of Phase D.
