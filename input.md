Summary: Sync CLI-FLAGS-003 ledgers with the Phase D removal evidence so the phi-carryover shim work can close cleanly before scaling resumes.
Context: Phase D1 evidence landed in Attempt #183, but the ledger and plan archive still indicate open work; we need to reconcile documents.
Scope: Documentation-only; update docs/fix_plan.md, archive the retired shim plan, refresh references, and append a ledger note to the existing Phase D bundle.
Expectation: Produce a clean paper trail confirming D2 closure and prepare the ground for a Phase D3 supervisor handoff.
Mode: Docs
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: docs/fix_plan.md; plans/archive/cli-phi-parity-shim/plan.md (new location, add closure preface); reports/2025-10-cli-flags/phase_phi_removal/phase_d/ledger_sync.md (or equivalent summary addendum)
Do Now: CLI-FLAGS-003 Phase D2 ledger sync — pytest --collect-only -q tests/test_cli_scaling_phi0.py
If Blocked: Log the blocker in docs/fix_plan.md Attempts (mark as blocked), drop ATTEMPT_BLOCKED.md under reports/2025-10-cli-flags/phase_phi_removal/phase_d/, and capture a short rationale before ending the loop.

Priorities & Rationale:
- plans/active/phi-carryover-removal/plan.md:58 shows D0/D1 marked done with D2/D3 pending; aligning the ledger is the prerequisite for archival.
- docs/fix_plan.md:451 is the canonical CLI-FLAGS-003 ledger entry; it must cite the 20251008T203504Z evidence bundle and mark D2 as complete.
- plans/active/cli-phi-parity-shim/plan.md remains in active status despite the shim removal; archiving avoids misleading future loops.
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/summary.md documents the proof bundle; referencing it in the ledger prevents evidence drift.
- galph_memory.md needs an explicit note once D2 closes so future supervisors understand the state progression.

How-To Map:
Step 1: Re-read plans/active/phi-carryover-removal/plan.md (focus on Context + Phase D table) to align wording and capture the artifact path accurately.
Step 2: Edit docs/fix_plan.md in the CLI-FLAGS-003 section; add a new Attempts bullet (Attempt #184) noting “Phase D2 ledger sync complete on YYYY-MM-DD” with the bundle path and mention of the archived plan.
Step 3: In the same section rewrite the Next Actions block so only Phase D3 supervisor handoff plus Phase L scaling tasks remain; drop references to D2 entirely.
Step 4: Use git mv to move plans/active/cli-phi-parity-shim/plan.md to plans/archive/cli-phi-parity-shim/plan.md; at the top of the moved file add a closure paragraph summarising D1 and pointing to the Phase D bundle.
Step 5: Update plans/active/phi-carryover-removal/plan.md dependencies so any references to the legacy active plan now point to plans/archive/cli-phi-parity-shim/plan.md.
Step 6: Search (`rg "cli-phi-parity-shim" -n`) to ensure no stale references remain under plans/active/, docs/fix_plan.md, or prompts/supervisor.md; fix any that still point to the old path.
Step 7: Append a short ledger_sync.md (or paragraph in summary.md) inside reports/2025-10-cli-flags/phase_phi_removal/phase_d/ noting the ledger update, date, and documents touched.
Step 8: Run pytest --collect-only -q tests/test_cli_scaling_phi0.py (set KMP_DUPLICATE_LIB_OK=TRUE if needed); save the output to collect_YYYYMMDD.log within the same Phase D directory.
Step 9: Record today's command list in commands.txt (append) inside the Phase D directory to keep reproduction history current.
Step 10: Update galph_memory.md with a concise entry summarising D2 completion, referencing the updated fix_plan section and the archived plan path.
Step 11: Before finalizing, review git status; ensure only the intended documentation/report files changed.
Step 12: Stage with git add -A, commit using message “SUPERVISOR: CLI-FLAGS-003 Phase D2 ledger sync - tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py”, then push.

Pitfalls To Avoid:
- Do not modify production code under src/; this loop is restricted to documentation and reports.
- Preserve Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md) exactly as listed.
- When moving the plan file, keep history via git mv; avoid copy+delete which breaks blame.
- Maintain Markdown table integrity in docs/fix_plan.md; mismatched pipes will break rendering.
- Keep existing evidence files intact; append new notes rather than replacing previous logs.
- Ensure pytest collect-only runs from repo root so relative imports resolve; record the command and environment in the Phase D directory.
- Verify that no `.cpu()` or `.cuda()` snippets are introduced while editing docs; device/dtype neutrality remains mandatory even in examples.
- After archiving the plan, double-check that plans/index scripts or fix_plan references no longer assume its active location.
- Remember to update galph_memory.md at the end; failure to log supervisor actions breaks loop continuity.
- Do not forget to push; alignment work must land on feature/spec-based-2 for Ralph to pick up.

Execution Notes:
Line 1: Start by opening the relevant plan and ledger files side-by-side (e.g., use `code` or your editor) to minimise context switching.
Line 2: When editing docs/fix_plan.md, keep Attempt numbering consistent with prior entries; use the next sequential number.
Line 3: In the new Attempts bullet, reference both the Phase D bundle path and the archived plan destination to create a bi-directional breadcrumb.
Line 4: In Next Actions, explicitly mention “Phase D3 supervisor handoff memo” so the following loop has clear guidance.
Line 5: The archived plan should include a header, date stamp, and a pointer to plans/active/phi-carryover-removal/plan.md for historical navigation.
Line 6: After running pytest collect-only, note whether the collection count (2 tests) matches prior logs; mention any discrepancy in reports/ ledger note.
Line 7: Update commands.txt with the exact commands executed this loop (git mv, pytest collect-only, git status, etc.).
Line 8: Run `rg "phi_carryover"` after updates to confirm only historical docs reference the term; report findings in ledger_sync.md.
Line 9: When updating galph_memory.md, specify that D2 is complete and highlight that D3 is now the sole remaining shim task.
Line 10: Before committing, rerun pytest --collect-only if prior attempt failed or files changed significantly, to ensure reproducibility.
Line 11: Confirm input.md remains untouched after you begin working; only galph should write it.
Line 12: Keep commit scope focused on documentation; if unexpected files appear in git status, investigate and revert.
Line 13: After pushing, verify `git status` returns “working tree clean” to signal readiness for the next loop.

