Summary: Capture Sprint 0 closure artifacts and sync the ledger/tracker before scoping the Phase M2 gradient guard.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] Phase M1f — Sprint 0 ledger refresh
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_m1/$STAMP/summary.md; reports/2026-01-test-suite-triage/phase_m2/$STAMP/strategy.md; remediation_tracker.md
Do Now: Execute docs/fix_plan.md [TEST-SUITE-TRIAGE-001] Next Actions #1 — Phase M1f ledger refresh (doc updates only, no pytest)
If Blocked: Log the blocker + attempted command in docs/fix_plan.md Attempt history and drop a TODO in reports/2026-01-test-suite-triage/phase_m1/$STAMP/summary.md; stop and wait for supervisor guidance.

Priorities & Rationale:
- docs/fix_plan.md:3-48 — Next Actions now require the M1f ledger refresh and Phase M2 brief before any new fixes.
- plans/active/test-suite-triage.md:11-26 — Status snapshot notes Sprint 0 clusters closed and calls out M1f + M2 as the remaining Phase M1 work.
- plans/active/test-suite-triage.md:210-215 — Row M1e marked [D]; row M1f still open pending ledger/tracker updates.
- reports/2026-01-test-suite-triage/phase_m1/20251011T170539Z/shape_models/summary.md:1 — Source of Attempt #27 data that must be rolled into the new summary bundle.
- docs/development/testing_strategy.md:52-86 — Authoritative guidance for documenting environment + commands even when no tests run.

How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2026-01-test-suite-triage/phase_m1/$STAMP` and `reports/2026-01-test-suite-triage/phase_m2/$STAMP`.
2. Copy key metrics from Attempt #27: summarise 11 remaining failures, Sprint 0 completion, and artifact pointers into `reports/2026-01-test-suite-triage/phase_m1/$STAMP/summary.md` (include command log snippets and environment notes per testing_strategy §1.5).
3. Update `remediation_tracker.md` Sprint 0 rows with Attempt #27 data (failure counts, status → COMPLETE) and record the new STAMP/path.
4. Append Attempt #27 closure + the new summary path to `[TEST-SUITE-TRIAGE-001]` Attempts in docs/fix_plan.md; note that Sprint 0 is done and Phase M2 planning is next.
5. Draft Phase M2 guard brief: create `reports/2026-01-test-suite-triage/phase_m2/$STAMP/strategy.md` describing the proposed `NANOBRAGG_DISABLE_COMPILE=1` guard, expected selectors (`pytest -v tests/test_gradients.py -k "gradcheck"`), and documentation touch points.
6. Confirm plans/active/test-suite-triage.md row M1f flips to [D] and reference the new summary; leave M2a ready for delegation.

Pitfalls To Avoid:
- Do not rerun pytest; this loop is evidence-only.
- Preserve prior Attempt numbering in docs/fix_plan.md; append rather than overwrite.
- Keep `$STAMP` directories unique—never reuse an existing timestamp.
- Include environment + command strings in the summary even if no tests were executed.
- When editing remediation_tracker.md, update both the table row and any aggregate counts.
- Reference the Attempt #27 artifact path exactly (`20251011T170539Z`) when citing prior evidence.
- Avoid editing production code or deleting historical artifacts.
- Maintain UTF-8 ASCII only; no fancy characters beyond what already exists.
- Double-check Mode in future loops before dispatching new work.
- Leave Phase M2 implementation tasks untouched; we only author the strategy doc this loop.

Pointers:
- docs/fix_plan.md:3-48
- plans/active/test-suite-triage.md:11-222
- reports/2026-01-test-suite-triage/phase_m1/20251011T170539Z/shape_models/summary.md:1
- docs/development/testing_strategy.md:52-86
- remediation_tracker.md:1-200

Next Up: Phase M2a — implement the gradient compile guard once the brief is approved.
