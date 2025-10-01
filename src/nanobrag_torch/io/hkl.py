"""
HKL file reader and Fdump binary cache for nanoBragg PyTorch.

Implements AT-STR-001, AT-STR-002, and AT-IO-003 from spec-a.md.
"""

import struct
from pathlib import Path
from typing import Tuple, Optional

import torch
import numpy as np


def read_hkl_file(
    filepath: str,
    default_F: float = 0.0,
    device=None,
    dtype=torch.float32
) -> Tuple[torch.Tensor, dict]:
    """
    Read HKL text file with two-pass algorithm matching C implementation.

    C-Code Implementation Reference (from nanoBragg.c):
    - First pass: count lines, track min/max of h,k,l, warn on non-integers
    - Second pass: allocate 3D grid and populate with F values
    - Unspecified grid points retain default_F

    Args:
        filepath: Path to HKL file with "h k l F" format (one per line)
        default_F: Default structure factor for unspecified reflections
        device: PyTorch device
        dtype: PyTorch dtype

    Returns:
        tuple: (F_grid, metadata_dict) where:
            - F_grid is a 3D tensor indexed by [h-h_min, k-k_min, l-l_min]
            - metadata_dict contains h_min, h_max, k_min, k_max, l_min, l_max
    """
    device = device if device is not None else torch.device("cpu")

    # First pass: find bounds and count reflections
    h_min, h_max = float('inf'), float('-inf')
    k_min, k_max = float('inf'), float('-inf')
    l_min, l_max = float('inf'), float('-inf')

    reflections = []
    non_integer_warned = False

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) >= 4:
                try:
                    h, k, l = float(parts[0]), float(parts[1]), float(parts[2])
                    F = float(parts[3])

                    # Check for non-integer indices and warn
                    if not non_integer_warned:
                        if h != int(h) or k != int(k) or l != int(l):
                            print(f"WARNING: Non-integer h,k,l values found: {h}, {k}, {l}")
                            non_integer_warned = True

                    # Track bounds
                    h_int, k_int, l_int = int(round(h)), int(round(k)), int(round(l))
                    h_min = min(h_min, h_int)
                    h_max = max(h_max, h_int)
                    k_min = min(k_min, k_int)
                    k_max = max(k_max, k_int)
                    l_min = min(l_min, l_int)
                    l_max = max(l_max, l_int)

                    reflections.append((h_int, k_int, l_int, F))

                except ValueError:
                    continue  # Skip malformed lines

    # Check if we found any valid reflections
    if not reflections:
        raise ValueError(f"No valid reflections found in {filepath}")

    # Calculate ranges
    h_range = h_max - h_min
    k_range = k_max - k_min
    l_range = l_max - l_min

    # Check for invalid ranges (as per C code)
    if h_range < 0 or k_range < 0 or l_range < 0:
        raise ValueError(f"Invalid HKL ranges: h_range={h_range}, k_range={k_range}, l_range={l_range}")

    # Second pass: allocate grid and populate
    # Grid size is (h_range+1) × (k_range+1) × (l_range+1)
    F_grid = torch.full(
        (h_range + 1, k_range + 1, l_range + 1),
        default_F,
        device=device,
        dtype=dtype
    )

    # Populate grid with actual F values
    for h, k, l, F in reflections:
        h_idx = h - h_min
        k_idx = k - k_min
        l_idx = l - l_min
        F_grid[h_idx, k_idx, l_idx] = F

    metadata = {
        'h_min': h_min,
        'h_max': h_max,
        'k_min': k_min,
        'k_max': k_max,
        'l_min': l_min,
        'l_max': l_max,
        'h_range': h_range,
        'k_range': k_range,
        'l_range': l_range
    }

    return F_grid, metadata


