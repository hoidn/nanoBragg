Summary: Execute Sprint 4 (PERF-001) to capture AT-PERF-003 bandwidth evidence, refresh the test threshold, and update the perf policy docs.
Focus: docs/fix_plan.md#test-suite-triage-002-full-pytest-rerun-and-triage-refresh — Next Action 24 (Sprint 4 performance tolerance refresh)
Branch: feature/spec-based-2
Mapped tests:
- env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization --maxfail=1 --durations=25
- env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_at_perf_003.py --maxfail=1 --durations=25
Artifacts: reports/2026-01-test-suite-refresh/phase_n/<STAMP>/sprint4/
Next Up (optional): Guarded full-suite rerun once Sprint 4 closes and docs/fix_plan.md is updated accordingly

Do Now: Follow docs/plans/2026-01-29-sprint4-perf1-plan.md Tasks 1–3 verbatim—capture baseline+stressed bandwidth stats, update `tests/test_at_perf_003.py` with the new ratio constant, refresh docs/development/testing_strategy.md §4 + docs/development/pytorch_runtime_checklist.md, add the durable finding, and log Attempt #26 in docs/fix_plan.md citing the plan and `reports/2026-01-test-suite-refresh/phase_n/<STAMP>/sprint4/` evidence bundle. Reference docs/development/testing_strategy.md §4.1 and docs/development/pytorch_runtime_checklist.md §3 when documenting the policy.
