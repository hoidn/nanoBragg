Summary: Capture the Phase O post-Sprint baseline by rerunning the ten-chunk pytest ladder and updating the tracker with fresh counts.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-001 / Phase O chunked baseline
Branch: feature/spec-based-2
Mapped tests: pytest chunk ladder covering the entire tests/ tree (see How-To Map)
Artifacts: reports/2026-01-test-suite-triage/phase_o/$STAMP/{commands.txt,chunks/chunk_##/pytest.log,chunks/chunk_##/pytest.xml,summary.md}
Do Now: [TEST-SUITE-TRIAGE-001] Phase O chunked baseline — env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_at_abs_001.py tests/test_at_cli_009.py tests/test_at_io_002.py tests/test_at_parallel_007.py tests/test_at_parallel_017.py tests/test_at_parallel_028.py tests/test_at_pol_001.py tests/test_at_src_002.py tests/test_cli_scaling.py tests/test_detector_pivots.py tests/test_physics.py --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_01/pytest.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_01/pytest.log (repeat chunk_02–chunk_10 sequentially per How-To Map)
If Blocked: Capture stdout/stderr plus context in reports/2026-01-test-suite-triage/phase_o/$STAMP/blocked.md and log the blocker in docs/fix_plan.md Attempts History before stopping.
Priorities & Rationale:
- plans/active/test-suite-triage.md:280 — Phase O launches only after C15 validation; chunk ladder is the gate to refresh the baseline (12 failures).
- docs/fix_plan.md:1 — Active Focus now requires the Phase O rerun before any new remediation work.
- reports/2026-01-test-suite-triage/phase_m3/20251015T002610Z/mixed_units/summary.md:1 — Confirms C15 closure and mandates a refreshed suite snapshot.
- docs/development/testing_strategy.md:15 — Enforces environment guards and chunk-first cadence for parity loops.
How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2026-01-test-suite-triage/phase_o/$STAMP/{chunks,logs}`; start logging commands via `tee` into `reports/2026-01-test-suite-triage/phase_o/$STAMP/commands.txt`.
2. For each chunk below, run the command exactly, capturing logs and junit XML (replace `chunk_##` with the matching two-digit index) and record the exit code in `chunks/chunk_##/exit_code.txt`:
```
# chunk_01
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_abs_001.py tests/test_at_cli_009.py tests/test_at_io_002.py \
  tests/test_at_parallel_007.py tests/test_at_parallel_017.py tests/test_at_parallel_028.py \
  tests/test_at_pol_001.py tests/test_at_src_002.py tests/test_cli_scaling.py \
  tests/test_detector_pivots.py tests/test_physics.py \
  --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_01/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_01/pytest.log
# chunk_02
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_bkg_001.py tests/test_at_crystal_absolute.py tests/test_at_io_003.py \
  tests/test_at_parallel_008.py tests/test_at_parallel_018.py tests/test_at_parallel_029.py \
  tests/test_at_pre_001.py tests/test_at_src_003.py tests/test_cli_scaling_phi0.py \
  tests/test_divergence_culling.py tests/test_pivot_mode_selection.py \
  --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_02/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_02/pytest.log
# chunk_03
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py \
  tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py \
  tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py \
  tests/test_gradients.py tests/test_show_config.py \
  --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_03/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_03/pytest.log
# chunk_04
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_002.py tests/test_at_geo_001.py tests/test_at_noise_001.py \
  tests/test_at_parallel_010.py tests/test_at_parallel_021.py tests/test_at_perf_002.py \
  tests/test_at_roi_001.py tests/test_at_str_001.py tests/test_crystal_geometry.py \
  tests/test_mosflm_matrix.py tests/test_suite.py \
  --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_04/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_04/pytest.log
# chunk_05
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_003.py tests/test_at_geo_002.py tests/test_at_parallel_001.py \
  tests/test_at_parallel_011.py tests/test_at_parallel_022.py tests/test_at_perf_003.py \
  tests/test_at_sam_001.py tests/test_at_str_002.py tests/test_custom_vectors.py \
  tests/test_multi_source_integration.py tests/test_trace_pixel.py \
  --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_05/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_05/pytest.log
# chunk_06
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_004.py tests/test_at_geo_003.py tests/test_at_parallel_002.py \
  tests/test_at_parallel_012.py tests/test_at_parallel_023.py tests/test_at_perf_004.py \
  tests/test_at_sam_002.py tests/test_at_str_003.py tests/test_debug_trace.py \
  tests/test_oversample_autoselect.py tests/test_tricubic_vectorized.py \
  --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_06/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_06/pytest.log
# chunk_07
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_005.py tests/test_at_geo_004.py tests/test_at_parallel_003.py \
  tests/test_at_parallel_013.py tests/test_at_parallel_024.py tests/test_at_perf_005.py \
  tests/test_at_sam_003.py tests/test_at_str_004.py tests/test_detector_basis_vectors.py \
  tests/test_parity_coverage_lint.py tests/test_units.py \
  --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_07/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_07/pytest.log
# chunk_08
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_006.py tests/test_at_geo_005.py tests/test_at_parallel_004.py \
  tests/test_at_parallel_014.py tests/test_at_parallel_025.py tests/test_at_perf_006.py \
  tests/test_at_src_001.py tests/test_at_tools_001.py tests/test_detector_config.py \
  tests/test_parity_matrix.py \
  --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_08/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_08/pytest.log
# chunk_09
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_007.py tests/test_at_geo_006.py tests/test_at_parallel_005.py \
  tests/test_at_parallel_015.py tests/test_at_parallel_026.py tests/test_at_perf_007.py \
  tests/test_at_src_002.py tests/test_at_tools_002.py tests/test_detector_offsets.py \
  tests/test_pix0_alias.py tests/test_vectorization_masks.py \
  --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_09/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_09/pytest.log
# chunk_10
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_008.py tests/test_at_geo_007.py tests/test_at_parallel_006.py \
  tests/test_at_parallel_016.py tests/test_at_parallel_027.py tests/test_at_perf_008.py \
  tests/test_at_src_003.py tests/test_at_tools_003.py tests/test_detector_validation.py \
  tests/test_pix0_vector.py tests/test_vectorization_summary.py \
  --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_10/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_10/pytest.log
```
3. After all chunks pass or fail, aggregate counts + durations into `reports/2026-01-test-suite-triage/phase_o/$STAMP/summary.md` (include pass/fail/skipped totals, slowest 25 tests, notable failures) and update `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` and `docs/fix_plan.md` (Attempt #46) with the new baseline.
4. Note any remaining failures (identify cluster IDs) and queue follow-up recommendations in `summary.md` for Phase 1.5 focus.
Pitfalls To Avoid:
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` on every invocation; missing the env var invalidates the run.
- Do not merge chunk command outputs; preserve one log + XML per chunk for diffability.
- Maintain harness runtime <360 s per chunk; if a command threatens the limit, capture partial results and flag in summary.md.
- Avoid editing production code or test tolerances this loop; evidence only.
- Do not overwrite previous phase_m* artifacts; always write to the new Phase O STAMP.
- Capture exit codes even for successes; missing exit_code.txt forces reruns.
- Ensure `--junitxml` paths resolve (directory must exist before invoking pytest).
- If GPU becomes available mid-run, stay on CPU per directive; note the deviation if GPU execution is required.
Pointers:
- plans/active/test-suite-triage.md:20,280
- docs/fix_plan.md:40,48
- reports/2026-01-test-suite-triage/phase_m3/20251015T002610Z/mixed_units/summary.md:1
- docs/development/testing_strategy.md:32
Next Up: After baseline capture, likely pivot to C17 polarization semantics or C18 performance expectation depending on the updated counts.
