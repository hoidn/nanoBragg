Summary: Build a comprehensive supervisor guard design memo so the next loop can implement protections without ambiguity.
Mode: Docs
Focus: [ROUTING-SUPERVISOR-001] supervisor.sh automation guard
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/routing/<STAMP>-supervisor-guard-design.md; docs/fix_plan.md Attempt update; plans/active/supervisor-loop-guard/plan.md Phase B status; pytest collect log snippet embedded in memo
Do Now: Complete plan Phase B1 — author the supervisor guard design memo, refresh plan/fix_plan bookkeeping, then confirm pytest collection passes by running `pytest --collect-only -q` after staging documentation changes.
If Blocked: Record the obstacle (missing data, conflicting policy, tooling issue) inside reports/routing/<STAMP>-supervisor-guard-design.md with command transcripts, and log a partial Attempt in docs/fix_plan.md describing why Phase B1 could not finish.

Priorities & Rationale:
- plans/active/supervisor-loop-guard/plan.md:32 — Context plus dependency list clarifies that supervisor guard must mirror loop guard and cites critical documents; review this before drafting to avoid drift.
  Re-reading the plan ensures the memo captures every mandated guard feature (timeouted pull, single-run execution, conditional push, Protected Assets update).
- plans/active/supervisor-loop-guard/plan.md:55 — Phase B1 is explicitly a design deliverable; until it is written the code cannot change, so the memo is the highest priority artifact for unlocking implementation.
  The exit criteria call for a documented guard design hook referenced by the plan itself; make sure the memo is linked back into the checklist.
- docs/fix_plan.md:407 — Active Focus shows ROUTING-SUPERVISOR-001 with Phase B tasks pending; updating this ledger keeps long-term automation hygiene goals transparent.
  Fix_plan is the canonical progress log; without updating it, other collaborators will not know that Phase B1 is complete.
- docs/fix_plan.md Attempt #2 (2025-10-09) — Newly added evidence describes missing guard elements; the design memo should cite this attempt and expand on each finding.
  Treat Attempt #2 as the audit baseline—pull key bullet points into the memo so the narrative remains connected to recorded evidence.
- reports/routing/20251009T043816Z-supervisor-regression.txt — Contains the exact diff and notes; the memo should lift relevant lines (e.g., 20-iteration loop, missing timeout guard, unconditional push) and elaborate on remediation tactics.
  Quote the file path and timestamp inside the memo header so auditors can jump back to the source artifact quickly.
- plans/active/routing-loop-guard/plan.md:18-120 — Documented guard restoration for loop.sh is the template; mimic its verified approach so supervisor guard stays consistent across automation scripts.
  Highlight parity requirements such as `timeout 30 git pull --rebase` with fallback, conditional push logic, and dry-run expectations.
- prompts/meta.md:1-200 — Routing SOP spells out automation policies (single work item, authoritative commands, commit hygiene); the memo must describe how the guard enforces these automatically to prevent regressions.
  Include a short paragraph on how the guard guarantees the two-message loop policy and prevents multi-iteration runs.
- docs/index.md:12-40 — Protected Assets list currently omits supervisor.sh; the memo needs to plan for adding it during Phase B5 while preserving ordering and rationale in that document.
  Mention the Protected Assets rule explicitly so design readers know why docs/index.md changes are mandatory.
- galph_memory.md:1-120 — Historical supervisor notes flag this guard as unresolved; referencing them demonstrates continuity and avoids forgetting prior decisions.
  Summarise the latest galph entry relevant to ROUTING-SUPERVISOR-001 within the memo’s context section.
- docs/development/testing_strategy.md:58-120 — Provides command sourcing guidance and device/dtype discipline; cite it in the memo when describing testing expectations for implementation phases.
  Include a reminder that even doc-only loops must record their authoritative test command.

Detailed Steps:
1. Export authoritative commands reference:
   `export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md`
   Document this export in the memo so readers know where pytest command sourcing came from.
2. Capture UTC timestamp:
   `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`
   Use this stamp in both the memo filename and header for reproducibility.
3. Create memo file:
   `OUT=reports/routing/${STAMP}-supervisor-guard-design.md; touch "$OUT"`
   Start the document with title, timestamp, git commit (current HEAD), and reference to Attempt #2.
4. Section 1 — Context:
   Summarise regression findings, list missing guard features, and link to relevant plan sections; explain why automation must remain paused until guard implementation completes.
