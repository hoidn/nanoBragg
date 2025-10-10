Summary: Draft the Phase C trace plan for the 4096² parity regression, converting Phase C1–C3 into a concrete trace question + tap point checklist.
Mode: Docs
Focus: VECTOR-PARITY-001 / Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_c/<STAMP>/trace_plan.md
Do Now: VECTOR-PARITY-001 Phase C staging — create `reports/2026-01-vectorization-parity/phase_c/$(date -u +%Y%m%dT%H%M%SZ)/trace_plan.md` outlining the trace question, chosen pixel/ROI, instrumentation scope, and tap-point checklist per `plans/active/vectorization-parity-regression.md` Phase C.
If Blocked: Capture the obstacle and any partial notes in `reports/2026-01-vectorization-parity/phase_c/<STAMP>/trace_plan.md` (mark as BLOCKED at top) and log the blocker in fix_plan attempt summary; do not pivot to implementation.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md:52-74 — Phase C tasks demand a trace question and tap-point plan before code instrumentation.
- docs/fix_plan.md:4015-4032 — Next Actions now call for Phase C staging after ROI scope.
- docs/debugging/debugging.md:15-60 — Parallel trace SOP we must follow; plan should cite entry→sink variables.
- specs/spec-a-parallel.md:90-118 — AT-012 ROI thresholds inform pixel/ROI selection for the trace.
- reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/roi_scope.md — Use these findings to justify ROI choice and edge hypotheses.
How-To Map:
- From repo root: `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `OUTDIR=reports/2026-01-vectorization-parity/phase_c/$STAMP`.
- `mkdir -p "$OUTDIR"` then `cat <<'MD' > "$OUTDIR"/trace_plan.md` to draft the document.
- Include sections: **Question & Initiative Context**, **Target ROI & Pixel Selection** (cite ROI metrics), **Instrumentation Scope** (C trace edits + PyTorch script hooks), **Tap Points & Owners**, **Expected Outputs & Storage**, **Open Questions / Risks**.
- Reference spec clauses and plan rows in-line so the supervisor can cross-check easily.
Pitfalls To Avoid:
- Do not start editing production code or instrumentation until the plan is signed off.
- Keep ROI indices in (slow, fast) order; reference central ROI 1792–2304 unless justifying alternatives.
- Cite the exact command templates (C + PyTorch) you expect to run; no ad-hoc args.
- Avoid duplicating large trace logs in git; the plan should refer to future artifact locations only.
- Preserve Protected Assets (`docs/index.md`, `CLAUDE.md`, `input.md`).
- Stay device/dtype neutral in proposed scripts; mention `KMP_DUPLICATE_LIB_OK=TRUE` in plan.
- Note NB_C_BIN precedence (`./golden_suite_generator/nanoBragg`).
- Leave TODOs explicit if something requires supervisor confirmation.
Pointers:
- plans/active/vectorization-parity-regression.md:52-74 — Phase C checklist.
- docs/debugging/debugging.md:21-84 — Trace workflow details.
- docs/development/testing_strategy.md:52-105 — nb-compare + acceptance thresholds.
- reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/roi_scope.md — Latest ROI analysis feeding trace scope.
- docs/development/pytorch_runtime_checklist.md:1-120 — Runtime guardrails to cite in trace plan.
Next Up: Optionally schedule 1024² ROI parity capture to map edge behavior before Phase C instrumentation.
