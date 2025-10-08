Summary: Sync the parity-shim docs and checklists with the dual-threshold tolerance decision before we resume nb-compare parity work.
Mode: Docs
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — Phase L3k.3c.4/5 doc sync
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts:
- reports/2025-10-cli-flags/phase_l/rot_vector/20251201_dual_threshold/
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md (updated section + references)
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md (VG-1 rows updated)
Do Now: CLI-FLAGS-003 L3k.3c.4/5 — KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py (run after documenting the tolerance updates and capture stdout in the new report folder)
If Blocked: If diagnosis.md or fix_checklist.md edits collide with previous supervisor instructions, capture the conflicting text in reports/2025-10-cli-flags/phase_l/rot_vector/20251201_dual_threshold/blocked.md, reference it in docs/fix_plan.md, and halt further doc edits until clarified.
Context Reminders:
- The c-parity shim stays opt-in; spec defaults remain fresh φ rotations (specs/spec-a-core.md:211).
- Dtype probe artifacts live in reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/ — cite them verbatim.
- We cannot change Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md).
Priorities & Rationale:
- plans/active/cli-phi-parity-shim/plan.md:11 — Status flag shows documentation/test updates are the last blockers post dtype probe.
- plans/active/cli-phi-parity-shim/plan.md:47 — C4 now green but hand-off to documentation (C5) is gated on this loop.
- plans/active/cli-phi-parity-shim/plan.md:57 — C4d remains [P]; syncing plan/checklist here lets us flip it to done.
- docs/fix_plan.md:450 — Next Actions explicitly call for syncing plans/checklists, updating diagnosis, and logging a new attempt before moving to nb-compare.
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:116 — Needs a dual-threshold section referencing the dtype probe so VG-1 expectations are explicit.
- docs/bugs/verified_c_bugs.md:166 — Must mention the relaxed |Δk| ≤ 5e-5 gate for c-parity and keep the spec-compliant baseline intact.
- specs/spec-a-core.md:211 — Reminds us that spec still enforces fresh rotations; documentation must highlight the separation between spec mode and parity mode.
How-To Map:
- Step 0 — Workspace prep
  • mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector/20251201_dual_threshold
  • touch reports/2025-10-cli-flags/phase_l/rot_vector/20251201_dual_threshold/commands.txt
  • echo "export KMP_DUPLICATE_LIB_OK=TRUE" >> .../commands.txt to log the required env var
  • Record todays timestamp in commands.txt for traceability (e.g. date -u >> commands.txt)
- Step 1 — Diagnosis update
  • Open reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md in an editor
  • Add a subsection (e.g., "## 2025-12-01: Dual-Threshold Decision") summarising the dtype probe results
  • Cite analysis_summary.md and delta_metrics.json from reports/.../20251201_dtype_probe/
  • State explicitly: spec |Δk| ≤ 1e-6, c-parity |Δk| ≤ 5e-5; note that VG-1 passes under the relaxed threshold
  • Mention any outstanding follow-ups (nb-compare, supervisor command) so readers know what remains
- Step 2 — Checklist alignment
  • Edit reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md
  • Update VG-1 rows to reference the 20251201_dtype_probe artifacts and note the relaxed tolerance
  • Flip VG-1.4 Status from ⚠️ to ✅/GREEN if the relaxed gate is satisfied
  • Preserve historical commentary about earlier measurements; append the new tolerance note rather than replacing history
- Step 3 — Plan refresh
  • Adjust plans/active/cli-noise-pix0/plan.md within Phase L3k so C4d references the checklist/doc refresh and can be set to [D]
  • Ensure C5 guidance now talks about documentation + attempt logging instead of diagnostics
  • Mention the directory reports/.../20251201_dual_threshold/ so future loops know where evidence lives
- Step 4 — Bug log update
  • In docs/bugs/verified_c_bugs.md under C-PARITY-001, add a short paragraph describing the opt-in shim, dual thresholds, and artifact locations
  • Clarify that spec path stays strict (≤1e-6) while parity path accepts ≤5e-5 to match the C bug
