Summary: Re-run Phase M0 chunked pytest baseline with env-prefixed commands so the rerun actually executes.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests; chunk_01‒chunk_10 pytest splits (see How-To Map)
Artifacts: reports/2026-01-test-suite-triage/phase_m0/$STAMP/{preflight,commands.txt,chunks/chunk_##/{commands.txt,pytest.log,pytest.xml}}
Do Now: [TEST-SUITE-TRIAGE-001] Full pytest run and triage — Preflight: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/preflight/collect_only.log
If Blocked: If the prefixed command still errors, capture stdout/stderr to phase_m0/$STAMP/preflight/blocked.log, record the failing command + exit code in phase_m0/$STAMP/commands.txt, and ping supervisor before touching chunk_02.
Priorities & Rationale:
- plans/active/test-suite-triage.md:168 — Phase M0 tasks M0a–M0c remain open; runtime guard note now stresses env-prefix + STAMP export.
- docs/fix_plan.md:48, 52 — Attempt #20 logged as blocked because the env assignment split; redo required before MOSFLM remediation can proceed.
- reports/2026-01-test-suite-triage/phase_m0/chunks/chunk_01/pytest.log — Shows `/bin/bash: CUDA_VISIBLE_DEVICES=-1: command not found`; fix by keeping env + pytest on one line.
- docs/development/testing_strategy.md:18 — Maintain CPU-only env and timestamped artifacts for parity evidence.
How-To Map:
- Export STAMP=`date -u +%Y%m%dT%H%M%SZ`; mkdir -p reports/2026-01-test-suite-triage/phase_m0/$STAMP/{preflight,chunks}; :> reports/2026-01-test-suite-triage/phase_m0/$STAMP/commands.txt.
- Record the export in commands.txt: `printf "STAMP=%s\n" "$STAMP" >> reports/2026-01-test-suite-triage/phase_m0/$STAMP/commands.txt`.
- Preflight (M0a): env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/preflight/collect_only.log; append `printf "M0a collect_only exit=%s\n" "$?" >> .../commands.txt`.
- Capture env context: `python - <<'PY' > reports/2026-01-test-suite-triage/phase_m0/$STAMP/preflight/env.txt` followed by:
  ```python
import json, platform, torch
info = {
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_version": torch.version.cuda,
}
print(json.dumps(info, indent=2))
  ```
  and run `python -m pip freeze > reports/2026-01-test-suite-triage/phase_m0/$STAMP/preflight/pip_freeze.txt`.
- For each chunk N in 01..10:
  - mkdir -p reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_NN.
  - Run the command below (single line, note `env` prefix) and tee to chunk_NN/pytest.log; afterward, append the command + exit code + wall time to both chunk_NN/commands.txt and the root commands.txt.
  - Chunk 01: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v --maxfail=0 --durations=5 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_01/pytest.xml tests/test_at_abs_001.py tests/test_at_cli_009.py tests/test_at_io_002.py tests/test_at_parallel_007.py tests/test_at_parallel_017.py tests/test_at_parallel_028.py tests/test_at_pol_001.py tests/test_at_src_002.py tests/test_cli_scaling.py tests/test_detector_pivots.py tests/test_physics.py 2>&1 | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_01/pytest.log
  - Chunk 02: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v --maxfail=0 --durations=5 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_02/pytest.xml tests/test_at_bkg_001.py tests/test_at_crystal_absolute.py tests/test_at_io_003.py tests/test_at_parallel_008.py tests/test_at_parallel_018.py tests/test_at_parallel_029.py tests/test_at_pre_001.py tests/test_at_src_003.py tests/test_cli_scaling_phi0.py tests/test_divergence_culling.py tests/test_pivot_mode_selection.py 2>&1 | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_02/pytest.log
  - Chunk 03: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v --maxfail=0 --durations=5 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_03/pytest.xml tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py tests/test_gradients.py tests/test_show_config.py 2>&1 | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_03/pytest.log
  - Chunk 04: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v --maxfail=0 --durations=5 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_04/pytest.xml tests/test_at_cli_002.py tests/test_at_geo_001.py tests/test_at_noise_001.py tests/test_at_parallel_010.py tests/test_at_parallel_021.py tests/test_at_perf_002.py tests/test_at_roi_001.py tests/test_at_str_001.py tests/test_crystal_geometry.py tests/test_mosflm_matrix.py tests/test_suite.py 2>&1 | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_04/pytest.log
  - Chunk 05: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v --maxfail=0 --durations=5 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_05/pytest.xml tests/test_at_cli_003.py tests/test_at_geo_002.py tests/test_at_parallel_001.py tests/test_at_parallel_011.py tests/test_at_parallel_022.py tests/test_at_perf_003.py tests/test_at_sam_001.py tests/test_at_str_002.py tests/test_custom_vectors.py tests/test_multi_source_integration.py tests/test_trace_pixel.py 2>&1 | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_05/pytest.log
  - Chunk 06: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v --maxfail=0 --durations=5 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_06/pytest.xml tests/test_at_cli_004.py tests/test_at_geo_003.py tests/test_at_parallel_002.py tests/test_at_parallel_012.py tests/test_at_parallel_023.py tests/test_at_perf_004.py tests/test_at_sam_002.py tests/test_at_str_003.py tests/test_debug_trace.py tests/test_oversample_autoselect.py tests/test_tricubic_vectorized.py 2>&1 | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_06/pytest.log
  - Chunk 07: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v --maxfail=0 --durations=5 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_07/pytest.xml tests/test_at_cli_005.py tests/test_at_geo_004.py tests/test_at_parallel_003.py tests/test_at_parallel_013.py tests/test_at_parallel_024.py tests/test_at_perf_005.py tests/test_at_sam_003.py tests/test_at_str_004.py tests/test_detector_basis_vectors.py tests/test_parity_coverage_lint.py tests/test_units.py 2>&1 | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_07/pytest.log
  - Chunk 08: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v --maxfail=0 --durations=5 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_08/pytest.xml tests/test_at_cli_006.py tests/test_at_geo_005.py tests/test_at_parallel_004.py tests/test_at_parallel_014.py tests/test_at_parallel_025.py tests/test_at_perf_006.py tests/test_at_src_001.py tests/test_at_tools_001.py tests/test_detector_config.py tests/test_parity_matrix.py 2>&1 | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_08/pytest.log
  - Chunk 09: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v --maxfail=0 --durations=5 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_09/pytest.xml tests/test_at_cli_007.py tests/test_at_geo_006.py tests/test_at_parallel_005.py tests/test_at_parallel_015.py tests/test_at_parallel_026.py tests/test_at_perf_007.py tests/test_at_src_001_cli.py tests/test_beam_center_offset.py tests/test_detector_conventions.py tests/test_perf_pytorch_005_cudagraphs.py 2>&1 | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_09/pytest.log
  - Chunk 10: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v --maxfail=0 --durations=5 --junitxml=reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_10/pytest.xml tests/test_at_cli_008.py tests/test_at_io_001.py tests/test_at_parallel_006.py tests/test_at_parallel_016.py tests/test_at_parallel_027.py tests/test_at_perf_008.py tests/test_at_src_001_simple.py tests/test_cli_flags.py tests/test_detector_geometry.py tests/test_perf_pytorch_006.py 2>&1 | tee reports/2026-01-test-suite-triage/phase_m0/$STAMP/chunks/chunk_10/pytest.log
- After all chunks finish, parse junit logs (or the pytest output) to tally total passed/failed/skipped counts; write the combined summary to phase_m0/$STAMP/summary.md and start triage_summary.md (even a draft bullet list is fine for this loop).
Pitfalls To Avoid:
- Do not omit the `env` prefix; splitting env vars from the command reproduces the Attempt #20 failure.
- Export a fresh STAMP once and reuse it; never write directly to phase_m0/chunks/.
- Keep `CUDA_VISIBLE_DEVICES=-1` on every invocation; no GPU smoke runs until parity rerun completes.
- Ensure junit XML is emitted for each chunk; a missing file invalidates the attempt.
- Append commands + exit codes immediately after each run to maintain an auditable ledger.
Pointers:
- plans/active/test-suite-triage.md:168-214
- docs/fix_plan.md:48-80, 71-80
- reports/2026-01-test-suite-triage/phase_m0/20251011T152004Z/summary.md
- reports/2026-01-test-suite-triage/phase_m0/chunks/chunk_01/pytest.log:1
Next Up: Once all chunks land, start Phase M0c triage_summary.md before touching MOSFLM remediation.
