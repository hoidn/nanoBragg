# Main Strategy: Probabilistic Forward Modeling (3–6 Months)

Date: 2026-01-29
Horizon: 3–6 months
Owner: nanoBragg PyTorch initiative

## Thesis
The near-term scientific objective is to replace Monte Carlo mosaic sampling with an analytic probabilistic forward model that preserves physical fidelity while delivering faster, smoother refinement. The core claim is that the diffraction simulator should marginalize over orientation distributions rather than enumerate them, turning a numerical nuisance into a closed-form, differentiable operator. This shift is positioned as a publishable methodological advance, not just an optimization, and it becomes the enabling layer for later probabilistic inference and multi-image refinement.

This strategy is anchored in the design decisions documented in:
- `docs/plans/2026-01-29-probabilistic-simulator-design.md`
- `docs/plans/2026-01-29-probabilistic-simulator-implementation.md`
- SUPERVISOR: add plans as the project progresses


Here is a refined version of the strategy document, elevated to the tone of a Technical Lead/Product Owner briefing. It emphasizes **strategic intent, scientific ROI, and risk management** while retaining the specific technical mandates required for execution.

***

# Strategy: Probabilistic Forward Modeling (Horizon: 3–6 Months)

**Document ID:** STRAT-2026-01-PROB
**Status:** Active / Execution Phase
**Owner:** nanoBragg PyTorch Initiative
**Date:** 2026-01-29

## 1. Executive Summary
The primary objective for the next cycle is to transform `nanoBragg` from a stochastic simulation tool into a **differentiable probabilistic engine**.

Currently, modeling crystal disorder (mosaicity) relies on brute-force Monte Carlo sampling, which scales linearly with fidelity ($O(N)$) and injects stochastic noise into gradients. We will replace this with an **analytic probabilistic model** that marginalizes over orientation distributions in closed form.

**Strategic Value:** This is not merely an optimization; it is a **methodological pivot**. By converting the numerical nuisance of mosaicity into a smooth, differentiable operator, we unlock:
1.  **Orders-of-magnitude speedups** (10x–100x) for diffuse scattering refinement.
2.  **Noise-free gradients**, enabling the use of advanced optimizers (LBFGS) and Variational Inference (VI).
3.  **A publishable advance** in differentiable crystallography.

## 2. The Scientific Thesis
**Current State:** Mosaicity is simulated by summing intensities from $N$ discrete crystal copies.
*   *Problem:* High fidelity requires high $N$ (slow). Low $N$ creates noisy loss landscapes (optimization fails).
*   *Result:* Refinement of diffuse scattering is computationally prohibitive.

**Future State:** Mosaicity is modeled as a resolution-dependent Gaussian convolution in reciprocal space.
*   *Insight:* The rotational distribution of the crystal maps analytically to a Gaussian broadening of the Reciprocal Lattice Point (RLP).
*   *Benefit:* The cost becomes $O(1)$ (independent of mosaic spread). The loss landscape becomes smooth and convex.

## 3. Technical Design Anchors (Non-Negotiables)
To ensure this initiative integrates cleanly with the existing ecosystem, the following architectural decisions are **binding**:

### A. The "Drop-in" API Contract
The new capability will be exposed via a subclass, `ProbabilisticSimulator`, which inherits strictly from `Simulator`.
*   **Constraint:** It must accept the *exact same* configuration objects (`CrystalConfig`, etc.) as the standard engine.
*   **Behavior:** The parameter `mosaic_domains` is treated as infinite/irrelevant. The parameter `mosaic_spread_deg` drives the analytic width $\sigma$.
*   **Why:** This ensures zero friction for A/B testing and allows existing scripts to switch backends by changing a single class instantiation.

### B. Physically Grounded "Angular" Broadening
We reject simple isotropic blurring. The model must preserve the physics of rotational disorder:
*   **Constraint:** The Gaussian width $\sigma$ must scale with the scattering vector magnitude $|q|$.
*   **Kernel Logic:** `sigma = |q| * tan(mosaic_spread_rad) + epsilon`.
*   **Why:** This preserves the physical reality that high-resolution spots blur more than low-resolution spots, which is critical for accurate parameter refinement.

### C. Generalized Geometry (Full Metric Tensor)
We reject "cubic-only" shortcuts.
*   **Constraint:** Reciprocal mismatch $\Delta Q$ must be calculated using the rotated reciprocal vectors:
    `dQ = dh*a* + dk*b* + dl*c*`
