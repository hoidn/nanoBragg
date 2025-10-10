Summary: Capture the dtype-cache remediation blueprint so implementation can start with zero discovery.
Mode: Docs
Focus: [DTYPE-NEUTRAL-001] dtype neutrality guardrail
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_c/{remediation_plan.md,tests.md,docs_updates.md}
Do Now: `[DTYPE-NEUTRAL-001]` Phase C blueprint — author the three phase_c docs (no pytest this loop)
If Blocked: Document the blocker in `reports/.../phase_c/<STAMP>/summary.md`, ping supervisor via fix_plan Attempts, and halt further changes.
Priorities & Rationale:
- Phase B already isolated the 4-line fix; Phase C blueprint is the gate before implementation (plans/active/dtype-neutral.md:Status Snapshot).
- docs/fix_plan.md active focus now points to this blueprint; we must clear it to unblock `[DETERMINISM-001]`.
- Phase B summary.md captures the diff; Phase C should translate that into actionable docs for Ralph.
How-To Map:
- Create a fresh timestamped folder under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_c/` (reuse prior naming convention from phase_a/phase_b).
- Write `remediation_plan.md` summarising scope, exact diff (detector.py:762-777), owner, rollback, and sequencing; base it on Phase B `summary.md` and `plans/active/dtype-neutral.md` Phase C table.
- Populate `tests.md` with authoritative commands from Phase B summary (AT-PARALLEL-013/024 reruns, detector geometry smoke); note expected post-fix outcomes and device coverage per testing_strategy §1.5.
- Draft `docs_updates.md` listing the detector cache note (docs/architecture/detector.md:79-88) and runtime checklist entry (docs/development/pytorch_runtime_checklist.md §2), plus any follow-up doc touchpoints.
- Update `docs/fix_plan.md` Attempts (Phase C) once artifacts land; follow the template used for Attempts #0-#2.
Pitfalls To Avoid:
- No production code edits this loop; stay strictly in planning/docs territory.
- Keep artifact paths exact; do not overwrite Phase A/B folders.
- Maintain ASCII text; no fancy formatting beyond markdown headings/lists.
- Reference authoritative docs (specs/spec-a-core.md, detector.md) instead of ad-hoc assumptions.
- Do not run pytest or other heavy commands until implementation phase.
Pointers:
- plans/active/dtype-neutral.md:Status Snapshot/Phase C table
- reports/2026-01-test-suite-triage/phase_d/20251010T173558Z/dtype-neutral/phase_b/summary.md
- docs/architecture/detector.md:79-102 (cache semantics)
- docs/development/testing_strategy.md §1.4-1.5
- docs/development/pytorch_runtime_checklist.md §2
Next Up: Prepare Phase D implementation handoff once blueprint is committed.
