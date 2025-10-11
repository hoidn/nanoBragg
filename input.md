Summary: Build Phase J remediation tracker bundle so we can hand failures to targeted fix streams.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_j/<STAMP>/{remediation_tracker.md,remediation_sequence.md,commands.txt}
Do Now: [TEST-SUITE-TRIAGE-001] Phase J — author remediation tracker + sequence docs (no pytest run; docs only)
If Blocked: Capture a note under reports/2026-01-test-suite-triage/phase_j/<STAMP>/blocked.md explaining what data is missing and update docs/fix_plan.md Attempts.
Priorities & Rationale:
- Use Phase I cluster data to map every failure to an owner and fix-plan item (reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/docs/triage_summary.md).
- Follow plan guidance for deliverables (plans/active/test-suite-triage.md:11-140) so J1–J3 close cleanly.
- Keep fix_plan ledger authoritative (docs/fix_plan.md:1-110) with Attempt #12 summary and updated Next Actions.
- Reference testing strategy for command formatting and env notes (docs/development/testing_strategy.md:1-120).
How-To Map:
- Create a new ISO timestamped folder under reports/2026-01-test-suite-triage/phase_j/ and record the timestamp inside commands.txt (include provenance + inputs consulted).
- Draft remediation_tracker.md: table listing cluster ID, failure count, owner, fix_plan ID, reproduction selector (from triage_summary), dependencies, exit criteria.
- Draft remediation_sequence.md: narrative ordering of clusters (e.g., determinism → source weighting → vectorization) with gating tests and rationale; cite spec/arch lines where relevant.
- Update docs/fix_plan.md Attempt history with Attempt #12 (Phase J start) and refresh Next Actions to reflect remaining follow-ups (mark tracker tasks done once artifacts exist).
- Add entries to reports/.../commands.txt describing how triage_summary.md and classification_overview.md were consumed; link both docs explicitly.
Pitfalls To Avoid:
- Do not run pytest or edit production code this loop.
- Keep protected assets (loop.sh, input.md, docs/index.md) untouched.
- Preserve vectorization parity gating; do not promise code changes until tracker is signed off.
- Ensure cluster owners/IDs exactly match triage_summary.md (no renumbering).
- Include env notes (KMP_DUPLICATE_LIB_OK, CUDA visibility) in commands.txt even if no tests run.
- Avoid inventing new fix-plan IDs; reuse the ledger entries already listed.
Pointers:
- docs/fix_plan.md:1-110 (Active Focus + Next Actions expectations)
- plans/active/test-suite-triage.md:11-140 (Phase J task definitions)
- reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/docs/triage_summary.md:1-80 (cluster table + selectors)
- reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/docs/classification_overview.md:1-120 (rationale + deltas)
Next Up: If you finish early, prep a skeleton for remediation_sequence.md dependencies cross-check (no code changes).
