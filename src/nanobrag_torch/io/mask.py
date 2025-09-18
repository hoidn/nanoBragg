"""SMV file I/O for nanoBragg PyTorch implementation.

Handles reading SMV format files including images and masks.
"""

import struct
from pathlib import Path
from typing import Dict, Optional, Tuple

import torch


def parse_smv_header(filename: str) -> Dict[str, str]:
    """Parse SMV header from a file.

    Per spec AT-CLI-004 and AT-IO-001:
    - SMV files have ASCII header followed by binary data
    - Header is exactly 512 bytes
    - Contains key=value pairs separated by semicolons
    - Can be used for both -img and -mask files

    Args:
        filename: Path to SMV file

    Returns:
        Dictionary of header key-value pairs

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If header format is invalid
    """
    path = Path(filename)
    if not path.exists():
        raise FileNotFoundError(f"SMV file not found: {filename}")

    with open(path, "rb") as f:
        # Read header (exactly 512 bytes per SMV spec)
        header_bytes = f.read(512)
        header_str = header_bytes.decode("ascii", errors="ignore")

        # Find header content between { and }
        start_idx = header_str.find("{")
        end_idx = header_str.find("}")

        if start_idx == -1 or end_idx == -1:
            raise ValueError(f"Invalid SMV header format in {filename}")

        header_content = header_str[start_idx+1:end_idx]

        # Parse key=value pairs
        header_dict = {}
        for line in header_content.split(";"):
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                header_dict[key.strip()] = value.strip()

    return header_dict


def apply_smv_header_to_config(header: Dict[str, str], config: dict,
                              is_mask: bool = False) -> None:
    """Apply SMV header values to configuration dictionary.

    Per spec AT-CLI-004 and section "File I/O":
    - Recognized header fields initialize corresponding parameters
    - For -mask headers, BEAM_CENTER_Y is interpreted with a flip
    - Updates config dict in-place

    Args:
        header: Dictionary of SMV header key-value pairs
        config: Configuration dictionary to update
        is_mask: True if this is a mask file (affects Y beam center interpretation)
    """
    # Pixel counts
    if "SIZE1" in header:
        config["fpixels"] = int(header["SIZE1"])
    if "SIZE2" in header:
        config["spixels"] = int(header["SIZE2"])

    # Pixel size (mm)
    if "PIXEL_SIZE" in header:
        config["pixel_size_mm"] = float(header["PIXEL_SIZE"])

    # Distances (mm)
    if "DISTANCE" in header:
        config["distance_mm"] = float(header["DISTANCE"])
    if "CLOSE_DISTANCE" in header:
        config["close_distance_mm"] = float(header["CLOSE_DISTANCE"])

    # Wavelength (Å)
    if "WAVELENGTH" in header:
        config["wavelength_A"] = float(header["WAVELENGTH"])

    # Beam centers (mm) - key part of AT-CLI-004
    if "BEAM_CENTER_X" in header:
        beam_x_mm = float(header["BEAM_CENTER_X"])
        config["beam_center_f"] = beam_x_mm  # Direct mapping for X

    if "BEAM_CENTER_Y" in header:
        beam_y_mm = float(header["BEAM_CENTER_Y"])
        if is_mask:
            # Per spec: For -mask, Y is interpreted as detsize_s - value_mm
            # We need detector size to do this flip
            if "spixels" in config and "pixel_size_mm" in config:
                detsize_s = config["spixels"] * config["pixel_size_mm"]
                config["beam_center_s"] = detsize_s - beam_y_mm
            else:
                # Store raw value with flag for later processing
                config["beam_center_s_raw"] = beam_y_mm
                config["beam_center_s_needs_flip"] = True
        else:
            # For -img, use value directly
            config["beam_center_s"] = beam_y_mm

    # XDS origin (pixels)
    if "XDS_ORGX" in header:
        config["orgx"] = float(header["XDS_ORGX"])
    if "XDS_ORGY" in header:
        config["orgy"] = float(header["XDS_ORGY"])

    # Phi and oscillation (degrees)
    if "PHI" in header:
        config["phi_start_deg"] = float(header["PHI"])
    if "OSC_START" in header:
        config["phi_start_deg"] = float(header["OSC_START"])
    if "OSC_RANGE" in header:
        config["osc_range_deg"] = float(header["OSC_RANGE"])

    # Two-theta (degrees)
    if "TWOTHETA" in header:
        config["detector_twotheta_deg"] = float(header["TWOTHETA"])