- Step 5 — Command + checksum hygiene
  • Append every command you run (edits, pytest, sha256) to commands.txt in execution order
  • After all artifacts are saved, run: (cd reports/2025-10-cli-flags/phase_l/rot_vector/20251201_dual_threshold && sha256sum * > sha256.txt)
  • If new files are added later, re-run sha256sum so hashes stay current
- Step 6 — Collect-only confirmation
  • Execute KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
  • Pipe stdout to reports/2025-10-cli-flags/phase_l/rot_vector/20251201_dual_threshold/collect_only.log
  • Note the command in commands.txt and verify the log mentions both spec and c-parity tests being discovered
- Step 7 — Attempt log entry
  • In docs/fix_plan.md under CLI-FLAGS-003 add an Attempt describing the documentation updates, collect-only evidence, and new artifact paths
  • State that Phase L3k.3c.4 plan/checklist sync is done and Phase C5 documentation is now active
Deliverables Checklist:
- [ ] reports/.../20251201_dual_threshold/commands.txt with ordered commands
- [ ] reports/.../20251201_dual_threshold/collect_only.log from pytest --collect-only
- [ ] reports/.../20251201_dual_threshold/sha256.txt covering every new artifact
- [ ] Updated diagnosis.md section summarising the tolerance decision
- [ ] Updated fix_checklist.md VG-1 rows referencing relaxed thresholds
- [ ] plans/active/cli-noise-pix0/plan.md showing C4d [D] and C5 ready
- [ ] docs/bugs/verified_c_bugs.md paragraph calling out the relaxed gate for parity mode
- [ ] docs/fix_plan.md attempt entry with metrics + artifact references
Pitfalls To Avoid:
- Do not edit specs or architecture docs; we are documenting parity-mode behavior only.
- Avoid production code changes—this loop is strictly documentation and planning.
- Keep historical notes in diagnosis.md and fix_checklist.md; append new info rather than overwriting.
- Respect Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md) and avoid renames/deletions.
- Stick to the mapped collect-only pytest; leave nb-compare and full suites for Phase L3k.3d.
- Ensure commands.txt reflects exact commands in chronological order; no retroactive summaries.
- Keep all files ASCII (no smart quotes or non-ASCII characters) when editing manuals.
- Re-run sha256 whenever you add or modify files in the report folder to keep hashes accurate.
- Mention the relaxed tolerance only in parity context—spec path must remain ≤1e-6 everywhere else.
- Double-check git diff before finishing to ensure no unintended edits slipped in.
Pointers:
- plans/active/cli-phi-parity-shim/plan.md:47
- plans/active/cli-phi-parity-shim/plan.md:57
- docs/fix_plan.md:450
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:116
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:10
- docs/bugs/verified_c_bugs.md:166
- specs/spec-a-core.md:211
Next Up: Phase L3k.3d — rerun nb-compare ROI parity with c-parity after the documentation, checklist, and fix_plan updates are in place.
Verification Notes:
- After editing diagnosis.md, run git diff reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md to confirm only the new subsection changed.
- Review fix_checklist.md diff to ensure historical rows remain intact and only VG-1 notes were appended.
- Check that plans/active/cli-noise-pix0/plan.md shows C4d toggled to [D] and references the 20251201_dual_threshold folder.
- Confirm docs/bugs/verified_c_bugs.md still cites the reproduction command and now references the shim flag + tolerance.
- Make sure docs/fix_plan.md Attempt log includes timestamps, command summaries, and artifact paths for the new evidence.
- Re-run wc -l commands.txt to ensure every command is captured (no silent actions).
- Verify sha256.txt lists hashes for commands.txt, collect_only.log, and any added markdown notes.
- Before finishing, run git status to confirm only documentation files and input.md changed this loop.
Closing Reminders:
- Commit message should mention CLI-FLAGS-003 doc sync and note tests: collect-only.
- Leave tree clean; if any doc edits remain unstaged, record why in docs/fix_plan.md before ending the loop.
- Push after commit so the supervisor log stays current for the next run.
- Ping galph if any unexpected parity regressions appear while updating docs.
