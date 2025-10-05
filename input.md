Header: 2025-10-05 22:44:27Z | Commit 7acf149 | Author galph | Active Focus: [CLI-FLAGS-003] Phase B3 detector override fix + parity smoke prep
Context 1: Phase A evidence for -nonoise/-pix0_vector_mm lives in reports/2025-10-cli-flags/phase_a/; preserve it while adding new artifacts.
Context 2: Current first divergence (docs/fix_plan.md:664) is the detector override returning without assigning self.pix0_vector, blocking CLI execution for the supervisor command.
Context 3: Plan checkpoint (plans/active/cli-noise-pix0/plan.md Phase B) shows B1/B2 completed but B3[P]; you are landing the override implementation and cache hygiene now.
Context 4: Long-term goal is the full C↔PyTorch parity command at prompts/supervisor.md; this loop unblocks that by making the CLI accept pix0 overrides while honoring -nonoise.
Context 5: Environment guardrails remain approvals=never, sandbox=danger-full-access, shell=zsh; always prefix Python with KMP_DUPLICATE_LIB_OK=TRUE and add PYTHONPATH=src when invoking repo code.
Context 6: Detector caching still assumes pix0_vector exists; any override must populate self.pix0_vector and _cached_pix0_vector before get_pixel_coords() runs.
Context 7: CUSTOM convention must still trigger when either pix0 flag is used (see src/nanobrag_torch/__main__.py:448); do not regress axis swaps for MOSFLM defaults.
Context 8: Protected Assets (docs/index.md) include loop.sh, supervisor.sh, input.md; limit edits to sanctioned files only and document any rationale when touching protected files.
Context 9: Record every attempt in docs/fix_plan.md under [CLI-FLAGS-003] with timestamps, commands, and artifact paths; missing entries stall plan closure and future audits.
Context 10: Archive new outputs under reports/2025-10-cli-flags/phase_b/ with subfolders (argparse/, detector/, pytest/, smoke/, attempt_fail/) to mirror Phase A layout for continuity.
Context 11: Keep the supervisor harness prompts/main.md loop alignment by referencing input.md changes inside docs/fix_plan.md attempts; note which tasks transition from [P] to [D].
Context 12: The CLI still sets config['convention']='CUSTOM' when pix0 overrides arrive; ensure any refactor respects this branch so MOSFLM offsets do not bleed into custom setups.
Context 13: Detector invalidate_cache() currently re-runs _calculate_pix0_vector(); the override logic must survive repeated cache busts without leaking stale tensors.
Context 14: Noise pipeline already respects suppress_noise; confirm the guard still passes AT-NOISE acceptance thresholds after your edits (Phase D later, but avoid regressions now).
Context 15: Future Phase C tests will rely on reproducible outputs; capture deterministic seeds and CLI echoes while you implement the override fix.
Context 16: Pipette any temporary diagnostics into scripts/ (if needed) and delete before commit; random notebooks or scratch files outside reports/ are forbidden.
Context 17: Coordination with future loops depends on reports being well-organized—include README.md inside new report folders summarizing commands and outcomes.
Context 18: Use ASCII only; repo policy forbids smart quotes/em dashes in instructions or documentation updates.
Context 19: The supervisor command includes both -pix0_vector_mm and -nonoise; verify your dry run uses exactly those parameters to ensure parity.
Context 20: Watch for device/dtype neutrality—tests may upgrade to CUDA soon, so avoid CPU-only assumptions when creating override tensors.

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — complete plan Phase B task B3 (detector override wiring) and verify via KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src pytest tests/test_cli_entrypoint.py -q
Milestone 1: `_calculate_pix0_vector()` assigns the override tensor, updates cached copies, and passes the Detector smoke snippet without AttributeError; evidence stored at reports/phase_b/detector/post_fix_smoke.txt.
Milestone 2: CLI config echo shows `suppress_noise=True` when -nonoise is present, and pix0 overrides propagate as meters (print_configuration output stored under reports/phase_b/detector/config_echo.txt).
Milestone 3: Post-fix pytest run is clean and logged (reports/2025-10-cli-flags/phase_b/pytest/cli_entrypoint.log) with summary appended to docs/fix_plan.md attempt; include command + exit code.
Milestone 4: Dry-run of the supervisor command validates argument parsing and override wiring, even if the full simulation is not executed yet; capture CLI echo in reports/phase_b/smoke/dry_run.txt.

