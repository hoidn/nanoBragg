"""SMV format writer for nanoBragg PyTorch.

This module implements the SMV (Simple Molecular Viewer) format writer
per spec-a.md AT-IO-001 requirements.
"""

import struct
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union, Tuple

import numpy as np
import torch


def read_smv(filepath: Union[str, Path]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Read an SMV format file.

    Args:
        filepath: Path to the SMV file

    Returns:
        Tuple of (image_data, header_dict) where:
        - image_data: numpy array with shape (slow, fast)
        - header_dict: dictionary of header key-value pairs
    """
    filepath = Path(filepath)

    with open(filepath, 'rb') as f:
        # Read the 512-byte header
        header_bytes = f.read(512)
        header_text = header_bytes.decode('ascii', errors='ignore')

        # Parse header into dictionary
        header = {}

        # Find the start and end of header content (between { and })
        start = header_text.find('{')
        end = header_text.find('}')

        if start == -1 or end == -1:
            raise ValueError(f"Invalid SMV header in {filepath}")

        # Parse key=value pairs
        header_content = header_text[start+1:end]
        for line in header_content.split('\n'):
            line = line.strip()
            if '=' in line and line.endswith(';'):
                # Remove trailing semicolon
                line = line[:-1]
                key, value = line.split('=', 1)
                header[key.strip()] = value.strip()

        # Extract dimensions
        fpixels = int(header.get('SIZE1', 0))
        spixels = int(header.get('SIZE2', 0))

        if fpixels == 0 or spixels == 0:
            raise ValueError(f"Invalid dimensions in {filepath}: {fpixels}x{spixels}")

        # Determine byte order
        byte_order = header.get('BYTE_ORDER', 'little_endian')
        endian = '<' if 'little' in byte_order else '>'

        # Read image data
        data_type = header.get('TYPE', 'unsigned_short')
        if data_type == 'unsigned_short':
            dtype = np.uint16
            bytes_per_pixel = 2
        elif data_type == 'signed_short':
            dtype = np.int16
            bytes_per_pixel = 2
        elif data_type == 'unsigned_int':
            dtype = np.uint32
            bytes_per_pixel = 4
        elif data_type == 'signed_int':
            dtype = np.int32
            bytes_per_pixel = 4
        elif data_type == 'float':
            dtype = np.float32
            bytes_per_pixel = 4
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Read the binary data
        num_pixels = fpixels * spixels
        data_bytes = f.read(num_pixels * bytes_per_pixel)

        # Unpack based on data type and endianness
        if len(data_bytes) < num_pixels * bytes_per_pixel:
            raise ValueError(f"Insufficient data: expected {num_pixels * bytes_per_pixel} bytes, got {len(data_bytes)}")

        # Use numpy for efficient unpacking
        if endian == '<':
            data = np.frombuffer(data_bytes, dtype=np.dtype(dtype).newbyteorder('<'))
        else:
            data = np.frombuffer(data_bytes, dtype=np.dtype(dtype).newbyteorder('>'))

        # Reshape to (slow, fast) - data is stored fast-major
        image_data = np.array(data, dtype=dtype).reshape((spixels, fpixels))

    return image_data, header


def write_smv(
    filepath: Union[str, Path],
    image_data: Union[torch.Tensor, np.ndarray],
    pixel_size_mm: float,
    distance_mm: float,
    wavelength_angstrom: float,
    beam_center_x_mm: float,
    beam_center_y_mm: float,
    close_distance_mm: Optional[float] = None,
    phi_deg: Optional[float] = None,
    osc_start_deg: Optional[float] = None,
    osc_range_deg: Optional[float] = None,
    twotheta_deg: float = 0.0,
    detector_sn: str = "000",
    beamline: str = "nanoBragg",
    convention: str = "MOSFLM",
    byte_order: str = "little_endian",
    data_type: str = "unsigned_short",
    scale: float = 1.0,
    adc_offset: float = 40.0,
) -> None:
    """Write image data in SMV format per spec AT-IO-001.

    The SMV format consists of:
    1. A 512-byte text header with metadata
    2. Binary image data in fast-major (row-wise) order

    Args:
        filepath: Output file path
        image_data: Image data with shape (slow, fast) or (spixels, fpixels)
        pixel_size_mm: Pixel size in mm
        distance_mm: Sample-to-detector distance in mm
        wavelength_angstrom: X-ray wavelength in Angstroms
        beam_center_x_mm: Beam center X position in mm
        beam_center_y_mm: Beam center Y position in mm
        close_distance_mm: Minimum distance from sample to detector plane in mm
        phi_deg: Phi angle in degrees
        osc_start_deg: Oscillation start angle in degrees
        osc_range_deg: Oscillation range in degrees
        twotheta_deg: Two-theta angle in degrees
        detector_sn: Detector serial number
        beamline: Beamline name
        convention: Detector convention (affects origin calculations)
        byte_order: Byte order for binary data
        data_type: Data type for binary data
        scale: Scaling factor for float->int conversion
        adc_offset: ADC offset to add before conversion

    Per spec AT-IO-001:
    - Header includes all required keys exactly as listed
    - Header closed with "}\\f" and padded to 512 bytes
    - Data is fast-major (row-wise) with pixel index = slow*fpixels + fast
    """
    filepath = Path(filepath)

    # Convert torch tensor to numpy if needed
    if isinstance(image_data, torch.Tensor):
        image_data = image_data.detach().cpu().numpy()

    # Ensure 2D array
    if image_data.ndim != 2:
        raise ValueError(f"Image data must be 2D, got shape {image_data.shape}")

    # Image dimensions (slow, fast)
    spixels, fpixels = image_data.shape

    # Calculate detector size
    detsize_f_mm = fpixels * pixel_size_mm
    detsize_s_mm = spixels * pixel_size_mm

    # Build header dictionary with all required keys per spec
    # Use reduced precision to fit within 512 byte limit
    header = {
        "HEADER_BYTES": "512",
        "DIM": "2",
        "BYTE_ORDER": byte_order,
        "TYPE": data_type,
        "SIZE1": str(fpixels),  # Fast axis
        "SIZE2": str(spixels),  # Slow axis
        "PIXEL_SIZE": f"{pixel_size_mm:.3f}",
        "DISTANCE": f"{distance_mm:.2f}",
        "WAVELENGTH": f"{wavelength_angstrom:.3f}",
        "BEAM_CENTER_X": f"{beam_center_x_mm:.2f}",
        "BEAM_CENTER_Y": f"{beam_center_y_mm:.2f}",
    }

    # Write ALL convention-specific beam centers per spec AT-IO-001
    # Use reduced precision to fit within 512 bytes
    # ADXV origin at pixel (1,1)
    adxv_x = beam_center_x_mm / pixel_size_mm + 1.0
    adxv_y = beam_center_y_mm / pixel_size_mm + 1.0
    header["ADXV_CENTER_X"] = f"{adxv_x:.1f}"
    header["ADXV_CENTER_Y"] = f"{adxv_y:.1f}"

    # MOSFLM: pixel coordinates with origin at (0,0)
    mosflm_x = beam_center_x_mm / pixel_size_mm
    mosflm_y = beam_center_y_mm / pixel_size_mm
    header["MOSFLM_CENTER_X"] = f"{mosflm_x:.1f}"
    header["MOSFLM_CENTER_Y"] = f"{mosflm_y:.1f}"

    # DENZO: origin at center of pixel (0,0)
    denzo_x = beam_center_x_mm / pixel_size_mm + 0.5
    denzo_y = beam_center_y_mm / pixel_size_mm + 0.5
    header["DENZO_X_BEAM"] = f"{denzo_x:.1f}"
    header["DENZO_Y_BEAM"] = f"{denzo_y:.1f}"

    # DIALS origin: offset from pixel (0,0) in mm
    header["DIALS_ORIGIN"] = f"{beam_center_x_mm:.1f},{beam_center_y_mm:.1f},0.0"

    # XDS origin (always included)
    # XDS uses pixel coordinates with origin at pixel (1,1)
    xds_orgx = beam_center_x_mm / pixel_size_mm + 1.0
    xds_orgy = beam_center_y_mm / pixel_size_mm + 1.0
    header["XDS_ORGX"] = f"{xds_orgx:.1f}"
    header["XDS_ORGY"] = f"{xds_orgy:.1f}"

    # CLOSE_DISTANCE is required per AT-IO-001
    # If not provided, use the distance value as a default
    if close_distance_mm is not None:
        header["CLOSE_DISTANCE"] = f"{close_distance_mm:.2f}"
    else:
        header["CLOSE_DISTANCE"] = f"{distance_mm:.2f}"

    # These fields are also required per AT-IO-001, default to 0.0 if not provided
    header["PHI"] = f"{phi_deg:.1f}" if phi_deg is not None else "0.0"
    header["OSC_START"] = f"{osc_start_deg:.1f}" if osc_start_deg is not None else "0.0"
    header["OSC_RANGE"] = f"{osc_range_deg:.1f}" if osc_range_deg is not None else "0.0"

    header["TWOTHETA"] = f"{twotheta_deg:.1f}"
    header["DETECTOR_SN"] = detector_sn
    header["BEAMLINE"] = beamline

    # Build header string
    header_lines = []
    header_lines.append("{")
    for key, value in header.items():
        header_lines.append(f"{key}={value};")
    header_str = "\n".join(header_lines)

    # Close with "}\f" per spec and encode to bytes
    header_str += "\n}\f"
    header_bytes = header_str.encode("ascii")

    # Pad to exactly 512 bytes with nulls
    if len(header_bytes) > 512:
        raise ValueError(f"Header too large: {len(header_bytes)} > 512 bytes")
    header_bytes = header_bytes.ljust(512, b'\x00')

    # Convert image data based on data type
    if data_type == "unsigned_short":
        # Apply scale and ADC offset, clip to uint16 range
        # Per spec-a-cli.md line 181: integer pixel = floor(min(65535, float*scale + adc))
        # Use float64 for scaling to match Python's int() behavior and avoid float32 rounding errors
        scaled_data = image_data.astype(np.float64) * scale + adc_offset
        clipped_data = np.clip(scaled_data, 0, 65535)
        output_data = np.floor(clipped_data).astype(np.uint16)
        dtype_str = "u2"
    elif data_type == "signed_short":
        scaled_data = image_data * scale + adc_offset
        clipped_data = np.clip(scaled_data, -32768, 32767)
        output_data = np.floor(clipped_data).astype(np.int16)
        dtype_str = "i2"
    elif data_type == "unsigned_int":
        scaled_data = image_data * scale + adc_offset
        clipped_data = np.clip(scaled_data, 0, 2**32-1)
        output_data = np.floor(clipped_data).astype(np.uint32)
        dtype_str = "u4"
    elif data_type == "signed_int":
        scaled_data = image_data * scale + adc_offset
        clipped_data = np.clip(scaled_data, -2**31, 2**31-1)
        output_data = np.floor(clipped_data).astype(np.int32)
        dtype_str = "i4"
    elif data_type == "float":
        output_data = image_data.astype(np.float32)
        dtype_str = "f4"
    else:
        raise ValueError(f"Unsupported data type: {data_type}")

    # Set endianness
    endian = "<" if byte_order == "little_endian" else ">"
    dtype_full = f"{endian}{dtype_str}"

    # Convert to fast-major (row-wise) order
    # Shape is (slow, fast), so this is already C-contiguous (row-major)
    # Ensure C-contiguous layout for correct binary output
    output_data = np.ascontiguousarray(output_data, dtype=dtype_full)

    # Write file
    with open(filepath, "wb") as f:
        f.write(header_bytes)
        output_data.tofile(f)