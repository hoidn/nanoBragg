Summary: Capture Phase D4 closure evidence for source weighting by syncing trackers/analysis to show cluster C3 resolved and logging the Attempt #19 deltas.
Mode: Docs
Focus: [SOURCE-WEIGHT-002] Simulator source weighting
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting/
Do Now: [SOURCE-WEIGHT-002] Simulator source weighting — author the Phase D4 closure bundle (tracker updates + closure memo); no pytest this loop
If Blocked: Record blocker notes in `$outdir/notes.md`, include links to any files you could not update, and stop.
Priorities & Rationale:
- plans/active/source-weighting.md marks D2 done and leaves D4 tracker/ledger sync outstanding (lines 5-35, 73-83).
- docs/fix_plan.md:155-205 sets new Next Actions for D4 (tracker sync, closure memo, final status update).
- reports/2026-01-test-suite-triage/phase_d/20251011T093344Z/source_weighting/ holds Attempt #19 logs that must anchor the closure memo.
- remediation tracker still lists C3 with 4 failures, so Sprint 1 metrics remain stale (`reports/.../remediation_tracker.md:24-88`).
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `outdir=reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting`; `mkdir -p "$outdir" "$outdir/artifacts"`.
- Diff the current tracker docs (`reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/{remediation_tracker.md,remediation_sequence.md}`) and Phase K analysis files (`reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/{summary.md,classification_overview.md}`); update each to reflect C3=0, total failures 27, pass count 516, skip count 143.
- In `$outdir/closure.md`, summarise: targeted selector results (10/10 pass), full-suite totals (516/27/143, 2 xfail), default dtype coverage outcome, and reference the Attempt #19 artifacts (`20251011T093344Z`).
- Note edits in `commands.txt` within `$outdir` (list files touched + git status snippets).
- After document edits, update `docs/fix_plan.md` Attempts History with the new Attempt ID and note where closure memo lives; adjust plan status if anything changed beyond the tracker counts.
Pitfalls To Avoid:
- Do not rerun pytest; this is a documentation loop only.
- Keep Attempt numbering consistent when you log the closure (next Attempt should be #20 for this initiative).
- Preserve Protected Assets from docs/index.md; do not relocate existing report folders.
- When editing trackers, retain the sprint sequencing tables and only adjust the counts/status fields relevant to C3.
- Ensure all markdown tables remain properly aligned; avoid introducing trailing spaces in tables.
Pointers:
- plans/active/source-weighting.md:1-85
- docs/fix_plan.md:1-220, 620-700
- reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md:1-120
- reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md:1-200
- reports/2026-01-test-suite-triage/phase_d/20251011T093344Z/source_weighting/summary.md:1-120
Next Up: 1. Once C3 is marked resolved, archive `[SOURCE-WEIGHT-002]` (mark done + update Sprint 1 metrics). 2. Begin prep for `[VECTOR-PARITY-001]` Tap 5.3 instrumentation brief per plan Phase E.
