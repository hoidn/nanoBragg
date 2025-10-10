Summary: Capture determinism failure evidence for AT-PARALLEL-013/024 under Phase A of the new RNG plan.
Mode: Parity
Focus: [DETERMINISM-001] PyTorch RNG determinism
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_013.py; tests/test_at_parallel_024.py
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/determinism/phase_a/
Do Now: [DETERMINISM-001] PyTorch RNG determinism — run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q`
If Blocked: If pytest collection fails, capture the traceback in `reports/.../phase_a/collect_failure.log` and rerun with `-vv` to narrow scope before proceeding.
Priorities & Rationale:
- plans/active/determinism.md: Phase A tasks require collect-only env snapshot before reproducing failures.
- docs/fix_plan.md:100 calls for Phase A Attempt #1 artifacts prior to advancing triage ladder.
- specs/spec-a-core.md:520 documents seed contracts you must reference when summarising findings.
- specs/spec-a-parallel.md: lines for AT-PARALLEL-013/024 define the acceptance tolerances we need to restate in Phase A summary.
- docs/development/testing_strategy.md:30 enforces device/dtype notes you must include in `env.json`.
- reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/triage_summary.md:59 details the determinism failure cluster; keep its terminology for the summary table.
How-To Map:
- After collect-only run, export commit/dtype/device details into `reports/2026-01-test-suite-triage/phase_d/<STAMP>/determinism/phase_a/env.json` (include torch/numpy versions and `torch.backends.cudnn.deterministic`).
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py --maxfail=0 --durations=10` and store stdout/stderr in `.../at_parallel_013/pytest.log`; note each failing assertion in `summary.md`.
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py --maxfail=0 --durations=10` capturing logs under `.../at_parallel_024/` and record misset angle outputs if printed.
- If a control script exists (`debug_misset_seed.py`), invoke it and capture output; otherwise document the absence explicitly in `summary.md`.
- Update docs/fix_plan.md Attempts History with Attempt #1 once artifacts are in place; include timestamps and failure excerpts.
Pitfalls To Avoid:
- Do not touch production code; evidence run only.
- Maintain `KMP_DUPLICATE_LIB_OK=TRUE` for every pytest invocation.
- Keep timestamps consistent (`date -u +%Y%m%dT%H%M%SZ`) when creating `<STAMP>` directories.
- Ensure artifacts stay under `reports/.../determinism/phase_a/`; no ad-hoc paths.
- Record exact failing assertions and tolerances—do not paraphrase spec language loosely.
- Avoid deleting existing artifacts or golden data (Protected Assets rule).
- No full pytest suite runs this loop; limit to the mapped selectors.
- Preserve default dtype (float64) noted in tests; document if overrides occur.
Pointers:
- plans/active/determinism.md:1
- docs/fix_plan.md:86
- specs/spec-a-core.md:520
- specs/spec-a-parallel.md:1
- tests/test_at_parallel_013.py:1
- tests/test_at_parallel_024.py:1
Next Up: If time remains, queue Phase B callchain variables (analysis_question, initiative_id) in `phase_b/` stub without executing tracing.
