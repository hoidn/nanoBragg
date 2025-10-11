Summary: Build the Phase K classification bundle from the completed pytest run and refresh the remediation tracker.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/{triage_summary.md,classification_overview.md,summary.md}; reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/{remediation_tracker.md,remediation_sequence.md}
Do Now: [TEST-SUITE-TRIAGE-001] Phase K K2–K3 analysis — curate triage_summary.md and refresh the remediation tracker (no pytest run).
If Blocked: Draft reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/blocked.md describing why the classification or tracker update could not be completed, list missing data, and stop for supervisor review.
Priorities & Rationale:
- docs/fix_plan.md:1-110 — Next Actions now demand the Phase K analysis bundle plus tracker refresh before remediation resumes.
- plans/active/test-suite-triage.md:120-180 — Phase K table (K2/K3) specifies the exact artifacts and owners expected for this loop.
- reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/summary.md — Completed rerun results (31 failures) that the new triage summary must reconcile.
- reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/docs/triage_summary.md — Prior baseline to diff against when computing Phase K deltas.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md before starting so shell history captures the reference doc.
- Set STAMP=20251011T072940Z (the successful Phase K run). mkdir -p reports/2026-01-test-suite-triage/phase_k/$STAMP/analysis/ if it does not exist.
- Copy Phase I docs as a starting point (`cp reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/docs/*.md reports/2026-01-test-suite-triage/phase_k/$STAMP/analysis/`) and edit them to reflect the 31-failure inventory, tagging each as implementation bug vs deprecation candidate and noting pass/fail delta vs Phase I.
- Summarise the changes in analysis/summary.md (include counts, major cluster shifts, and any newly passing areas) and capture supporting metrics from pytest_full.xml if helpful.
- Update reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md and remediation_sequence.md with the new counts/owners; annotate which items remain blocked behind Phase K data.
- Append commands run and decision notes to reports/2026-01-test-suite-triage/phase_k/$STAMP/commands.txt; record env or helper scripts if used.
- Prepare to log Attempt #16 in docs/fix_plan.md once artifacts are saved; list file paths and highlight any follow-up needs.
Pitfalls To Avoid:
- Do not rerun pytest; this loop is documentation/evidence only.
- Keep all edits timestamped under 20251011T072940Z; do not spawn new STAMP directories unless supervisor instructs otherwise.
- Preserve original Phase I docs for auditing—work on copies inside the Phase K analysis folder.
- Ensure classification labels distinguish implementation bugs from deprecation candidates; ambiguous tags stall remediation sequencing.
- Update both remediation_tracker.md and remediation_sequence.md; leaving them out of sync causes planning drift.
- Document every shell command in commands.txt for provenance.
- Avoid editing protected assets listed in docs/index.md (loop.sh, input.md, etc.).
Pointers:
- docs/fix_plan.md:1-120 — Active focus, Next Actions, and Attempt #15 notes.
- plans/active/test-suite-triage.md:5-180 — Phase K checklist and guidance for K2/K3 outputs.
- reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/logs/pytest_full.log:1-400 — Source data for counts and failure list.
Next Up: 1) Once the analysis bundle lands, tee up docs/fix_plan.md Attempt #16 and prep guidance for resuming Sprint 1 remediation.
