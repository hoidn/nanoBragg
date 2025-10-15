Summary: Capture a guard-friendly chunk 03 baseline by rerunning the shard ladder with the slow gradient tests isolated and timed.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Phase O chunk 03 guard rerun (O5)
Branch: feature/spec-based-2
Mapped tests: tests/test_at_cli_001.py; tests/test_at_flu_001.py; tests/test_at_io_004.py; tests/test_at_parallel_009.py; tests/test_at_parallel_020.py; tests/test_at_perf_001.py; tests/test_at_pre_002.py; tests/test_at_sta_001.py; tests/test_configuration_consistency.py; tests/test_show_config.py; tests/test_gradients.py::TestProperties::test_property_metric_duality; tests/test_gradients.py::TestProperties::test_property_volume_consistency; tests/test_gradients.py::TestProperties::test_property_hkl_consistency; tests/test_gradients.py::TestProperties::test_property_gradient_stability; tests/test_gradients.py::TestLongRunning::test_gradient_flow_simulation
Artifacts: reports/2026-01-test-suite-triage/phase_o/${STAMP}/{commands.txt,summary.md,gradients/,chunks/chunk_03/{pytest_part1.*,pytest_part2.*,pytest_part3a.*,pytest_part3b.*,summary.md}}
Do Now: [TEST-SUITE-TRIAGE-001] Next Action 9 — implement Phase O5a–O5h; after creating the selector shards run `timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part1.txt -k "not gradcheck" --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part1.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part1.log`
If Blocked: Stop immediately, note elapsed time and last test in `${STAMP}/commands.txt`, keep partial logs, and ping supervisor before rerunning or adjusting timeouts.
Priorities & Rationale:
- plans/active/test-suite-triage.md:304-312 drives the four-way shard workflow and timing goals.
- docs/fix_plan.md:38-109 records Attempt #74 fallout and mandates executing O5a–O5h next.
- reports/2026-01-test-suite-triage/phase_o/20251015T041005Z/chunks/chunk_03/summary.md captures the current timeout analysis and expectations for the gradient timings.
- docs/development/testing_strategy.md:70-115 reiterates device/dtype guardrails and targeted pytest practices that apply here.
How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ) && mkdir -p reports/2026-01-test-suite-triage/phase_o/${STAMP}/{gradients,chunks/chunk_03}`
2. `cp reports/2026-01-test-suite-triage/phase_o/20251015T014403Z/grad_guard/{summary.md,exit_code.txt,pytest.xml} reports/2026-01-test-suite-triage/phase_o/${STAMP}/gradients/`
3. Create selectors (one per shard) under `reports/2026-01-test-suite-triage/phase_o/` using the exact module/test lists in the plan: part1, part2, part3a (three property tests), part3b (stability + flow simulation). Document rationale in `${STAMP}/commands.txt`.
4. Run the shard ladder in the same shell (commands listed in Do Now plus):
   - Part2: `timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part2.txt -k "not gradcheck" --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part2.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part2.log`
   - Part3a: `timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part3a.txt --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part3a.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part3a.log`
   - Part3b: `timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part3b.txt --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part3b.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part3b.log`
5. Aggregate counts: run the Python helper from the plan (copy the `python - <<'PY' ... PY` snippet into `${STAMP}/commands.txt`, execute it with `$STAMP` exported, and paste the output into the summary).
6. Update `reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/summary.md` with pass/fail/skip/xfail counts, slowest tests, and a "Gradient Timing" section including wall times for the two slow tests. Refresh `phase_o/${STAMP}/summary.md` accordingly.
7. Once results are complete, relocate the stray grad_guard pytest.xml into the new `${STAMP}/gradients/` directory, then update remediation_tracker/status snapshot per plan O6.
Pitfalls To Avoid:
- Losing `$STAMP` by opening a new shell; keep all commands chained after the initial export.
- Forgetting to set `NANOBRAGG_DISABLE_COMPILE=1`, which will reintroduce gradcheck failures.
- Omitting the new selectors (part3a/part3b) or mis-listing tests; validate each file before running pytest.
- Allowing tee to write outside the `${STAMP}` tree; double-check the paths before executing.
- Skipping per-test timing notes; record the duration for both slow property tests even if they finish quickly.
- Failing to capture junit XML before aggregation; verify files exist before running the helper.
Pointers:
- plans/active/test-suite-triage.md:304-312 for the exact shard definitions and commands.
- docs/fix_plan.md:38-109 for current Next Actions + Attempt #70–#74 context.
- reports/2026-01-test-suite-triage/phase_o/20251015T041005Z/chunks/chunk_03/summary.md for the prior timeout analysis to compare against.
Next Up: Refresh `reports/2026-01-test-suite-triage/remediation_tracker.md` and docs/fix_plan.md (O6) once the shard run produces clean artifacts.
