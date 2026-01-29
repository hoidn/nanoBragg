# Prior Schedule Canonical Benchmark Summary

**Date:** 2026-01-29
**Plan:** docs/plans/2026-01-29-vi-prior-geometry.md §Task 4
**Detector:** 64×64 (best from Task 3 sweep)
**Iterations:** 150
**Prior schedule:** start=2.0°, end=0.5°, warmup=120 steps, log_σ=0.2
**KL annealing:** β=0.2→1.0, warmup=120 steps
**Observations:** mean=25, normalization=mean, seed=321

## Results

| Method   | Final σ (°) | Final Loss     | ≥1.5° criterion |
|----------|-------------|----------------|-----------------|
| MC       | 1.517       | 48.49          | PASS             |
| Analytic | 2.866       | 591.70         | PASS (overshoot) |
| VI       | 0.166       | -325993.59     | **FAIL**         |

## Analysis

1. **VI FAILED the ≥1.5° criterion.** The posterior collapsed to σ=0.166° after 150 iterations despite informative prior scheduling (start=2.0°→0.5° over 120 steps) and KL annealing (β=0.2→1.0 over 120 steps).
2. **MC achieved 1.517°** (passes), confirming the observation-scale parity fix works for MSE-based refinement.
3. **σ trajectory (from log):** VI σ peaked somewhere during the warmup phase then collapsed: iter 80 σ≈0.30°, iter 100 σ≈0.20°, iter 120 σ≈0.21°, iter 140 σ≈0.25°, iter 149 σ≈0.21°. The prior schedule delays but does not prevent collapse.
4. **Root cause:** The Poisson likelihood landscape is structurally flat near σ≈0.1–0.3° for this 100Å cubic cell / 6.2Å wavelength / 64×64 geometry. No combination of prior scheduling, KL annealing, temperature scaling, IWAE, or alternative parameterizations has overcome this barrier.

## Conclusion

**Informative priors do not recover VI σ ≥ 1.5°.** The prior schedule is a useful regularization tool but cannot overcome the fundamental likelihood landscape geometry. The VI posterior collapse is a structural optimization issue.

**Recommended next steps:**
1. Investigate multi-scale crystal geometry (smaller cell, shorter wavelength) to place more Bragg peaks on detector → richer likelihood curvature
2. Consider normalizing flows or mixture posteriors that can represent multimodal σ landscapes
3. Explore discrete-continuous hybrid approaches where VI learns a soft selection over MC domain counts
