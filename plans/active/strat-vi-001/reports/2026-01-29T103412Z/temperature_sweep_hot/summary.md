# Extended Temperature Sweep Summary (T = {1, 2, 4, 8})

**Date:** 2026-01-29
**Objective:** standard ELBO
**Config:** 25 iterations, k=4 samples, obs_mean=25, normalization=mean, seed=321, 32×32 detector

## Results

| Temperature | σ_mean (°) | LogLik     | KL       | |∇μ|      | |∇ρ|     |
|-------------|-----------|------------|----------|----------|---------|
| 1.0         | 0.809     | 8.713e+04  | 9.37e-01 | 2.04e+01 | 3.05e+00 |
| 2.0         | 0.808     | 1.743e+05  | 9.91e-01 | 4.03e+01 | 4.83e+00 |
| 4.0         | 0.808     | 3.485e+05  | 1.03e+00 | 8.01e+01 | 8.21e+00 |
| 8.0         | 0.807     | 6.970e+05  | 1.06e+00 | 1.60e+02 | 1.48e+01 |

## Observations

- **σ_mean is unchanged across temperatures** (~0.81° for all T). Hotter temperatures do not improve σ recovery within 25 iterations.
- **Gradient magnitudes scale linearly with T** (as expected: ∂(ll/T)/∂θ = (1/T)·∂ll/∂θ scaled by T gives same direction, larger step). |∇μ| goes 20→160, |∇ρ| goes 3→15.
- **No NaN or divergence** at T=8.
- **Interpretation:** The likelihood temperature rescales gradients uniformly but does not change the loss landscape geometry enough to escape the σ ≈ 0.8° plateau. The posterior collapse is structural, not a gradient-magnitude issue.
