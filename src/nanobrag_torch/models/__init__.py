"""
Core object models for nanoBragg PyTorch implementation.

This package contains the Crystal and Detector classes that encapsulate
the geometric and physical properties of the diffraction experiment.
"""

from .crystal import Crystal
from .detector import Detector

__all__ = ["Crystal", "Detector"]
