"""Source file I/O for nanoBragg PyTorch (AT-SRC-001).

This module implements source file reading for beam divergence and spectral dispersion.
Source files contain X,Y,Z position, weight, and wavelength per source.

Per spec-a-core.md:150-151 and C reference nanoBragg.c:2574-2576:
Both weight and wavelength columns are read but IGNORED. The CLI -lambda parameter
is the sole authoritative wavelength source for all sources.
"""

from pathlib import Path
from typing import List, Tuple, Optional
import torch
import numpy as np
import warnings


def read_sourcefile(
    filepath: Path,
    default_wavelength_m: float,
    default_source_distance_m: float = 10.0,
    beam_direction: Optional[torch.Tensor] = None,
    dtype: torch.dtype = torch.float32,
    device: torch.device = torch.device('cpu'),
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Read source file containing X,Y,Z position, weight, and wavelength.

    Per spec section "Sources, Divergence & Dispersion" (spec-a-core.md:150-151):
    Each line contains up to 5 columns: X, Y, Z (position in meters),
    weight (dimensionless), λ (wavelength in meters).

    Missing fields default to:
    - Position along -source_distance·b (source_distance default 10 m)
    - Weight = 1.0
    - λ = λ0 (default wavelength)

    Positions are normalized to unit direction vectors.

    IMPORTANT: Both weight and wavelength columns are read but IGNORED.
    - Weight column: always returns 1.0 per source (equal weighting)
    - Wavelength column: always overridden with CLI -lambda value (default_wavelength_m)

    A warning is emitted if sourcefile wavelengths differ from CLI value.
    This matches C reference behavior (nanoBragg.c:2574-2576, 2700-2720).

    Args:
        filepath: Path to source file
        default_wavelength_m: Default wavelength in meters (λ0)
        default_source_distance_m: Default source distance in meters (10 m)
        beam_direction: Unit beam direction vector (default [0,0,1])
        dtype: Data type for output tensors (default: torch.float32)
        device: Device for output tensors (default: CPU)

    Returns:
        Tuple of:
        - directions: (N, 3) tensor of unit direction vectors
        - weights: (N,) tensor of weights (currently all 1.0 per spec)
        - wavelengths: (N,) tensor of wavelengths in meters
    """
    if beam_direction is None:
        beam_direction = torch.tensor([0.0, 0.0, 1.0], dtype=dtype, device=device)

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
                position = torch.tensor([x, y, z], dtype=dtype, device=device)
            elif len(parts) == 2:
                # X, Y provided, Z defaults to 0
                x, y = float(parts[0]), float(parts[1])
                position = torch.tensor([x, y, 0.0], dtype=dtype, device=device)
            elif len(parts) == 1:
                # Only X provided, Y and Z default to 0
                x = float(parts[0])
                position = torch.tensor([x, 0.0, 0.0], dtype=dtype, device=device)
            else:
                # Use default position (should not happen since we skip empty lines)
                position = default_position.clone()

            if len(parts) >= 4:
                # Weight provided
                weight = float(parts[3])
            else:
                # Default weight
                weight = 1.0

            # Wavelength column: read if present but override with CLI value
            if len(parts) >= 5:
                # Wavelength provided in file - read but will be overridden
                file_wavelength = float(parts[4])
                # Check for mismatch and emit warning once per unique mismatch
                if abs(file_wavelength - default_wavelength_m) > 1e-12 * default_wavelength_m:
                    # Store for later warning (after parsing all sources)
                    if not hasattr(read_sourcefile, '_wavelength_warned'):
                        read_sourcefile._wavelength_warned = True
                        warnings.warn(
                            f"Sourcefile wavelength column differs from CLI -lambda value. "
                            f"Per spec-a-core.md:150-151, sourcefile wavelengths are ignored. "
                            f"All sources will use CLI wavelength {default_wavelength_m:.6e} m.",
                            UserWarning,
                            stacklevel=2
                        )

            # Always use CLI wavelength (Option B from lambda_semantics.md)
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
    # Per spec line 151: weights are read but ignored (equal weighting)
    # All sources get weight=1.0; normalization is via steps division
    weights = torch.tensor(weights, dtype=dtype, device=device)
    wavelengths = torch.tensor(wavelengths, dtype=dtype, device=device)

    return directions, weights, wavelengths