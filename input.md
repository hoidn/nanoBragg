Summary: Draft Priority 1 determinism documentation updates and capture provenance for Phase D.
Mode: Docs
Focus: [DETERMINISM-001] PyTorch RNG determinism — Phase D docs integration
Branch: main
Mapped tests: pytest --collect-only -q
Artifacts: reports/determinism-callchain/phase_d/<STAMP>/docs_integration/
Do Now: Carry out Phase D Task D1 (update `docs/architecture/c_function_reference.md` RNG section) and record the change; verify imports with `pytest --collect-only -q` (set `KMP_DUPLICATE_LIB_OK=TRUE`).
If Blocked: Capture a short blocker note in `reports/determinism-callchain/phase_d/<STAMP>/docs_integration/blockers.md` and ping supervisor via docs/fix_plan Attempts.
Priorities & Rationale:
- Phase D Task D1 is the highest-priority doc edit per `plans/active/determinism.md` and blocks closure.
- `docs_updates.md` spells out exact content required; aligning early avoids rework on later doc files.
- Recording provenance under `reports/determinism-callchain/phase_d/` keeps determinism evidence contiguous with prior phases.
How-To Map:
- Edit `docs/architecture/c_function_reference.md` to add the Minimal Standard LCG overview, seed domain table, pointer side-effect warning, and invocation-site table (see `reports/determinism-callchain/phase_c/20251011T052920Z/docs_updates.md` §1.1).
- Log commands and a brief summary to `reports/determinism-callchain/phase_d/<STAMP>/docs_integration/commands.txt`; include file checksums in `sha256.txt` if practical.
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` after edits; store the output in `collect_only.log` inside the same directory.
Pitfalls To Avoid:
- Do not touch Protected Assets (`loop.sh`, `input.md`, files referenced in docs/index.md`).
- Keep doc updates ASCII and cite exact C line ranges (use code fences, no paraphrasing of the C snippet per Rule #11 guidance).
- Avoid altering determinism code paths this loop—docs only.
- Preserve device/dtype neutrality examples; no CPU-only assumptions beyond the documented env guard text.
- Ensure new tables follow existing Markdown style; no HTML tables.
Pointers:
- plans/active/determinism.md — Phase D table (D1–D5)
- reports/determinism-callchain/phase_c/20251011T052920Z/docs_updates.md — Priority 1 checklist
- docs/architecture/pytorch_design.md §1.1.5 — reference for citing source-weight guardrail context
Next Up: Phase D Task D2 (update `src/nanobrag_torch/utils/c_random.py` docstrings) once D1 lands.
