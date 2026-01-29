# Flow vs Log-Normal Diagnostics Summary

**Date:** 2026-01-29
**Task:** STRAT-VI-001 Task 26 — Flow posterior evaluation
**Setup:** 25 iters, 32x32 detector, obs_mean=25, k=4, KL weight=1.0 (no annealing for diagnostics)

## Results

| Metric | Flow (4-layer, hidden=32) | Log-Normal (baseline) |
|--------|--------------------------|----------------------|
| sigma_final | ~37-56 deg (blow-up) | 0.81 deg |
| sigma trajectory | 0.49 -> blow-up to 50+ deg | 0.49 -> 0.81 deg (monotonic) |
| gradient |grad_mu| | 100-1800 (erratic) | ~17 (stable) |
| gradient |grad_rho| | 3-143 (erratic) | ~2.5 (stable) |
| loss (final) | ~-80k (unstable) | ~-86.6k (stable) |

## Analysis

The normalizing flow posterior exhibits **catastrophic sigma blow-up**: instead of constraining sigma toward the target 2.0 deg, the flow layers amplify log-sigma samples, driving sigma to 37-56 degrees within 25 iterations. The gradient norms are 10-100x larger than baseline and highly erratic.

The log-normal baseline shows the expected gradual sigma increase (0.49 -> 0.81 deg) with stable gradients, consistent with prior findings (FND-VI-2026-01).

## 150-iter Canonical Benchmark

The flow posterior diverges to **NaN by iteration 2** on the 64x64 canonical benchmark (with KL annealing beta=0.2->1.0, prior schedule 2.0->0.5 deg). The flow layers introduce instability that compounds with the larger detector and warm-up schedule.

**Result: FAILED >= 1.5 deg criterion.** Flow posterior is not viable without significant architectural changes (e.g., spectral normalization, gradient clipping, or much smaller learning rates).

## Conclusion

The normalizing flow posterior does NOT resolve the structural VI posterior collapse. Instead, it introduces a new failure mode (sigma blow-up / NaN divergence) that is worse than the log-normal baseline's sigma collapse.

**Recommendation:** Escalate to hybrid MC-VI mitigation plan.
