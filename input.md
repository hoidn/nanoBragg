Summary: Roll out the C18 slow-gradient timeout marker so Phase Q can close the tolerance cluster.
Mode: Perf
Focus: TEST-SUITE-TRIAGE-001 / Next Action 13 — Phase Q tolerance rollout
Branch: feature/spec-based-2
Mapped tests: tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability
Artifacts: reports/2026-01-test-suite-triage/phase_q/$STAMP/
Do Now: STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-triage/phase_q/$STAMP && python -m pip show pytest-timeout > reports/2026-01-test-suite-triage/phase_q/$STAMP/precheck.md; after applying Phase Q Q2–Q3 edits to pyproject.toml and tests/test_gradients.py, timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_q/$STAMP/chunk_03_part3b.xml | tee reports/2026-01-test-suite-triage/phase_q/$STAMP/chunk_03_part3b.log
If Blocked: If `python -m pip show pytest-timeout` fails, stop and log the output plus a brief note in reports/2026-01-test-suite-triage/phase_q/$STAMP/precheck.md before touching configs; ping supervisor for dependency guidance.
Priorities & Rationale:
- docs/fix_plan.md:5 — Active focus now requires executing the pytest.ini marker rollout to retire C18.
- plans/active/test-suite-triage.md:357 — Phase Q table defines Q1–Q3 as the immediate work before rerunning chunk 03.
- reports/2026-01-test-suite-triage/phase_p/20251015T060354Z/c18_timing.md:15 — Option A mandates a slow-gradient marker with 900 s tolerance.
- reports/2026-01-test-suite-triage/phase_p/20251015T061848Z/chunk_03_rerun/summary.md:21 — Validation rerun confirmed the baseline and green-lit implementation.
- pyproject.toml:48 — Existing pytest markers section needs the new timeout defaults documented in Phase Q.
How-To Map:
- Set STAMP once and reuse it for every artifact path in this loop. Keep all new files under reports/2026-01-test-suite-triage/phase_q/$STAMP/.
- Capture the plugin audit via `python -m pip show pytest-timeout`; append a short sentence noting whether the package is installed.
- Update pyproject.toml markers/timeouts per Phase Q Q2, then add the `@pytest.mark.slow_gradient(timeout=900)` (or equivalent) decorator above `tests/test_gradients.py:574`.
- After edits, run the targeted pytest command with the guard env vars; on success, copy the duration string into chunk_03_part3b_timing.txt alongside the log and XML.
- Draft reports/2026-01-test-suite-triage/phase_q/$STAMP/config_update.md that lists the edited files, key diff points, and references to c18_timing.md §5.1.
Pitfalls To Avoid:
- Do not drop the existing `slow` marker; add the new entry without rewriting the list ordering.
- Keep the test CPU-only (CUDA_VISIBLE_DEVICES=-1) and leave compile guard enabled.
- Avoid broad pytest selectors; only run the single target until docs are updated.
- Document plugin absence before installing anything—supervisor must approve dependency changes.
- Note the new marker in code comments sparingly; rely on docs updates later.
- Preserve ASCII; no fancy Unicode in config files or docs.
- Do not touch docs/development/testing_strategy.md yet—Phase Q Q4 will handle docs in the next loop.
- Respect protected assets listed in docs/index.md.
- After pytest, record exit status in reports/2026-01-test-suite-triage/phase_q/$STAMP/chunk_03_part3b_exit_code.txt.
Pointers:
- docs/fix_plan.md:1
- plans/active/test-suite-triage.md:357
- reports/2026-01-test-suite-triage/phase_p/20251015T060354Z/c18_timing.md:15
- reports/2026-01-test-suite-triage/phase_p/20251015T061848Z/chunk_03_rerun/summary.md:21
- pyproject.toml:48
- tests/test_gradients.py:574
Next Up: After the marker lands and the targeted test passes, refresh docs (Phase Q Q4) and rerun all chunk 03 shards (Q5) before closing C18 in the tracker.
