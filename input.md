Summary: Close SOURCE-WEIGHT Phase I by archiving the initiative cleanly.
Mode: Docs
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-11-source-weights/phase_i/<STAMP>/, plans/archive/source-weight-normalization.md
Do Now: [SOURCE-WEIGHT-001] Correct weighted source normalization — Phase I3; KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q
If Blocked: Capture a fresh <STAMP> directory with collect-only proof and notes on why archival was deferred; log the attempt in docs/fix_plan.md before exiting.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:3-12 — Phase I3 is the only remaining gate after Attempt #39, so finishing the archive unblocks plan closure.
- docs/fix_plan.md:4065-4080 — Ledger still lists Phase I3 as pending; flipping it to done requires the archive packet and galph_memory update.
- specs/spec-a-core.md:146-160 — Normative statement on equal weighting must be cited in the closure summary so future readers see spec alignment.
- docs/development/pytorch_runtime_checklist.md:22-31 — Runtime checklist item #4 should be referenced when summarizing residual guardrails.
How-To Map:
- Export STAMP="$(date -u +%Y%m%dT%H%M%SZ)" and mkdir -p reports/2025-11-source-weights/phase_i/$STAMP. Record all commands in commands.txt and narrative in notes.md under that directory.
- Run KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee reports/2025-11-source-weights/phase_i/$STAMP/collect.log to confirm test discovery remains stable post-doc updates.
- Draft plans/archive/source-weight-normalization.md with a concise context, phase highlights, artifact pointers, and residual risks (cite parity memo + C comment bug).
- Update plans/active/source-weight-normalization.md by moving Phase I3 guidance into the archive file, then remove the active plan file once the archive lands; ensure docs/index.md remains untouched per Protected Assets.
- Edit docs/fix_plan.md to set [SOURCE-WEIGHT-001] status to done, log Attempt #40 with artifact paths, and note remaining dependency on [C-SOURCEFILE-001].
- Append the archival decision to galph_memory.md with links to the archive plan and report stamp.
Pitfalls To Avoid:
- Do not delete or rename assets listed in docs/index.md (Protected Assets rule).
- Avoid touching production code; this loop is documentation-only.
- Keep path references consistent (reports/<year>-11-source-weights/...); no ad-hoc directories.
- When editing docs/fix_plan.md, preserve existing attempts history ordering and markdown tables.
- Ensure STAMP directories stay uncommitted; list them in notes only.
- Maintain correlation thresholds (≥0.999, |sum_ratio−1| ≤5e-3) references exactly as in the parity memo.
- Do not run a full pytest suite; collect-only suffices for doc validation here.
- Keep summary language consistent with specs/spec-a-core.md phrasing on equal weighting.
- Update galph_memory.md once, at the end, to avoid conflicting supervisor notes.
Pointers:
- plans/active/source-weight-normalization.md:1-57
- docs/fix_plan.md:4065-4080
- specs/spec-a-core.md:146-160
- docs/architecture/pytorch_design.md:93-118
- docs/development/pytorch_runtime_checklist.md:22-31
Next Up: Prepare the galph_memory Phase A3 readiness note for VECTOR-TRICUBIC-002 once archival closes.
