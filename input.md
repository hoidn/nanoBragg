Summary: Lift the slow-gradient timeout ceiling to 905 s, update the docs, and prove the new guardrail with the guarded chunk‑03 selector.
Mode: Perf
Focus: [TEST-SUITE-TRIAGE-001] Phase R tolerance uplift (R2)
Branch: feature/spec-based-2
Mapped tests: timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability --maxfail=0 --durations=25
Artifacts: reports/2026-01-test-suite-triage/phase_r/$STAMP/tolerance_update/
Do Now: Next Action 16 — Phase R tolerance uplift (R2); run `timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability --maxfail=0 --durations=25`
If Blocked: Capture the failing command output (stdout + exit code) under `reports/2026-01-test-suite-triage/phase_r/$STAMP/tolerance_update/attempt_blocked/` and log the blocker in docs/fix_plan.md Attempts History.
Priorities & Rationale:
- plans/active/test-suite-triage.md:374 — Phase R now requires the timeout uplift before the final ladder capture.
- docs/fix_plan.md:794 — Next Action 16 explicitly calls for the 905 s timeout + doc refresh.
- reports/2026-01-test-suite-triage/phase_r/20251015T091543Z/chunks/chunk_03/summary.md — Evidence that 900.02 s breach creates a false failure.
- docs/development/testing_strategy.md:526 — Update the published performance expectations to match the new ceiling.
- arch.md:376 — Architecture ADR must stay aligned with the tolerance policy.
- docs/development/pytorch_runtime_checklist.md:41 — Runtime guardrail needs the same ceiling to avoid divergence.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `mkdir -p reports/2026-01-test-suite-triage/phase_r/$STAMP/tolerance_update/chunks/chunk_03` before piping logs.
- Edit `tests/test_gradients.py:576` to change `@pytest.mark.timeout(900)` → `@pytest.mark.timeout(905)`.
- Update `docs/development/testing_strategy.md:526-529`, `arch.md:376-379`, and `docs/development/pytorch_runtime_checklist.md:41` to cite the 905 s ceiling with Phase Q (839.14 s) and Phase R (900.02 s) evidence.
- Record the rationale in `reports/2026-01-test-suite-triage/phase_r/$STAMP/tolerance_update/design.md` (include before/after timings and doc references).
- Run `timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_r/$STAMP/tolerance_update/chunks/chunk_03/pytest.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_r/$STAMP/tolerance_update/chunks/chunk_03/pytest.log` and write the exit code to `exit_code.txt`.
- Drop an updated `timing_summary.md` alongside the logs noting observed runtime vs 905 s ceiling.
Pitfalls To Avoid:
- Do not forget `mkdir -p` before piping to `tee`; we already lost a log last attempt.
- Keep `CUDA_VISIBLE_DEVICES=-1` and `NANOBRAGG_DISABLE_COMPILE=1` in place; compile guard is mandatory for gradchecks.
- Do not touch files listed in docs/index.md protected-assets (e.g., loop.sh, input.md path).
- Maintain vectorization—no Python-side loops while editing tests.
- Preserve ASCII formatting and existing doc structure; avoid reflowing unrelated paragraphs.
- Reference Phase Q and Phase R evidence explicitly; no vague "recent run" wording.
- Run only the mapped test; the full suite waits until the ladder rerun step.
- Keep `pytest-timeout` dependency unchanged aside from timeout annotation.
- Avoid editing unrelated tests; only adjust the annotated slow-gradient test.
Pointers:
- plans/active/test-suite-triage.md:374
- docs/fix_plan.md:794
- tests/test_gradients.py:576
- docs/development/testing_strategy.md:526
- arch.md:376
- docs/development/pytorch_runtime_checklist.md:41
- reports/2026-01-test-suite-triage/phase_r/20251015T091543Z/chunks/chunk_03/summary.md
Next Up: When the timeout uplift lands, tackle Next Action 17 (Phase R chunk 03 rerun) with the refreshed roster.
