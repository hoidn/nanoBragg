Summary: Execute Sprint 2 (VEC-001) to harden tricubic gather tests against global dtype pollution and document the fix.
Focus: docs/fix_plan.md#test-suite-triage-002-full-pytest-rerun-and-triage-refresh — Next Action 22 (Sprint 2 dtype reset)
Branch: feature/spec-based-2
Mapped tests:
- pytest -vv tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_respects_float32_when_global_dtype_changes
- pytest -vv tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar
- pytest -vv tests/test_tricubic_vectorized.py
Artifacts: plans/active/test-suite-triage-phase-h/reports/20260129T045731Z/
Next Up (optional): Sprint 3 gradient timeout policy once Sprint 2 lands

Do Now: Follow docs/plans/2026-01-29-sprint2-vec1-plan.md Tasks 1–2 exactly—add the regression test + dtype guard, capture the Phase N/STAMP artifacts, and update docs/fix_plan.md when Sprint 2 validation passes. Reference docs/development/testing_strategy.md §1.4 for device/dtype guardrails and cite Phase M cluster mapping when writing dtype_investigation.md.
