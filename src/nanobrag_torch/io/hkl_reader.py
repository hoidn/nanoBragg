"""HKL file reader for nanoBragg PyTorch implementation."""

import torch
from typing import Tuple, Optional


def read_hkl_file(filepath: str, default_F: float = 0.0,
                  device=None, dtype=torch.float64) -> Tuple[torch.Tensor, Tuple[int, int, int, int, int, int]]:
    """
    Read structure factors from HKL file.

    Implements the two-pass approach from nanoBragg.c:
    1. First pass: find min/max HKL ranges
    2. Second pass: load data into 3D tensor

    Args:
        filepath: Path to HKL file containing h k l F values
        default_F: Default structure factor for unspecified reflections
        device: PyTorch device
        dtype: PyTorch data type

    Returns:
        Tuple of (F_hkl tensor, (h_min, h_max, k_min, k_max, l_min, l_max))
    """
    device = device if device is not None else torch.device('cpu')

    # First pass: find ranges
    h_min = k_min = l_min = float('inf')
    h_max = k_max = l_max = float('-inf')

    reflections = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) >= 4:
                try:
                    h = int(float(parts[0]))
                    k = int(float(parts[1]))
                    l = int(float(parts[2]))
                    F = float(parts[3])

                    h_min = min(h_min, h)
                    h_max = max(h_max, h)
                    k_min = min(k_min, k)
                    k_max = max(k_max, k)
                    l_min = min(l_min, l)
                    l_max = max(l_max, l)

                    reflections.append((h, k, l, F))
                except ValueError:
                    # Skip lines that can't be parsed
                    pass

    if not reflections:
        raise ValueError(f"No valid reflections found in {filepath}")

    # Create 3D tensor
    h_range = h_max - h_min + 1
    k_range = k_max - k_min + 1
    l_range = l_max - l_min + 1

    F_hkl = torch.full((h_range, k_range, l_range), default_F, device=device, dtype=dtype)

    # Second pass: populate tensor
    for h, k, l, F in reflections:
        F_hkl[h - h_min, k - k_min, l - l_min] = F

    return F_hkl, (h_min, h_max, k_min, k_max, l_min, l_max)