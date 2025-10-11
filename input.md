Summary: Implement Option A Phase C fixes for source-file parsing and acceptance tests.
Mode: Parity
Focus: [SOURCE-WEIGHT-002] Simulator source weighting
Branch: feature/spec-based-2
Mapped tests: tests/test_at_src_001_simple.py::test_sourcefile_dtype_propagation; tests/test_at_src_001.py
Artifacts: reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/{commands.txt,pytest_simple.log,pytest_full.log,source.py.diff,test_at_src_001.py.diff,summary.md}
Do Now: Phase C1–C3 — add the dtype regression test, confirm it fails, implement the parser dtype fix + AT-SRC-001 expectation updates, then rerun `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py tests/test_at_src_001.py` (capture stdout/stderr in the artifact bundle).
If Blocked: Write blockers.md under the `<STAMP>/source_weighting/` directory outlining the obstacle and updated reproduction command, then halt for supervisor review.
Priorities & Rationale:
- plans/active/source-weighting.md:55-79 — Phase C table lists parser dtype fix, regression test, and AT-SRC-001 alignment as the next gated tasks.
- docs/fix_plan.md:154-212 — `[SOURCE-WEIGHT-002]` Next Actions now call for Phase C1–C3 execution and Phase C artifact logging.
- reports/2026-01-test-suite-triage/phase_j/20251011T062955Z/source_weighting/semantics.md — Option A decision keeps equal weighting; only dtype/test updates are required.
- specs/spec-a-core.md:142-166 — authoritative statement that file λ/weights are ignored; tests must match this behaviour.
- docs/architecture/pytorch_design.md:95-116 — documents equal-weight source handling; reinforce vectorized path while editing parser/tests.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2026-01-test-suite-triage/phase_j/$STAMP/source_weighting` and log every command to `commands.txt` (append with `tee -a`).
- Implement Phase C1: adjust `src/nanobrag_torch/io/source.py` signature to `dtype: Optional[torch.dtype] = None`, default via `torch.get_default_dtype()`, ensure all tensor constructions use the resolved dtype/device; avoid `.cpu()`/`.numpy()`.
- Implement Phase C2: add `test_sourcefile_dtype_propagation` in `tests/test_at_src_001_simple.py` (parametrise over float32/float64/None); run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py::test_sourcefile_dtype_propagation` before the fix to confirm the failure, recording output to `pytest_simple.log` (expected fail message documents baseline).
- Implement Phase C3: update `tests/test_at_src_001.py` docstrings and wavelength assertions so both sources use CLI λ (6.2e-10) while weights remain read-only; cite spec lines in comments.
- After code + test edits land, run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py tests/test_at_src_001.py` and store stdout/stderr in `pytest_full.log`; expected result is 8/8 passing.
- Save `git diff src/nanobrag_torch/io/source.py > source.py.diff` and `git diff tests/test_at_src_001*.py > test_at_src_001.py.diff`; summarise outcomes in `summary.md` (include pass counts, runtime, dtype evidence).
Pitfalls To Avoid:
- Do not introduce per-source weighting or λ usage; Option A keeps equal weighting semantics.
- Maintain tensor device neutrality (`device` argument already supplied by caller); no implicit CPU allocations.
- Preserve vectorization; avoid Python loops when adjusting normalization.
- Keep new regression test deterministic (no random seeds, no device-specific asserts beyond dtype equality).
- Ensure new warnings/errors are not silenced; fail fast if pytest still reports dtype mismatches.
- Reference spec sections in test comments; avoid duplicating semantics prose elsewhere.
- Update docs/fix_plan Attempts once artifacts are archived; include `<STAMP>` in the note.
- Retain Protected Assets (docs/index.md references) untouched.
Pointers:
- plans/active/source-weighting.md:55-79
- docs/fix_plan.md:154-212
- reports/2026-01-test-suite-triage/phase_j/20251011T062955Z/source_weighting/semantics.md
- specs/spec-a-core.md:142-166
- docs/architecture/pytorch_design.md:95-116
Next Up: Prepare Phase D documentation diff (spec text + runtime checklist) once targeted tests pass.
