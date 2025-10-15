Summary: Draft the Phase J guardrails design bundle so collection-time fixtures are fully specified before implementation.
Mode: Docs
Focus: TEST-SUITE-TRIAGE-002 (Next Action 17 — Phase J collection guardrails design package)
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-refresh/phase_j/$STAMP/{analysis/session_fixture_design.md,analysis/gradient_policy_guard.md,analysis/validation_plan.md,notes/open_questions.md}
Do Now: TEST-SUITE-TRIAGE-002#17 — (export STAMP=$(date -u +%Y%m%dT%H%M%SZ); BASE=reports/2026-01-test-suite-refresh/phase_j/$STAMP; mkdir -p $BASE/{analysis,notes}; printenv | sort > $BASE/notes/env_snapshot.txt; cat <<'DOC' > $BASE/analysis/session_fixture_design.md
# Session Infrastructure Fixture (Phase J — Task J1)

## Purpose & Scope

## Preconditions

## Failure Messaging & Remediation Steps

DOC
cat <<'DOC' > $BASE/analysis/gradient_policy_guard.md
# Gradient Policy Guard Fixture (Phase J — Task J2)

## Purpose & Scope

## Environment Checks & Enforcement

## Skip/Xfail Handling

DOC
cat <<'DOC' > $BASE/analysis/validation_plan.md
# Validation Strategy (Phase J — Task J3)

## Targeted Selectors

## Artifact Expectations

## Exit Criteria

DOC
cat <<'DOC' > $BASE/notes/open_questions.md
# Phase J Guardrails — Open Questions

- 

DOC
printf "%s\n" "$STAMP" > $BASE/STAMP.txt)
If Blocked: Capture unresolved design questions in $BASE/notes/open_questions.md (with rationale + owners), note the blocker at the top of each analysis file, and log the partial status in docs/fix_plan.md before exiting.
Priorities & Rationale:
- docs/fix_plan.md:1-20,142-165 elevates Next Action 17 to design the guardrails before the next rerun.
- plans/active/test-suite-triage-phase-h.md:14-64,95-123 defines Phase J tasks (J1–J3) and required deliverables; we need concrete fixture specs before implementation.
- reports/2026-01-test-suite-refresh/phase_h/20251015T171757Z/analysis/infrastructure_gate.md summarises Phase H findings we must carry forward into the fixture design.
- docs/development/testing_strategy.md:20-120 (device/dtype & Do Now policies) ensure fixtures enforce existing guardrails without violating runtime discipline.
How-To Map:
- Populate each analysis/*.md file with detailed prose, pseudocode, and references that satisfy the corresponding plan task (J1–J3); cite specs/arch/testing docs where behavior is defined.
- Update plans/active/test-suite-triage-phase-h.md to record Task J1/J2/J3 status (mark [P]/[D] as appropriate) and capture cross-links to the new STAMP.
- Log Attempt #18 in docs/fix_plan.md with STAMP, summary of guardrail decisions, and explicit follow-up actions for implementation.
- No pytest execution this loop; focus on documentation quality, reproducibility guidance, and ready-to-implement instructions.
Pitfalls To Avoid:
- Do not edit simulator or test code; this loop is planning only.
- Keep STAMP directories immutable after creation; never overwrite an existing STAMP.
- Ensure fixtures respect NB_C_BIN precedence and gradient guard requirements documented in Phase H/I artifacts.
- Avoid hand-waving; provide concrete failure messages, enforcement rules, and reproduction selectors.
- Remember to update both the plan and fix_plan ledger once deliverables are drafted.
- Maintain ASCII-only formatting in all new documentation files.
- Reference authoritative docs (specs/arch/testing_strategy) instead of introducing new conventions.
- Do not run pytest or nb-compare; evidence-only per directive.
- Preserve environment snapshots under notes/ for traceability.
- Keep artifact paths aligned with plans/active expectations (`reports/2026-01-test-suite-refresh/phase_j/$STAMP/`).
Pointers:
- docs/fix_plan.md:142-165
- plans/active/test-suite-triage-phase-h.md:14-123
- reports/2026-01-test-suite-refresh/phase_h/20251015T171757Z/analysis/infrastructure_gate.md
- docs/development/testing_strategy.md:20-180
- arch.md:200-360
Next Up: (1) Translate the approved fixture designs into pytest fixture implementations once documentation clears review.
