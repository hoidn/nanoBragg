Summary: Finish determinism documentation edits and validate the workflow so Sprint 1 can advance.
Mode: Docs
Focus: [DETERMINISM-001] PyTorch RNG determinism
Branch: feature/spec-based-2
Mapped tests: CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py
Artifacts: reports/determinism-callchain/phase_d/<STAMP>/docs_integration/, reports/determinism-callchain/phase_e/<STAMP>/validation/
Do Now: Execute [DETERMINISM-001] Phase D3–D4 doc integration, then Phase E validation using the mapped pytest command above; log commands/env in the new Phase D/Phase E artifact folders.
If Blocked: Capture the failure (command + stderr) under reports/determinism-callchain/blockers/<STAMP>/ and note it in docs/fix_plan.md Attempts before stopping.
Priorities & Rationale:
- docs/fix_plan.md:103 — Next Actions call for finishing Phase D3–D4, then validating.
- plans/active/determinism.md:56 — Phase D guidance spells out ADR/testing_strategy updates.
- reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_sequence.md:47 — Sprint 1.1 hinges on determinism closure.
- reports/determinism-callchain/phase_d/20251011T055456Z/docs_integration/commands.txt — latest docstring attempt; reuse the timestamp pattern.
How-To Map:
- Create fresh UTC stamp (e.g., 20260117THHMMSSZ) under reports/determinism-callchain/phase_d/ and copy template commands.txt + sha256.txt from the 20251011 attempt before editing.
- Edit arch.md ADR-05 to add the pointer-side-effect + LCGRandom parity note (cite docs_updates.md §1.2); keep changes confined to the ADR-05 subsection.
- Update docs/development/testing_strategy.md with a new determinism workflow section (env guards, selectors, artifact expectations) sourced from testing_strategy_notes.md.
- Run git diff to ensure only documentation files changed; stage them, then capture collect-only sanity via `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` (log output in the Phase D folder alongside commands).
- After docs are staged, execute the mapped determinism pytest command with the env guards; store logs, commands, and env snapshot under reports/determinism-callchain/phase_e/<STAMP>/validation/.
- Update docs/fix_plan.md Attempts + Next Actions and plans/active/determinism.md Phase D/E tables with the new stamp before wrapping.
Pitfalls To Avoid:
- Do not touch production code or tests when editing docs.
- Keep Protected Assets (`docs/index.md` references) unchanged.
- Maintain ASCII encoding; avoid fancy punctuation when updating docs.
- Preserve existing ADR numbering and headings in arch.md.
- Ensure env guards in documentation exactly match the command you run.
- Avoid running full pytest suite; only the mapped selectors and collect-only probe are allowed.
- Capture sha256 manifests for each artifact bundle like prior attempts.
- Record Attempt updates in docs/fix_plan.md without dropping existing history.
Pointers:
- docs/fix_plan.md:103
- plans/active/determinism.md:56
- reports/determinism-callchain/phase_c/20251011T052920Z/testing_strategy_notes.md
- reports/determinism-callchain/phase_d/20251011T054542Z/docs_integration/summary.md
- arch.md:85
Next Up: Prep Phase A evidence for [SOURCE-WEIGHT-002] once determinism is closed.
