Summary: Execute Sprint 3 (GRAD-001) to isolate the slow-gradient chunk behind an explicit flag/env guard and document the policy.
Focus: docs/fix_plan.md#test-suite-triage-002-full-pytest-rerun-and-triage-refresh — Next Action 23 (Sprint 3 slow-gradient chunk policy)
Branch: feature/spec-based-2
Mapped tests:
- pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability
- pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability --run-slow-gradient-chunk
Artifacts: reports/2026-01-test-suite-refresh/phase_n/<STAMP>/sprint3/
Next Up (optional): Sprint 4 performance tolerance refresh once slow-gradient policy is enforced

Do Now: Follow docs/plans/2026-01-29-sprint3-grad1-plan.md Tasks 1–2 exactly—add the pytest flag/env guard, prove the skip + opt-in runs, capture STAMPed evidence, and update docs/fix_plan.md per the plan while citing docs/development/testing_strategy.md §4.1 and docs/development/pytorch_runtime_checklist.md runtime guidance.