*   **Why:** This guarantees support for triclinic, monoclinic, and non-orthogonal systems immediately, preventing "demo fragility" where the code breaks on real-world protein data.

### D. "Stash-and-Patch" Isolation
*   **Constraint:** The `ProbabilisticSimulator` must manage its own state injection. It will temporarily patch the configuration to `mosaic=0` (to freeze the geometric center) while passing the true spread to the physics kernel.
*   **Why:** This decouples the probabilistic logic from the legacy Monte Carlo geometry engine without requiring a rewrite of the core `Simulator.run` loop.

## 4. Evidence Strategy: "The Killer Demo"
We will drive this development via a single, decisive benchmark artifact.

**The Benchmark:** `scripts/benchmark_probabilistic.py`
*   **Scenario:** Refinement of a small-cell, high-mosaicity (2.0°) dataset (derived from `refinement_demo_diffuse`).
*   **Competition:**
    *   *Baseline:* Monte Carlo Simulator (`domains=5`). Fast but noisy.
    *   *Challenger:* Probabilistic Simulator. Fast and smooth.
*   **Ground Truth:** Monte Carlo Simulator (`domains=50`). High fidelity, very slow.

**Success Criteria (The "Win"):**
1.  **Speed:** Analytic iteration time is **>4x faster** than the Baseline.
2.  **Convergence:** Analytic loss curve is monotonic and reaches a lower final error than the Baseline.
3.  **Visual:** A generated plot (`demo_outputs/probabilistic_vs_mc_loss.png`) visibly demonstrates the analytic curve plummeting while the Monte Carlo curve jitters.

**Measured Results (2026-01-29, 150 iterations, CPU, 64×64 detector):**
- Speedup: **1.9×** (baseline 0.009s/iter, probabilistic 0.005s/iter).
- Baseline converged from 0.5° → 1.46° (true: 2.0°), final loss 1.30e-04.
- Probabilistic spread did not move (0.5° → 0.5°), final loss 2.57e-04.
- **Finding:** The analytic Gaussian envelope produces near-zero gradients for `mosaic_spread_deg` in this geometry regime because `σ ≫ |ΔQ|` for all sampled pixels, making the envelope ≈ 1.0 everywhere. This is the **Model Mismatch** risk from §5. Next step: investigate higher-resolution or non-cubic geometries where off-Bragg contributions are more significant.
- Artifacts: `demo_outputs/probabilistic_vs_mc_loss.png`, `demo_outputs/probabilistic_vs_mc_summary.json`, `plans/active/strat-prob-002/reports/2026-01-29T061003Z/`.

## 5. Risk Assessment & Mitigation

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Model Mismatch** | Analytic Gaussian does not perfectly match the sum-of-discrete-rotations. | Use the "Angular Broadening" ($\sigma \propto |q|$) constraint to minimize physical discrepancy. Accept slight residual if convergence behavior is superior. |
| **Gradient Detachment** | Implementation accidentally detaches gradients (e.g., using `.item()` on spread). | Strict code review enforcing `torch.autograd.gradcheck` on the new kernel during development. |
| **Scope Creep** | Temptation to implement Voigt profiles, spectral dispersion, or beam divergence simultaneously. | **Strict Scope Boundary:** Mosaicity only. Beam divergence remains discrete (Monte Carlo) for this phase. |

## 6. Strategic Horizon (What this enables)
Completing this initiative creates the **foundation** for the next two major milestones:

1.  **Sparse/Grainy Modeling:** Once we have a differentiable probability distribution, we can replace the single Gaussian with a *Mixture of Gaussians* to model sparse, grainy crystals (e.g., VAE latent spaces).
2.  **Multi-Image Global Refinement:** "Recovering the structure factor" requires thousands of forward passes. This is computationally impossible with the slow Monte Carlo engine but becomes feasible with the $O(1)$ Probabilistic engine.

## 7. Immediate Action Plan
1.  **Implement** `src/nanobrag_torch/simulators/probabilistic.py` (The Kernel).
2.  **Implement** `scripts/benchmark_probabilistic.py` (The Evidence).
3.  **Execute** Benchmark and generate the plot.
4.  **Review** results with PIs to authorize the Multi-Image Refinement phase.