def write_fdump(
    F_grid: torch.Tensor,
    metadata: dict,
    filepath: str
):
    """
    Write binary Fdump.bin cache file matching C format.

    C-Code Implementation Reference (from nanoBragg.c):
    Header: six integers (h_min h_max k_min k_max l_min l_max) + newline + form feed
    Data: For each h in 0..h_range, for each k in 0..k_range, array of (l_range+1) doubles

    Args:
        F_grid: 3D tensor of structure factors
        metadata: Dict with h_min, h_max, k_min, k_max, l_min, l_max
        filepath: Output path for Fdump.bin
    """
    with open(filepath, 'wb') as f:
        # Write header: six integers followed by newline and form feed
        header = f"{metadata['h_min']} {metadata['h_max']} {metadata['k_min']} {metadata['k_max']} {metadata['l_min']} {metadata['l_max']}\n\f"
        f.write(header.encode('ascii'))

        # Convert to numpy for efficient binary writing
        F_numpy = F_grid.cpu().numpy().astype(np.float64)

        # Write data in native endianness (matching C code behavior)
        # Order is [h][k][l] with l varying fastest
        F_numpy.tofile(f)


def read_fdump(filepath: str, device=None, dtype=torch.float32) -> Tuple[torch.Tensor, dict]:
    """
    Read binary Fdump.bin cache file.

    Note: Fdump.bin always stores data as float64 (C doubles) per spec, but the returned
    tensor dtype can be specified to match the caller's precision requirements.
    Default is float32 per DTYPE-DEFAULT-001 project policy.

    Returns:
        tuple: (F_grid, metadata_dict) same as read_hkl_file
    """
    device = device if device is not None else torch.device("cpu")

    with open(filepath, 'rb') as f:
        # Read header line
        header_bytes = b''
        while True:
            byte = f.read(1)
            if byte == b'\f':  # Form feed marks end of header
                break
            header_bytes += byte

        # Parse header
        header_str = header_bytes.decode('ascii').strip()
        parts = header_str.split()
        h_min, h_max, k_min, k_max, l_min, l_max = map(int, parts)

        # Calculate dimensions
        h_range = h_max - h_min
        k_range = k_max - k_min
        l_range = l_max - l_min

        # Read binary data (always float64 in Fdump.bin format)
        num_elements = (h_range + 1) * (k_range + 1) * (l_range + 1)
        F_data = np.fromfile(f, dtype=np.float64, count=num_elements)

        # Reshape to 3D grid
        F_grid = F_data.reshape((h_range + 1, k_range + 1, l_range + 1))

        # Convert to torch tensor with requested dtype
        F_tensor = torch.from_numpy(F_grid).to(device=device, dtype=dtype)

        metadata = {
            'h_min': h_min,
            'h_max': h_max,
            'k_min': k_min,
            'k_max': k_max,
            'l_min': l_min,
            'l_max': l_max,
            'h_range': h_range,
            'k_range': k_range,
            'l_range': l_range
        }

        return F_tensor, metadata


def try_load_hkl_or_fdump(
    hkl_path: Optional[str] = None,
    fdump_path: str = "Fdump.bin",
    default_F: float = 0.0,
    write_cache: bool = True,
    device=None,
    dtype=torch.float32
) -> Tuple[Optional[torch.Tensor], Optional[dict]]:
    """
    Attempt to load HKL data with caching behavior matching C code.

    Logic from spec-a.md:
    - If hkl_path provided: read it and optionally write Fdump.bin cache
    - If no hkl_path but Fdump.bin exists: read from cache
    - If neither available and default_F == 0: return None (program should exit)
    - If neither available but default_F > 0: can proceed with default values only

    Args:
        hkl_path: Optional path to HKL text file
        fdump_path: Path to binary cache file (default "Fdump.bin")
        default_F: Default structure factor value
        write_cache: Whether to write Fdump.bin after reading HKL
        device: PyTorch device
        dtype: PyTorch dtype

    Returns:
        tuple: (F_grid, metadata) or (None, None) if no data available
    """
    # Try to load HKL file if provided
    if hkl_path and Path(hkl_path).exists():
        F_grid, metadata = read_hkl_file(hkl_path, default_F, device, dtype)

        # Write cache if requested
        if write_cache:
            try:
                write_fdump(F_grid, metadata, fdump_path)
            except Exception as e:
                print(f"Warning: Could not write Fdump cache: {e}")

        return F_grid, metadata

    # Try to load from cache if no HKL provided
    if Path(fdump_path).exists():
        try:
            return read_fdump(fdump_path, device, dtype)
        except Exception as e:
            print(f"Warning: Could not read Fdump cache: {e}")

    # No data available
    if default_F == 0:
        return None, None
    else:
        # Can proceed with only default_F values
        return None, None