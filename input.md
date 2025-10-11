Summary: Sprint 0 quick fixes from Phase M0 baseline to retire C1/C3/C4/C5/C7 failures.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py::TestPix0VectorAlias::test_pix0_meters_alias; env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params; env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag; env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution; env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model
Artifacts: reports/2026-01-test-suite-triage/phase_m1/$STAMP/{cli_fixtures,detector_dtype,debug_trace,simulator_api,shape_models,summary.md}
Do Now: [TEST-SUITE-TRIAGE-001] Phase M1a — env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py::TestPix0VectorAlias::test_pix0_meters_alias (after exporting STAMP and preparing phase_m1 dirs)
If Blocked: Capture failing command + traceback to reports/2026-01-test-suite-triage/phase_m1/$STAMP/blocked/pytest.log, append reproduction details to summary.md, and stop before touching other selectors. Ping supervisor via Attempts History.
Priorities & Rationale:
- plans/active/test-suite-triage.md:202 — Sprint 0 checklist defines C1/C3/C4/C5/C7 as immediate burn-down scope.
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:31 — Cluster C1 root cause (missing default_F) reproduces in today’s command.
- docs/fix_plan.md:3 — Active focus escalates Phase M1 quick-fix sprint before MOSFLM remediation.
How-To Map:
- Export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-triage/phase_m1/$STAMP/{cli_fixtures,detector_dtype,debug_trace,shape_models,simulator_api,blocked}; printf "STAMP=%s\n" "$STAMP" > reports/2026-01-test-suite-triage/phase_m1/$STAMP/commands.txt.
- Run the Do Now command with env prefix; tee output to reports/.../phase_m1/$STAMP/cli_fixtures/pytest.log and append exit code to commands.txt.
- If tests pass, stage patches for CLI fixtures, capture git diff to cli_fixtures/diff.patch, and note residual failures in summary.md; proceed to next selector in mapped tests order, routing each log to the matching subdir.
- After all five selectors pass, append aggregate pass/fail counts + remaining suite failures to summary.md and update docs/fix_plan Attempts History before ending loop.
Pitfalls To Avoid:
- Do not run the full pytest suite this loop; stay on mapped selectors only.
- Keep env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE on every command to avoid GPU drift or MKL crashes.
- Reuse the same STAMP for all Phase M1 artifacts; no writes to legacy phase_m0 directories.
- Maintain dtype/device neutrality in Detector fixes (avoid .cpu()/.item()).
- Do not edit Protected Assets (docs/index.md references) during CLI fixture updates.
- Avoid merging unrelated remediation work (C6/C8/C9) until Sprint 0 closes.
- Ensure junit XML expectation changes remain aligned with spec; log any deviations instead of guessing.
Pointers:
- plans/active/test-suite-triage.md:202
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:31
- docs/fix_plan.md:38
Next Up: 1) Phase M1b detector beam-center tensorization; 2) Phase M2 gradient compile guard draft once Sprint 0 selectors are green.
