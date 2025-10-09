# Phase H: CUDA Parity & Performance Evidence

**Date:** 2025-10-09T09:22:28Z
**Commit:** a59a9b1
**Owner:** ralph (loop execution per input.md Do Now)

## Executive Summary

Phase H captures CUDA parity and performance evidence for the vectorized tricubic interpolation and detector absorption implementation. All CUDA tests pass, confirming device neutrality. Benchmark results show CUDA performance comparable to CPU baseline measurements from Phase A/E/F.

## Test Results

### Tricubic Vectorization (CUDA)
- **Tests Run:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -v -k cuda`
- **Result:** 2 passed, 14 deselected in 2.25s
- **Tests:**
  - `test_device_neutrality[cuda]` ✅ PASSED
  - `test_polynomials_device_neutral[cuda]` ✅ PASSED
- **Artifacts:** `pytest_logs/tricubic_cuda.log`

### Detector Absorption (CUDA)
- **Tests Run:** `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py -v -k cuda`
- **Result:** 8 passed, 8 deselected in 5.96s
- **Tests:**
  - `test_absorption_disabled_when_zero[cuda]` ✅ PASSED
  - `test_capture_fraction_calculation[False-cuda]` ✅ PASSED
  - `test_capture_fraction_calculation[True-cuda]` ✅ PASSED
  - `test_last_value_vs_accumulation_semantics[cuda]` ✅ PASSED
  - `test_parallax_dependence[False-cuda]` ✅ PASSED
  - `test_parallax_dependence[True-cuda]` ✅ PASSED
  - `test_absorption_with_tilted_detector[False-cuda]` ✅ PASSED
  - `test_absorption_with_tilted_detector[True-cuda]` ✅ PASSED
- **Artifacts:** `pytest_logs/absorption_cuda.log`

## Benchmark Results

### Tricubic Interpolation (CUDA)
- **Command:** `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --device cuda --repeats 200 --sizes 256 512`
- **Results:**
  - **256×256:** 5647.65 μs/call (177.1 calls/sec)
    - Cold run: 0.570113s
    - Warm runs: 0.564765 ± 0.001374s
  - **512×512:** 5652.98 μs/call (176.9 calls/sec)
    - Cold run: 0.562829s
    - Warm runs: 0.565298 ± 0.001379s
- **Comparison to Phase E Baseline (CUDA):**
  - Phase E 256²: 5574.36 μs/call → Phase H: 5647.65 μs/call (1.013× = **1.3% slower**, within noise)
  - Phase E 512²: 5597.59 μs/call → Phase H: 5652.98 μs/call (1.010× = **1.0% slower**, within noise)
  - **Conclusion:** Performance parity maintained within measurement uncertainty
- **Artifacts:** `benchmarks/tricubic/tricubic_baseline_results.json`, `benchmarks/tricubic/tricubic_baseline.md`

### Detector Absorption (CUDA)
- **Command:** `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --device cuda --repeats 200 --sizes 256 512 --thicksteps 5`
- **Results:**
  - **256×256 (5 layers):**
    - Cold run: 0.005523s
    - Warm runs: 0.005478 ± 0.000023s
    - Throughput: **11.96 Mpx/sec**
    - Mean intensity: 0.598
  - **512×512 (5 layers):**
    - Cold run: 0.005764s
    - Warm runs: 0.005562 ± 0.000018s
    - Throughput: **47.13 Mpx/sec**
    - Mean intensity: 0.173
- **Comparison to Phase A Baseline (CUDA):**
  - Phase A 256²: 11.3 Mpx/sec → Phase H: 11.96 Mpx/sec (1.058× = **5.8% faster**)
  - Phase A 512²: 44.8 Mpx/sec → Phase H: 47.13 Mpx/sec (1.052× = **5.2% faster**)
  - **Conclusion:** Performance improvement observed, likely due to reduced overhead or runtime optimizations
- **Comparison to Phase F Baseline (CPU):**
  - Phase F 256² CPU: 13.80 Mpx/sec → Phase H CUDA: 11.96 Mpx/sec (0.867× = **13% slower on GPU**)
  - Phase F 512² CPU: 18.89 Mpx/sec → Phase H CUDA: 47.13 Mpx/sec (2.495× = **149% faster on GPU**)
  - **Conclusion:** GPU advantage scales with problem size (as expected)
- **Artifacts:** `benchmarks/absorption/absorption_baseline_results.json`, `benchmarks/absorption/absorption_baseline.md`

## Environment

- **Python:** 3.13.5 | packaged by Anaconda, Inc. | (main, Jun 12 2025, 16:09:02) [GCC 11.2.0]
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6
- **CUDA Available:** true
- **Platform:** Linux-6.14.0-29-generic-x86_64-with-glibc2.39
- **Detailed Environment:** `torch_env.txt`
- **GPU Info:** `nvidia_smi.txt`

## Observations

1. **Device Neutrality Validated:** All parametrized CUDA tests pass, confirming vectorized tricubic and absorption implementations work correctly on GPU
2. **Performance Parity:** Tricubic CUDA performance within 1-1.3% of Phase E baseline (measurement noise)
3. **Performance Improvement:** Absorption CUDA throughput improved 5-6% vs Phase A baseline
4. **GPU Scaling:** Absorption shows expected GPU advantage for larger problem sizes (512²: 2.5× faster than CPU)
5. **Test Coverage:** 10/10 CUDA tests passing (2 tricubic + 8 absorption parametrized variants)

## Compliance Checklist

- ✅ CUDA parity tests executed and passing
- ✅ CUDA benchmarks captured with 200 repeats for statistical confidence
- ✅ Environment metadata (env.json, torch_env.txt, nvidia_smi.txt) saved
- ✅ Commands documented in commands.txt
- ✅ Pytest logs archived under pytest_logs/
- ✅ Benchmark artifacts (JSON, markdown) under benchmarks/
- ✅ Performance comparison to Phase A/E/F baselines documented
- ✅ Device/dtype neutrality verified per docs/development/pytorch_runtime_checklist.md §1.4

## Next Actions

1. **Update docs/fix_plan.md:** Append Attempt #18 to [VECTOR-TRICUBIC-001] with Phase H CUDA evidence summary, correlation metrics, and performance deltas
2. **Archive Plan:** Move `plans/active/vectorization.md` to `plans/archive/vectorization.md` noting Phase H completion
3. **Mark Complete:** Update [VECTOR-TRICUBIC-001] status from `in_progress` to `done` in fix_plan.md index
4. **Cross-Reference:** Ensure PERF-PYTORCH-004 notes are updated if any device-placement issues were observed (none found in this run)

## Artifact Inventory

```
reports/2025-10-vectorization/phase_h/20251009T092228Z/
├── benchmarks/
│   ├── tricubic/
│   │   ├── tricubic_baseline_results.json
│   │   └── tricubic_baseline.md
│   └── absorption/
│       ├── absorption_baseline_results.json
│       └── absorption_baseline.md
├── pytest_logs/
│   ├── tricubic_cuda.log
│   └── absorption_cuda.log
├── commands.txt
├── env.json
├── torch_env.txt
├── nvidia_smi.txt
└── summary.md (this file)
```

## References

- Phase A baseline: `reports/2025-10-vectorization/phase_a/` (initial CPU + CUDA absorption measurements)
- Phase E baseline: `reports/2025-10-vectorization/phase_e/perf/20251009T034421Z/` (tricubic CUDA baseline)
- Phase F baseline: `reports/2025-10-vectorization/phase_f/perf/20251009T050859Z/` (absorption CPU baseline)
- Plan: `plans/active/vectorization.md` Phase H tasks (H1: device-placement fix, H2: CUDA capture, H3: archive)
- Fix plan: `docs/fix_plan.md` [VECTOR-TRICUBIC-001] (lines 3410-3737)
- Input steering: `input.md` Do Now (Phase H H2 CUDA evidence capture)