If Blocked: Capture failing reproduction (command, stderr, exit code) to reports/2025-10-cli-flags/phase_b/attempt_fail/pix0_override_failure.txt and log the outcome in docs/fix_plan.md before retrying.
Fallback 1: If override still crashes, run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/test_pix0_minimal.py --override-mm` to isolate the stack; archive stdout/stderr in attempt_fail/minimal_override.log.
Fallback 2: If pytest flakes due to cached bytecode, clean with `find src -name '__pycache__' -exec rm -rf {} +` then rerun and note the cleanup in Attempt log; avoid deleting compiled golden data.
Fallback 3: Should noise suppression regress, diff the float/noise outputs against Phase A logs via nb-compare and stash comparisons under reports/phase_b/smoke/ before adjusting code.
Fallback 4: When encountering spec ambiguity, pause coding, annotate the discrepancy in docs/fix_plan.md, and request supervisor guidance next loop; do not guess on unit conventions.
Fallback 5: If the override works on CPU but fails on CUDA smoke, capture both logs (cpu_smoke.txt, cuda_smoke.txt) and flag the inconsistency in fix_plan before iterating further.
Fallback 6: For git conflicts, stop coding, run `git status` + `git diff`, snapshot the state in reports/phase_b/attempt_fail/git_status.txt, then resolve before resuming.

Priorities & Rationale:
- src/nanobrag_torch/models/detector.py:392 retains a bare `return` on override; assign self.pix0_vector and cached copies to unblock parity and eliminate the AttributeError shown in today’s reproduction.
- docs/fix_plan.md:664 documents the new failure point; updating this entry with the fix and fresh metrics is required before moving to Phase C validation and ensures auditability.
- docs/architecture/detector.md:178-214 describe pix0 caching expectations; overrides must respect cache invalidation so get_pixel_coords() remains deterministic across devices.
- specs/spec-a-cli.md:157-170 mandates that -pix0_vector_mm normalize to meters while mirroring CUSTOM behavior; verify parse_and_validate_args keeps convention=Custom and unit conversions precise.
- plans/active/cli-noise-pix0/plan.md#L24 still shows B4/B5 unchecked; while landing B3 ensure the design leaves room for shared override plumbing (unit parity + cache hygiene) so future loops are straightforward.
- reports/2025-10-cli-flags/phase_a/README.md captures the C reference pix0 vector; match that structure when documenting Phase B findings for consistent traceability.

How-To Map:
Step 1: Reproduce current failure for the log — run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY'` snippet instantiating DetectorConfig(pix0_override_m=(0.1,0.2,0.3)); store traceback at reports/2025-10-cli-flags/phase_b/detector/pre_fix_trace.txt for baseline.
Step 1a: Annotate the failing stack trace in docs/fix_plan.md Attempt entry, noting the AttributeError line number and command used; this locks the regression for later comparison.
Step 2: Modify `_calculate_pix0_vector()` so the override branch sets `self.pix0_vector`, clones to `_cached_pix0_vector`, and coerces tensors onto detector device/dtype without detaching; integrate into invalidate_cache() path as well.
Step 2a: Ensure the override branch updates `self.distance_corrected` if needed and leaves r_factor consistent; if no change is required, explicitly comment in fix_plan attempt.
Step 3: Confirm invalidate_cache() respects overrides by mutating config.pix0_override_m inside a small harness (e.g., scripts/test_pix0_minimal.py) and capturing before/after geometry versions in reports/phase_b/detector/cache_hygiene.txt.
Step 3a: Check that `_geometry_version` increments and `_cached_pix0_vector` matches the new override; log both values for CPU (and GPU if available) in the same file.
Step 4: Run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY'` snippet again to verify the override now prints the expected tensor; append success note and tensor values to reports/phase_b/detector/post_fix_smoke.txt.
Step 4a: Include both tuple and tensor override inputs in the smoke script to confirm type flexibility; note any differences in dtype casting.
Step 5: Execute `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src pytest tests/test_cli_entrypoint.py -k pix0 -q | tee reports/2025-10-cli-flags/phase_b/pytest/cli_entrypoint.log`; ensure exit code 0 and summarise results (pass counts, duration) in docs/fix_plan.md attempt.
Step 5a: If tests were added/modified, run full module `pytest tests/test_cli_entrypoint.py -v` to ensure no stray regressions; record run time and outcomes in the same log.
Step 6: Run `nanoBragg --help | sed -n '160,220p' > reports/2025-10-cli-flags/phase_b/argparse/help_snapshot.txt` to confirm -nonoise/-pix0_vector_mm text persists after edits; compare against spec wording.
Step 6a: Highlight any discrepancies between help text and specs/spec-a-cli.md in fix_plan attempt and adjust parser descriptions if needed.
Step 7: Dry-run the supervisor command via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch <args>` with `-nonoise` and pix0 override, stopping after argument parsing using a temporary debug flag; log output under reports/phase_b/smoke/dry_run.txt and remove temporary code afterward.
Step 7a: Capture the resulting pix0 override tensor from print_configuration and confirm it matches the meter-normalized values documented in Phase A.
Step 8: Update docs/fix_plan.md Attempt for [CLI-FLAGS-003] with reproduction commands, artifact paths, observations (precision, device/dtype notes, cache version increments), and a checklist of plan tasks touched.
Step 9: Review git diff to ensure only intended files changed (docs/fix_plan.md, plan.md, input.md, relevant source/tests); stage and commit after confirming pytest status.
Step 10: Push updates and monitor for conflicts; if push fails, run `timeout 30 git pull --rebase`, resolve, and document in galph_memory.md per supervisor SOP.

Pitfalls To Avoid:
- Avoid `.detach()`, `.cpu()`, or tensor cloning without dtype/device alignment in override handling; keep gradients intact for future optimization work.
- Do not bypass CUSTOM convention triggers; keep args.pix0_vector/_mm forcing config['convention']='CUSTOM' so MOSFLM offsets stay isolated.
- Resist adding new CLI flags outside plan scope; changes must narrow to -nonoise and pix0 override plumbing to maintain focus.
- Keep vectorized operations intact; no per-pixel Python loops when verifying geometry outputs or writing tests.
- Preserve existing noise behavior when suppress_noise is False; regression will break AT-NOISE suites and Phase D follow-ups.
- Respect docs/index.md Protected Assets; no edits to loop.sh, supervisor.sh (beyond their plan tasks), or removal of listed files.
- When editing docs/fix_plan.md, maintain ASCII formatting and accurate line references to avoid merge pain during future pulls.
- Ensure git workspace stays clean apart from intentional edits; capture reasoning in docs/fix_plan.md if intermediate artifacts remain for next loop.
- Maintain compatibility with future GPU runs; use `.to(device=self.device, dtype=self.dtype)` consistently when creating override tensors or cached copies.
- Keep command transcripts in reports/ with timestamps so future audits can trace progress and recreate the workflow.
- Do not forget to set KMP_DUPLICATE_LIB_OK=TRUE before any torch import; missing the env var causes OpenMP aborts mid-loop.
- Avoid editing tests without updating expected artifacts; mismatched baselines slow future parity checks.

Pointers:
- plans/active/cli-noise-pix0/plan.md#L24 — current Phase B table with status markers updated this loop.
- docs/fix_plan.md:664 — active fix-plan entry capturing first divergence and attempts for [CLI-FLAGS-003].
- src/nanobrag_torch/models/detector.py:392 — override branch requiring assignment and cache updates.
- src/nanobrag_torch/__main__.py:187 — parser block defining pix0 flags and CUSTOM triggers.
- docs/architecture/detector.md:178 — pix0 vector, cache, and convention expectations.
- specs/spec-a-cli.md:157 — authoritative flag descriptions for -nonoise and -pix0_vector aliases.
- reports/2025-10-cli-flags/phase_a/README.md — Phase A findings to mirror when documenting Phase B results.
- prompts/supervisor.md — canonical parity command to dry-run after implementation.

Next Up: After B3 passes, tee up Phase C1 regression test additions (CLI flag cases) and gather parity smoke metrics for the supervisor command; coordinate which path to pursue in the next loop and log the decision in docs/fix_plan.md.
Next Up Alt: If time permits, begin scoping B4/B5 (unit parity + cache hygiene) tasks by drafting acceptance checks, but document any preparatory work without committing code until B3 is merged.
Notes 1: Keep NB_C_BIN unset unless explicitly running the C binary; the PyTorch CLI relies on internal defaults for this loop.
Notes 2: Update galph_memory.md only if new supervisor decisions occur; otherwise state that no substantial update was required.
Notes 3: When creating temporary instrumentation, gate it under DEBUG flags and strip before commit.
Notes 4: Record wall-clock timings for key commands (smoke script, pytest) to help future profiling comparisons.
Notes 5: For reproducibility, log random seeds and detector device/dtype in each report file.
Notes 6: Validate override behavior on both tuple inputs and torch.tensor inputs to confirm API flexibility.
Notes 7: Track geometry_version increments to ensure cache invalidation functions after overrides are toggled.
Notes 8: Include summary tables in reports README files listing command, exit status, and artifact path.
Notes 9: Maintain consistent naming for log files (snake_case, descriptive) to avoid confusion in archives.
Notes 10: If additional tests are authored, follow docs/development/testing_strategy.md guidelines for Tier 1/2 coverage.
Notes 11: Keep commit message format `SUPERVISOR: ...` with explicit test status to satisfy supervisor SOP.
Notes 12: Push immediately after commit to avoid drift; if push blocked, rerun pull workflow before ending loop.
