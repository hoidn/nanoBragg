Summary: Capture the guarded chunked pytest run so we can close out TEST-SUITE-TRIAGE-001 with a zero-failure baseline.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-001 / Next Action 16 – Phase R guarded full-suite closure
Branch: feature/spec-based-2
Mapped tests: chunk ladder (chunks 01–10) per plans/active/test-suite-triage.md:180-209,374-383
Artifacts: reports/2026-01-test-suite-triage/phase_r/${STAMP}/ (chunks/, summary.md, env/)
Do Now: TEST-SUITE-TRIAGE-001 / Next Action 16 – Phase R guarded full-suite closure; set STAMP with `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then run chunk 01 via `timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_at_abs_001.py tests/test_at_cli_009.py tests/test_at_io_002.py tests/test_at_parallel_007.py tests/test_at_parallel_017.py tests/test_at_parallel_028.py tests/test_at_pol_001.py tests/test_at_src_002.py tests/test_cli_scaling.py tests/test_detector_pivots.py tests/test_physics.py --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_01/pytest.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_01/pytest.log`.
If Blocked: If any chunk times out, capture the partial `pytest.log` under phase_r/${STAMP}/chunks/chunk_##/timeout.log and log the blocker + failing selector in docs/fix_plan.md Attempt history before stopping.
Priorities & Rationale:
- plans/active/test-suite-triage.md:374-383 — defines Phase R tasks (R1–R3) and guard requirements.
- docs/fix_plan.md:63-64 — Next Action 16 expects the guarded full-suite rerun + ledger update.
- reports/2026-01-test-suite-triage/phase_o/20251015T003950Z/summary.md — prior chunk ladder reference highlighting missing chunk 10 coverage.
- docs/development/testing_strategy.md:34-78 — runtime guardrails (KMP, device neutrality, compile guard) for suite runs.
- plans/active/test-suite-triage.md:332-347 — aggregation helper we must reuse to prove zero failures.
How-To Map:
- Prep dirs & selectors: `mkdir -p reports/2026-01-test-suite-triage/phase_r/${STAMP}/{env,chunks/chunk_{01..10}}` then copy the chunk roster from plans/active/test-suite-triage.md:180-209 into `phase_r/${STAMP}/chunks/chunk_##/selectors.txt` (drop any tests that pytest reports as missing).
- Chunk 01 command (already in Do Now) writes `pytest.log` + `pytest.xml` under chunk_01.
- Chunk 02:
  ```bash
  timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
    pytest -vv tests/test_at_bkg_001.py tests/test_at_crystal_absolute.py tests/test_at_io_003.py \
    tests/test_at_parallel_008.py tests/test_at_parallel_018.py tests/test_at_parallel_029.py \
    tests/test_at_pre_001.py tests/test_at_src_003.py tests/test_cli_scaling_phi0.py \
    tests/test_divergence_culling.py tests/test_pivot_mode_selection.py \
    --maxfail=0 --durations=25 \
    --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_02/pytest.xml \
    2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_02/pytest.log
  ```
- Chunk 03 (gradients, allow 20 min):
  ```bash
  timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
    pytest -vv tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py \
    tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py \
    tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py \
    tests/test_gradients.py tests/test_show_config.py \
    --maxfail=0 --durations=25 \
    --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_03/pytest.xml \
    2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_03/pytest.log
  ```
- Chunk 04:
  ```bash
  timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
    pytest -vv tests/test_at_cli_002.py tests/test_at_geo_001.py tests/test_at_noise_001.py \
    tests/test_at_parallel_010.py tests/test_at_parallel_021.py tests/test_at_perf_002.py \
    tests/test_at_roi_001.py tests/test_at_str_001.py tests/test_crystal_geometry.py \
    tests/test_mosflm_matrix.py tests/test_suite.py \
    --maxfail=0 --durations=25 \
    --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_04/pytest.xml \
    2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_04/pytest.log
  ```
- Chunk 05:
  ```bash
  timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
    pytest -vv tests/test_at_cli_003.py tests/test_at_geo_002.py tests/test_at_parallel_001.py \
    tests/test_at_parallel_011.py tests/test_at_parallel_022.py tests/test_at_perf_003.py \
    tests/test_at_sam_001.py tests/test_at_str_002.py tests/test_custom_vectors.py \
    tests/test_multi_source_integration.py tests/test_trace_pixel.py \
    --maxfail=0 --durations=25 \
    --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_05/pytest.xml \
    2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_05/pytest.log
  ```
- Chunk 06:
  ```bash
  timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
    pytest -vv tests/test_at_cli_004.py tests/test_at_geo_003.py tests/test_at_parallel_002.py \
    tests/test_at_parallel_012.py tests/test_at_parallel_023.py tests/test_at_perf_004.py \
    tests/test_at_sam_002.py tests/test_at_str_003.py tests/test_debug_trace.py \
    tests/test_oversample_autoselect.py tests/test_tricubic_vectorized.py \
    --maxfail=0 --durations=25 \
    --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_06/pytest.xml \
    2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_06/pytest.log
  ```
