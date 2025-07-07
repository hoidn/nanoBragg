"""
Vectorized physics utilities for nanoBragg PyTorch implementation.

This module contains PyTorch implementations of physical models and
calculations from the original C code.
"""

import torch


def sincg(u: torch.Tensor, N: torch.Tensor) -> torch.Tensor:
    """
    Calculate Fourier transform of 1D grating (parallelepiped shape factor).

    Used for crystal shape modeling in the original C code.

    Args:
        u: Fractional Miller index difference (h - h0)
        N: Number of elements in grating

    Returns:
        torch.Tensor: Shape factor values sin(Nπu)/sin(πu)
    """
    # Calculates sin(N*π*u)/sin(π*u), handling the u=0 case
    pi_u = torch.pi * u
    return torch.where(u.abs() < 1e-9, N, torch.sin(N * pi_u) / torch.sin(pi_u))


def sinc3(x: torch.Tensor) -> torch.Tensor:
    """
    Calculate 3D Fourier transform of sphere (spherical shape factor).

    Used for round crystal shape modeling in the original C code.

    Args:
        x: Input values

    Returns:
        torch.Tensor: Shape factor values
    """
    # TODO: Implement vectorized sinc3 function
    # Reference: C_Function_Reference.md sinc3 function
    raise NotImplementedError("sinc3 function to be implemented in Phase 2")


def polarization_factor(
    kahn_factor: torch.Tensor,
    incident: torch.Tensor,
    diffracted: torch.Tensor,
    axis: torch.Tensor,
) -> torch.Tensor:
    """
    Calculate polarization correction factor for scattering geometry.

    Args:
        kahn_factor: Polarization factor (0 to 1)
        incident: Incident beam vectors with shape (..., 3)
        diffracted: Diffracted beam vectors with shape (..., 3)
        axis: Polarization axis vectors with shape (..., 3)

    Returns:
        torch.Tensor: Polarization correction factors
    """
    # TODO: Implement vectorized polarization calculation
    # Reference: C_Function_Reference.md polarization_factor function
    raise NotImplementedError("polarization_factor function to be implemented in Phase 2")
