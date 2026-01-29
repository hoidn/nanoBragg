# Extended Temperature Sweep Summary (T={1,2,4,8})

**Timestamp:** 2026-01-29T104711Z
**Plan:** `docs/plans/2026-01-29-vi-temperature-iwae-followup.md` Task 1

## Configuration
- Iterations: 25, k-samples: 4, detector: 32x32
- Observation: mean=25.0, normalization=mean, seed=321
- Objective: standard ELBO
- Temperatures: 1.0, 2.0, 4.0, 8.0

## Results

| T | σ_mean (°) | |∇μ| | |∇ρ| | ll/kl grad ratio |
|---|-----------|------|------|-----------------|
| 1.0 | 0.809 | 20.4 | 3.1 | 98.9 |
| 2.0 | 0.808 | 40.3 | 4.8 | 197.2 |
| 4.0 | 0.808 | 80.1 | 8.2 | 393.6 |
| 8.0 | 0.807 | 159.6 | 14.8 | 786.0 |

## Key Findings
- σ_mean is invariant to temperature (~0.81° for all T). Only gradient magnitudes scale linearly.
- No NaN or divergence at T=8.
- The σ plateau is structural — hotter likelihoods amplify gradients but do not change the optimization landscape geometry.

## Conclusion
Temperature alone does not resolve the VI posterior collapse. The σ≈0.81° barrier persists regardless of gradient magnitude.
