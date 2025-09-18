"""Test AT-IO-001: SMV header and data ordering.

From spec-a.md:
- Header SHALL include all required keys exactly as listed (HEADER_BYTES, DIM,
  BYTE_ORDER, TYPE, SIZE1/2, PIXEL_SIZE, DISTANCE, WAVELENGTH, BEAM_CENTER_X/Y,
  ADXV/MOSFLM/DENZO centers, DIALS_ORIGIN, XDS_ORGX/ORGY, CLOSE_DISTANCE,
  PHI/OSC_START/OSC_RANGE, TWOTHETA, DETECTOR_SN, BEAMLINE)
- Header closed with "}\\f" and padded to 512 bytes
- Data SHALL be fast-major (row-wise) with pixel index = slow*fpixels + fast
"""

import os
import tempfile
import struct
from pathlib import Path
import numpy as np
import torch

from nanobrag_torch.io import write_smv


class TestAT_IO_001:
    """Test SMV file format writing per AT-IO-001."""

    def test_smv_header_required_keys(self):
        """Test that SMV header includes all required keys."""
        with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Create test data
            image_data = np.random.randint(0, 1000, (128, 128), dtype=np.uint16)

            # Write SMV with all required parameters
            write_smv(
                filepath=tmp_path,
                image_data=image_data,
                pixel_size_mm=0.1,
                distance_mm=100.0,
                wavelength_angstrom=1.54,
                beam_center_x_mm=51.2,
                beam_center_y_mm=51.2,
                close_distance_mm=95.0,
                phi_deg=0.0,
                osc_start_deg=0.0,
                osc_range_deg=1.0,
                twotheta_deg=10.0,
                detector_sn="123",
                beamline="TestLine",
                convention="MOSFLM",
            )

            # Read and verify header
            with open(tmp_path, "rb") as f:
                header_bytes = f.read(512)

                # Verify header is exactly 512 bytes
                assert len(header_bytes) == 512, f"Header size {len(header_bytes)} != 512"

                # Parse header
                header_text = header_bytes.decode("ascii", errors="ignore")

                # Check for closing marker
                assert "}\f" in header_text, "Header not closed with '}\\f'"

                # Extract key-value pairs
                header_dict = {}
                for line in header_text.split("\n"):
                    if "=" in line and ";" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.rstrip(";").strip()
                        header_dict[key] = value

                # Check all required keys
                required_keys = [
                    "HEADER_BYTES", "DIM", "BYTE_ORDER", "TYPE",
                    "SIZE1", "SIZE2", "PIXEL_SIZE", "DISTANCE",
                    "WAVELENGTH", "BEAM_CENTER_X", "BEAM_CENTER_Y",
                    "TWOTHETA", "DETECTOR_SN", "BEAMLINE"
                ]

                for key in required_keys:
                    assert key in header_dict, f"Required key '{key}' missing from header"

                # Verify values
                assert header_dict["HEADER_BYTES"] == "512"
                assert header_dict["DIM"] == "2"
                assert header_dict["SIZE1"] == "128"  # Fast axis
                assert header_dict["SIZE2"] == "128"  # Slow axis
                assert header_dict["PIXEL_SIZE"] == "0.100000"
                assert float(header_dict["DISTANCE"]) == 100.0
                assert float(header_dict["WAVELENGTH"]) == 1.54

                # Check optional keys that were provided
                assert "CLOSE_DISTANCE" in header_dict
                assert "PHI" in header_dict
                assert "OSC_START" in header_dict
                assert "OSC_RANGE" in header_dict

                # Check convention-specific keys for MOSFLM
                assert "MOSFLM_CENTER_X" in header_dict
                assert "MOSFLM_CENTER_Y" in header_dict
                assert "XDS_ORGX" in header_dict
                assert "XDS_ORGY" in header_dict

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_smv_data_ordering(self):
        """Test that SMV data is written in fast-major (row-wise) order."""
        with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Create test pattern where we can verify ordering
            spixels, fpixels = 3, 4
            image_data = np.arange(spixels * fpixels, dtype=np.float32).reshape(spixels, fpixels)
            # image_data looks like:
            # [[0,  1,  2,  3],
            #  [4,  5,  6,  7],
            #  [8,  9, 10, 11]]

            write_smv(
                filepath=tmp_path,
                image_data=image_data,
                pixel_size_mm=0.1,
                distance_mm=100.0,
                wavelength_angstrom=1.54,
                beam_center_x_mm=0.2,
                beam_center_y_mm=0.2,
                data_type="unsigned_short",
                scale=1.0,
                adc_offset=0.0,
            )

            # Read binary data
            with open(tmp_path, "rb") as f:
                # Skip header
                f.seek(512)

                # Read data as uint16
                data_bytes = f.read(spixels * fpixels * 2)
                data = struct.unpack("<" + "H" * (spixels * fpixels), data_bytes)

                # Verify fast-major ordering: pixel[slow, fast] at index slow*fpixels + fast
                for slow in range(spixels):
                    for fast in range(fpixels):
                        expected = image_data[slow, fast]
                        index = slow * fpixels + fast
                        actual = data[index]
                        assert actual == expected, (
                            f"Pixel [{slow},{fast}] expected {expected}, got {actual} at index {index}"
                        )

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_smv_convention_specific_headers(self):
        """Test convention-specific header keys for different detector conventions."""
        conventions_and_keys = [
            ("MOSFLM", ["MOSFLM_CENTER_X", "MOSFLM_CENTER_Y"]),
            ("ADXV", ["ADXV_CENTER_X", "ADXV_CENTER_Y"]),
            ("DENZO", ["DENZO_X_BEAM", "DENZO_Y_BEAM"]),
            ("DIALS", ["DIALS_ORIGIN"]),
        ]

        for convention, expected_keys in conventions_and_keys:
            with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # Write with specific convention
                image_data = np.ones((10, 10), dtype=np.uint16)
                write_smv(
                    filepath=tmp_path,
                    image_data=image_data,
                    pixel_size_mm=0.1,
                    distance_mm=100.0,
                    wavelength_angstrom=1.0,
                    beam_center_x_mm=0.5,
                    beam_center_y_mm=0.5,
                    convention=convention,
                )

                # Read header and check for convention-specific keys
                with open(tmp_path, "rb") as f:
                    header_bytes = f.read(512)
                    header_text = header_bytes.decode("ascii", errors="ignore")

                    for key in expected_keys:
                        assert key in header_text, (
                            f"Convention {convention} missing required key {key}"
                        )

                    # XDS keys should always be present
                    assert "XDS_ORGX" in header_text
                    assert "XDS_ORGY" in header_text

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_smv_torch_tensor_input(self):
        """Test that SMV writer accepts torch tensors."""
        with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Create torch tensor
            image_tensor = torch.randn(64, 64) * 100 + 500

            write_smv(
                filepath=tmp_path,
                image_data=image_tensor,
                pixel_size_mm=0.075,
                distance_mm=150.0,
                wavelength_angstrom=0.98,
                beam_center_x_mm=2.4,
                beam_center_y_mm=2.4,
            )

            # Verify file was created and has correct structure
            assert os.path.exists(tmp_path)
            with open(tmp_path, "rb") as f:
                header = f.read(512)
                assert len(header) == 512

                # Verify data section exists
                f.seek(512)
                data_bytes = f.read(8)  # Read a few bytes
                assert len(data_bytes) == 8

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_smv_byte_order(self):
        """Test both little-endian and big-endian byte orders."""
        for byte_order, endian_char in [("little_endian", "<"), ("big_endian", ">")]:
            with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # Create simple test data
                image_data = np.array([[256, 512], [1024, 2048]], dtype=np.uint16)

                write_smv(
                    filepath=tmp_path,
                    image_data=image_data,
                    pixel_size_mm=0.1,
                    distance_mm=100.0,
                    wavelength_angstrom=1.0,
                    beam_center_x_mm=0.1,
                    beam_center_y_mm=0.1,
                    byte_order=byte_order,
                    data_type="unsigned_short",
                    scale=1.0,
                    adc_offset=0.0,
                )

                # Read and verify byte order in header and data
                with open(tmp_path, "rb") as f:
                    header_bytes = f.read(512)
                    header_text = header_bytes.decode("ascii", errors="ignore")
                    assert f"BYTE_ORDER={byte_order}" in header_text

                    # Read data with correct endianness
                    f.seek(512)
                    data_bytes = f.read(8)  # 4 uint16 values
                    data = struct.unpack(endian_char + "4H", data_bytes)

                    # Verify values match
                    expected = [256, 512, 1024, 2048]
                    assert list(data) == expected

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)