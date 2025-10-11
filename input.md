Summary: Deliver `[SOURCE-WEIGHT-002]` Phase B semantics brief + design so Sprint 1.2 can advance to implementation.
Mode: Docs+Parity
Focus: [SOURCE-WEIGHT-002] Simulator source weighting
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/{semantics.md,implementation_map.md,verification_checklist.md,env.json}
Do Now: Execute `[SOURCE-WEIGHT-002]` Phase B tasks B1–B4 — create the semantics/design artifact bundle under a fresh `<STAMP>` in `reports/2026-01-test-suite-triage/phase_j/` (no pytest run this loop; planning deliverables only).
If Blocked: Capture an interim blockers.md in the `<STAMP>` directory summarising what prevented the brief and note the dependency in docs/fix_plan.md Attempts; stop for supervisor review.
Priorities & Rationale:
- docs/fix_plan.md:5-7,160-175 — Sprint 1.2 now requires the Phase B semantics brief before code edits.
- plans/active/source-weighting.md:32-87 — Phase B table defines B1–B4 deliverables needed to unlock implementation.
- specs/spec-a-core.md:142-210 — authoritative sourcefile semantics that must be reconciled with AT-SRC-001 expectations.
- tests/test_at_src_001.py:1-230 — current acceptance criteria demonstrating the required per-source weight/λ behaviour.
- docs/architecture/pytorch_design.md:95-116 — existing equal-weight assumption we must revisit in the design brief.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2026-01-test-suite-triage/phase_j/$STAMP/source_weighting`.
- Capture env snapshot for traceability: `python -m platform` info, `torch.__version__`, and current git SHA into `env.json` inside the new directory.
- Draft `semantics.md` covering spec text vs test behaviour, proposed resolution, and any spec amendment notes; cite exact line numbers.
- Create `implementation_map.md` outlining modules/files to touch (io/source.py, BeamConfig, simulator) with current line anchors and guardrails (vectorization, dtype neutrality, differentiability).
- Write `verification_checklist.md` enumerating targeted pytest selectors, gradient checks, documentation updates, and artifact expectations for Phases C/D.
- Update plans/active/source-weighting.md status section if new insights arise; log the artifact paths + key decisions in Attempt history when reporting back.
Pitfalls To Avoid:
- Do not modify production code or tests yet; this loop is planning only.
- Keep all new docs ASCII and reference authoritative spec sections directly.
- Respect Protected Assets (docs/index.md); do not relocate input.md/loop.sh.
- Ensure dtype/device guidance aligns with runtime guardrails (no `.cpu()`/`.cuda()` shortcuts in proposals).
- Avoid inventing new scripts; place artifacts under the prescribed reports path.
- Include concrete file:line anchors for planned code edits; avoid vague directives.
- Note spec contradictions explicitly; do not silently overwrite the current contract.
Pointers:
- plans/active/source-weighting.md:32-87
- docs/fix_plan.md:160-175
- specs/spec-a-core.md:142-210
- docs/architecture/pytorch_design.md:95-116
- tests/test_at_src_001_simple.py:1-60
Next Up: Once Phase B artifacts are committed, proceed to Phase C implementation tasks (C1–C3) with targeted pytest selectors.
