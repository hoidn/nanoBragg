"""
Core object models for nanoBragg PyTorch implementation.

This package contains the Crystal and Detector classes that encapsulate
the geometric and physical properties of the diffraction experiment.

ExperimentModel is provided as an optional Stage-A optimization helper
and is imported lazily to avoid circular import issues with Simulator.
"""

from .crystal import Crystal
from .detector import Detector

__all__ = ["Crystal", "Detector", "ExperimentModel"]


def __getattr__(name):
    """Lazy attribute access to avoid import-time cycles.

    ExperimentModel depends on Simulator, which depends on models.crystal /
    models.detector. Import ExperimentModel on first access rather than at
    package import time to prevent circular imports when Simulator is imported.
    """
    if name == "ExperimentModel":
        from .experiment import ExperimentModel  # type: ignore

        return ExperimentModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
