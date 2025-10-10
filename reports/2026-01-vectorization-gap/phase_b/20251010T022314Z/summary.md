# Phase B1 Profiler Rerun (20251010T022314Z)

## Status: ❌ BLOCKED (parity threshold not met)

## Command
```bash
NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts
```

## Metrics

- **correlation_warm**: 0.721175 (CRITICAL: −38% from ≥0.999 threshold)
- **correlation_cold**: 0.721175 (same, deterministic issue)
- **speedup_warm**: 1.15× (PyTorch faster than C)
- **speedup_cold**: 0.30× (C faster, includes compilation overhead)
- **cache_speedup**: 64480.5× (setup time: cold=169.1ms, warm=0.0ms)

## Threshold Analysis

Per `plans/active/vectorization-gap-audit.md` Phase B1 and `input.md` blocked protocol:

- **Required**: correlation ≥ 0.999 and |sum_ratio − 1| ≤ 5e-3
- **Actual**: correlation = 0.721175 (−0.278 below threshold, 27.8% deficit)
- **Verdict**: BLOCKED - profiler trace cannot be used for hotspot analysis until parity restored

## Artifacts

- Profile trace: `reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/failed/profile_4096x4096/trace.json` (UNRELIABLE until parity fixed)
- Benchmark results: `reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/failed/benchmark_results.json`
- Profile run log: `reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/profile_run.log`
- Test collection: `reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/collect.log` (694 tests discovered)
- Environment: `reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/env.json` (Python 3.13.5, PyTorch 2.7.1+cu126)
- Commands: `reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/commands.txt`

## Root Cause Hypotheses

This is the **EIGHTH consecutive profiler failure** at correlation ≈0.721 (Attempts #3, #4, #6, #7, and now #8 in fix_plan.md [VECTOR-GAPS-002]). The issue is:

1. **Deterministic**: Both cold and warm runs show identical low correlation (0.721175) → not a caching/compilation artifact
2. **Persistent**: Unchanged across multiple sessions and commits from 2025-12-25 through 2025-10-10
3. **Contradicts prior evidence**: Attempt #5 (2025-12-25) showed correlation_warm=0.999998, indicating a regression occurred after that date
4. **Scope**: Large benchmark (4096×4096) fails parity, but whether smaller ROIs also fail is unknown

### Hypothesized causes (ordered by likelihood):

1. **Regression between Attempt #5 (2025-12-25) and current HEAD (22ea5c18)**
   - Commits after 2025-12-25 may have introduced a physics bug affecting large ROI simulations
   - Git bisect between known-good and current HEAD required

2. **SOURCE-WEIGHT-001 Phase H incomplete**
   - Phase H parity memo exists (`reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md`)
   - But did it validate ≥0.999 correlation for 4096² benchmark specifically, or only smaller test cases?
   - If memo only covers small ROIs, Phase H may need reopening for large-ROI validation

3. **Configuration mismatch in benchmark_detailed.py**
   - C invocation vs PyTorch setup may have implicit differences
   - Compare parameters vs known-good Attempt #5 run

4. **Device/dtype configuration issue**
   - Command specifies `--device cpu --dtype float32`, but C code uses different precision
   - Verify C binary is compiled with consistent floating-point settings

5. **RNG seed or normalization divergence**
   - Weighted-source normalization, mosaic RNG, or noise RNG may have regressed
   - Parallel trace comparison required to identify first numeric divergence

## Immediate Next Actions (per blocked protocol)

1. **ESCALATE TO SUPERVISOR (galph)** — This is a critical regression requiring triage
2. **BLOCK Phase B2/B3** — Cannot proceed with vectorization gap analysis until correlation ≥0.999
3. **RUN AT-PARALLEL VALIDATION**:
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py
   ```
4. **PARALLEL TRACE DEBUGGING** (per `docs/debugging/debugging.md` §2.1):
   ```bash
   python scripts/debug_pixel_trace.py  # PyTorch trace
   # Compare vs instrumented C trace to find first numeric divergence
   ```
5. **GIT BISECT** (if AT-PARALLEL tests also fail):
   ```bash
   git bisect start
   git bisect bad HEAD
   git bisect good <commit-from-attempt-5>  # Find SHA from 2025-12-25
   # Test each commit with benchmark_detailed.py correlation check
   ```

## Notes

- Cache effectiveness (64480.5× speedup) validates PERF-PYTORCH-004 caching work
- Warm speedup 1.15× indicates PyTorch is faster than C when parity is ignored (but physics is wrong)
- Test collection passed (694 tests), suggesting import/collection health is good
- Per `input.md` blocked protocol, this failure has been logged in `docs/fix_plan.md` [VECTOR-GAPS-002] Attempts History
