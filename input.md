Summary: Sync Phase M2 results into the ledger and stage Phase M3 cluster packets so the remaining 13 failures are actionable.
Mode: Docs
Focus: TEST-SUITE-TRIAGE-001 / Post-M2 triage bundle
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md; reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md; reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/{gradients_guard,mosflm_offset,mixed_units,detector_orthogonality}/
Do Now: delegate
If Blocked: Capture the blocker in reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/blocked.md and append a short note to docs/fix_plan.md Attempt #41 so we preserve traceability.
Priorities & Rationale:
- docs/fix_plan.md:38-51 — Next Actions now demand tracker updates plus a Phase M3 evidence bundle for C2/C8/C15/C16.
- plans/active/test-suite-triage.md:11-27 — Status snapshot marks Phase M2 complete but keeps Phase M pending until the new documentation lands.
- plans/active/test-suite-triage.md:246-255 — Phase M3 table records C9+gradient follow-up as open items needing fresh STAMP 20251011T193829Z artifacts.
- reports/2026-01-test-suite-triage/phase_m/20251011T193829Z/summary.md — Chunked rerun counts (561/13/112) must be copied into downstream trackers.
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/summary.md — Use this prior baseline to explain the −33 failure delta when writing the new summaries.
How-To Map:
- Clone the Phase M2 counts into reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md (update headline table + narrative delta vs Phase K and M0).
- Refresh reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md (adjust totals, Sprint progress, and note the four active clusters with owners).
- mkdir -p reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/{gradients_guard,mosflm_offset,mixed_units,detector_orthogonality}.
- For each directory: add summary.md capturing reproduction command, classification (implementation bug vs infrastructure), relevant prior attempts, and cite the specific chunk log line(s) from phase_m/20251011T193829Z/chunks/.
- Link each new summary back into docs/fix_plan.md Attempt #41 (reference filenames) once the notes are written.
Pitfalls To Avoid:
- Stay docs-only; do not touch src/ or tests/ while we are in review mode.
- Preserve the 20251011T193829Z STAMP across every new artifact and avoid overwriting older phase_m3 data.
- When editing tracker files, keep existing tables intact (no column drift, no accidental whitespace trimming of Markdown tables).
- Quote reproduction commands exactly as written in the chunk logs to maintain auditability.
- Don’t delete earlier MOSFLM/orthogonality packets; add additive updates under the new STAMP instead.
- Keep environment guard guidance consistent with arch.md/testing_strategy (no ad-hoc env vars recorded elsewhere).
Pointers:
- docs/fix_plan.md:38-51
- plans/active/test-suite-triage.md:11-27
- plans/active/test-suite-triage.md:246-255
- reports/2026-01-test-suite-triage/phase_m/20251011T193829Z/summary.md
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/summary.md
Next Up: After the documentation lands, we can queue targeted remediation starting with the gradient guard harness integration.
