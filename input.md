Summary: Land SOURCE-WEIGHT-001 Phase I documentation updates that encode the Phase H parity decision.
Mode: Docs
Focus: [SOURCE-WEIGHT-001] Phase I documentation updates
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-11-source-weights/phase_i/<STAMP>/
Do Now: [SOURCE-WEIGHT-001] Phase I1 — edit docs/architecture/pytorch_design.md, docs/development/pytorch_runtime_checklist.md, and the spec acceptance text so they cite the Phase H memo (corr ≥0.999, |sum_ratio−1| ≤5e-3); capture notes + diffs under reports/2025-11-source-weights/phase_i/<STAMP>/ and finish with NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q.
If Blocked: Write the snag and pending edits to reports/2025-11-source-weights/phase_i/<STAMP>/blockers.md, leave files untouched, and ping supervisor before proceeding elsewhere.
Priorities & Rationale:
- docs/fix_plan.md:4065 — Next Actions now call for Phase I doc propagation keyed to the parity memo.
- plans/active/source-weight-normalization.md:55 — Phase I1 checklist explicitly names the docs to revise.
- docs/bugs/verified_c_bugs.md:169 — Ledger already clarifies C-PARITY-001 scope; documentation must echo the same thresholds.
- plans/active/vectorization.md:14 — Vectorization relaunch waits on SOURCE-WEIGHT docs settling before Phase B refresh.
- plans/active/vectorization-gap-audit.md:14 — Profiling backlog is ready once the documentation patch lands.
How-To Map:
- Create reports/2025-11-source-weights/phase_i/<STAMP>/ (use ISO-like timestamp) and record commands + sha256 in notes.md.
- Update docs/architecture/pytorch_design.md sources/integration section to state equal weighting, cite the 20251010T002324Z memo, and reiterate corr ≥0.999 / |sum_ratio−1| ≤5e-3 thresholds.
- Amend docs/development/pytorch_runtime_checklist.md to include an explicit guardrail item for sourcefile handling and reference the same memo.
- Inspect specs/spec-a-core.md §4; if language already matches, add a short parenthetical pointing to the memo, otherwise align the wording and quote thresholds.
- After edits, run NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q and stash the log in the <STAMP> directory.
- Record git diff snippets or `md5sum` hashes of touched files inside the notes.
Pitfalls To Avoid:
- Do not alter simulator code or tests this loop — documentation only.
- Keep nanoBragg.c quotations intact when adding prose (Rule #11).
- Maintain existing vectorization/device wording; add context without rewriting unrelated sections.
- Preserve ASCII; avoid typographic quotes or unicode dashes.
- Reference the parity memo by path (`reports/2025-11-source-weights/phase_h/20251010T002324Z/`) exactly.
- Do not change docs/index.md or Protected Asset lists in this loop.
- Ensure thresholds stay corr ≥0.999 and |sum_ratio−1| ≤5e-3 everywhere.
- Capture collect-only output after edits; skip full pytest runs.
- Use relative paths in notes; no absolute machine paths.
Pointers:
- docs/fix_plan.md:4065
- plans/active/source-weight-normalization.md:55
- docs/architecture/pytorch_design.md:17
- docs/development/pytorch_runtime_checklist.md:1-120
- specs/spec-a-core.md:140-165
Next Up: Phase I2 — propagate refreshed documentation into dependent ledgers once the edits land.
