Summary: Finish Phase M2d by documenting the compile guard and syncing ledgers so we can advance to Phase M3 triage.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] Phase M2 — Gradient Infrastructure Gate
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_m2/$STAMP/{summary.md,docs_diff/}; reports/2026-01-test-suite-triage/phase_m2/$STAMP/gradients_gpu/ (only if optional CUDA proof is run)
Do Now: Execute docs/fix_plan.md [TEST-SUITE-TRIAGE-001] Next Actions #1 — author the Phase M2d documentation + ledger updates before touching any new code paths.
If Blocked: Capture a short report under reports/2026-01-test-suite-triage/phase_m2/$STAMP/blocked.md explaining the obstacle (include git status + pending edits) and halt for supervisor guidance.

Priorities & Rationale:
- plans/active/test-suite-triage.md:223 — M2d remains open; doc updates are the gate to Phase M3 handoff.
- docs/fix_plan.md:44 — Next Actions now target documentation + tracker refresh using Attempt #29 evidence.
- reports/2026-01-test-suite-triage/phase_m2/20251011T172830Z/summary.md:1 — Source log describing the successful gradcheck run to cite in the doc updates.
- arch.md:322 — Differentiability section needs a compile-guard callout aligned with the gradient workflow.
- docs/development/testing_strategy.md:18 — Device/dtype discipline must now mention the guard requirement for gradcheck.
- docs/development/pytorch_runtime_checklist.md:1 — Runtime checklist needs a compile-guard bullet so future edits keep the flag in mind.

How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2026-01-test-suite-triage/phase_m2/$STAMP/{docs_diff}` to stage the summary + diff notes.
2. Update `arch.md` §15 (line ~322) with a concise paragraph documenting the `NANOBRAGG_DISABLE_COMPILE=1` guard, its rationale, and reference to the Phase M2 artifacts.
3. In `docs/development/testing_strategy.md` (§1.4 and §4.1) add guidance that gradient tests must set the guard before importing torch and include the authoritative selector already logged in Attempt #29.
4. Append a checklist item to `docs/development/pytorch_runtime_checklist.md` covering the compile guard for gradcheck suites, linking back to the testing strategy section.
5. Refresh `remediation_tracker.md` and this ledger entry’s Attempts list with the new STAMP, citing Attempt #29 evidence and the doc updates; capture a short `summary.md` noting what was edited and where the artifacts live.
6. If CUDA hardware is available and you choose to run the optional GPU selector, archive logs under `phase_m2/$STAMP/gradients_gpu/`; otherwise state “GPU skipped” in summary.md.

Pitfalls To Avoid:
- Do not re-run the full test suite; this loop is documentation-only.
- Keep edits ASCII and respect Protected Assets referenced in docs/index.md.
- Preserve existing guard behavior—no code modifications unless documentation reveals a bug.
- When editing docs, note subsection anchors so future references remain stable.
- Record the new Attempt in docs/fix_plan.md without disturbing prior numbering.
- Maintain consistent terminology (`NANOBRAGG_DISABLE_COMPILE=1`) across all documents.
- If you can’t complete every doc in one go, stop after logging partial progress in summary.md and avoid mixing unfinished edits in git.
- Don’t delete prior Phase M2 artifacts; new STAMP directories must be unique.
- Ensure remediation_tracker.md counts still total 11→1 failures before/after so ledger stays accurate.
- Leave environment variables unset when you finish to avoid contaminating later runs.

Pointers:
- plans/active/test-suite-triage.md:223
- docs/fix_plan.md:44
- reports/2026-01-test-suite-triage/phase_m2/20251011T172830Z/summary.md:1
- arch.md:322
- docs/development/testing_strategy.md:18
- docs/development/pytorch_runtime_checklist.md:1
- reports/2026-01-test-suite-triage/phase_m2/20251011T171454Z/strategy.md:140

Next Up: Prep Phase M3a scope notes once M2d is committed.
