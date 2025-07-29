"""
Vectorized 3D geometry utilities for nanoBragg PyTorch implementation.

This module contains PyTorch implementations of all vector and geometry
operations from the original C code, designed for broadcasting and GPU acceleration.
"""

from typing import Tuple

import torch


def dot_product(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """
    Calculate dot product of vectors x and y.

    Args:
        x, y: Tensors with shape (..., 3) representing 3D vectors

    Returns:
        torch.Tensor: Scalar dot product for each vector pair
    """
    return torch.sum(x * y, dim=-1)


def cross_product(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """
    Calculate cross product of vectors x and y.

    Args:
        x, y: Tensors with shape (..., 3) representing 3D vectors

    Returns:
        torch.Tensor: Cross product vectors with shape (..., 3)
    """
    return torch.cross(x, y, dim=-1)


def magnitude(vector: torch.Tensor) -> torch.Tensor:
    """
    Calculate magnitude of vectors.

    Args:
        vector: Tensor with shape (..., 3) representing 3D vectors

    Returns:
        torch.Tensor: Magnitude for each vector
    """
    return torch.sqrt(torch.sum(vector * vector, dim=-1))


def unitize(vector: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Normalize vectors to unit length.

    Args:
        vector: Tensor with shape (..., 3) representing 3D vectors

    Returns:
        Tuple of (unit_vector, original_magnitude)
    """
    mag = magnitude(vector)
    # Use a small epsilon to avoid division by zero
    safe_mag = torch.where(mag > 1e-12, mag, torch.ones_like(mag))
    unit_vector = vector / safe_mag.unsqueeze(-1)
    # Ensure zero vectors remain zero
    unit_vector = torch.where(
        mag.unsqueeze(-1) > 1e-12, unit_vector, torch.zeros_like(unit_vector)
    )
    return unit_vector, mag


def rotate_axis(v: torch.Tensor, axis: torch.Tensor, phi: torch.Tensor) -> torch.Tensor:
    """
    Rotate vectors around arbitrary axes using Rodrigues' formula.

    Args:
        v: Vectors to rotate with shape (..., 3)
        axis: Unit vectors defining rotation axes with shape (..., 3)
        phi: Rotation angles in radians

    Returns:
        torch.Tensor: Rotated vectors with shape (..., 3)
    """
    # Ensure axis is unit vector for stability
    axis_unit, _ = unitize(axis)

    # Rodrigues' formula: v_rot = v*cos(phi) + (axis × v)*sin(phi) + axis*(axis·v)*(1-cos(phi))
    cos_phi = torch.cos(phi).unsqueeze(-1)
    sin_phi = torch.sin(phi).unsqueeze(-1)

    axis_dot_v = dot_product(axis_unit, v).unsqueeze(-1)
    axis_cross_v = cross_product(axis_unit, v)

    v_rot = (
        v * cos_phi + axis_cross_v * sin_phi + axis_unit * axis_dot_v * (1 - cos_phi)
    )

    return v_rot


def rotate_umat(v: torch.Tensor, umat: torch.Tensor) -> torch.Tensor:
    """
    Rotate vectors using rotation matrices.

    Args:
        v: Vectors to rotate with shape (..., 3)
        umat: Rotation matrices with shape (..., 3, 3)

    Returns:
        torch.Tensor: Rotated vectors with shape (..., 3)
    """
    # Matrix multiplication: umat @ v (broadcasting over leading dimensions)
    return torch.matmul(umat, v.unsqueeze(-1)).squeeze(-1)
