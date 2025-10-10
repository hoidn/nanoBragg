Summary: Draft the 4096² validation-path memo to unblock Phase B3.
Mode: Docs
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_b/$STAMP/{validation_path.md,summary.md,commands.txt}
Do Now: [VECTOR-PARITY-001] Draft Phase B3 validation-path memo (document options; no pytest selector yet)
If Blocked: Capture current obstacles in reports/2026-01-vectorization-parity/phase_b/$STAMP/blockers.md and notify galph in docs/fix_plan.md attempts.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md:30 — Phase B3 requires a decision before any further parity evidence.
- docs/fix_plan.md:4016 — Next Actions now hinge on a written validation-path recommendation.
- specs/spec-a-parallel.md:90 — High-resolution AT-012 variant defines required acceptance thresholds.
- tests/test_at_parallel_012.py:364 — Current skip documents missing infrastructure; memo must reference constraints.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-vectorization-parity/phase_b/$STAMP/.
- Summarise prior artifacts (`20251010T030852Z`, `20251010T031841Z`) and spec expectations in validation_path.md; include pros/cons for Options A–C and recommended path with acceptance checklist.
- Record supporting context (commands run, files reviewed) in commands.txt; include the exact pytest selector output reference path rather than rerunning.
- Capture conclusions + open questions in summary.md; update docs/fix_plan.md attempts when done.
Pitfalls To Avoid:
- Do not un-skip or edit tests this loop; documentation only.
- Keep Protected Assets (docs/index.md references) untouched.
- No new benchmark runs; rely on existing artifacts for evidence.
- Avoid inventing tolerances—quote spec values or prior plan guidance.
- Preserve device/dtype neutrality in recommendations.
- Do not spawn subagents without embedding full context per CLAUDE.md if you choose to delegate.
- Avoid editing production code or golden data files.
- Document any blockers immediately rather than guessing missing data.
- Maintain ASCII formatting in new files.
Pointers:
- plans/active/vectorization-parity-regression.md:12
- plans/active/vectorization-parity-regression.md:30
- docs/fix_plan.md:4016
- specs/spec-a-parallel.md:90
- tests/test_at_parallel_012.py:364
Next Up: Phase B4 nb-compare ROI checks once validation-path memo is accepted.
