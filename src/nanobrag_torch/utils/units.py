"""
Unit conversion utilities for nanoBragg PyTorch implementation.

This module provides functions to convert between user-friendly units (e.g., mm)
and the internal unit system (Angstroms for length, radians for angles).
All functions preserve tensor properties and gradients.
"""

import torch
from typing import Union


def mm_to_angstroms(value: Union[float, torch.Tensor]) -> Union[float, torch.Tensor]:
    """
    Convert millimeters to Angstroms.

    Args:
        value: Value in millimeters

    Returns:
        Value in Angstroms (1 mm = 10,000,000 Å)
    """
    return value * 1e7


def meters_to_angstroms(
    value: Union[float, torch.Tensor],
) -> Union[float, torch.Tensor]:
    """
    Convert meters to Angstroms.

    Args:
        value: Value in meters

    Returns:
        Value in Angstroms (1 m = 1e10 Å)
    """
    return value * 1e10


def degrees_to_radians(value: Union[float, torch.Tensor]) -> Union[float, torch.Tensor]:
    """
    Convert degrees to radians.

    Args:
        value: Angle in degrees

    Returns:
        Angle in radians
    """
    if isinstance(value, torch.Tensor):
        return torch.deg2rad(value)
    else:
        # For scalar values, use torch's function but return scalar
        return torch.deg2rad(torch.tensor(value)).item()


def angstroms_to_mm(value: Union[float, torch.Tensor]) -> Union[float, torch.Tensor]:
    """
    Convert Angstroms to millimeters.

    Args:
        value: Value in Angstroms

    Returns:
        Value in millimeters (1 Å = 1e-7 mm)
    """
    return value * 1e-7


def angstroms_to_meters(
    value: Union[float, torch.Tensor],
) -> Union[float, torch.Tensor]:
    """
    Convert Angstroms to meters.

    Args:
        value: Value in Angstroms

    Returns:
        Value in meters (1 Å = 1e-10 m)
    """
    return value * 1e-10


def radians_to_degrees(value: Union[float, torch.Tensor]) -> Union[float, torch.Tensor]:
    """
    Convert radians to degrees.

    Args:
        value: Angle in radians

    Returns:
        Angle in degrees
    """
    if isinstance(value, torch.Tensor):
        return torch.rad2deg(value)
    else:
        # For scalar values, use torch's function but return scalar
        return torch.rad2deg(torch.tensor(value)).item()


def mm_to_meters(value: Union[float, torch.Tensor]) -> Union[float, torch.Tensor]:
    """
    Convert millimeters to meters.

    Args:
        value: Value in millimeters

    Returns:
        Value in meters (1 mm = 0.001 m)
    """
    return value * 0.001


def micrometers_to_meters(value: Union[float, torch.Tensor]) -> Union[float, torch.Tensor]:
    """
    Convert micrometers to meters.

    Args:
        value: Value in micrometers

    Returns:
        Value in meters (1 µm = 1e-6 m)
    """
    return value * 1e-6


def mrad_to_radians(value: Union[float, torch.Tensor]) -> Union[float, torch.Tensor]:
    """
    Convert milliradians to radians.

    Args:
        value: Value in milliradians

    Returns:
        Value in radians (1 mrad = 0.001 rad)
    """
    return value * 0.001
