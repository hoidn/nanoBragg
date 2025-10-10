Summary: Capture dtype-mismatch evidence for `Detector` caches (Phase A A1–A5 of `[DTYPE-NEUTRAL-001]`).
Mode: Parity
Focus: [DTYPE-NEUTRAL-001] dtype neutrality guardrail
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_013.py::TestAT_PARALLEL_013_Determinism::test_pytorch_determinism_same_seed; tests/test_at_parallel_024.py::TestAT_PARALLEL_024_MissetDeterminism::test_pytorch_determinism
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_a/
Do Now: [DTYPE-NEUTRAL-001] dtype neutrality guardrail — run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q`
If Blocked: If collection fails, capture stderr to `reports/.../dtype-neutral/phase_a/collect_failure.log`, rerun with `-vv`, and note the traceback in `summary.md` before proceeding.
Priorities & Rationale:
- plans/active/dtype-neutral.md:12 — Phase A exit criteria require env snapshot + reproductions before any fix design.
- docs/fix_plan.md:534 — Next Actions demand Phase A/B artifacts to unblock determinism plan.
- docs/development/testing_strategy.md:23 — Device/dtype discipline must be documented in `env.json`.
- docs/development/pytorch_runtime_checklist.md:8 — Checklist reiterates dtype neutrality expectations the evidence should verify.
- reports/2026-01-test-suite-triage/phase_d/20251010T171010Z/determinism/phase_a/summary.md — Use prior Attempt #1 format for continuity when drafting the new summary.
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; create `reports/2026-01-test-suite-triage/phase_d/$STAMP/dtype-neutral/phase_a/{at_parallel_013,at_parallel_024}` before running tests.
- After the collect-only run, record environment details with `python scripts/validation/dump_env.py` (or equivalent snippet) into `env.json` capturing Python/Torch/numpy versions, default dtype, CUDA availability, and seed values; cite testing_strategy.md §1.4 in the file header.
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py::TestAT_PARALLEL_013_Determinism::test_pytorch_determinism_same_seed --maxfail=0 --durations=10`, tee stdout/stderr to `.../at_parallel_013/pytest.log`, and extract the RuntimeError snippet into `summary.md` with precise tensor dtypes.
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py::TestAT_PARALLEL_024_MissetDeterminism::test_pytorch_determinism --maxfail=0 --durations=10`, capture output in `.../at_parallel_024/pytest.log`, and note any additional assertions.
- For A4, draft a minimal reproducer: reuse `tests/test_detector_geometry.py` if a dtype toggle test exists; otherwise place a short script `reproduce_dtype_cache.py` under the same `phase_a/` folder that instantiates `Detector` in float32, calls `get_pixel_coords()`, switches to float64, and records the failure stack trace in `trace/dtype_cache.txt`.
- Summarise findings in `phase_a/summary.md` referencing spec citations and highlighting that determinism tests cannot proceed without dtype fix; include table of commands run.
- Update `docs/fix_plan.md` Attempts History for `[DTYPE-NEUTRAL-001]` with Attempt #1 details (command list, artifact path, failure signature).
Pitfalls To Avoid:
- Do not modify production code or existing tests; evidence only.
- Keep every pytest invocation prefixed with `KMP_DUPLICATE_LIB_OK=TRUE`.
- Use UTC stamps consistently; no ad-hoc directory names.
- Store scripts/logs under the designated `dtype-neutral/phase_a/` tree; avoid clutter elsewhere.
- Record exact error text (RuntimeError) and tensor dtypes; no paraphrasing.
- Respect Protected Assets per docs/index.md; avoid touching tracked binaries/scripts.
- Do not run the full test suite; stay within mapped selectors and collect-only.
- If CUDA unavailable, note it explicitly in `env.json` instead of assuming CPU-only.
Pointers:
- plans/active/dtype-neutral.md:1
- docs/fix_plan.md:534
- docs/development/testing_strategy.md:23
- docs/development/pytorch_runtime_checklist.md:8
- src/nanobrag_torch/models/detector.py:720
- reports/2026-01-test-suite-triage/phase_d/20251010T171010Z/determinism/phase_a/summary.md
Next Up: Stage Phase B `analysis.md` skeleton once Phase A artifacts are committed.
