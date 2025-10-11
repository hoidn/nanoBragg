Summary: Draft Phase M3b detector-orthogonality owner notes so Cluster C8 has a clear handoff.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] Phase M3b detector orthogonality notes
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_m3/$STAMP/detector_ortho/notes.md
Do Now: Execute docs/fix_plan.md [TEST-SUITE-TRIAGE-001] Next Actions #1 by authoring the Phase M3b detector_ortho notes for Cluster C8; capture the reproduction selector without running it.
If Blocked: Write reports/2026-01-test-suite-triage/phase_m3/$STAMP/blocked.md (include obstacle summary + `git status`) and stop.

Priorities & Rationale:
- docs/fix_plan.md:48-50 — Next Actions now focus on M3b owner notes before any mixed-units work.
- plans/active/test-suite-triage.md:236 — Plan expects `phase_m3/$STAMP/detector_ortho/notes.md` with ownership + selector context.
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:247 — Cluster C8 failure details and reproduction command must be quoted in the notes.
- docs/development/testing_strategy.md:14 — Guardrails demand we log authoritative selectors even when we do doc-only prep.

How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`
- `mkdir -p reports/2026-01-test-suite-triage/phase_m3/$STAMP/detector_ortho`
- Review `triage_summary.md:247-266` for Cluster C8 context and copy the exact error text / reproduction command.
- Read `plans/active/test-suite-triage.md:228-240` to mirror Phase M3 expectations (owner, deliverables, exit criteria).
- Draft `detector_ortho/notes.md` covering: failure summary, reproduction selector, proposed owner, required plan/doc touchpoints, and open design questions; cite file + line anchors in situ.
- Update `docs/fix_plan.md` Attempt history with the new artifact path and refresh `plans/active/test-suite-triage.md` if additional guidance emerges.

Pitfalls To Avoid:
- Do not run pytest; this loop is documentation-only.
- Keep edits ASCII; no smart quotes or Unicode bullets.
- Reference authoritative commands verbatim—no guessing at selectors.
- Note unresolved blockers explicitly; don’t silently defer them.
- Preserve fix-plan attempt numbering and historical context.
- Don’t modify Protected Assets (see docs/index.md).
- When updating plans/ledger, cite exact artifact paths created this loop.
- Leave environment variables unset after finishing.
- Avoid editing simulator code; analysis only.
- Keep notes succinct—focus on actionable owner guidance.

Pointers:
- docs/fix_plan.md:48-50
- plans/active/test-suite-triage.md:236
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:247
- docs/development/testing_strategy.md:14

Next Up: After detector_ortho notes land, move to Phase M3c mixed-units hypotheses.
