Summary: Execute Sprint 5 (guarded slow-gradient chunk + full-suite rerun) per docs/plans/2026-01-29-sprint5-suite-plan.md to validate Sprints 1–4 under end-to-end load and log evidence.
Focus: docs/fix_plan.md#test-suite-triage-002-full-pytest-rerun-and-triage-refresh — Next Action 25 (Sprint 5 guarded full-suite validation)
Branch: feature/spec-based-2
Mapped tests:
- timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 NB_RUN_SLOW_GRADIENT=1 pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability --run-slow-gradient-chunk --maxfail=1 --durations=25 --junitxml=reports/2026-01-test-suite-refresh/phase_n/$STAMP/sprint5/artifacts/slow_gradient.junit.xml
- timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905 --durations=25" pytest -vv tests/ --junitxml=reports/2026-01-test-suite-refresh/phase_n/$STAMP/sprint5/artifacts/pytest_full.xml
Artifacts: reports/2026-01-test-suite-refresh/phase_n/$STAMP/sprint5/
Next Up (optional): Phase O rerun with updated fixtures if metrics drift beyond Phase L baseline
