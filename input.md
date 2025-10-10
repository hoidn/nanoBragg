Summary: Map triage clusters to fix-plan follow-ups and document remaining blockers.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: docs/fix_plan.md; plans/active/test-suite-triage.md; reports/2026-01-test-suite-triage/phase_c/20251010T134156Z/triage_summary.md
Do Now: [TEST-SUITE-TRIAGE-001] — Complete Phase C3/C4 mapping for clusters C1–C14 (doc-only; no pytest execution this loop).
If Blocked: Log unresolved questions in triage_summary.md (Pending Actions section) and ping supervisor via docs/fix_plan.md Attempts History.
Priorities & Rationale:
- Align triage output with ledger so remediation work can start (docs/fix_plan.md:34-37).
- Plan expects Phase C3/C4 ownership mapping before Phase D handoff (plans/active/test-suite-triage.md:44-49).
- Classification clusters already identified (reports/2026-01-test-suite-triage/phase_c/20251010T134156Z/triage_summary.md:12-28).
How-To Map:
1) Update triage_summary.md with a new “Pending Actions” table (Cluster ID → proposed fix-plan link/owner/status) and note the ~172 unexecuted tests as a blocker. 2) Under docs/fix_plan.md `[TEST-SUITE-TRIAGE-001]`, add a bullet list mapping each cluster to an existing fix-plan ID or a placeholder you introduce (e.g., propose IDs for determinism, debug trace, dual runner, detector config; leave status `in_planning`). 3) Refresh plans/active/test-suite-triage.md so Phase C3 reflects progress (mark [P] or [D] once mapping recorded) and document any remaining open owners for C4. Keep edits ASCII and reference artifact paths explicitly.
Pitfalls To Avoid:
- Do not run pytest or modify production code.
- Respect Protected Assets (docs/index.md references like loop.sh, input.md).
- Keep new fix-plan identifiers consistent (UPPERCASE with hyphenated numeric suffix).
- When adding placeholders, note that creation ≠ implementation; avoid implying work completed.
- Preserve timestamped report directories; create new ones only if generating fresh artifacts.
Pointers:
- docs/fix_plan.md:22-41
- plans/active/test-suite-triage.md:44-49
- reports/2026-01-test-suite-triage/phase_c/20251010T134156Z/triage_summary.md:12-37
Next Up: If you finish early, outline the Phase B rerun command set with expected runtime budget inside triage_summary.md.