Verification Checklist:
Item 1: docs/fix_plan.md shows Attempt #184 with ledger sync summary and D2 removed from Next Actions.
Item 2: plans/archive/cli-phi-parity-shim/plan.md exists with closure note; no copy left in plans/active/.
Item 3: reports/2025-10-cli-flags/phase_phi_removal/phase_d/ledger_sync.md (or appended summary) documents today’s update and command log.
Item 4: pytest collect-only log stored alongside Phase D artifacts; command listed in commands.txt.
Item 5: galph_memory.md latest entry references the ledger sync and points to the archived plan path.
Item 6: git push completed without conflicts; working tree clean post-push.

Pointers:
- plans/active/phi-carryover-removal/plan.md:58 for Phase D status snapshot and checklist wording.
- docs/fix_plan.md:451 for the CLI-FLAGS-003 ledger entry to update.
- plans/active/cli-noise-pix0/plan.md:12 for Phase L scaling tasks to reference in Next Actions.
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/summary.md for existing Phase D evidence.
- galph_memory.md latest section (2025-12-14 entries) to maintain chronological notes.

Next Up: Phase D3 supervisor handoff memo — once ledger sync lands, prepare to focus the next loop on documenting the handoff and steering Ralph back to plans/active/cli-noise-pix0/plan.md Phase L scaling tasks.

Background Notes:
Line A: Attempt #183 (2025-10-08) delivered the proof-of-removal bundle and removed the stale row-batching code in simulator.py, so our documentation must reflect that fix.
Line B: The Phase D bundle already contains trace_py_spec.log, trace_c_spec.log, pytest.log, collect.log, commands.txt, env.json, sha256.txt, and rg_phi_carryover.txt; today’s additions should not overwrite these assets.
Line C: docs/bugs/verified_c_bugs.md explicitly states PyTorch rejects the φ carryover bug; ensure any new references maintain that framing.
Line D: CLAUDE.md Protected Assets rule requires us to cross-check docs/index.md before moving or deleting files referenced there.
Line E: plans/archive/ holds prior initiatives; follow their formatting (context block + phase summaries) when adding the archived shim plan.
Line F: Feature branch feature/spec-based-2 already contains previous supervisor commits (see history); keep commit message structure consistent for easier auditing.
Line G: Reports directory naming convention uses UTC timestamps; if you add ledger_sync.md, timestamp the filename or include the datetime inside the file.
Line H: When logging commands, include git mv, pytest command, and git status so future auditors can replay the exact flow.
Line I: Ensure pytest collect-only uses the same selector as earlier bundles (tests/test_cli_scaling_phi0.py) to keep parity with existing evidence.
Line J: After moving the plan, update any README or index files inside plans/ if they reference the active directory listing (check with `rg "cli-phi-parity-shim" plans -n`).
Line K: Remember to set `KMP_DUPLICATE_LIB_OK=TRUE` in the environment if the collect-only run starts Python and torch; document whether it was needed in commands.txt.
Line L: If git push fails because of remote updates, follow supervisor SOP — run `timeout 30 git pull --rebase`, resolve conflicts, continue with `timeout 30 git rebase --continue --no-edit`, and document decisions in galph_memory.md.
Line M: Keep eyes open for any residual references to phi_carryover_mode in prompts or docs; note findings in ledger_sync.md even if nothing was changed.
Line N: The upcoming Phase L work (plans/active/cli-noise-pix0/plan.md) depends on the ledger being clean; highlight this dependency in the Next Actions text so context is preserved.
Line O: After finishing, re-open input.md briefly to ensure no accidental edits happened during the loop; Ralph must receive it unchanged.
Line P: When appending to galph_memory.md, maintain chronological order and mention both plan update and fix_plan modifications.
Line Q: Document the omission of new tests beyond collect-only in galph_memory.md so future loops know the testing scope.
Line R: When updating docs/fix_plan.md, maintain the indentation style used elsewhere (two spaces before sub-bullets) to keep formatting consistent.
Line S: If you create ledger_sync.md, include sha256 sums for any new logs to maintain integrity checks.
Line T: Add a short explanation in ledger_sync.md clarifying why D2 lagged behind D1 (administrative catch-up) to give context to readers.
Line U: Confirm that plans/archive/cli-phi-parity-shim/plan.md retains the original tables and checklists for historical reference; only prepend closure text.
Line V: Check that the archived plan still references the Phase D bundle path so historians can find the evidence quickly.
Line W: After all edits, run `rg "phi_carryover_mode"` to confirm only historical docs mention it; include results in the reports note.
Line X: Keep the collect-only log small by running with `-q`; mention the quiet flag when logging the command.
Line Y: For commands.txt, append rather than overwrite to preserve prior loop entries; use UTC timestamps to differentiate runs.
Line Z: When writing ledger_sync.md, include a short checklist verifying each deliverable (fix_plan update, plan archive, galph_memory entry, pytest log) for future audits.
