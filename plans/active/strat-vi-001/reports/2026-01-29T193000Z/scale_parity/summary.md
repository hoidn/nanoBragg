# VI Observation Scale Parity — Benchmark Report

**Date:** 2026-01-29T19:30Z
**Plan:** `docs/plans/2026-01-29-vi-observation-scale-parity.md` (Task 4)

## Benchmark Command

```bash
KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
python scripts/benchmark_vi_mosaic.py \
  --iterations 150 \
  --observation-mean 25.0 --observation-normalization mean --observation-seed 321 \
  --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120 \
  --diagnostics-log plans/active/strat-vi-001/reports/2026-01-29T193000Z/scale_parity/vi_diagnostics.json \
  --outdir plans/active/strat-vi-001/reports/2026-01-29T193000Z/scale_parity
```

## Observation Metadata

| Metric | Value |
| :--- | :--- |
| observation_scale | 30.88 |
| scale_mode | mean |
| seed | 321 |
| raw_mean | 0.810 |
| raw_max | 6.384 |
| target_mean_counts | 25.0 |
| mean_counts | 24.97 |
| max_counts | 234 |

## Results

| Method | Final σ (deg) | Target σ (deg) | ≥1.5° criterion |
| :--- | :--- | :--- | :--- |
| **MC** | **1.517** | 2.0 | **PASS** |
| VI | 0.086 | 2.0 | FAIL |
| Analytic | 2.866 | 2.0 | PASS (overshoots) |

## Interpretation

- **MC σ=1.517°** — observation-scale parity fixes the units mismatch and MC now recovers σ≥1.5° on scaled Poisson data for the first time.
- **VI σ=0.086°** — the posterior still collapses despite correct scaling. The Poisson likelihood landscape is locally flat near σ≈0.1–0.3° for this detector geometry (64×64, 100Å cubic cell, 1.0Å wavelength). This is consistent with all prior experiments (FND-VI-2026-01, FND-VI-2026-01b).
- **Analytic σ=2.866°** — overshoots target but demonstrates MSE loss converges in the right direction.

## Conclusion

Observation-scale parity is **necessary but not sufficient** for VI σ recovery. The fix correctly aligns all pipelines on the same scaled-count space and enables MC to pass the ≥1.5° criterion. VI's structural posterior collapse is an optimization geometry problem, not a units/scaling mismatch.

## Recommended Next Steps

1. Evaluate **temperature-scaled likelihoods** (multiply log-likelihood by T>1 to sharpen the gradient landscape)
2. Investigate **longer training schedules** (500–1000 iterations) with slower warmup
3. Consider **alternative posterior families** (mixture of log-normals, flow-based posteriors)
4. Explore **larger detector geometries** where the likelihood landscape may have more curvature
