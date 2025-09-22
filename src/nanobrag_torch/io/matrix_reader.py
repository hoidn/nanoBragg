"""Matrix file reader for nanoBragg PyTorch implementation."""

import torch
import numpy as np
from typing import Tuple


def read_matrix_file(filepath: str, wavelength: float = 1.0,
                    device=None, dtype=torch.float64) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Read MOSFLM-style A matrix file.

    The matrix file contains reciprocal lattice vectors scaled by 1/λ.

    Args:
        filepath: Path to matrix file
        wavelength: Wavelength in Angstroms to unscale the matrix
        device: PyTorch device
        dtype: PyTorch data type

    Returns:
        Tuple of (A_matrix, reciprocal_vectors) tensors
    """
    device = device if device is not None else torch.device('cpu')

    # Read matrix values from file
    values = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Parse numerical values
            parts = line.split()
            for part in parts:
                try:
                    values.append(float(part))
                except ValueError:
                    pass

    if len(values) < 9:
        raise ValueError(f"Matrix file must contain at least 9 values, found {len(values)}")

    # Take first 9 values and reshape into 3x3 matrix
    A_matrix = torch.tensor(values[:9], device=device, dtype=dtype).reshape(3, 3)

    # The matrix contains reciprocal vectors scaled by 1/λ
    # Unscale to get true reciprocal vectors
    reciprocal_vectors = A_matrix * wavelength

    return A_matrix, reciprocal_vectors