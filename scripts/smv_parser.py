#!/usr/bin/env python3
"""
SMV format parser for nanoBragg.c output images.

This module provides functionality to parse SMV (Simple Molecular Viewer) format
image files produced by nanoBragg.c, including header parsing and binary data extraction.
"""

import re
import struct
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


def parse_smv_header(header_bytes: bytes) -> Dict[str, str]:
    """Parse SMV header into a dictionary.

    The SMV header is a text section at the start of the file containing
    key-value pairs in the format KEY=VALUE; separated by semicolons.

    Args:
        header_bytes: Raw bytes of the header section

    Returns:
        Dictionary mapping header keys to string values
    """
    header_text = header_bytes.decode("ascii", errors="ignore")

    # Remove the opening and closing braces
    header_text = header_text.strip().strip("{}")

    # Parse key=value pairs
    header_dict = {}

    # Split on semicolons and parse each pair
    for pair in header_text.split(";"):
        pair = pair.strip()
        if "=" in pair:
            key, value = pair.split("=", 1)
            header_dict[key.strip()] = value.strip()

    return header_dict


def parse_smv_image(filepath: str) -> Tuple[np.ndarray, Dict[str, str]]:
    """Parse SMV format image file into numpy array and header.

    Handles the binary image data from nanoBragg.c intimage.img output,
    including header parsing and proper data type conversion.

    The SMV format consists of:
    1. A text header (typically 512 bytes) containing metadata
    2. Binary image data in the specified format

    Args:
        filepath: Path to SMV format image file

    Returns:
        Tuple of:
        - np.ndarray: Image data with shape (spixels, fpixels)
        - Dict: Header metadata

    Reference: SMV format spec in docs/architecture/pytorch_design.md
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"SMV file not found: {filepath}")

    with open(filepath, "rb") as f:
        # Read header first
        header_bytes = f.read(512)  # Standard SMV header size
        header = parse_smv_header(header_bytes)

        # Extract image parameters from header
        header_bytes_size = int(header.get("HEADER_BYTES", 512))
        size1 = int(header["SIZE1"])  # Fast axis (columns)
        size2 = int(header["SIZE2"])  # Slow axis (rows)
        data_type = header["TYPE"]
        byte_order = header.get("BYTE_ORDER", "little_endian")

        # Seek to start of image data (in case header is not exactly 512 bytes)
        f.seek(header_bytes_size)

        # Determine numpy dtype
        endian = "<" if byte_order == "little_endian" else ">"
        if data_type == "unsigned_short":
            dtype = f"{endian}u2"  # 16-bit unsigned
        elif data_type == "signed_short":
            dtype = f"{endian}i2"  # 16-bit signed
        elif data_type == "unsigned_int":
            dtype = f"{endian}u4"  # 32-bit unsigned
        elif data_type == "signed_int":
            dtype = f"{endian}i4"  # 32-bit signed
        elif data_type == "float":
            dtype = f"{endian}f4"  # 32-bit float
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Read binary image data
        image_bytes = f.read()

        # Convert to numpy array
        image_data = np.frombuffer(image_bytes, dtype=dtype)

        # Reshape to 2D image - note SMV uses (slow, fast) = (rows, cols) = (SIZE2, SIZE1)
        if len(image_data) != size1 * size2:
            raise ValueError(
                f"Image data size mismatch: expected {size1 * size2}, got {len(image_data)}"
            )

        image = image_data.reshape((size2, size1))  # (slow, fast) = (rows, cols)

        return image, header


def validate_smv_file(filepath: str) -> bool:
    """Validate that a file is a proper SMV format.

    Args:
        filepath: Path to file to validate

    Returns:
        True if file appears to be valid SMV format
    """
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return False

        with open(filepath, "rb") as f:
            header_bytes = f.read(512)

        # Check for SMV header markers
        header_text = header_bytes.decode("ascii", errors="ignore")

        # Should contain key SMV fields
        required_fields = ["HEADER_BYTES", "SIZE1", "SIZE2", "TYPE"]
        for field in required_fields:
            if field not in header_text:
                return False

        return True

    except Exception:
        return False


def extract_image_info(header: Dict[str, str]) -> Dict:
    """Extract key image information from SMV header.

    Args:
        header: Parsed SMV header dictionary

    Returns:
        Dictionary with key image parameters
    """
    info = {}

    # Image dimensions
    info["width"] = int(header.get("SIZE1", 0))
    info["height"] = int(header.get("SIZE2", 0))
    info["data_type"] = header.get("TYPE", "unknown")

    # Detector parameters
    info["pixel_size"] = float(header.get("PIXEL_SIZE", 0))
    info["distance"] = float(header.get("DISTANCE", 0))
    info["wavelength"] = float(header.get("WAVELENGTH", 0))

    # Beam center
    info["beam_center_x"] = float(header.get("BEAM_CENTER_X", 0))
    info["beam_center_y"] = float(header.get("BEAM_CENTER_Y", 0))

    # Rotation parameters
    info["phi"] = float(header.get("PHI", 0))
    info["osc_start"] = float(header.get("OSC_START", 0))
    info["osc_range"] = float(header.get("OSC_RANGE", 0))
    info["twotheta"] = float(header.get("TWOTHETA", 0))

    return info


if __name__ == "__main__":
    # Example usage and testing
    print("SMV Parser - Example Usage")
    print("=" * 30)

    # Test with existing golden suite image
    test_file = "golden_suite_generator/intimage.img"

    if Path(test_file).exists():
        try:
            print(f"Parsing test file: {test_file}")

            # Validate file
            if validate_smv_file(test_file):
                print("✅ File validation passed")
            else:
                print("❌ File validation failed")
                exit(1)

            # Parse image
            image, header = parse_smv_image(test_file)

            print(f"\nImage shape: {image.shape}")
            print(f"Data type: {image.dtype}")
            print(f"Value range: {image.min():.2e} to {image.max():.2e}")
            print(f"Mean value: {image.mean():.2e}")

            # Display header info
            info = extract_image_info(header)
            print(f"\nImage Info:")
            for key, value in info.items():
                print(f"  {key}: {value}")

            print("\nFull Header:")
            for key, value in header.items():
                print(f"  {key}: {value}")

        except Exception as e:
            print(f"❌ Error parsing SMV file: {e}")
    else:
        print(f"⚠️  Test file not found: {test_file}")
        print("Run a nanoBragg.c simulation first to generate test data")
