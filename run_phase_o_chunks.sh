#!/bin/bash
# Phase O chunked execution script
# STAMP: 20251015T003950Z

STAMP="20251015T003950Z"
BASEDIR="reports/2026-01-test-suite-triage/phase_o/$STAMP"

# Chunk 03
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py \
  tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py \
  tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py \
  tests/test_gradients.py tests/test_show_config.py \
  --maxfail=0 --durations=25 --junitxml "$BASEDIR/chunks/chunk_03/pytest.xml" \
  2>&1 | tee "$BASEDIR/chunks/chunk_03/pytest.log"
echo $? > "$BASEDIR/chunks/chunk_03/exit_code.txt"

# Chunk 04
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_002.py tests/test_at_geo_001.py tests/test_at_noise_001.py \
  tests/test_at_parallel_010.py tests/test_at_parallel_021.py tests/test_at_perf_002.py \
  tests/test_at_roi_001.py tests/test_at_str_001.py tests/test_crystal_geometry.py \
  tests/test_mosflm_matrix.py tests/test_suite.py \
  --maxfail=0 --durations=25 --junitxml "$BASEDIR/chunks/chunk_04/pytest.xml" \
  2>&1 | tee "$BASEDIR/chunks/chunk_04/pytest.log"
echo $? > "$BASEDIR/chunks/chunk_04/exit_code.txt"

# Chunk 05
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_003.py tests/test_at_geo_002.py tests/test_at_parallel_001.py \
  tests/test_at_parallel_011.py tests/test_at_parallel_022.py tests/test_at_perf_003.py \
  tests/test_at_sam_001.py tests/test_at_str_002.py tests/test_custom_vectors.py \
  tests/test_multi_source_integration.py tests/test_trace_pixel.py \
  --maxfail=0 --durations=25 --junitxml "$BASEDIR/chunks/chunk_05/pytest.xml" \
  2>&1 | tee "$BASEDIR/chunks/chunk_05/pytest.log"
echo $? > "$BASEDIR/chunks/chunk_05/exit_code.txt"

# Chunk 06
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_004.py tests/test_at_geo_003.py tests/test_at_parallel_002.py \
  tests/test_at_parallel_012.py tests/test_at_parallel_023.py tests/test_at_perf_004.py \
  tests/test_at_sam_002.py tests/test_at_str_003.py tests/test_debug_trace.py \
  tests/test_oversample_autoselect.py tests/test_tricubic_vectorized.py \
  --maxfail=0 --durations=25 --junitxml "$BASEDIR/chunks/chunk_06/pytest.xml" \
  2>&1 | tee "$BASEDIR/chunks/chunk_06/pytest.log"
echo $? > "$BASEDIR/chunks/chunk_06/exit_code.txt"

# Chunk 07
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_005.py tests/test_at_geo_004.py tests/test_at_parallel_003.py \
  tests/test_at_parallel_013.py tests/test_at_parallel_024.py tests/test_at_perf_005.py \
  tests/test_at_sam_003.py tests/test_at_str_004.py tests/test_detector_basis_vectors.py \
  tests/test_parity_coverage_lint.py tests/test_units.py \
  --maxfail=0 --durations=25 --junitxml "$BASEDIR/chunks/chunk_07/pytest.xml" \
  2>&1 | tee "$BASEDIR/chunks/chunk_07/pytest.log"
echo $? > "$BASEDIR/chunks/chunk_07/exit_code.txt"

# Chunk 08
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_006.py tests/test_at_geo_005.py tests/test_at_parallel_004.py \
  tests/test_at_parallel_014.py tests/test_at_parallel_025.py tests/test_at_perf_006.py \
  tests/test_at_src_001.py tests/test_at_tools_001.py tests/test_detector_config.py \
  tests/test_parity_matrix.py \
  --maxfail=0 --durations=25 --junitxml "$BASEDIR/chunks/chunk_08/pytest.xml" \
  2>&1 | tee "$BASEDIR/chunks/chunk_08/pytest.log"
echo $? > "$BASEDIR/chunks/chunk_08/exit_code.txt"

# Chunk 09
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_007.py tests/test_at_geo_006.py tests/test_at_parallel_005.py \
  tests/test_at_parallel_015.py tests/test_at_parallel_026.py tests/test_at_perf_007.py \
  tests/test_at_src_002.py tests/test_at_tools_002.py tests/test_detector_offsets.py \
  tests/test_pix0_alias.py tests/test_vectorization_masks.py \
  --maxfail=0 --durations=25 --junitxml "$BASEDIR/chunks/chunk_09/pytest.xml" \
  2>&1 | tee "$BASEDIR/chunks/chunk_09/pytest.log"
echo $? > "$BASEDIR/chunks/chunk_09/exit_code.txt"

# Chunk 10
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv \
  tests/test_at_cli_008.py tests/test_at_geo_007.py tests/test_at_parallel_006.py \
  tests/test_at_parallel_016.py tests/test_at_parallel_027.py tests/test_at_perf_008.py \
  tests/test_at_src_003.py tests/test_at_tools_003.py tests/test_detector_validation.py \
  tests/test_pix0_vector.py tests/test_vectorization_summary.py \
  --maxfail=0 --durations=25 --junitxml "$BASEDIR/chunks/chunk_10/pytest.xml" \
  2>&1 | tee "$BASEDIR/chunks/chunk_10/pytest.log"
echo $? > "$BASEDIR/chunks/chunk_10/exit_code.txt"

echo "All chunks complete"
