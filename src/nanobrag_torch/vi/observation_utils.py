"""Poisson observation sampling utilities for VI experiments.

Converts simulator intensity outputs to realistic photon counts by scaling
to a target fluence and applying Poisson sampling.  This bridges the gap
between the C-code default fluence (~1e28 photons/m²) and experimentally
realistic count levels (~1e13 photons/m²).

Reference: docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md Task 1
"""

from __future__ import annotations

import torch

# The C-code default fluence (photons per square metre).
C_DEFAULT_FLUENCE: float = 1.25932015286227086360700780544e28

# A realistic fluence for VI benchmarks (photons per square metre).
DEFAULT_FLUENCE_PHOTONS: float = 1e13


def poisson_sample_observations(
    image: torch.Tensor,
    *,
    fluence_scale: float = 1.0,
    seed: int | None = None,
) -> tuple[torch.Tensor, dict]:
    """Scale an intensity image and draw Poisson counts.

    Args:
        image: Non-negative intensity tensor (any shape).
        fluence_scale: Multiplicative factor applied to *image* before
            Poisson sampling.  For example, to convert from C-default
            fluence to 1e13 photons/m², pass ``1e13 / BeamConfig().fluence``.
        seed: Deterministic seed for the Poisson draw.

    Returns:
        ``(counts, metadata)`` where *counts* is a float32 tensor of
        integer photon counts and *metadata* is a dict with summary
        statistics suitable for JSON logging.
    """
    expected = image.clamp(min=0.0) * fluence_scale
    gen = torch.Generator(device=image.device)
    if seed is not None:
        gen.manual_seed(seed)
    counts = torch.poisson(expected.double(), generator=gen).float()
    meta = {
        "fluence_scale": fluence_scale,
        "seed": seed,
        "mean_counts": float(counts.double().mean().item()),
        "max_counts": float(counts.max().item()),
    }
    return counts, meta
