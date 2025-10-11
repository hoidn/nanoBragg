Summary: Make AT-SRC-001 tests dtype-neutral so we can prove the source-weighting cluster is cleared by a full-suite run.
Mode: Parity
Focus: [SOURCE-WEIGHT-002] Simulator source weighting
Branch: feature/spec-based-2
Mapped tests: tests/test_at_src_001_simple.py; tests/test_at_src_001.py; tests/
Artifacts: reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting/
Do Now: [SOURCE-WEIGHT-002] Simulator source weighting — patch dtype-neutral assertions, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py tests/test_at_src_001.py` followed by `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ --maxfail=0 --durations=25`
If Blocked: Capture the failing log under the same $STAMP directory with a notes.md summarising the blocker and stop.
Priorities & Rationale:
- Fix-plan next steps demand dtype-neutral tests before rerunning the suite (`docs/fix_plan.md:155`).
- The active plan marks Phase D2 blocked until that dtype work lands (`plans/active/source-weighting.md:74`).
- Spec AT-SRC-001 enforces equal weighting plus dtype guardrails (`specs/spec-a-core.md:635`).
- Testing strategy mandates authoritative commands and device/dtype discipline for parity verification (`docs/development/testing_strategy.md:44`).
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `outdir=reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting`; `mkdir -p "$outdir" "$outdir/artifacts" "$outdir/env"`.
- After edits, `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py tests/test_at_src_001.py --junitxml "$outdir/artifacts/pytest_targeted.xml" | tee "$outdir/pytest_targeted.log"`.
- Record env snapshot: `python - <<'PY' > "$outdir/env/default_dtype.txt"\nimport torch;print(torch.get_default_dtype())\nPY`; `pip freeze > "$outdir/env/pip_freeze.txt"`.
- Full suite: `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ --maxfail=0 --durations=25 --junitxml "$outdir/artifacts/pytest_full.xml" | tee "$outdir/pytest_full.log"`.
- Update `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md` and tracker files once counts shift; note edits in Attempts History.
Pitfalls To Avoid:
- Do not reintroduce float32 assumptions in tests; derive expectations from actual tensor dtypes.
- Keep Option A semantics (equal weighting, CLI wavelength) intact; no per-weight scaling.
- Avoid bringing back `--maxfail` limits once rerunning the suite; we need full counts.
- Preserve vectorization and device neutrality; no `.cpu()`/`.cuda()` in hot paths.
- Respect Protected Assets list in `docs/index.md`; do not touch those files.
- Capture artifacts under the new $STAMP; do not overwrite earlier Phase D bundles.
- Maintain torch default dtype hygiene in tests using fixtures/context managers, not global side effects.
- Keep Attempt numbering consistent in `docs/fix_plan.md` when logging results.
Pointers:
- `docs/fix_plan.md:155`
- `plans/active/source-weighting.md:74`
- `specs/spec-a-core.md:635`
- `docs/development/testing_strategy.md:44`
Next Up: 1. After D2 succeeds, close Phase D4 (docs/fix_plan.md update + tracker refresh). 2. If time remains, prep `[VECTOR-PARITY-001]` Tap 5.3 instrumentation brief per plan Phase E.
