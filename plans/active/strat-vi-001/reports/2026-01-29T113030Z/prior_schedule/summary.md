# Prior Schedule Multi-Geometry Sweep Summary

**Date:** 2026-01-29
**Plan:** docs/plans/2026-01-29-vi-prior-geometry.md §Task 3
**Prior schedule:** start=2.0°, end=0.5°, warmup=20 steps, log_σ=0.2
**Common params:** 25 iterations, k_samples=4, observation_mean=25, normalization=mean, seed=321

## Results

| Detector | σ_first (°) | σ_last (°) | σ_max_last (°) | |∇μ|_last | |∇ρ|_last | Status |
|----------|-------------|------------|-----------------|----------|----------|--------|
| 32×32    | 0.493       | 0.757      | 1.063           | 8.06     | 1.42     | OK     |
| 64×64    | 0.493       | 0.771      | 1.082           | 23.17    | 11.09    | OK     |
| 128×128  | 0.493       | —          | —               | NaN      | NaN      | CRASH  |

## Observations

1. **σ does not reach 1.5° at any resolution.** After 25 iterations with an informative prior (start=2.0°, end=0.5°), the posterior mean σ plateaus near ~0.76° for both 32×32 and 64×64.
2. **64×64 slightly outperforms 32×32** (σ_last=0.771° vs 0.757°), with ~3× higher gradient norms, indicating stronger likelihood signal at higher resolution.
3. **128×128 produces NaN gradients** at iteration 0 and crashes at iteration 1. The gradient computation fails with `RuntimeError: element 0 of tensors does not require grad`. This suggests a numerical issue (likely overflow or underflow in the Poisson likelihood) at 16384 pixels with observation_mean=25.
4. **Prior schedule effect:** The prior mean anneals from 2.0° → 0.5° over 20 steps. KL divergence drops from ~24 to ~2.3 by iteration 24, indicating the posterior is tracking the prior schedule. However, the likelihood signal is insufficient to push σ beyond ~0.77°.
5. **Gradient ratios:** At 64×64, the likelihood-to-KL gradient ratio for ρ is ~99×, meaning the likelihood dominates ρ updates. For μ the ratio is ~3×. This asymmetry suggests μ is more constrained by the prior.

## Conclusion

Informative priors with a linear schedule delay σ collapse but do not recover σ ≥ 1.5°. The 64×64 geometry is the best performer. The 128×128 crash needs investigation (likely numerical overflow in Poisson log-likelihood at scale).

**Recommendation for Task 4:** Use 64×64 for the 150-iter benchmark. Expect σ will plateau below 1.0°; the 1.5° criterion will likely not be met.
