Summary: Capture the 2026 failure classification bundle (triage ledger + follow-up table) so remediation sequencing can resume.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_f/<STAMP>/
Do Now: [TEST-SUITE-TRIAGE-001] triage refresh — create triage_summary.md, cluster_deltas.md, and pending_actions.md in reports/2026-01-test-suite-triage/phase_f/$STAMP/, using the 49-node failure list from phase_e/20251010T180102Z.
If Blocked: write reports/2026-01-test-suite-triage/phase_f/$STAMP/blocked.md summarising the snag (include attempted commands), update docs/fix_plan.md Attempt history with the blockage, then stop.
Priorities & Rationale:
- plans/active/test-suite-triage.md:11 highlights that the 2026 full-suite rerun is complete and only the classification refresh remains before coordination restarts.
- plans/active/test-suite-triage.md:82-91 spells out the outstanding worksheet, ownership, and pending-actions deliverables.
- docs/fix_plan.md:45-52 moves the Next Actions focus to staging the phase_f bundle and logging Attempt #8.
- reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/failures_raw.md:1-60 lists the exact 49 failures the refresh must classify.
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create `ROOT=reports/2026-01-test-suite-triage/phase_f/$STAMP`; run `mkdir -p "$ROOT"`.
- Copy the prior worksheet: `cp reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/triage_summary.md "$ROOT"/triage_summary.md` and update the counts/annotations so C1 (CLI defaults) is marked cleared while the remaining clusters reflect the 49 current failures.
- Generate `cluster_deltas.md`: tabulate Attempt #5 vs Attempt #7 counts (use the failure list + previous table) and note any cluster ownership changes; include a section for newly resolved items.
- Author `pending_actions.md` with one row per cluster (owner, priority, reproduction command, expected artifact). Ensure each entry links back to the relevant fix-plan ID.
- Record provenance: append a short `commands.txt` (copy commands used above), and update docs/fix_plan.md attempts with the new STAMP + artifact paths once the docs are in place.
Pitfalls To Avoid:
- Do not renumber existing cluster IDs; keep continuity with the Phase C worksheet.
- Avoid editing tests or production code—this is a documents-only task.
- Maintain ASCII output; no embedded spreadsheets or binary attachments.
- Ensure Attempt numbering in docs/fix_plan.md moves forward (log this as Attempt #8).
- Reference authoritative selectors from the worksheet; do not invent new pytest commands.
- Keep CLI defaults cluster marked complete rather than deleting it; note its resolution in cluster_deltas.md.
Pointers:
- plans/active/test-suite-triage.md:11
- plans/active/test-suite-triage.md:82-91
- docs/fix_plan.md:45-52
- reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/triage_summary.md:1-60
- reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/summary.md:1-120
Next Up: Prepare the remediation ladder addendum (phase_d handoff update) once the refreshed pending_actions.md is committed.
