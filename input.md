Summary: Execute Phase D Task D2 docstring updates for the determinism workstream and capture provenance.
Mode: Docs
Focus: [DETERMINISM-001] PyTorch RNG determinism — Phase D doc integration
Branch: main
Mapped tests: pytest --collect-only -q
Artifacts: reports/determinism-callchain/phase_d/<STAMP>/docs_integration/
Do Now: Carry out Phase D Task D2 (refresh `src/nanobrag_torch/utils/c_random.py` module + `mosaic_rotation_umat()` docstrings) and verify imports with `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q`.
If Blocked: Log findings in `reports/determinism-callchain/phase_d/<STAMP>/docs_integration/blockers.md`, note the blocker in docs/fix_plan.md Attempts, and halt edits for supervisor review.
Priorities & Rationale:
- Phase D2 is the next pending checklist item in plans/active/determinism.md; completing it unblocks the remaining documentation tasks before validation.
- `docs_updates.md` §2.1 enumerates the exact language required, ensuring parity with the C pointer-side-effect contract recorded in Phase B3.
- Keeping provenance under the Phase D docs_integration directory preserves continuity with the new Attempt #8 artifacts.
How-To Map:
- Update `src/nanobrag_torch/utils/c_random.py` module docstring and the `mosaic_rotation_umat()` docstring per `reports/determinism-callchain/phase_c/20251011T052920Z/docs_updates.md` §2.1; include pointer-side-effect commentary and RNG consumption bullets.
- Record commands in `reports/determinism-callchain/phase_d/<STAMP>/docs_integration/commands.txt` (include git status + pytest selector). Capture the pytest output in `collect_only.log` and add file checksums in `sha256.txt` if practical.
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` after edits to confirm imports; no other tests this loop.
Pitfalls To Avoid:
- Keep edits ASCII and avoid modifying production RNG code paths beyond docstrings.
- Preserve existing C-code citations; add new ones only if sourced directly per Rule #11 (no paraphrasing).
- Do not touch Protected Assets named in docs/index.md (including this input file) outside of required updates.
- Maintain device/dtype-neutral language—no CPU-only assumptions in examples.
- Ensure docstrings remain wrapped at sensible lengths and respect existing formatting conventions.
Pointers:
- plans/active/determinism.md — Phase D table (D2 focus)
- reports/determinism-callchain/phase_c/20251011T052920Z/docs_updates.md §2.1 — docstring checklist
- reports/determinism-callchain/phase_d/20251011T054542Z/docs_integration/ — Attempt #8 precedent for artifact layout
Next Up: Phase D Task D3 (augment `arch.md` ADR-05 with the pointer side-effect implementation note).
