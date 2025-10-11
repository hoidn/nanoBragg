# Phase K Full Test Suite Execution

## Commands Executed

```bash
export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p reports/2026-01-test-suite-triage/phase_k/$STAMP/{artifacts,logs,analysis,env}
pytest --version
python -m torch.utils.collect_env
timeout 3600 CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_k/$STAMP/artifacts/pytest_full.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_k/$STAMP/logs/pytest_full.log
```

## Runtime
- Start: 2025-10-11 07:29:40 UTC
- End: 2025-10-11 08:00:21 UTC  
- Duration: 1841.28s (30 min 41 s)
- Exit code: 0 (pytest completed, failures present)

## Summary
- **Total tests:** 687 collected (1 skipped during collection)
- **Passed:** 512 (74.5%)
- **Failed:** 31 (4.5%)
- **Skipped:** 143 (20.8%)
- **xfailed:** 2 (expected failures)
- **Warnings:** 6

## Key Improvements vs Phase I (36 failures)
- **Net reduction:** -5 failures (36→31, -13.9% decrease)
- Overall pass rate increased from ~73.8% to 74.5%

## Failed Tests (31 total)
1. test_at_parallel_015.py::test_mixed_units_comprehensive
2. test_at_parallel_026.py::test_triclinic_absolute_peak_position_vs_c
3-5. test_at_src_001.py (3 failures - source weighting)
6. test_at_src_001_simple.py::test_sourcefile_parsing
7-8. test_at_str_003.py (2 failures - lattice shape models)
9. test_at_tools_001.py::test_script_integration
10-11. test_cli_flags.py (2 failures - pix0 override, HKL roundtrip)
12-15. test_debug_trace.py (4 failures - debug flags)
16-17. test_detector_config.py (2 failures - initialization)
18. test_detector_conventions.py::test_denzo_beam_center_mapping
19-20. test_detector_pivots.py (2 failures)
21. test_gradients.py::test_gradient_flow_simulation
22-24. test_perf_pytorch_005_cudagraphs.py (3 failures)
25-29. test_suite.py (5 failures - legacy tests)
30-31. test_tricubic_vectorized.py (2 failures)

## Artifacts Generated
- Junit XML: reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/artifacts/pytest_full.xml
- Full log: reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/logs/pytest_full.log
- Environment: reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/env/torch_env.txt
- Commands: reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/commands.txt

