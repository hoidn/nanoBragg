# Variational Mosaicity Simulator Design (Per-Crystal VI)

Date: 2026-01-29
Owner: nanoBragg PyTorch initiative
Status: Proposed

## Summary
Replace the analytic mosaic broadening kernel with a variational inference (VI)
model that directly samples mosaic rotations from a reparameterized posterior.
The new simulator marginalizes over orientations via a small Monte Carlo average
(K samples) and optimizes a per-crystal posterior over mosaic spread. This
restores meaningful gradients for mosaicity while keeping compute manageable and
fully differentiable. The likelihood uses a Poisson model over observed counts.

## Goals
- Replace analytic Gaussian mosaic envelope with VI over mosaic rotations.
- Per-crystal posterior over mosaic spread (mosaicity-only VI).
- Reparameterized sampling for stable gradients and gradcheck compatibility.
- Preserve existing API surface; new simulator is a drop-in alternative.
- Provide benchmark + tests that compare MC, analytic, and VI behaviors.

## Non-Goals
- Joint VI over orientation, beam divergence, scale, or noise parameters.
- Full Bayesian treatment of structure factors or multi-image refinement.
- Introducing new noise models beyond the Poisson likelihood.

## Model Definition
We model mosaicity as a latent rotation distribution centered at the identity.
For each forward pass, we sample K rotations and average their intensities.

- Latent parameter: mosaic spread (sigma) per crystal.
- Variational posterior: log-normal or normal over log sigma.
- Prior: log-normal or half-normal over sigma.
- Likelihood: Poisson on observed counts given simulated intensities.

ELBO:
  E_q[ log p(y | I(R, phi)) ] - KL(q(sigma) || p(sigma))

## Variational Family and Reparameterization
- Sample epsilon ~ N(0, 1)
- sigma = exp(mu + rho * epsilon)
- Sample base axes and base angles epsilon_theta ~ N(0, 1)
- theta = sigma * epsilon_theta
- Rotation R(u, theta) via Rodrigues formula (u is normalized base axis)

This mirrors the deterministic mosaic rotation generator but replaces the fixed
spread with a differentiable latent. It avoids analytic envelopes entirely.

## Data Flow (Per Forward Pass)
1) Compute baseline geometry (phi steps, detector vectors) once.
2) Sample K mosaic rotations from q(sigma) (per crystal).
3) For each rotation, compute intensity using existing physics kernels.
4) Average intensities across K to approximate E_q.
5) Evaluate Poisson log-likelihood against observed data.
6) Add KL(q||p) penalty to form ELBO.

## Architecture Plan
- New simulator: `VariationalMosaicSimulator` (subclass of `Simulator`).
- New module for VI parameters and KL: `src/nanobrag_torch/vi/mosaic_posterior.py`.
- New kernel: `compute_vi_mosaic_physics(...)` with K-sample loop.
- New training/benchmark script to compare MC vs analytic vs VI.

## Deprecation Plan (Analytic)
Once VI is validated against benchmarks and tests, the analytic mosaic simulator
will be deprecated:
- Documentation marks analytic as legacy.
- New workflows recommend VI by default.
- Analytic remains available for reproduction until removal is approved.

## Testing
- Determinism test with fixed seed and K=1.
- Gradcheck for q(sigma) parameters.
- Sigma->0 convergence to no-mosaic baseline.
- K->large convergence towards analytic envelope behavior.
- Benchmark plot: speed vs loss vs gradient stability.

## Risks
- Small K may under-approximate the posterior; use K=4-8 for stability.
- Poor prior choice can bias sigma; keep a weakly informative prior.
- Performance regressions if K is too large; enforce a hard cap.

## References
- docs/plans/2026-01-29-probabilistic-simulator-design.md
- docs/strategy/mainstrategy.md
- docs/architecture/pytorch_design.md (gradient/reparameterization guidance)