- Chunk 07:
  ```bash
  timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
    pytest -vv tests/test_at_cli_005.py tests/test_at_geo_004.py tests/test_at_parallel_003.py \
    tests/test_at_parallel_013.py tests/test_at_parallel_024.py tests/test_at_perf_005.py \
    tests/test_at_sam_003.py tests/test_at_str_004.py tests/test_detector_basis_vectors.py \
    tests/test_parity_coverage_lint.py tests/test_units.py \
    --maxfail=0 --durations=25 \
    --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_07/pytest.xml \
    2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_07/pytest.log
  ```
- Chunk 08:
  ```bash
  timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
    pytest -vv tests/test_at_cli_006.py tests/test_at_geo_005.py tests/test_at_parallel_004.py \
    tests/test_at_parallel_014.py tests/test_at_parallel_025.py tests/test_at_perf_006.py \
    tests/test_at_src_001.py tests/test_at_tools_001.py tests/test_detector_config.py \
    tests/test_parity_matrix.py \
    --maxfail=0 --durations=25 \
    --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_08/pytest.xml \
    2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_08/pytest.log
  ```
- Chunk 09:
  ```bash
  timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
    pytest -vv tests/test_at_cli_007.py tests/test_at_geo_006.py tests/test_at_parallel_005.py \
    tests/test_at_parallel_015.py tests/test_at_parallel_026.py tests/test_at_perf_007.py \
    tests/test_at_src_001_cli.py tests/test_beam_center_offset.py tests/test_detector_conventions.py \
    tests/test_perf_pytorch_005_cudagraphs.py \
    --maxfail=0 --durations=25 \
    --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_09/pytest.xml \
    2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_09/pytest.log
  ```
- Chunk 10:
  ```bash
  timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
    pytest -vv tests/test_at_cli_008.py tests/test_at_io_001.py tests/test_at_parallel_006.py \
    tests/test_at_parallel_016.py tests/test_at_parallel_027.py tests/test_at_perf_008.py \
    tests/test_at_src_001_simple.py tests/test_cli_flags.py tests/test_detector_geometry.py \
    tests/test_perf_pytorch_006.py \
    --maxfail=0 --durations=25 \
    --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_10/pytest.xml \
    2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_10/pytest.log
  ```
- After each chunk command, capture the return code: `printf "%s\n" $? > reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_0X/exit_code.txt` (replace `0X` with the chunk number).
- Capture environment snapshot:
  ```bash
  python - <<'PY' > reports/2026-01-test-suite-triage/phase_r/${STAMP}/env/python_torch_env.txt
  import json, platform, torch
  print(json.dumps({
      "python": platform.python_version(),
      "torch": torch.__version__,
      "cuda_available": torch.cuda.is_available(),
      "device_count": torch.cuda.device_count(),
      "platform": platform.platform()
  }, indent=2))
  PY
  ```
- Aggregate junit totals after all chunks:
  ```bash
  python - <<'PY'
  import xml.etree.ElementTree as ET
  from collections import Counter
  import pathlib, os
  stamp = os.environ['STAMP']
  base = pathlib.Path('reports/2026-01-test-suite-triage/phase_r') / stamp / 'chunks'
  totals = Counter()
  for chunk in sorted(base.glob('chunk_*')):
      junit = chunk / 'pytest.xml'
      if junit.exists():
          suite = ET.parse(junit).getroot().find('testsuite')
          totals['tests'] += int(suite.attrib.get('tests', 0))
          totals['failures'] += int(suite.attrib.get('failures', 0))
          totals['errors'] += int(suite.attrib.get('errors', 0))
          totals['skipped'] += int(suite.attrib.get('skipped', 0))
  passed = totals['tests'] - totals['failures'] - totals['errors'] - totals['skipped']
  print(f"passes={passed} failures={totals['failures']} errors={totals['errors']} skipped={totals['skipped']}")
  PY
  ```
  Append the summary and slowest tests table to `reports/2026-01-test-suite-triage/phase_r/${STAMP}/summary.md`.
- Update docs: add Attempt #81 (Phase R) to docs/fix_plan.md and refresh `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` with the zero-failure baseline + Phase R STAMP.
Pitfalls To Avoid:
- Keep `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1` on every pytest command; missing any guard will resurrect gradcheck failures.
- Use the same STAMP for all artifacts so aggregation works; do not mix directories.
- Watch for missing test files; remove them from the command instead of letting pytest error out.
- Ensure junit/log paths exist before running pytest to avoid tee failures.
- Do not delete or move files listed in docs/index.md (loop.sh, supervisor.sh, input.md).
- Capture exit codes (save to `exit_code.txt`) before moving on to the next chunk.
- Avoid running the entire suite without chunking—timeout caps are 600 s (1200 s for chunk 03) per command per testing strategy.
- Keep ASCII formatting when editing docs/fix_plan.md or remediation_tracker.md.
- Confirm aggregation reports zero failures before marking the ledger complete.
- Leave compile guard documentation untouched; this loop only records evidence.
Pointers:
- plans/active/test-suite-triage.md:180-209,332-347,374-383
- docs/fix_plan.md:48-64
- docs/development/testing_strategy.md:34-78
- reports/2026-01-test-suite-triage/phase_o/20251015T003950Z/summary.md
- docs/development/pytorch_runtime_checklist.md:12-48
Next Up: If the guarded ladder is green early, draft the closure summary for docs/fix_plan.md and stage plan archival notes for Phase R.
