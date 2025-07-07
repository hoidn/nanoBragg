"""
Configuration dataclasses for nanoBragg PyTorch implementation.

This module defines strongly-typed configuration objects that replace the large
set of variables in the original C main() function.
"""

from dataclasses import dataclass


@dataclass
class CrystalConfig:
    """Configuration for crystal properties and orientation."""

    pass  # TODO: Implement based on C_Parameter_Dictionary.md


@dataclass
class DetectorConfig:
    """Configuration for detector geometry and properties."""

    pass  # TODO: Implement based on C_Parameter_Dictionary.md


@dataclass
class BeamConfig:
    """Configuration for X-ray beam properties."""

    pass  # TODO: Implement based on C_Parameter_Dictionary.md
