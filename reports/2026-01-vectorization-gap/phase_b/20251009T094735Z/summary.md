# Vectorization Gap Audit — Phase B1 Profiler Capture

**Initiative:** [VECTOR-GAPS-002]
**Phase:** B1 — Profiler Evidence Capture
**Date:** 2025-10-09 (UTC: 20251009T094735Z)
**Branch:** feature/spec-based-2
**Commit:** 8f1b96b

## Executive Summary

Successfully captured fresh profiler evidence to replace the stale 20251009T062238Z data (correlation 0.721). The new capture confirms the **low correlation issue persists** (0.7212), indicating a fundamental parity gap that blocks vectorization gap ranking until resolved.

## Test Configuration

- **Detector Size:** 4096×4096 (16,777,216 pixels)
- **Device:** CPU
- **Dtype:** float32
- **Profiling:** Enabled with PyTorch profiler
- **Iterations:** 1 (cold + warm run)
- **C Binary:** `./golden_suite_generator/nanoBragg`

## Key Metrics

### Correlation (Critical Finding)
- **C vs PyTorch:** 0.7212 (both cold and warm)
- **Expected Threshold:** ≥0.99 per `specs/spec-a-parallel.md` §2.3
- **Status:** ⚠️ **BELOW THRESHOLD** — indicates parity issue

### Performance
| Run Type | Time (s) | Setup (ms) | Simulation (s) | Memory (MB) |
|----------|----------|------------|----------------|-------------|
| C        | 0.537    | —          | —              | 0.0         |
| PyTorch (cold) | 2.516 | 171.6 | 2.306 | 437.7 |
| PyTorch (warm) | 0.675 | 0.0017 | 0.636 | 14.1 |

**Speedup Analysis:**
- Cold run: 0.21× (C is 4.69× faster)
- Warm run: 0.79× (C is 1.26× faster)
- Setup speedup: 102,841× (warm cache hit effective)

### Cache Effectiveness
- ✓ PERF-PYTORCH-005 exit criteria MET: warm setup 0.0ms < 50ms target
- Cache hit confirmed on warm run
- Setup time reduced from 171.6ms to 0.0017ms

## Profiler Artifacts

All artifacts saved under: `reports/2026-01-vectorization-gap/phase_b/20251009T094735Z/`

- **Profiler trace:** `profile/profile_4096x4096/trace.json` (Chrome Tracing format)
- **Benchmark results:** `profile/benchmark_results.json`
- **Commands log:** `commands.txt`
- **Environment snapshot:** `env.json`
- **PyTorch environment:** `torch_env.txt`
- **Correlation metrics:** `correlation.txt`
- **Profiler run log:** `profile/run.log`
- **Pytest collection:** `pytest_collect.log` (557 tests collected, exit code 0)

## Top-N Kernel Analysis

**Note:** Detailed kernel profiling requires parsing `trace.json`. Key expected kernels to analyze in Phase B2:
- Autograd operations (Miller index computation, sincg evaluations)
- Tensor broadcasting operations (source/phi/mosaic batching)
- Detector geometry calculations
- Structure factor lookups
- Shape factor (sincg) evaluations

**Action for Phase B2:** Parse `trace.json` with `torch.profiler` utilities to extract inclusive time percentages for each major kernel and map to Phase A loop inventory.

## Critical Findings

### ⚠️ Parity Gap (Blocking)

**The 0.7212 correlation is FAR BELOW the ≥0.99 threshold**, indicating fundamental physics or numerical discrepancies between C and PyTorch implementations. This blocks vectorization gap ranking because:

1. **Cannot trust profiler hotspots** until parity is restored (optimizing incorrect physics is counterproductive)
2. **Phase A loop inventory** assumed baseline parity; low correlation invalidates that assumption
3. **SOURCE-WEIGHT-001 completion** (Phase D, commit c49e3be per `docs/fix_plan.md`) was supposed to close the parity gap

**Recommended Actions Before Phase B2:**
1. Reopen SOURCE-WEIGHT-001 or create new parity task
2. Run parallel trace comparison (`scripts/debug_pixel_trace.py` vs instrumented C code)
3. Identify first divergence point per `docs/debugging/debugging.md` workflow
4. Do NOT proceed with Phase B2 correlation analysis until parity restored to ≥0.99

### ✓ Warm Cache Performance

- Setup time: 0.0017ms (well below 50ms threshold)
- 102,841× speedup confirms torch.compile caching works
- PERF-PYTORCH-004 Phase 3 warm-run goals validated

## Environment Context

- **Python:** 3.13.5
- **PyTorch:** 2.7.1+cu126
- **CUDA Available:** Yes (1 device: NVIDIA GeForce RTX 3090)
- **System:** Linux 6.14.0-29-generic (Ubuntu 24.04.1)
- **CPU Cores:** 32
- **RAM:** 125.7 GB

## Commands Executed

### Pytest Collection
```bash
pytest --collect-only -q | tee reports/2026-01-vectorization-gap/phase_b/20251009T094735Z/pytest_collect.log
```
**Result:** 557 tests collected (exit code 0)

### Profiler Execution
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py \
  --sizes 4096 \
  --device cpu \
  --dtype float32 \
  --profile \
  --keep-artifacts \
  --iterations 1
```
**Result:** Successful profiler run with trace.json generated

## Next Actions (Phase B2 — BLOCKED)

**Phase B2 is BLOCKED pending parity restoration.** Original plan was:

1. Parse `trace.json` to extract kernel inclusive times
2. Map hotspots to Phase A loop inventory
3. Create `hot_loops.csv` with priority ranking
4. Cross-reference with SOURCE-WEIGHT-001 resolution metrics

**Revised Next Actions:**

1. **Diagnose parity gap:** Run `nb-compare` with detailed diff to identify divergence regions
2. **Trace comparison:** Execute parallel trace workflow per `docs/debugging/debugging.md` §2.1
3. **Review SOURCE-WEIGHT-001:** Check if Phase D completion (commit c49e3be) actually resolved weighted-source semantics
4. **Validate fix:** Re-run profiler command after parity restored and confirm correlation ≥0.99
5. **Only then proceed** to Phase B2 correlation analysis

## References

- **Plan:** `plans/active/vectorization-gap-audit.md` (Phase B guidance)
- **Fix Plan Entry:** `docs/fix_plan.md` lines 3763-3810 ([VECTOR-GAPS-002])
- **Testing Strategy:** `docs/development/testing_strategy.md` §1.4 (device/dtype discipline)
- **Prior Evidence:** `reports/2025-10-vectorization/phase_h/20251009T092228Z/summary.md` (CUDA parity baseline)
- **Phase A Inventory:** `reports/2026-01-vectorization-gap/phase_a/20251009T065238Z/summary.md` (loop classification)
- **Debugging SOP:** `docs/debugging/debugging.md` (parallel trace workflow)

## Signature

**Captured by:** Ralph (loop execution)
**Supervised by:** Galph (Phase B1 steering via `input.md`)
**Evidence Status:** Complete (but reveals blocking parity issue)
