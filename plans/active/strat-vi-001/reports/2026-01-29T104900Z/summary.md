# STRAT-VI-001 — Adaptive Poisson Scaling Benchmark Summary

**Date:** 2026-01-29
**Plan:** `docs/plans/2026-01-29-vi-canonical-benchmark-refresh.md`

## Result

VI σ **did NOT** reach the ≥1.5° target. Final σ = 0.103° (target 2.0°).

## Key Metrics

| Method | σ final (deg) | Loss first | Loss last |
|--------|--------------|-----------|----------|
| VI | 0.103 | -79386 | -79818 |
| MC | 0.024 | 2278.1 | 2277.2 |
| Analytic | 3.214 | 2439.8 | 2336.4 |

## Observation Stats

- raw_mean: 0.810, raw_max: 6.384
- scale: 30.88, scale_mode: mean
- mean_counts: 24.97, max_counts: 234
- seed: 321

## Follow-Up

σ collapsed despite adaptive scaling producing non-zero observations. Next: decompose likelihood vs KL per iteration, try higher observation counts, consider non-centered posterior.
