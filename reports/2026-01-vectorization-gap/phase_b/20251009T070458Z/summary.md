# Phase B1 Profiler Capture Summary — Vectorization Gap Audit

**Date:** 2025-10-09T07:04:58Z
**Plan:** plans/active/vectorization-gap-audit.md Phase B Task B1
**Commit:** b069274ceee35029d0865376a3179cc8ae9a831c

## Executive Summary

Captured warm-run profiler trace for 4096x4096 detector (16.7M pixels) on CPU with float32 to identify remaining Python loop hotspots. Phase B1 complete; artifacts ready for Phase B2 correlation with Phase A static loop inventory.

## Profiler Configuration

- **Command:** `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --keep-artifacts --iterations 1`
- **Detector:** 4096x4096 (16,777,216 pixels)
- **Device:** CPU (32 cores)
- **Dtype:** float32 (production default per DTYPE initiative)
- **Iterations:** 1 (warm run with cached simulator)
- **Profiler:** torch.profiler with CPU activity, shapes, memory, and stack traces

## Key Performance Metrics

| Metric | C Reference | PyTorch COLD | PyTorch WARM | Speedup Warm |
|--------|------------|--------------|--------------|--------------|
| **Total Time** | 0.527s | 8.285s | 0.675s | 0.78x (C faster) |
| **Simulation** | 0.527s | 8.077s | 0.637s | 0.83x (C faster) |
| **Setup** | — | 0.170s | 0.000s | ∞ (cache hit) |
| **Memory** | 0.0 MB | 546.0 MB | 24.0 MB | — |
| **Correlation** | — | 0.721175 | 0.721175 | — |

### Observations

1. **❌ BLOCKER: Low Correlation (0.72 vs expected >0.99)**
   - PyTorch and C outputs diverge significantly
   - This was **not** flagged in Phase A and requires investigation before Phase B2
   - Likely related to known issues in PERF-PYTORCH-004 (weighted source normalization, per-source polarization)
   - **Action Required:** Defer Phase B2 until correlation >0.99 restored

2. **⚠️ Performance Deficit: 1.28x slower than C (warm run)**
   - Target: PyTorch ≥1.0x C speed (or at minimum parity)
   - Current: C is 1.28x faster even after warm cache
   - This confirms Phase B profiling is needed to identify bottlenecks

3. **✓ Cache Effectiveness: PERF-PYTORCH-005 Exit Criteria Met**
   - Warm setup: 0.0ms (< 50ms threshold)
   - Cache speedup: 79357.6x
   - Simulator reuse working as designed

## Profiler Artifacts

- **Trace File:** `profile/profile_4096x4096/trace.json` (1.7 MB Chrome trace format)
- **Metrics:** `profile/benchmark_results.json` (675 bytes)
- **Run Log:** `profile_run.log` (full stdout/stderr)
- **Env Info:** `env.json` (Python/torch versions, CUDA availability)
- **Test Collection:** `pytest_collect.log` (test suite snapshot)

## Phase A Cross-Reference

Phase A (20251009T065238Z) identified:
- **Vectorized:** 4 loops (polin2/polin3 helpers)
- **Safe:** 17 loops (I/O, config, debug)
- **TODO:** 2 loops (noise.py:171 LCG loop [HIGH], simulator.py:1568 phi-loop [MEDIUM])
- **Uncertain:** 1 loop (needs Phase B profiler)

**Next Step (B2):** Map these static entries to profiler hotspots (≥1% inclusive time) once correlation issue resolved.

## Blocking Issues for Phase B2

### Issue 1: Low Correlation (0.721 vs >0.99)
- **Root Cause:** Likely multi-source normalization/polarization bugs (PERF-PYTORCH-004 P3.0b/P3.0c)
- **Impact:** Cannot trust profiler hotspots if physics is incorrect
- **Resolution:** Fix PERF-PYTORCH-004 tasks P3.0b (per-source polarization) and P3.0c (normalization) before continuing Phase B
- **Verification Command:** `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "simple_cubic"`

### Issue 2: Performance Target Not Met
- **Target:** PyTorch ≥1.0x C speed (warm run)
- **Current:** 0.78x (C is 1.28x faster)
- **Impact:** Confirms vectorization gaps exist but cannot quantify until correlation restored
- **Resolution:** Complete Phase B2/B3 after correlation fix to identify and prioritize loop targets

## Preliminary Hotspot Candidates (Pending B2 Analysis)

Based on Phase A static analysis, expect these loops to appear in profiler:

1. **noise.py:171** — LCG RNG loop (HIGH priority)
   - Affects all noise image generation
   - Not vectorizable (stateful sequential RNG)
   - May be hot in noise paths but not core physics

2. **simulator.py:1568** — Phi-loop (MEDIUM uncertain)
   - Affects oscillation sweeps
   - Potentially vectorizable to batched dimension
   - Phase B2 profiler correlation will confirm/reject

3. **Uncertain Loop (Phase A)** — TBD from profiler
   - One loop flagged as needing runtime evidence
   - Phase B2 will identify and classify

## Recommendations for Phase B2

1. **BLOCKER:** Fix correlation issue first
   - Execute PERF-PYTORCH-004 P3.0b/P3.0c fixes
   - Rerun this profiler command after fix
   - Verify correlation >0.99 before proceeding to B2

2. **After correlation fix:**
   - Extract profiler call stacks with ≥1% inclusive time
   - Map to Phase A loop inventory (module, line number)
   - Produce `hot_loops.csv` with timing data
   - Flag GPU-relevant loops lacking CPU heat

3. **Defer B3 (backlog publication) until:**
   - Phase B2 completes with valid correlation
   - Top 3-5 loop targets identified with quantified impact
   - Design packets can reference accurate profiler evidence

## Artifacts Checklist (Phase B1 Complete)

- [x] Profiler trace captured (`trace.json` 1.7 MB)
- [x] Benchmark metrics recorded (`benchmark_results.json`)
- [x] Full command + metadata logged (`commands.txt`)
- [x] Environment snapshot (`env.json`)
- [x] Pytest collection log (`pytest_collect.log`)
- [x] Summary document (this file)
- [ ] Phase B2 hotspot correlation (BLOCKED on correlation fix)
- [ ] Phase B3 prioritised backlog (BLOCKED on B2)

## Next Actions

1. **Immediate (BLOCKER):** Fix PERF-PYTORCH-004 correlation issue
   - Reference: `docs/fix_plan.md` lines 120-200 (Attempt #16 identified weighted source divergence)
   - Fix tasks P3.0b (per-source polarization) + P3.0c (normalization)
   - Rerun profiler after fix with same command

2. **After correlation >0.99:**
   - Execute Phase B2 (loop→trace correlation)
   - Produce `hot_loops.csv` under this same stamp directory
   - Update fix_plan with Phase B2 metrics

3. **Archive plan after Phase C:**
   - Complete B3 (backlog publication)
   - Execute Phase C handoff (design packets for top targets)
   - Mark VECTOR-GAPS-002 as `done` when all high-priority loops vectorized or deferred with rationale

## Sign-Off

Phase B1 profiler capture complete with artifacts. **Phase B2 BLOCKED on correlation restoration.**
Supervisor (galph) handoff required to resolve PERF-PYTORCH-004 before continuing vectorization work.

---

**Stamped:** 2025-10-09T07:04:58Z
**Next Review:** After PERF-PYTORCH-004 P3.0b/P3.0c fixes land
