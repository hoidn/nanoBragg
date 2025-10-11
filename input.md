Summary: Capture Phase M2 chunked rerun results so we can finish TEST-SUITE-TRIAGE-001 Phase M handoff.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-001 / Phase M2 chunk rerun
Branch: feature/spec-based-2
Mapped tests: pytest subsets per Phase M0 chunk ladder (chunks 01-10)
Artifacts: reports/2026-01-test-suite-triage/phase_m/$STAMP/{commands.txt,chunks/,summary.md}
Do Now: [TEST-SUITE-TRIAGE-001] Phase M2 chunk rerun — run `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_abs_001.py tests/test_at_cli_009.py tests/test_at_io_002.py tests/test_at_parallel_007.py tests/test_at_parallel_017.py tests/test_at_parallel_028.py tests/test_at_pol_001.py tests/test_at_src_002.py tests/test_cli_scaling.py tests/test_detector_pivots.py tests/test_physics.py --maxfail=0 --durations=25 --junitxml="reports/2026-01-test-suite-triage/phase_m/$STAMP/chunks/chunk_01/pytest.xml" | tee "reports/2026-01-test-suite-triage/phase_m/$STAMP/chunks/chunk_01/pytest.log"` after defining $STAMP as below, then continue through the ladder.
If Blocked: Run `pytest --collect-only -q tests/test_at_abs_001.py` and log to `reports/2026-01-test-suite-triage/phase_m/$STAMP/blocked_collect_only.log`, then update docs/fix_plan.md Attempts with the blocker summary.
Priorities & Rationale:
- plans/active/test-suite-triage.md:256 — M2 now mandates the 10-chunk ladder to satisfy the 600 s harness limit.
- docs/fix_plan.md:48 — Next Actions promote the Phase M2 chunk rerun as the top blocker before tracker updates.
- reports/2026-01-test-suite-triage/phase_m/20251011T191757Z/blocked.md:1 — Attempt #34 timed out at 600 s, confirming the single-command approach is infeasible.
- docs/development/testing_strategy.md:30 — Supervisor handoffs must cite authoritative pytest selectors and guardrails.
- docs/development/testing_strategy.md:373 — Execution requires `KMP_DUPLICATE_LIB_OK=TRUE` for PyTorch.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
- base=reports/2026-01-test-suite-triage/phase_m/$STAMP
- mkdir -p "$base"/chunks/{chunk_01,chunk_02,chunk_03,chunk_04,chunk_05,chunk_06,chunk_07,chunk_08,chunk_09,chunk_10}
- touch "$base"/commands.txt
- For each command below: run it verbatim, note `$?`, and append a line `chunk_0N exit=<code>` to "$base"/commands.txt before moving to the next chunk.
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_abs_001.py tests/test_at_cli_009.py tests/test_at_io_002.py tests/test_at_parallel_007.py tests/test_at_parallel_017.py tests/test_at_parallel_028.py tests/test_at_pol_001.py tests/test_at_src_002.py tests/test_cli_scaling.py tests/test_detector_pivots.py tests/test_physics.py --maxfail=0 --durations=25 --junitxml="$base/chunks/chunk_01/pytest.xml" | tee "$base/chunks/chunk_01/pytest.log"
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_bkg_001.py tests/test_at_crystal_absolute.py tests/test_at_io_003.py tests/test_at_parallel_008.py tests/test_at_parallel_018.py tests/test_at_parallel_029.py tests/test_at_pre_001.py tests/test_at_src_003.py tests/test_cli_scaling_phi0.py tests/test_divergence_culling.py tests/test_pivot_mode_selection.py --maxfail=0 --durations=25 --junitxml="$base/chunks/chunk_02/pytest.xml" | tee "$base/chunks/chunk_02/pytest.log"
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py tests/test_gradients.py tests/test_show_config.py --maxfail=0 --durations=25 --junitxml="$base/chunks/chunk_03/pytest.xml" | tee "$base/chunks/chunk_03/pytest.log"
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_002.py tests/test_at_geo_001.py tests/test_at_noise_001.py tests/test_at_parallel_010.py tests/test_at_parallel_021.py tests/test_at_perf_002.py tests/test_at_roi_001.py tests/test_at_str_001.py tests/test_crystal_geometry.py tests/test_mosflm_matrix.py tests/test_suite.py --maxfail=0 --durations=25 --junitxml="$base/chunks/chunk_04/pytest.xml" | tee "$base/chunks/chunk_04/pytest.log"
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_003.py tests/test_at_geo_002.py tests/test_at_parallel_001.py tests/test_at_parallel_011.py tests/test_at_parallel_022.py tests/test_at_perf_003.py tests/test_at_sam_001.py tests/test_at_str_002.py tests/test_custom_vectors.py tests/test_multi_source_integration.py tests/test_trace_pixel.py --maxfail=0 --durations=25 --junitxml="$base/chunks/chunk_05/pytest.xml" | tee "$base/chunks/chunk_05/pytest.log"
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_004.py tests/test_at_geo_003.py tests/test_at_parallel_002.py tests/test_at_parallel_012.py tests/test_at_parallel_023.py tests/test_at_perf_004.py tests/test_at_sam_002.py tests/test_at_str_003.py tests/test_debug_trace.py tests/test_oversample_autoselect.py tests/test_tricubic_vectorized.py --maxfail=0 --durations=25 --junitxml="$base/chunks/chunk_06/pytest.xml" | tee "$base/chunks/chunk_06/pytest.log"
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_005.py tests/test_at_geo_004.py tests/test_at_parallel_003.py tests/test_at_parallel_013.py tests/test_at_parallel_024.py tests/test_at_perf_005.py tests/test_at_sam_003.py tests/test_at_str_004.py tests/test_detector_basis_vectors.py tests/test_parity_coverage_lint.py tests/test_units.py --maxfail=0 --durations=25 --junitxml="$base/chunks/chunk_07/pytest.xml" | tee "$base/chunks/chunk_07/pytest.log"
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_006.py tests/test_at_geo_005.py tests/test_at_parallel_004.py tests/test_at_parallel_014.py tests/test_at_parallel_025.py tests/test_at_perf_006.py tests/test_at_src_001.py tests/test_at_tools_001.py tests/test_detector_config.py tests/test_parity_matrix.py --maxfail=0 --durations=25 --junitxml="$base/chunks/chunk_08/pytest.xml" | tee "$base/chunks/chunk_08/pytest.log"
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_007.py tests/test_at_geo_006.py tests/test_at_parallel_005.py tests/test_at_parallel_015.py tests/test_at_parallel_026.py tests/test_at_perf_007.py tests/test_at_src_001_cli.py tests/test_beam_center_offset.py tests/test_detector_conventions.py tests/test_perf_pytorch_005_cudagraphs.py --maxfail=0 --durations=25 --junitxml="$base/chunks/chunk_09/pytest.xml" | tee "$base/chunks/chunk_09/pytest.log"
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_008.py tests/test_at_io_001.py tests/test_at_parallel_006.py tests/test_at_parallel_016.py tests/test_at_parallel_027.py tests/test_at_perf_008.py tests/test_at_src_001_simple.py tests/test_cli_flags.py tests/test_detector_geometry.py tests/test_perf_pytorch_006.py --maxfail=0 --durations=25 --junitxml="$base/chunks/chunk_10/pytest.xml" | tee "$base/chunks/chunk_10/pytest.log"
```
- After all chunks, summarise totals vs Attempt #34 and Phase K in "$base"/summary.md" (include pass/fail/skip counts, slowest cases, notable deltas).
- Copy Attempt #34 partial log reference into summary (`reports/.../blocked.md`) and note any new failures or timeouts.
- Update docs/fix_plan.md Attempts and `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md` with the new counts once the chunk rerun completes.
Pitfalls To Avoid:
- Do not re-run the single-command full suite; it will time out at 600 s.
- Keep env vars on the same line as pytest; splitting them reproduces the `CUDA_VISIBLE_DEVICES=-1: command not found` error (Attempt #20).
- Ensure each chunk writes logs under the matching chunk directory and uses the shared STAMP.
- Record exit codes immediately; missing entries break post-run analysis.
- Avoid rerunning only failing chunks unless explicitly instructed; capture all ten for parity.
- Leave prior phase_m0 artifacts untouched; new work must live under the fresh STAMP.
- Stay evidence-only (no code edits, no cleanup of protected assets listed in docs/index.md).
- If a chunk crashes mid-run, stop and document before proceeding to the next chunk.
- Keep CPU execution (`CUDA_VISIBLE_DEVICES=-1`) to match existing baselines.
Pointers:
- plans/active/test-suite-triage.md:248
- docs/fix_plan.md:38
- docs/fix_plan.md:48
- reports/2026-01-test-suite-triage/phase_m/20251011T191757Z/blocked.md:1
- docs/development/testing_strategy.md:30
- docs/development/testing_strategy.md:373
Next Up: After chunk rerun succeeds, sync tracker/analysis (phase_k summary + remediation_tracker) and draft Phase M3c mixed-units hypotheses.
