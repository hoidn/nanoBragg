Summary: Document the approved 900 s slow-gradient tolerance across the core guidance docs before closing C18.
Mode: Docs
Focus: TEST-SUITE-TRIAGE-001 / Next Action 14 — Phase Q documentation refresh
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_q/$STAMP/docs/
Do Now: [TEST-SUITE-TRIAGE-001] Next Action 14 — update docs/development/testing_strategy.md §4.1 with the 900 s tolerance (docs-only; no pytest run).
If Blocked: Capture the conflict in reports/2026-01-test-suite-triage/phase_q/$STAMP/docs/blocked.md (include offending section + rationale) and pause for supervisor review.
Priorities & Rationale:
- docs/fix_plan.md:5 — Active Focus now expects Phase Q Q4/Q6 wrap-up after the 839.14 s validation.
- docs/fix_plan.md:791 — Next Action 14 defines the required doc set and artifact expectations.
- plans/active/test-suite-triage.md:357 — Phase Q table lists Q4 (docs) and Q6 (ledger) as remaining open items.
- reports/2026-01-test-suite-triage/phase_q/20251015T071423Z/summary.md:95 — Validation summary specifies the narrative to fold into the docs.
- reports/2026-01-test-suite-triage/phase_p/20251015T060354Z/c18_timing.md:194 — Documentation touch points already scoped; follow them precisely.
How-To Map:
- STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-triage/phase_q/$STAMP/docs && note the STAMP in every summary you write.
- docs/development/testing_strategy.md: add a §4.1 call-out describing the 900 s ceiling, cite both Phase P timing packet and Phase Q validation, and mention the slow_gradient marker + compile guard linkage.
- arch.md §15: append a short note that gradient suites may legitimately run up to 900 s on CPU with float64 + compile guard, referencing the same artifacts.
- docs/development/pytorch_runtime_checklist.md section 5: insert a bullet under Documentation & Tests reminding engineers that slow gradient tests expect ≤900 s runtime (Phase Q evidence).
- Summarise the edits in reports/2026-01-test-suite-triage/phase_q/$STAMP/docs/summary.md (include file paths, key sentences added, and artifact citations).
- After saving, run git diff to sanity-check the doc wording; stage nothing yet—await review instructions.
Pitfalls To Avoid:
- Do not change acceptance criteria or tolerance numbers beyond 900 s.
- Keep wording ASCII; avoid smart quotes or symbols.
- Preserve existing cross-references; add new ones only where mandated.
- Don’t modify pytest markers or manifests in this loop—they are already landed.
- Avoid editing remediation trackers until the documentation diff is accepted.
- Ensure new text explicitly cites both Phase P packet and Phase Q validation bundle.
- Don’t delete prior subsections; append or extend them.
- Skip running pytest unless supervisor requests; this is a docs-only loop.
Pointers:
- docs/fix_plan.md:791
- plans/active/test-suite-triage.md:367
- docs/development/testing_strategy.md:500
- arch.md:322
- docs/development/pytorch_runtime_checklist.md:6
- reports/2026-01-test-suite-triage/phase_q/20251015T071423Z/summary.md:95
Next Up: TEST-SUITE-TRIAGE-001 / Next Action 15 — update remediation_tracker.md and ledger once the documentation lands.
