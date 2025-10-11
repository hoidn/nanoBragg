Summary: Scope Phase M3a by producing the MOSFLM remediation sync so C6 handoff is ready.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] Phase M3 staging
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_sync/summary.md
Do Now: Execute docs/fix_plan.md [TEST-SUITE-TRIAGE-001] Next Actions #1 — draft the Phase M3a MOSFLM remediation sync bundle.
If Blocked: Capture reports/2026-01-test-suite-triage/phase_m3/$STAMP/blocked.md summarising the obstacle (include git status) and stop.

Priorities & Rationale:
- docs/fix_plan.md:48-51 — Next Actions now require the MOSFLM sync before other Phase M3 work.
- plans/active/test-suite-triage.md:235-237 — Plan keeps M3a open; needs concrete scope + artifact path to advance.
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:186 — Cluster C6 findings and reproduction commands must be restated in the sync.
- plans/active/detector-config.md:30-44 — Detector remediation blueprint depends on owning the MOSFLM offset tasks that the sync should feed.
- docs/development/testing_strategy.md:14 — Guardrails demand we track detector fixes with authoritative selectors captured in the new summary.

How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`
- `mkdir -p reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_sync`
- Review `reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md` Cluster C6; cross-check `plans/active/detector-config.md` Phase B tasks and `docs/fix_plan.md` attempts.
- Draft `reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_sync/summary.md` covering: current failure count, reproduction commands, blocking dependencies, required plan updates, and expected exit criteria for `[DETECTOR-CONFIG-001]`.
- Update `plans/active/detector-config.md` (Phase B rows) and `docs/fix_plan.md` attempts if new decisions emerge; note file + line anchors inside summary.
- Append the new Attempt to `docs/fix_plan.md` and refresh `remediation_tracker.md` if scope or ownership changes are recorded.

Pitfalls To Avoid:
- Don’t run pytest; this loop is documentation-only.
- Keep artifacts under the stamped `phase_m3` directory; no reuse of prior timestamps.
- Reference spec/arch sections verbatim instead of paraphrasing to prevent drift.
- Maintain ASCII edits; avoid introducing new Unicode beyond existing punctuation.
- When updating plans/ledger, preserve Attempt numbering and historical context.
- Ensure MOSFLM sync cites authoritative commands (no invented selectors).
- Do not touch Protected Assets listed in docs/index.md.
- Call out unresolved blockers explicitly; don’t silently defer them.
- If detector-config plan changes, note rationale in both the plan and summary.
- Leave environment vars unset after finishing.

Pointers:
- docs/fix_plan.md:48-51
- plans/active/test-suite-triage.md:235-237
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:186
- plans/active/detector-config.md:30-44
- docs/development/testing_strategy.md:14

Next Up: After the sync, tackle Phase M3b detector-orthogonality owner notes using the new plan context.
