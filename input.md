Summary: Close Cluster C3 by keeping detector beam centers as tensors so Phase M1 quick fixes stay on track.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Phase M1 — Sprint 0 Quick Fixes (Cluster C3)
Branch: feature/spec-based-2
Mapped tests: tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params; tests/test_suite.py::TestTier1TranslationCorrectness
Artifacts: reports/2026-01-test-suite-triage/phase_m1/$STAMP/detector_dtype/
Do Now: Execute [TEST-SUITE-TRIAGE-001] Phase M1b and run env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params
If Blocked: Capture the failing log with the same selector under reports/2026-01-test-suite-triage/phase_m1/$STAMP/detector_dtype/baseline.log, note the traceback, and pause.
Priorities & Rationale:
- plans/active/test-suite-triage.md:200-214 keeps Phase M1 ladder authoritative; we must advance M1b now that M1a is done.
- docs/fix_plan.md:30-68 lists Sprint 0 quick fixes as the current critical path with C3 still open.
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:92-122 documents the dtype root cause and the reproduction selector.
- arch.md:317-319 reiterates dtype/device neutrality requirements that this fix must uphold.
- docs/development/testing_strategy.md:31-48 defines the targeted-test cadence we must obey (no full suite yet).
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ) and mkdir -p reports/2026-01-test-suite-triage/phase_m1/$STAMP/detector_dtype/
- env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params 2>&1 | tee reports/2026-01-test-suite-triage/phase_m1/$STAMP/detector_dtype/baseline.log
- Implement the tensor conversion guard in src/nanobrag_torch/models/detector.py per triage guidance; keep conversions device/dtype neutral.
- env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params --maxfail=1 2>&1 | tee reports/2026-01-test-suite-triage/phase_m1/$STAMP/detector_dtype/fix.log
- env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness 2>&1 | tee reports/2026-01-test-suite-triage/phase_m1/$STAMP/detector_dtype/regression.log
- Document before/after type() evidence in reports/2026-01-test-suite-triage/phase_m1/$STAMP/detector_dtype/notes.md and update docs/fix_plan.md Attempts plus remediation_tracker.md with results before requesting review.
Pitfalls To Avoid:
- Do not run the full pytest suite; stay on the mapped selectors.
- Preserve tensor devices/dtypes—no hard-coded .cpu()/.cuda() or float literals without torch.tensor.
- Avoid touching unrelated clusters (C4/C5/C7) until C3 evidence is committed.
- Keep DetectorConfig conversions differentiable; do not call .item() on tensors.
- Record artifacts under the stamped directory before cleaning logs.
- Leave Protected Assets listed in docs/index.md untouched.
- Follow KMP_DUPLICATE_LIB_OK=TRUE in every torch invocation to prevent MKL conflicts.
- Capture before/after type() evidence exactly as the plan requires so we can audit conversions later.
- Update attempts history only after tests pass; otherwise log under Attempts with a BLOCKED note.
Pointers:
- plans/active/test-suite-triage.md:210
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:92-122
- docs/fix_plan.md:30-68
- arch.md:317-319
- docs/development/testing_strategy.md:31-48
Next Up: M1c (debug trace init) once dtype conversion lands and logs are archived.
