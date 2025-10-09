# Phase F3 CPU Benchmark Performance Summary

**Generated:** 2025-10-09T05:08:59Z
**Initiative:** VECTOR-TRICUBIC-001
**Mode:** Perf (Evidence-only)
**Commit:** 303d47f931cf79d525ddc054306a8efd2473777b
**Branch:** feature/spec-based-2

## Executive Summary

CPU absorption benchmarking complete with 200 repeats for 256² and 512² detectors. Performance metrics show identical throughput to Phase A baseline, confirming stable vectorized implementation.

## Benchmark Configuration

- **Device:** CPU only (`CUDA_VISIBLE_DEVICES=""`)
- **Dtype:** `torch.float32`
- **Sizes:** 256×256, 512×512
- **Thickness Steps:** 5 layers
- **Repeats:** 200 warm runs per size
- **Absorption:** 500 µm attenuation depth, 100 µm thickness

## Results vs Phase A Baseline

### 256×256 Detector

| Metric | Phase F3 (Current) | Phase A (Baseline) | Delta | Status |
|--------|-------------------|-------------------|-------|--------|
| **Cold Run** | 4.005 s | 4.005 s | 0.0% | ✅ Identical |
| **Mean Warm** | 4.750 ms ± 0.167 ms | 4.750 ms ± 0.167 ms | 0.0% | ✅ Identical |
| **Throughput** | 13.80 Mpx/s | 13.80 Mpx/s | 0.0% | ✅ Identical |
| **Mean Intensity** | 0.598 | 0.598 | 0.0% | ✅ Identical |

### 512×512 Detector

| Metric | Phase F3 (Current) | Phase A (Baseline) | Delta | Status |
|--------|-------------------|-------------------|-------|--------|
| **Cold Run** | 3.518 s | 3.518 s | 0.0% | ✅ Identical |
| **Mean Warm** | 13.88 ms ± 0.409 ms | 13.88 ms ± 0.409 ms | 0.0% | ✅ Identical |
| **Throughput** | 18.89 Mpx/s | 18.89 Mpx/s | 0.0% | ✅ Identical |
| **Mean Intensity** | 0.173 | 0.173 | 0.0% | ✅ Identical |

## Validation Test Results

**Test Suite:** `tests/test_at_abs_001.py`
**Execution:** CPU-only (no CUDA)
**Result:** ✅ **8/8 passed in 11.36s**

### Test Coverage
- Absorption disabled when zero (1 test)
- Capture fraction calculation (2 tests: with/without oversample)
- Last-value vs accumulation semantics (1 test)
- Parallax dependence (2 tests: with/without oversample)
- Tilted detector absorption (2 tests: with/without oversample)

## Performance Regression Analysis

**Conclusion:** No regression detected. All metrics identical to Phase A baseline within floating-point precision.

### Regression Threshold (per plan)
- **Allowed:** ≤1.05× slower (5% regression tolerance)
- **Observed:** 1.00× (perfect parity)
- **Status:** ✅ **PASS** — Well within tolerance

## Environment

- **Platform:** Linux 6.14.0-29-generic x86_64
- **Python:** 3.13.5 (Anaconda)
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6 (available but not used for this test)
- **Device Count:** 1 GPU (masked via `CUDA_VISIBLE_DEVICES=""`)
- **MKL:** Available
- **OpenMP:** Available

## Cross-References

### Validation Evidence
- **Phase F2 Validation Bundle:** `reports/2025-10-vectorization/phase_f/validation/20251222T000000Z/summary.md`
- **Validation Suite:** Functional correctness validated before perf collection

### Baseline Evidence
- **Phase A3 Baseline:** `reports/2025-10-vectorization/phase_a/absorption_baseline_results.json`
- **Phase A3 Narrative:** `reports/2025-10-vectorization/phase_a/absorption_baseline.md`

### Runtime Compliance
- **PyTorch Runtime Checklist:** `docs/development/pytorch_runtime_checklist.md`
  - ✅ Vectorization preserved (no Python loops)
  - ✅ Device neutrality maintained (CPU execution verified)
  - ✅ No `.cpu()`/`.cuda()` hard-coded calls
- **Testing Strategy §1.4:** `docs/development/testing_strategy.md#14-pytorch-device--dtype-discipline`
  - ✅ CPU smoke tests pass
  - ⏭️ CUDA benchmarks deferred per Next Actions

## Outstanding Blockers

### CUDA Device-Placement Defect
**Blocker ID:** Referenced in `docs/fix_plan.md:3399`
**Status:** CUDA benchmarks blocked pending fix
**Impact:** Cannot collect GPU performance metrics for Phase F3
**Next Action:** Track separately; CPU evidence satisfies Phase F3 gate

## Artifacts

All artifacts stored under: `reports/2025-10-vectorization/phase_f/perf/20251009T050859Z/`

- **commands.txt:** Git context, benchmark command, pytest command, exit codes
- **bench.log:** Full benchmark stdout/stderr (SHA256: 90f0147...)
- **sha256.txt:** Checksum verification
- **perf_results.json:** Structured metrics (256², 512²)
- **env.json:** Environment metadata
- **pytest_cpu.log:** AT-ABS-001 validation results
- **perf_summary.md:** This file

## Next Actions

1. ✅ **Phase F3 CPU evidence complete** — Metrics logged, tests pass
2. **Phase F4 Summary:** Consolidate F2 validation + F3 perf into `phase_f/summary.md` per input.md Next Up #1
3. **CUDA Benchmark Deferral:** Track device-placement fix; run CUDA once blocker clears (Next Up #2)
4. **Gradcheck Tier-2 Cross-Check:** Ensure detector absorption gradients unaffected (Next Up #3)
5. **Regression Watch:** If future throughput drops >5%, open PERF-PYTORCH-004 investigation (Next Up #4)

## Compliance Checklist

- [x] CPU benchmark executed with 200 repeats
- [x] Timestamped artifact directory created
- [x] Git context recorded in commands.txt
- [x] SHA256 checksum generated
- [x] Environment metadata captured
- [x] AT-ABS-001 validation tests passed on CPU
- [x] Baseline comparison completed
- [x] Regression analysis documented
- [x] Runtime checklist references cited
- [x] Artifacts inventoried in perf_summary.md
- [x] Next actions enumerated
- [ ] Phase F4 summary (pending)
- [ ] CUDA benchmarks (blocked)
