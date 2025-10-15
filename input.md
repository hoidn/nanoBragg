Summary: Re-run the C18 slow gradient test to verify the 845.68 s baseline before raising the timeout.
Mode: Perf
Focus: TEST-SUITE-TRIAGE-001 / Next Action 12 — C18 validation rerun
Branch: feature/spec-based-2
Mapped tests: tests/test_gradients.py::TestAdvancedGradients::test_property_gradient_stability
Artifacts: reports/2026-01-test-suite-triage/phase_p/$STAMP/chunk_03_rerun/
Do Now: STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-triage/phase_p/$STAMP/chunk_03_rerun && timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestAdvancedGradients::test_property_gradient_stability --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_p/$STAMP/chunk_03_rerun/pytest.xml | tee reports/2026-01-test-suite-triage/phase_p/$STAMP/chunk_03_rerun/pytest.log
If Blocked: If the run hits timeout, stop immediately, capture the partial log + exit status in the same directory, and append a blockers.md summarising elapsed time and visible stack traces.
Priorities & Rationale:
- docs/fix_plan.md:3 — Active focus now requires executing the C18 validation rerun before altering tolerances.
- plans/active/test-suite-triage.md:346 — Phase P table marks P3 done and calls for §4/§5 validation steps next.
- reports/2026-01-test-suite-triage/phase_p/20251015T060354Z/c18_timing.md:15 — Validation plan specifies reusing the guard environment and 900 s target.
- docs/development/testing_strategy.md:513 — Gradient tests must run with NANOBRAGG_DISABLE_COMPILE=1 and capture evidence under controlled envs.
How-To Map:
- Export STAMP as above before running commands so artifacts live under a unique timestamp.
- After pytest completes, run `python --version > reports/2026-01-test-suite-triage/phase_p/$STAMP/chunk_03_rerun/env_python.txt`, `pip list | grep torch > .../env_torch.txt`, and `lscpu | grep "Model name" > .../env_cpu.txt` to log the environment.
- Extract the reported duration with `grep -i "test_property_gradient_stability" .../pytest.log | grep -oP '\\d+\\.\\d+s' | tee .../timing.txt`.
- Record a brief narrative in `reports/2026-01-test-suite-triage/phase_p/$STAMP/chunk_03_rerun/summary.md` noting runtime, pass/fail, and comparison to 845.68 s baseline.
Pitfalls To Avoid:
- Do not skip the guard env vars; the compile guard is mandatory for gradient timing.
- Stay within evidence scope: no tolerance edits or pytest.ini changes yet.
- Keep the run CPU-only (CUDA_VISIBLE_DEVICES=-1) to match the baseline.
- Avoid overwriting the Phase O artifacts; all new files must sit under the fresh STAMP path.
- Refrain from broad pytest selectors; only the targeted test should run this loop.
- Capture exit status even on timeout (write it to exit_code.txt) for traceability.
- Confirm STAMP export succeeded before launching pytest to prevent writing into root.
- Do not delete or move files referenced in docs/index.md (protected assets rule).
Pointers:
- docs/fix_plan.md:3
- plans/active/test-suite-triage.md:346
- reports/2026-01-test-suite-triage/phase_p/20251015T060354Z/c18_timing.md:15
- docs/development/testing_strategy.md:513
Next Up: If runtime stays ≤900 s, implement the pytest.ini slow gradient marker and rerun all four chunk 03 shards.
