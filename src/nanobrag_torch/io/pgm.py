"""PGM format writer for nanoBragg PyTorch.

This module implements the PGM (Portable Gray Map) format writer
per spec-a.md AT-IO-002 requirements.
"""

from pathlib import Path
from typing import Union

import numpy as np
import torch


def write_pgm(
    filepath: Union[str, Path],
    image_data: Union[torch.Tensor, np.ndarray],
    pgm_scale: float = 1.0,
) -> None:
    """Write image data in PGM format per spec AT-IO-002.

    The PGM format is a simple grayscale image format consisting of:
    1. Magic number "P5" for binary PGM
    2. Width and height
    3. Comment line with scale factor
    4. Maximum gray value (255)
    5. Binary pixel data

    Args:
        filepath: Output file path
        image_data: Image data with shape (slow, fast) or (height, width)
        pgm_scale: Scaling factor for float->byte conversion

    Per spec AT-IO-002:
    - File SHALL be P5 format (binary PGM)
    - Include width, height
    - One comment line "# pixels scaled by <pgm_scale>"
    - Maximum value 255
    - Followed by width*height bytes with values = floor(min(255, float_pixel * pgm_scale))
    """
    filepath = Path(filepath)

    # Convert torch tensor to numpy if needed
    if isinstance(image_data, torch.Tensor):
        image_data = image_data.detach().cpu().numpy()

    # Ensure 2D array
    if image_data.ndim != 2:
        raise ValueError(f"Image data must be 2D, got shape {image_data.shape}")

    # Image dimensions (height, width)
    height, width = image_data.shape

    # Scale and convert to bytes per spec
    # values = floor(min(255, float_pixel * pgm_scale))
    scaled_data = image_data * pgm_scale
    clipped_data = np.minimum(scaled_data, 255)
    byte_data = np.floor(clipped_data).astype(np.uint8)

    # Write PGM file
    with open(filepath, "wb") as f:
        # Write header in ASCII
        f.write(b"P5\n")  # Magic number for binary PGM
        f.write(f"{width} {height}\n".encode("ascii"))  # Width Height
        f.write(f"# pixels scaled by {pgm_scale}\n".encode("ascii"))  # Comment with scale
        f.write(b"255\n")  # Maximum gray value

        # Write binary pixel data in row-major order
        # PGM expects data in row-major (C-contiguous) order
        byte_data_contiguous = np.ascontiguousarray(byte_data)
        byte_data_contiguous.tofile(f)