5. Section 2 — Guard Parity Table:
   Construct a markdown table with columns: Guard Aspect | loop.sh (853cf08) | supervisor.sh (current) | Required Change.
   Follow the table with line-by-line commentary elaborating on each delta.
6. Section 3 — Timeout & Fallback Flow:
   Describe required commands, logging expectations, and how to ensure the script recovers gracefully; mention integration with `sync/state.json` handling.
7. Section 4 — Single Iteration Contract:
   Define behavior for both SYNC_VIA_GIT=0 and SYNC_VIA_GIT=1 modes; specify how to exit after a single prompt, and how to handle exit codes.
8. Section 5 — Conditional Push Logic:
   Explain detection of new commits, success checks, warning paths, and parity with loop.sh guard; include pseudo-code snippet.
9. Section 6 — Protected Assets Update Plan:
   Outline required docs/index.md change, potential updates to CLAUDE.md or other SOPs, and mention Protected Assets policy.
10. Section 7 — Verification Checklist:
    List dry-run, hygiene, pytest collect, git status verification, and artifact recording requirements for phases B3/B4.
11. Section 8 — Risks & Open Questions:
    Capture items such as Python orchestrator interaction, environment variable defaults, state file rotation, logging expectations; assign owners or follow-up notes.
12. Section 9 — Roadmap:
    Provide bullet list for B2 (implementation), B3 (dry run), B4 (hygiene), B5 (Protected Assets update + documentation), including artifact directories and gating commands.
13. Appendix — References:
    Include file:line anchors for plan rows, fix_plan entries, audit log, prompts/meta, docs/index.md, and relevant SOPs for quick cross-checking.
14. Once memo draft complete, update plans/active/supervisor-loop-guard/plan.md Phase B1 row to indicate completion and insert memo path into guidance column.
15. Append Attempt #3 in docs/fix_plan.md (under ROUTING-SUPERVISOR-001) noting Phase B1 completion, listing artifacts, summarising key design elements, and enumerating next actions.
16. Stage documentation updates (`git add reports/routing/... plans/active/supervisor-loop-guard/plan.md docs/fix_plan.md input.md`).
17. Run `pytest --collect-only -q`; capture command and output; add a short excerpt or log path to the memo and mention success in the Attempt entry.
18. Run `git status --short`; confirm only expected files are staged; document expected diff list in the memo for auditing.
19. If unexpected files appear, either clean them before finishing or record them in the memo with rationale for leaving them untouched.
20. Review the memo for ASCII-only characters, consistent formatting, and complete references before finalising.

Pitfalls To Avoid:
- No script edits during this loop; stick to documentation and planning work.
- Do not modify docs/index.md yet; simply plan the change.
- Avoid rearranging fix_plan history; append new entries only.
- Keep environment variable exports confined to shell session; do not commit them.
- Ensure memo uses fenced code blocks—not inline substitutions—to show commands.
- Do not run automation scripts (supervisor.sh/loop.sh/Python orchestrator) while preparing the memo.
- Keep pytest usage limited to `--collect-only`; additional testing awaits implementation loops.
- Verify that new report files reside under reports/routing/ using the timestamped naming scheme.
- Maintain Protected Assets awareness; reference docs/index.md without renaming or deleting protected files.
- Double-check that the memo and plan updates retain consistent table formatting (no stray whitespace or broken columns).

Pointers:
- plans/active/supervisor-loop-guard/plan.md:32-120
- docs/fix_plan.md:407-420
- reports/routing/20251009T043816Z-supervisor-regression.txt:1-200
- plans/active/routing-loop-guard/plan.md:18-120
- prompts/meta.md:1-200
- docs/index.md:12-40
- docs/development/testing_strategy.md:58-120
- galph_memory.md:1-120

Next Up: If time permits after Phase B1 deliverables, append to the memo a proposed execution schedule for B2-B5 (owners, commands, expected timestamps) so implementation can proceed efficiently next loop.

Additional Reminders:
- After running pytest, capture the full command line and exit status in the memo so audit trails remain complete.
- Include a brief checklist at the memo’s end confirming: memo written, plan updated, fix_plan updated, pytest collect ran, git status clean.
- When drafting the memo, cross-reference the relevant CLAUDE.md automation rules if any new guard logic touches supervisory policies.
- Keep timestamps in ISO 8601 with Z suffix for consistency across reports.
