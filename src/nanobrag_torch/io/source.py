"""Source file I/O for nanoBragg PyTorch (AT-SRC-001).

This module implements source file reading for beam divergence and spectral dispersion.
Source files contain X,Y,Z position, weight, and wavelength per source.
"""

from pathlib import Path
from typing import List, Tuple, Optional
import torch
import numpy as np


def read_sourcefile(
    filepath: Path,
    default_wavelength_m: float,
    default_source_distance_m: float = 10.0,
    beam_direction: Optional[torch.Tensor] = None,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Read source file containing X,Y,Z position, weight, and wavelength.

    Per spec section "Sources, Divergence & Dispersion":
    Each line contains up to 5 columns: X, Y, Z (position in meters),
    weight (dimensionless), λ (wavelength in meters).

    Missing fields default to:
    - Position along -source_distance·b (source_distance default 10 m)
    - Weight = 1.0
    - λ = λ0 (default wavelength)

    Positions are normalized to unit direction vectors.
    The weight column is read but ignored (equal weighting results).

    Args:
        filepath: Path to source file
        default_wavelength_m: Default wavelength in meters (λ0)
        default_source_distance_m: Default source distance in meters (10 m)
        beam_direction: Unit beam direction vector (default [0,0,1])

    Returns:
        Tuple of:
        - directions: (N, 3) tensor of unit direction vectors
        - weights: (N,) tensor of weights (currently all 1.0 per spec)
        - wavelengths: (N,) tensor of wavelengths in meters
    """
    if beam_direction is None:
        beam_direction = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)

    directions = []
    weights = []
    wavelengths = []

    # Default position is along -source_distance·b
    default_position = -default_source_distance_m * beam_direction

    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) == 0:
                continue

            # Parse available columns
            if len(parts) >= 3:
                # X, Y, Z provided
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                position = torch.tensor([x, y, z], dtype=torch.float64)
            elif len(parts) == 2:
                # X, Y provided, Z defaults to 0
                x, y = float(parts[0]), float(parts[1])
                position = torch.tensor([x, y, 0.0], dtype=torch.float64)
            elif len(parts) == 1:
                # Only X provided, Y and Z default to 0
                x = float(parts[0])
                position = torch.tensor([x, 0.0, 0.0], dtype=torch.float64)
            else:
                # Use default position (should not happen since we skip empty lines)
                position = default_position.clone()

            if len(parts) >= 4:
                # Weight provided
                weight = float(parts[3])
            else:
                # Default weight
                weight = 1.0

            if len(parts) >= 5:
                # Wavelength provided
                wavelength = float(parts[4])
            else:
                # Default wavelength
                wavelength = default_wavelength_m

            # Normalize position to unit direction vector
            direction = position / torch.linalg.norm(position)

            directions.append(direction)
            weights.append(weight)
            wavelengths.append(wavelength)

    if len(directions) == 0:
        raise ValueError(f"No valid source lines found in {filepath}")

    # Convert to tensors
    directions = torch.stack(directions)
    # Per spec AT-SRC-001: "intensity contributions SHALL sum with per-source λ and weight"
    # Note: There's a spec contradiction - line 151 says weights are ignored,
    # but AT-SRC-001 requires weights to be applied. We follow the normative test.
    weights = torch.tensor(weights, dtype=torch.float64)
    wavelengths = torch.tensor(wavelengths, dtype=torch.float64)

    return directions, weights, wavelengths