Summary: Refresh dependent plans with the new source-weight parity documentation before closing the initiative.
Mode: Docs
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization — Phase I2
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q
Artifacts: reports/2025-11-source-weights/phase_i/<STAMP>/
Do Now: [SOURCE-WEIGHT-001] Correct weighted source normalization — KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q
If Blocked: Capture the blocker analysis in <STAMP>/notes.md, run collect-only anyway, and log a fix_plan Attempt describing why Phase I2 must stay open.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:1-57 — Phase I2 requires propagating the doc updates through dependent ledgers before archival.
- docs/fix_plan.md:4065-4080 — Next Actions list I2/I3; keep the ledger synced with new artifacts.
- docs/architecture/pytorch_design.md:93-116 — New §1.1.5 documents the parity decision; dependent plans must cite it.
- docs/development/pytorch_runtime_checklist.md:22-28 — Runtime guard now encodes equal-weighting rules; ensure plans reference this checklist.
- plans/active/vectorization.md:1-76 & plans/active/vectorization-gap-audit.md:1-58 — Both plans rely on SOURCE-WEIGHT gating; update their status snapshots/Phase A references to include the new documentation sources.
How-To Map:
- Export STAMP="$(date -u +%Y%m%dT%H%M%SZ)" and mkdir -p reports/2025-11-source-weights/phase_i/$STAMP; record commands in commands.txt inside that directory.
- Edit plans/active/vectorization.md (Phase A snapshot/A3 guidance) and plans/active/vectorization-gap-audit.md (dependencies + Phase B1 note) so they cite docs/architecture/pytorch_design.md §1.1.5 and the updated runtime checklist item when referring to SOURCE-WEIGHT parity prerequisites.
- Update docs/fix_plan.md entries [VECTOR-TRICUBIC-002], [VECTOR-GAPS-002], and [PERF-PYTORCH-004] so their Next Actions reference the new documentation paths (pytorch_design.md §1.1.5, runtime checklist item #4) instead of the pre-Phase-I wording.
- Append an Attempt to docs/fix_plan.md [SOURCE-WEIGHT-001] capturing Phase I2 progress (artifacts, commands, doc updates) and note any follow-on requirements for Phase I3.
- Run KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee reports/2025-11-source-weights/phase_i/$STAMP/collect.log after edits to confirm suite importability.
- Summarise the work in reports/2025-11-source-weights/phase_i/$STAMP/notes.md (files touched, rationale, any follow-up) and include parity memo links for audit.
Pitfalls To Avoid:
- No production code edits; keep changes confined to plans and ledgers.
- Maintain the existing phased tables; do not rename or remove Protected Assets listed in docs/index.md.
- Keep parity thresholds (corr ≥0.999, |sum_ratio−1| ≤5e-3) intact when updating text.
- Do not commit the reports/ directory; reference paths only.
- Preserve numbering in pytorch_runtime_checklist.md (item #4 stays the equal-weighting guard).
- Confirm collect-only passes before logging Attempts; capture the command output in the artifact directory.
- Avoid inventing new selectors—cite existing ones from testing_strategy.md.
Pointers:
- plans/active/source-weight-normalization.md:48-57
- docs/fix_plan.md:3766-3782,4065-4080
- docs/architecture/pytorch_design.md:93-116
- docs/development/pytorch_runtime_checklist.md:22-28
- plans/active/vectorization.md:1-76
- plans/active/vectorization-gap-audit.md:1-58
Next Up: Phase I3 archival packet once the dependent plans/fix_plan entries reflect the new documentation.
