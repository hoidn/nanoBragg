# Main Strategy: Probabilistic Forward Modeling (3–6 Months)

Date: 2026-01-29
Horizon: 3–6 months
Owner: nanoBragg PyTorch initiative

## Thesis
The near-term scientific objective is to replace Monte Carlo mosaic sampling with an analytic probabilistic forward model that preserves physical fidelity while delivering faster, smoother refinement. The core claim is that the diffraction simulator should marginalize over orientation distributions rather than enumerate them, turning a numerical nuisance into a closed-form, differentiable operator. This shift is positioned as a publishable methodological advance, not just an optimization, and it becomes the enabling layer for later probabilistic inference and multi-image refinement.

This strategy is anchored in the design decisions documented in:
- `docs/plans/2026-01-29-probabilistic-simulator-design.md`
- `docs/plans/2026-01-29-probabilistic-simulator-implementation.md`

## Design Anchors (Non-Negotiables)
- **Drop-in API:** The analytic model is exposed as `ProbabilisticSimulator`, a subclass of `Simulator`, with identical configuration semantics. This is essential for clean A/B comparisons and community adoption. The numeric nuisance parameter `mosaic_domains` is treated as infinite (ignored) without altering physical parameter meaning.
- **Analytic Mosaic Envelope:** Mosaicity is modeled as an angular Gaussian in rotation space; its effect on reciprocal space broadening scales with |q|. The kernel uses `sigma = |q| * tan(mosaic_spread_rad) + eps`, yielding resolution-dependent blur that matches rotational mosaic physics.
- **Full Metric Geometry:** Reciprocal mismatch is computed via the full metric tensor using rotated reciprocal vectors: `dQ = dh*a* + dk*b* + dl*c*`, `dr2 = dot(dQ, dQ)`. This preserves correctness for triclinic and non-orthogonal unit cells, preventing demo fragility.
- **Stash-and-Patch Run Semantics:** The analytic simulator generates geometry with `mosaic_domains=1` and `mosaic_spread=0` while retaining the true spread for the analytic envelope. This prevents double counting and isolates the probabilistic model from Monte Carlo mechanics.

These anchors are not implementation details; they define the public scientific identity of the simulator and must remain stable throughout the 3–6 month horizon.

## Scientific Narrative
The simulator becomes a probabilistic likelihood engine: given a distribution over orientations, it returns a diffraction image without stochastic sampling noise. This supports deterministic gradients and enables inference workflows (including variational methods) without embedding the optimizer in the simulator. The narrative emphasizes that the algorithm is physically grounded (rotation-induced broadening), not a neural approximation. The analytic model is not a different physical regime; it is the closed-form limit of the existing Monte Carlo approach.

## Evidence Strategy (Demonstration-First)
The strategy prioritizes a single, decisive benchmark that is PI-facing and reproducible:
- **Benchmark Domain:** Diffuse, high-mosaicity synthetic images (derived from `scripts/refinement_demo_diffuse.py`).
- **Baseline:** Monte Carlo simulation with `mosaic_domains=5` for refinement, ground truth generated with `mosaic_domains=50`.
- **Innovation:** Analytic probabilistic simulation using `ProbabilisticSimulator` with identical physical parameters.
- **Primary Artifact:** Loss vs wall-clock time plot with both curves. The analytic curve must reach lower loss faster and with smoother monotonic convergence.

The benchmark script is the public-facing evidence and should be usable as a single command without data wrangling. Its existence is a success condition, not a convenience.

## Scope Boundary
This horizon explicitly defers:
- Multi-image refinement / global structure factor learning.
- Rich VI models (VAEs, mixture posteriors, amortized inference).
- Experimental data pipelines and metadata tooling.

The intent is to establish a robust probabilistic forward model first, then layer inference and dataset infrastructure only once the physics core is validated and credible.

## Success Conditions (Must Hold)
The strategy is successful only if all of the following are true:

**Scientific Validity**
- Analytic broadening matches rotational mosaicity behavior (resolution-dependent blur). The analytic model must not show systematic residual rings or bullseye artifacts under non-cubic cells.
- The analytic model remains differentiable with respect to `mosaic_spread_deg` and does not detach gradients via scalar extraction.

**Performance & Convergence**
- Median iteration time for analytic refinement is at least **4x faster** than the Monte Carlo baseline (`mosaic_domains=5`) under identical settings.
- Final loss from analytic refinement is **<=** the Monte Carlo baseline loss in the same wall-clock budget.
- Loss curve for analytic refinement is **monotonic or near-monotonic** (no large stochastic oscillations).

**Reproducible Artifact**
- A single benchmark script produces:
  - `demo_outputs/probabilistic_vs_mc_loss.png`
  - A JSON summary with timings and final parameter errors.
- The artifact can be regenerated without manual data setup and is robust to non-cubic unit cell parameters.

**Architectural Integrity**
- Existing `Simulator` behavior remains untouched; golden tests are not regressed by analytic work.
- The probabilistic kernel is isolated to a new module and can be disabled by class selection alone.

## Risk Posture
- **Risk:** Analytic model underfits highly grainy/sparse mosaics.
  - **Acceptable in this phase.** The objective is high-mosaic smooth broadening, not sparse grains.
- **Risk:** Parameter coupling (mosaic + orientation) produces flat loss basins.
  - **Mitigated by:** using benchmark configurations with stable convergence and reporting sensitivity.
- **Risk:** Claims of speedup are dismissed as “unfair.”
  - **Mitigated by:** identical physical parameters and clear disclosure that Monte Carlo domain count is a numerical nuisance parameter.

## Downstream Readiness Signals
If all success conditions hold, the strategy considers the following directions validated for the next horizon:
- Sparse-grain modeling as mixture distributions (multi-modal mosaicity).
- Variational inference with the probabilistic simulator as a likelihood engine.
- Multi-image refinement once per-image forward passes are demonstrably fast and stable.

This strategy is deliberately narrow: it favors a strong, publishable signal over broad capability. It defines what “done” looks like for this horizon and uses the probabilistic simulator as the hinge for future scientific impact.
