Summary: Align the Phase H parity evidence with our ledgers and dependent plans (H3/H4).
Mode: Docs
Focus: [SOURCE-WEIGHT-001] Phase H3-H4 ledger propagation
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: doc edits only (docs/fix_plan.md, plans/active/vectorization*.md, docs/bugs/verified_c_bugs.md)
Do Now: [SOURCE-WEIGHT-001] Phase H3-H4 — refresh docs/fix_plan.md, docs/bugs/verified_c_bugs.md, plans/active/vectorization.md, plans/active/vectorization-gap-audit.md, and the VECTOR-TRICUBIC-002 / VECTOR-GAPS-002 / PERF-PYTORCH-004 fix_plan entries so they cite the Phase H memo (`reports/2025-11-source-weights/phase_h/20251010T002324Z/`) and the new parity thresholds (corr ≥0.999, |sum_ratio−1| ≤5e-3).
If Blocked: Leave edit notes in `reports/2025-11-source-weights/phase_h/<STAMP>/ledger_followup.md` explaining which document could not be updated and why; notify supervisor before proceeding elsewhere.
Priorities & Rationale:
- docs/fix_plan.md:4065-4320 — Next Actions still reference Phase H1/H2 and outdated C-PARITY-001 text; needs rewording to highlight ledger/plan propagation.
- plans/active/source-weight-normalization.md:1-120 — Phase table now marks H1/H2 done; downstream docs must agree.
- plans/active/vectorization.md:1-120 — Phase A rows still point at Phase E/G artifacts and lack the Phase H memo/tolerance.
- plans/active/vectorization-gap-audit.md:1-120 — Status snapshot + B1 row reference Phases F–G; update to Phase H evidence path.
- docs/bugs/verified_c_bugs.md:1-160 — confirm no lingering claim that source weights are a C bug; add cross-link to `[C-SOURCEFILE-001]` if needed.
- docs/fix_plan.md entries for VECTOR-TRICUBIC-002, VECTOR-GAPS-002, PERF-PYTORCH-004 — adjust gating language to depend on Phase H memo rather than legacy divergence thresholds.
How-To Map:
- Edit docs/fix_plan.md `[SOURCE-WEIGHT-001]` section: ensure status reflects H1/H2 completion, replace C-PARITY-001 references with the 20251010T002324Z memo, and restate H3/H4 tasks (ledger refresh, plan notifications). Update linked initiative entries (VECTOR-TRICUBIC-002, VECTOR-GAPS-002, PERF-PYTORCH-004) to cite the memo and tolerance.
- Update plans/active/vectorization.md Phase A rows to reference the Phase H memo/test selector and new tolerances; clarify that A2 waits on H3/H4 propagation.
- Update plans/active/vectorization-gap-audit.md status snapshot + B1 guidance to require the Phase H memo (corr ≥0.999, |sum_ratio−1| ≤5e-3) before unblocking profiling.
- Review docs/bugs/verified_c_bugs.md: remove or annotate any mention of source weights under C-PARITY-001; add a note pointing to `[C-SOURCEFILE-001]` for the comment-line defect if context is still needed.
- After edits, run `git diff` to verify only documentation changes. No pytest execution required.
Pitfalls To Avoid:
- Do not alter test code or parity metrics; this loop is ledger/doc only.
- Preserve Rule #11 citations (keep the nanoBragg.c references intact when editing text).
- Leave historical attempts intact; annotate them as superseded rather than deleting content.
- Do not remove references to `[C-SOURCEFILE-001]`; that bug remains active.
- Keep thresholds consistent (corr ≥0.999, |sum_ratio−1| ≤5e-3) across every mention.
- Avoid introducing new report paths; reference the existing 20251010T002324Z bundle.
- Maintain Protected Assets (docs/index.md etc.) untouched.
- Run no full test suites; documentation edits only.
- Keep indentation/table formatting stable to avoid markdown rendering regressions.
Pointers:
- docs/fix_plan.md:4065-4320
- plans/active/source-weight-normalization.md:1-120
- plans/active/vectorization.md:1-120
- plans/active/vectorization-gap-audit.md:1-120
- docs/bugs/verified_c_bugs.md:1-160
Next Up: After ledger propagation, tackle Phase I1 documentation updates (pytorch_design.md / pytorch_runtime_checklist.md) if time permits.
