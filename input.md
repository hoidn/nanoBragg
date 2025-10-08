Summary: Establish failing tricubic polynomial vectorization tests so Phase D helpers can be implemented under strict spec, parity, and performance guardrails.
Mode: Perf
Focus: VECTOR-TRICUBIC-001 — Phase D polynomial vectorization
Branch: feature/spec-based-2
Mapped tests: none — new tests required
Artifacts: reports/2025-10-vectorization/phase_d/collect.log; reports/2025-10-vectorization/phase_d/pytest_cpu.log; reports/2025-10-vectorization/phase_d/pytest_cuda.log; reports/2025-10-vectorization/phase_d/implementation_notes.md; reports/2025-10-vectorization/phase_d/attempts.yaml
Do Now: VECTOR-TRICUBIC-001 Phase D3 – add polynomial regression tests; after authoring run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly --maxfail=1 -vv (expect failure until D2 lands).
If Blocked: Document the exact failure, command, and environment in reports/2025-10-vectorization/phase_d/notes.md; append an Attempt stub in docs/fix_plan.md with “blocked” status; stop before editing production modules or plan documents.
Priorities & Rationale:
- specs/spec-a-core.md:230-238 requires 4×4×4 tricubic interpolation neighbourhoods.
- specs/spec-a-core.md:595-603 enforces one-time warning and default_F fallback semantics.
- specs/spec-a-parallel.md sections on AT-STR-002 demand parity against C for interpolated structure factors.
- reports/2025-10-vectorization/phase_d/polynomial_validation.md §§2-4 define tensor shapes and denominator guards.
- reports/2025-10-vectorization/phase_d/polynomial_validation.md §9 enumerates candidate tests; align coverage with that list.
- plans/active/vectorization.md Phase D table marks D1 [D] and expects D2-D4 sequencing next.
- docs/development/testing_strategy.md:1.4-1.5 emphasises device/dtype parity and targeted Do Now commands.
- docs/development/pytorch_runtime_checklist.md sections on vectorization and device neutrality codify guardrails for both tests and implementation.
- reports/2025-10-vectorization/phase_c/implementation_notes.md §3 documents gather tensor layout `(B,4,4,4)` to reuse directly.
- docs/architecture/pytorch_design.md §§2.2–2.4 describe broadcast expectations that the new tests should validate.
- CLAUDE Rule #11 demands C-code docstrings quoting `nanoBragg.c:4150-4187`; tests will drive readiness for that insertion.
- docs/fix_plan.md §VECTOR-TRICUBIC-001 captures attempts history and sets expectation for this loop’s evidence.
How-To Map:
- Draft helper `make_polynomial_inputs(device, dtype, batch)` returning `sub_Fhkl`, `h_idx`, `k_idx`, `l_idx`, and `h_frac` per worksheet Table 2.1.
- Use small integer-based tensor values to minimise rounding noise while exercising all indices.
- Add module-level constant `POLY_FIXTURE = torch.tensor([...])` with deterministic data; annotate source referencing worksheet §2.2.
- Introduce `TestTricubicPoly` class scoped to new tests; keep existing gather tests untouched.
- Write `test_polint_matches_scalar_batched` expecting AttributeError or NotImplementedError until D2 adds vectorized helper.
- Write `test_polint_scalar_equivalence_cpu` computing scalar output via list comprehension for baseline comparison.
- Write `test_polin2_matches_scalar_batched` referencing nested interpolation; assert failure message includes helper name for clarity.
- Write `test_polin2_grad_flow` verifying `.grad_fn` presence; mark xfail with strict True if helper missing.
- Write `test_polin3_matches_scalar_batched` comparing full 3D interpolation; assert absence of warnings with recwarn fixture.
- Write `test_polin3_batch_shape_preserved` verifying output shape `(batch,)` even when batched path missing (xfail).
- Write `test_polynomials_support_float64` ensuring dtype override works; skip gracefully if dtype unsupported on CUDA.
- Parameterise over devices using `@pytest.mark.parametrize("device", pytest_helpers.available_devices())` style pattern.
- Parameterise over dtypes `[torch.float32, torch.float64]`; skip float64 on CUDA if hardware lacks support.
- Guard tests with `pytest.importorskip("torch")` and `pytest.importorskip("torch.autograd")` for grad-specific cases.
- Capture collect-only evidence with `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly --collect-only -q` redirected to reports/2025-10-vectorization/phase_d/collect.log.
- Capture failing CPU run with `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly --maxfail=1 -vv | tee reports/2025-10-vectorization/phase_d/pytest_cpu.log`.
- Capture CUDA run if available with `CUDA_VISIBLE_DEVICES=0 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly --maxfail=1 -vv -k cuda | tee reports/2025-10-vectorization/phase_d/pytest_cuda.log`.
- Record environment metadata (Python, torch, CUDA versions) at top of implementation_notes.md to keep evidence reproducible.
- Update reports/2025-10-vectorization/phase_d/implementation_notes.md with sections: Fixture design, Assertion strategy, Expected failure signatures, Device coverage, Follow-on steps.
- Populate reports/2025-10-vectorization/phase_d/attempts.yaml with structured entries (timestamp, command, exit_code, log_path).
- Append Attempt entry in docs/fix_plan.md referencing this evidence, emphasising that Phase D3 scaffolding is ready and D2 should implement helpers next.
- Leave production code untouched this loop; D2 implementation happens after red tests exist.
Evidence Checklist:
- Ensure collect.log includes command, timestamp, and exit status line.
- Ensure pytest_cpu.log captures traceback showing missing helper or assertion mismatch.
- Ensure pytest_cuda.log either captures equivalent failure or documents skip reason clearly.
- Ensure implementation_notes.md lists all new test names with short intent descriptions.
- Ensure attempts.yaml records both CPU and CUDA runs individually.
- Ensure docs/fix_plan.md Attempt entry cites polynomial_validation.md as guidance source.
- Ensure git diff shows only test/report/doc updates; no src/ modifications should appear for this loop.
- Ensure KMP_DUPLICATE_LIB_OK=TRUE environment variable is echoed in logs for audit.
Reporting Steps:
- Add SHA256 checksums for collect.log and pytest logs to implementation_notes.md or a separate hashes.txt file.
- Update reports directory README if one exists to index new artifacts.
- Mention in Attempt log whether gradcheck tests were added but xfailed, including tolerance values.
- Note any skipped device/dtype combinations and articulate rerun conditions.
- Provide pointer to scripts/benchmarks/tricubic_baseline.py for later Phase E comparisons.
- Prepare short summary paragraph for next loop referencing red tests and target helpers (polint, polin2, polin3).
Pitfalls To Avoid:
- Avoid modifying existing gather tests or fixtures.
- Avoid using `.item()` on tensors that participate in gradient flow.
- Avoid large batch sizes that could exhaust GPU memory during future gradchecks.
- Avoid running full pytest suite; stick to targeted selectors per testing_strategy.md.
- Avoid embedding helper implementations inside tests; keep failures pointing at production gaps.
- Avoid silent skips; always explain skip conditions in log or implementation notes.
- Avoid overwriting previous evidence files; include timestamps or append mode when logging.
- Avoid forgetting to set strict=True on xfail markers so accidental passes trigger action.
- Avoid writing CUDA-specific asserts without CPU fallbacks; maintain parity across devices.
- Avoid neglecting dtype neutrality; ensure tests convert fixtures with `.to(device=device, dtype=dtype)` once.
- Avoid forgetting to set torch default dtype back to float32 if modified inside tests.
- Avoid referencing protected files (docs/index.md assets); keep edits scoped to tests/reports/docs.
- Avoid moving plan files; only reference them.
- Avoid skipping documentation updates; record new tests in implementation_notes.md and fix_plan Attempt.
Additional Diagnostics:
- Capture torch.get_default_dtype() inside implementation notes to confirm baseline.
- Record torch.backends.cuda.is_built() result in logs for context.
- Note whether torch.set_float32_matmul_precision is set; may impact future perf checks.
- Include summary of torch.compile status (unused this loop) for completeness.
- Track random seeds used (if any) in attempts.yaml to ensure deterministic behaviour.
Pointers:
- specs/spec-a-core.md:230-238 — Tricubic neighbourhood definition.
- specs/spec-a-core.md:595-603 — OOB warning and fallback rules.
- specs/spec-a-parallel.md (structure-factor parity section) — Acceptance thresholds for tricubic parity.
- reports/2025-10-vectorization/phase_d/polynomial_validation.md §§2-11 — Tensor shapes, broadcast rules, tap points, open questions.
- plans/active/vectorization.md Phase D — Updated status snapshot and remaining tasks D2-D4.
- docs/development/testing_strategy.md:1.4-1.5 — Device/dtype discipline and targeted test policy.
- docs/development/pytorch_runtime_checklist.md — Vectorization and device/dtype guardrails.
- reports/2025-10-vectorization/phase_c/implementation_notes.md §3 — Gather tensor layout and device assertions.
- src/nanobrag_torch/utils/physics.py:315-445 — Scalar polint/polin2/polin3 references for expected behaviour.
- docs/fix_plan.md §VECTOR-TRICUBIC-001 — Attempts history, Next Actions, and context for this loop.
- reports/2025-10-vectorization/phase_a/tricubic_baseline.md — Baseline benchmark numbers for future comparison.
- scripts/benchmarks/tricubic_baseline.py — Command template for Phase E parity/perf validation.
- reports/2025-10-vectorization/phase_d/polynomial_validation.md §11 — Tap-point plan for instrumentation if parity drifts.
- docs/development/pytorch_runtime_checklist.md (Gradcheck section) — Reminder on float64 gradients.
Coordination Notes:
- Flag Ralph’s Attempt entry with Mode=Perf in docs/fix_plan.md for traceability.
- Ensure communication references “VECTOR-TRICUBIC-001 Phase D3” so bookkeeping stays aligned.
- After this loop, expect next supervisor memo to shift Do Now toward D2 implementation and rerun tests.
Next Up: Implement VECTOR-TRICUBIC-001 Phase D2 vectorized polynomials, rerun the newly authored tests on CPU and CUDA, and extend evidence with gradcheck plus microbenchmark metrics.
