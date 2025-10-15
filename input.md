Summary: Archive the test-suite triage initiative now that Phase R is complete.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] archival handoff (Next Action 17)
Branch: feature/spec-based-2
Mapped tests: none — docs-only
Artifacts: plans/archive/test-suite-triage.md; docs/fix_plan.md; reports/2026-01-test-suite-triage/phase_r/20251015T102654Z/summary.md
Do Now: Next Action 17 — archive [TEST-SUITE-TRIAGE-001]; no pytest run
If Blocked: Record the blocker under docs/fix_plan.md Attempt history for this initiative and ping in galph_memory.md with the partial edits; stop there.
Priorities & Rationale:
- docs/fix_plan.md:6 still flags the initiative as “READY TO ARCHIVE,” so clearing it unblocks downstream priorities.
- docs/fix_plan.md:65 defines Next Action 17 (archive + ledger sync) that must be executed before we pivot to vectorization.
- plans/active/test-suite-triage.md:379-386 confirms Phase R closure and states archival is the only remaining step.
- plans/active/test-suite-triage.md:395 captures S1 instructions for moving the plan into the archive with a closure note.
- reports/2026-01-test-suite-triage/phase_r/20251015T102654Z/summary.md:1 anchors the final metrics the archival note must cite.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md
- Use `git mv plans/active/test-suite-triage.md plans/archive/test-suite-triage.md`.
- Add a short closure preface at the top of the archived plan summarising Attempt #84 metrics (43 pass / 9 skip / 1 xfail, 846.60 s, 905 s tolerance) and link to the summary.md artifact.
- Update docs/fix_plan.md: remove the “READY TO ARCHIVE” bullet, mark Next Action 17 complete, and append a new Attempt entry documenting the archival with STAMP + artifact references.
- Ensure docs/fix_plan.md Index retains the row for [TEST-SUITE-TRIAGE-001] with Status `done` and, if helpful, note the plan now lives under plans/archive/.
- Re-run `git status` to verify only the intended docs moved/edited; no tests to execute.
Pitfalls To Avoid:
- Do not touch protected assets listed in docs/index.md.
- Keep edits ASCII-only; no fancy Unicode in the archival preface.
- Use `git mv` so history follows the plan into plans/archive/.
- Do not alter archived evidence bundles under reports/ beyond new references.
- Avoid changing statuses for unrelated fix_plan items or active plans.
- Skip pytest runs; this is a documentation-only loop.
- Preserve existing checklist tables and markers when editing markdown.
- Note the STAMP from summary.md when logging the archival attempt.
- Verify hyperlinks after moving the plan (e.g., update relative paths if needed).
- Keep Tap 5.3 instrumentation plans untouched until this archival step is signed off.
Pointers:
- docs/fix_plan.md:3-7
- docs/fix_plan.md:65
- plans/active/test-suite-triage.md:379-395
- plans/archive/ (target location for the plan)
- reports/2026-01-test-suite-triage/phase_r/20251015T102654Z/summary.md:1
Next Up: 1) Kick off `[VECTOR-PARITY-001]` Phase E16 PyTorch Tap 5.3 capture once the archival attempt lands.
