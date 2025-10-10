# Phase B1 Profiler Run - FAILED PARITY VALIDATION

**Timestamp:** 20251010T015244Z  
**Exit Status:** BLOCKED - Correlation threshold not met

## Failure Details

- **correlation_warm:** 0.721175 (required ≥0.999)
- **speedup_warm:** 1.19x (PyTorch faster than C)
- **Delta from threshold:** -0.278 (38% below required 0.999)

## Executed Command

```bash
NB_C_BIN=./golden_suite_generator/nanoBragg \
KMP_DUPLICATE_LIB_OK=TRUE \
python scripts/benchmarks/benchmark_detailed.py \
  --sizes 4096 \
  --device cpu \
  --dtype float32 \
  --profile \
  --iterations 1 \
  --keep-artifacts
```

## Artifacts

- `profile_run.log` — Full benchmark output
- `failed/benchmark_results.json` — Metrics JSON
- `failed/profile_4096x4096/trace.json` — PyTorch profiler trace (Chrome tracing format)
- `pytest_collect.log` — Test collection verification (105 tests discovered, collection passed)

## Observations

1. The 0.72 correlation indicates **significant C↔PyTorch divergence** in the 4096² case
2. This same correlation (0.721175) appeared in both COLD and WARM runs → deterministic issue, not cache-related
3. The profiler ran successfully and generated trace.json (185KB Chrome trace)
4. Test collection passed cleanly — no import/structural errors

## Root Cause Hypothesis

This correlation value (~0.72) is **far below** acceptance thresholds and suggests either:
- A regression in the PyTorch implementation since the last known-good run
- Source weighting / sampling divergence not yet resolved (despite SOURCE-WEIGHT-001 parity memo)
- Configuration mismatch between the benchmark harness and C reference

**Priority:** This is a **blocking failure** for Phase B1. Profiler data is available but cannot be trusted for vectorization analysis until C↔Py parity is restored.

## Next Actions (per input.md "If Blocked")

1. ✅ Captured artifacts to `failed/` directory
2. ✅ Verified test collection health (pytest --collect-only passed)
3. **TODO:** Record failure in `docs/fix_plan.md` Attempts History
4. **TODO:** Investigate regression (compare with last known-good 0.999998 run from 2025-10-09 interim re-audit)
5. **HOLD:** Phase B2/B3 profiler correlation pending resolution

## References

- Plan: `plans/active/vectorization-gap-audit.md` Phase B1
- Steering: `input.md` (2025-10-10)
- Known-good correlation: 0.999998 (simple-cubic harness, 2025-10-09 re-audit in `reports/benchmarks/20251009-161714/`)
- Thresholds: `docs/architecture/pytorch_design.md` §1.1.5 (corr ≥0.999, |sum_ratio−1| ≤5e-3)
