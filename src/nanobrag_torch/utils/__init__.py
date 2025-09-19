"""
Utility functions for nanoBragg PyTorch implementation.

This package contains vectorized PyTorch implementations of geometry and
physics calculations from the original C code.
"""

# Import key functions for easy access
from .geometry import cross_product, dot_product, rotate_axis, unitize
from .physics import polarization_factor, sinc3, sincg
from .c_random import CLCG, mosaic_rotation_umat, umat2misset

__all__ = [
    "dot_product",
    "cross_product",
    "unitize",
    "rotate_axis",
    "sincg",
    "sinc3",
    "polarization_factor",
    "CLCG",
    "mosaic_rotation_umat",
    "umat2misset",
]
