Summary: Author the Phase E rerun brief so we know when and how to rerun the full test suite.
Mode: Docs
Focus: TEST-SUITE-TRIAGE-002 (Next Action 11 – Phase E rerun brief)
Branch: feature/spec-based-2
Mapped tests: none — docs-only
Artifacts: reports/2026-01-test-suite-refresh/phase_e/$STAMP/{phase_e_brief.md,commands.txt}
Do Now: TEST-SUITE-TRIAGE-002#11 — Draft the Phase E rerun brief under reports/2026-01-test-suite-refresh/phase_e/$STAMP/ and update docs/fix_plan.md once the brief is written.
If Blocked: Capture the blocker in phase_e_brief.md ("Blocked" section), add the partial artifacts, and log the status in docs/fix_plan.md before exiting.
Priorities & Rationale:
- docs/fix_plan.md:68 calls for a Phase E rerun brief before any new suite execution.
- plans/archive/test-suite-triage-rerun.md:11 records the closure status we must build on.
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-VEC-001.md:32 confirms the remaining monitoring need (transient vectorization failure).
- docs/development/testing_strategy.md:18-34 keeps the command structure and guardrails aligned with policy.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-refresh/phase_e/$STAMP; printf '%s\n' "$STAMP" > reports/2026-01-test-suite-refresh/phase_e/$STAMP/commands.txt.
- Use cat > reports/2026-01-test-suite-refresh/phase_e/$STAMP/phase_e_brief.md to create a brief with sections: Context, Prereqs (env guards, evidence to verify), Proposed Command (guarded pytest tests/ line with timeout/env vars), Artifact Expectations, Follow-ups (full-suite success criteria, who updates fix_plan).
- Reference plans/archive/test-suite-triage-rerun.md Closure Status and the cluster summaries so the brief explicitly links to the Attempt numbers and STAMPs that justify rerun readiness.
- Update docs/fix_plan.md: add an Attempt entry for STAMP $STAMP and flip Next Action 11 from NEXT to ✅ COMPLETE with the brief location; cite key findings in the attempt note.
- Record a short summary in reports/2026-01-test-suite-refresh/phase_e/$STAMP/phase_e_brief.md noting who runs the rerun and what evidence to capture (pytest.log, junit xml, env dumps, timing table) once executed.
Pitfalls To Avoid:
- Do not run pytest or modify production code; this loop is documentation only.
- Keep the brief ASCII-only and reference existing artifacts instead of restating large logs.
- Ensure the rerun command preserves timeout 905s and compile guard env vars.
- Use UTC STAMPs; do not reuse the Phase D directories.
- When editing docs/fix_plan.md, avoid disturbing earlier attempt entries or other initiatives.
Pointers:
- docs/fix_plan.md:68
- plans/archive/test-suite-triage-rerun.md:11
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-VEC-001.md:32
- docs/development/testing_strategy.md:18
Next Up: 1. Once the brief is committed, outline the metrics sheet for the guarded rerun (phase_e/$STAMP/timing.md) before scheduling execution.
