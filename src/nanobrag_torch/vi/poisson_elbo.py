"""
Poisson ELBO helper for variational mosaic inference.

Computes the negative evidence lower bound (ELBO) for a Poisson likelihood
model over observed diffraction counts:

    loss = -[ E_q[log p(y | I(sigma))] - KL(q(sigma) || p(sigma)) ]

where the expectation is approximated by K-sample Monte Carlo averaging
through the VariationalMosaicSimulator.

Design reference: docs/plans/2026-01-29-vi-mosaic-design.md §Model Definition
Implementation plan: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md Task 3
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import torch


@dataclass
class ELBODiagnostics:
    """Per-iteration diagnostics payload for VI spread-collapse analysis.

    All tensor fields are detached scalars safe for logging; the ``simulated``
    tensor retains its graph attachment so callers can still differentiate
    through the returned loss.

    Reference: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md Task 7
    """

    log_likelihood: float = 0.0
    kl: float = 0.0
    loss: float = 0.0
    kl_weight: float = 1.0
    sigma_mean_deg: float = 0.0
    sigma_std_deg: float = 0.0
    sigma_min_deg: float = 0.0
    sigma_max_deg: float = 0.0
    mu_grad_norm: float = float("nan")
    rho_grad_norm: float = float("nan")
    simulated: torch.Tensor | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Serialisable dict (drops the ``simulated`` tensor)."""
        d = {k: v for k, v in self.__dict__.items() if k != "simulated"}
        return d


def poisson_elbo(
    simulator,
    observed_counts: torch.Tensor,
    *,
    k_samples: int = 4,
    reduce: str = "mean",
    generator: torch.Generator | None = None,
    seed: int | None = None,
    pixel_batch_size: int | None = None,
    stochastic_pixel_count: int | None = None,
    clamp_eps: float = 1e-12,
    kl_weight: float = 1.0,
    return_components: bool = False,
    **kwargs,
) -> torch.Tensor | tuple[torch.Tensor, ELBODiagnostics]:
    """Compute negative Poisson ELBO for variational mosaic inference.

    Args:
        simulator: VariationalMosaicSimulator instance with a mosaic_posterior.
        observed_counts: Observed photon counts tensor matching detector shape.
        k_samples: Number of mosaic spread samples for MC expectation.
        reduce: Reduction mode for K-sample averaging ("mean" or "sum").
        generator: Optional torch.Generator for deterministic sampling.
        seed: Optional seed (creates a generator if generator is None).
        pixel_batch_size: Forwarded to simulator.run().
        stochastic_pixel_count: Forwarded to simulator.run().
        clamp_eps: Floor for simulated intensities to avoid log(0).
        return_components: If True, return ``(loss, ELBODiagnostics)``.
            The diagnostics include log-likelihood, KL, sampled sigma stats
            (mean/std/min/max in degrees), and gradient norms for mu/rho
            (populated after ``loss.backward()`` by the caller — until then
            they are NaN).
        **kwargs: Additional kwargs forwarded to simulator.run().

    Returns:
        Scalar loss tensor (negative ELBO), or ``(loss, ELBODiagnostics)``
        when *return_components* is True.
    """
    posterior = simulator.mosaic_posterior

    if generator is None and seed is not None:
        generator = torch.Generator(device=simulator.device)
        generator.manual_seed(seed)

    simulated = simulator.run(
        k_samples=k_samples,
        generator=generator,
        reduce=reduce,
        pixel_batch_size=pixel_batch_size,
        stochastic_pixel_count=stochastic_pixel_count,
        **kwargs,
    )
    if isinstance(simulated, tuple):
        simulated = simulated[0]

    observed = observed_counts.to(device=simulator.device, dtype=simulator.dtype)
    sim_clamped = simulated.clamp_min(clamp_eps)

    # Poisson log-likelihood: sum_pixels [ y * log(lambda) - lambda ]
    # (dropping log(y!) which is constant w.r.t. parameters)
    log_lik = (observed * sim_clamped.log() - simulated).sum()

    kl = posterior.kl_divergence()

    loss = -(log_lik - kl_weight * kl)

    if return_components:
        # Sample sigma stats (detached, for logging only)
        with torch.no_grad():
            _gen = torch.Generator(device=simulator.device)
            _gen.manual_seed(0)
            _sigma_samples = posterior.sample(k=max(k_samples, 8), generator=_gen)
            _sigma_deg = _sigma_samples * (180.0 / torch.pi)

        diag = ELBODiagnostics(
            log_likelihood=log_lik.detach().item(),
            kl=kl.detach().item(),
            loss=loss.detach().item(),
            kl_weight=kl_weight,
            sigma_mean_deg=_sigma_deg.mean().item(),
            sigma_std_deg=_sigma_deg.std().item(),
            sigma_min_deg=_sigma_deg.min().item(),
            sigma_max_deg=_sigma_deg.max().item(),
            simulated=simulated,
        )
        return loss, diag
    return loss


def populate_grad_norms(diag: ELBODiagnostics, posterior) -> None:
    """Fill gradient-norm fields after ``loss.backward()`` has been called.

    This is a separate function because backward must run before grad norms
    are available, yet we want to keep ``poisson_elbo`` itself clean.
    """
    if posterior.mu.grad is not None:
        diag.mu_grad_norm = posterior.mu.grad.detach().abs().item()
    if posterior.rho.grad is not None:
        diag.rho_grad_norm = posterior.rho.grad.detach().abs().item()
