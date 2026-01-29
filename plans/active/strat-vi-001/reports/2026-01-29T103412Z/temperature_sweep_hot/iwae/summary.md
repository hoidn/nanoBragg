# IWAE + Temperature Sweep Summary

**Date:** 2026-01-29
**Objective:** IWAE (importance-weighted)
**Config:** 25 iterations, k=8 samples, obs_mean=25, normalization=mean, seed=321, 32×32 detector

## Results

| Temperature | σ_mean (°) | |∇μ|      | |∇ρ|      |
|-------------|-----------|----------|----------|
| 1.0         | 0.813     | ~2.6e+01 | ~1.4e+01 |
| 2.0         | 0.814     | ~5.3e+01 | ~2.5e+01 |
| 4.0         | 0.814     | ~1.1e+02 | ~5.1e+01 |
| 8.0         | 0.814     | ~2.3e+02 | ~1.0e+02 |

## Observations

- **σ_mean ≈ 0.81° for all configurations** — identical to the standard ELBO sweep. IWAE does not improve σ recovery.
- **IWAE produces slightly higher |∇ρ| than standard ELBO** at the same T, suggesting tighter gradient signal from importance weighting, but this does not translate to better σ movement.
- **No configuration reached σ ≥ 1.2°** — the conditional 150-iteration benchmark was **NOT triggered**.
- **Interpretation:** Neither hotter temperatures nor IWAE objective changes the fundamental σ plateau at ~0.81°. The posterior collapse appears to be a model/prior issue, not a gradient estimation or objective function issue.