def read_smv_mask(filename: str) -> Tuple[torch.Tensor, dict]:
    """Read a mask file in SMV format.

    Per spec AT-PRE-001 and AT-ROI-001:
    - Mask files use SMV format with binary data
    - Zero values indicate pixels to skip
    - Non-zero values indicate pixels to include
    - Header contains detector parameters that may override config

    Args:
        filename: Path to SMV mask file

    Returns:
        Tuple of:
        - mask_array: Binary mask tensor (spixels, fpixels) with 0=skip, 1=include
        - header_dict: Dictionary of header parameters from the mask file

    Raises:
        FileNotFoundError: If mask file doesn't exist
        ValueError: If mask file format is invalid
    """
    path = Path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Mask file not found: {filename}")

    with open(path, "rb") as f:
        # Read header (up to 512 bytes per SMV spec)
        header_bytes = f.read(512)
        header_str = header_bytes.decode("ascii", errors="ignore")

        # Parse header into dict
        header_dict = {}

        # Find header content between { and }
        start_idx = header_str.find("{")
        end_idx = header_str.find("}")

        if start_idx == -1 or end_idx == -1:
            raise ValueError(f"Invalid SMV header format in {filename}")

        header_content = header_str[start_idx+1:end_idx]

        # Parse key=value pairs
        for line in header_content.split(";"):
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                header_dict[key.strip()] = value.strip()

        # Extract dimensions
        if "SIZE1" not in header_dict or "SIZE2" not in header_dict:
            raise ValueError(f"Missing SIZE1/SIZE2 in mask header: {filename}")

        fpixels = int(header_dict["SIZE1"])
        spixels = int(header_dict["SIZE2"])

        # Determine byte order
        byte_order = header_dict.get("BYTE_ORDER", "little_endian")
        endian = "<" if byte_order == "little_endian" else ">"

        # Read data based on type
        data_type = header_dict.get("TYPE", "unsigned_short")

        if data_type == "unsigned_short":
            # Read unsigned short data (2 bytes per pixel)
            num_pixels = fpixels * spixels
            pixel_data = f.read(num_pixels * 2)

            if len(pixel_data) != num_pixels * 2:
                raise ValueError(f"Insufficient data in mask file: {filename}")

            # Unpack as unsigned shorts
            fmt = f"{endian}{num_pixels}H"
            values = struct.unpack(fmt, pixel_data)

            # Reshape to (spixels, fpixels) in row-major order
            # Per spec: pixel index = slow * fpixels + fast
            mask_array = torch.tensor(values, dtype=torch.float32).reshape(spixels, fpixels)

        else:
            raise ValueError(f"Unsupported mask data type: {data_type}")

    # Convert to binary mask (0 or 1)
    mask_array = (mask_array != 0).float()

    return mask_array, header_dict


def create_circular_mask(
    spixels: int,
    fpixels: int,
    center_s: float,
    center_f: float,
    radius: float
) -> torch.Tensor:
    """Create a circular mask centered at given position.

    Utility function for testing and simple mask generation.

    Args:
        spixels: Number of slow-axis pixels
        fpixels: Number of fast-axis pixels
        center_s: Center position on slow axis (pixels)
        center_f: Center position on fast axis (pixels)
        radius: Radius of circular mask (pixels)

    Returns:
        Binary mask tensor with 1 inside circle, 0 outside
    """
    s_coords = torch.arange(spixels).view(-1, 1).float()
    f_coords = torch.arange(fpixels).view(1, -1).float()

    # Calculate distance from center
    dist_s = s_coords - center_s
    dist_f = f_coords - center_f
    dist_squared = dist_s**2 + dist_f**2

    # Create binary mask
    mask = (dist_squared <= radius**2).float()

    return mask


def create_rectangle_mask(
    spixels: int,
    fpixels: int,
    roi_xmin: int,
    roi_xmax: int,
    roi_ymin: int,
    roi_ymax: int
) -> torch.Tensor:
    """Create a rectangular ROI mask.

    Utility function to create mask from ROI bounds.

    Args:
        spixels: Number of slow-axis pixels
        fpixels: Number of fast-axis pixels
        roi_xmin: Fast axis minimum (inclusive, 0-based)
        roi_xmax: Fast axis maximum (inclusive, 0-based)
        roi_ymin: Slow axis minimum (inclusive, 0-based)
        roi_ymax: Slow axis maximum (inclusive, 0-based)

    Returns:
        Binary mask tensor with 1 inside ROI, 0 outside
    """
    mask = torch.zeros(spixels, fpixels)

    # Set ROI region to 1
    # Note: slow axis is first dimension (rows), fast axis is second (columns)
    mask[roi_ymin:roi_ymax+1, roi_xmin:roi_xmax+1] = 1.0

    return mask