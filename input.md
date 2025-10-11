Summary: Capture the Option A design note for MOSFLM explicit vs auto beam-center handling so implementation can proceed without ambiguity.
Mode: Docs
Focus: DETECTOR-CONFIG-001 / Detector defaults audit
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_offset/design.md
Do Now: Draft the Option A remediation design under reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_offset/design.md (plan Phase B tasks B1–B4).
If Blocked: Capture blocker details in reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_offset/blocked.md and add a short note to docs/fix_plan.md Attempt log.
Priorities & Rationale:
- docs/fix_plan.md:229-264 — Next Actions now require design + implementation steps keyed to Option A.
- plans/active/detector-config.md:12-68 — Phase B tasks demand a design artifact before coding.
- reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md — Current failure analysis recommending Option A.
- specs/spec-a-core.md:68-86 — Normative MOSFLM +0.5 mapping rules the design must respect.
- arch.md:79-80 — ADR establishing offset behavior for MOSFLM and CUSTOM conventions.
How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_offset`.
2. Re-read specs/spec-a-core.md §§68–73 and arch.md §ADR-03 to quote the normative language in the design.
3. Compare Option A vs Option B from the existing summary; document the decision, CLI/config propagation plan, test/doc impact matrix, and risk notes (API-002, CONVENTION-001) in design.md.
4. End the document with acceptance criteria aligned to plan tasks (B1–B4) and call out pending implementation steps.
Pitfalls To Avoid:
- Don’t edit src/ or tests/ during this docs loop.
- Keep the new STAMP directory distinct; never overwrite 20251011T193829Z assets.
- Quote spec passages verbatim to avoid paraphrase drift.
- Capture interactions with pix0 overrides (API-002) and CUSTOM convention behavior explicitly.
- Preserve device/dtype neutrality requirements when describing future implementation.
- Reference targeted selectors exactly as in plan (no guesswork on pytest names).
- Avoid assuming future CLI parsing specifics without documenting fallback behavior for missing flags.
Pointers:
- docs/fix_plan.md:229-264
- plans/active/detector-config.md:1-73
- specs/spec-a-core.md:68-86
- arch.md:79-80
- reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md
Next Up: Implementation of Option A (plan Phase C tasks) once the design is approved.
