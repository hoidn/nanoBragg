"""
Tensor utility functions for nanoBragg PyTorch implementation.

This module provides helper functions for tensor operations that preserve
gradient flow and maintain differentiability.
"""

from typing import Union

import torch


def as_tensor_preserving_grad(
    x: Union[float, int, torch.Tensor],
    device: torch.device,
    dtype: torch.dtype
) -> torch.Tensor:
    """
    Convert scalar or tensor to tensor while preserving gradient graph.

    Unlike torch.tensor(), this function preserves requires_grad=True
    when the input is already a tensor, maintaining gradient flow.
    This is critical for differentiable parameters that may be passed
    as tensors with requires_grad=True for gradient-based optimization.

    Pattern: Uses x.to(device, dtype) if tensor, else torch.tensor(x, device, dtype).
    This matches the pattern used in Crystal for cell parameters (crystal.py:69-86).

    Args:
        x: Scalar value or tensor to convert
        device: Target device
        dtype: Target dtype

    Returns:
        Tensor on specified device/dtype with gradient graph preserved

    Example:
        >>> wavelength = torch.tensor(6.2, requires_grad=True)
        >>> # WRONG: torch.tensor() detaches the graph
        >>> w1 = torch.tensor(wavelength, device='cpu', dtype=torch.float64)
        >>> w1.requires_grad
        False
        >>> # CORRECT: as_tensor_preserving_grad() preserves the graph
        >>> w2 = as_tensor_preserving_grad(wavelength, device='cpu', dtype=torch.float64)
        >>> w2.requires_grad
        True
    """
    if isinstance(x, torch.Tensor):
        return x.to(device=device, dtype=dtype)
    return torch.tensor(x, device=device, dtype=dtype)
