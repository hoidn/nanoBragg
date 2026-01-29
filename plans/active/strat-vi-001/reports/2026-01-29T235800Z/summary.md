# Hybrid MC-VI Evidence — Turn Summary

**Date:** 2026-01-29
**Plan:** `docs/plans/2026-01-29-hybrid-benchmark-evidence.md`
**Focus:** STRAT-VI-001 Task 27 — Hybrid MC-VI escalation

## Results

### Diagnostics (10 MC + 50 VI iterations, 64×64, obs_mean=25, seed=321)
- MC warm-start σ trajectory: 0.45° → 0.04° (collapsed toward zero, not toward truth=2.0°)
- VI σ trajectory: oscillated 0.02°–0.31°, no recovery
- Total runtime: ~1.1s

### Canonical Benchmark (10 MC + 150 VI iterations, 64×64, obs_mean=25, KL β=0.2→1.0 warmup=120)
| Pipeline | Final σ (deg) | Target (deg) | Criterion |
|----------|--------------|-------------|-----------|
| MC standalone | 1.52 | 2.0 | ✅ ≥1.5° |
| Analytic | 2.87 | 2.0 | overshoots |
| VI standalone | 0.09 | 2.0 | ❌ collapsed |
| Hybrid MC→VI | 0.02 | 2.0 | ❌ collapsed |

### Root Cause
The MC warm-start stage's MSE loss landscape for this geometry (cubic 100Å cell, 64×64 detector) is biased toward σ→0. Rather than warm-starting σ near ground truth, MC pushes σ to 0.04°, worsening the VI initialization.

## Verdict
**FAILED ≥1.5° criterion.** This is the 9th failed VI mitigation attempt. STRAT-VI-001 should be closed as failed.

## Artifacts
- `hybrid_diagnostics/hybrid_summary.json` — 10+50 iter diagnostics
- `hybrid_benchmark/vi_vs_mc_summary.json` — canonical 150-iter benchmark
- `hybrid_benchmark/vi_vs_mc_loss.png` — loss curves

## Next Steps
Escalate to: (a) Gaussian likelihood, (b) amortized multi-image inference, or (c) corrected analytic kernel (FND-PROB-2026-01 unit fix).
