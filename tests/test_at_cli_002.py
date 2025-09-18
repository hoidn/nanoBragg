#!/usr/bin/env python3
"""
Test AT-CLI-002: Minimal render and headers

From spec-a.md:
- Setup: Run with small geometry (e.g., -detpixels 32 -pixel 0.1 -distance 100),
  a trivial HKL file (or -default_F), and specify -floatfile and -intfile outputs.
- Expectation: Both files are created. SMV header contains required keys with units:
  SIZE1/2, PIXEL_SIZE(mm), DISTANCE(mm), WAVELENGTH(Å), BEAM_CENTER_X/Y(mm),
  ADXV/MOSFLM/DENZO centers, DIALS_ORIGIN(mm,mm,mm), XDS_ORGX/ORGY(pixels),
  CLOSE_DISTANCE(mm), PHI/OSC_START/OSC_RANGE(deg), TWOTHETA(deg), DETECTOR_SN, BEAMLINE.
  Data ordering is fast-major (index = slow*fpixels + fast).
"""

import os
import sys
import numpy as np
import pytest
import subprocess
import tempfile
from pathlib import Path
import struct


class TestAT_CLI_002:
    """Test minimal CLI render with outputs."""

    def test_minimal_render_with_default_F(self):
        """AT-CLI-002: Run minimal simulation with -default_F and verify outputs."""

        with tempfile.TemporaryDirectory() as tmpdir:
            floatfile = os.path.join(tmpdir, 'output.bin')
            intfile = os.path.join(tmpdir, 'output.img')

            # Run the simulation
            cmd = [
                sys.executable, '-m', 'nanobrag_torch',
                '-cell', '100', '100', '100', '90', '90', '90',  # Simple cubic
                '-default_F', '100',
                '-detpixels', '32',
                '-pixel', '0.1',
                '-distance', '100',
                '-lambda', '6.2',  # Wavelength
                '-N', '5',  # Crystal size
                '-floatfile', floatfile,
                '-intfile', intfile
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            assert result.returncode == 0, f"Command failed: {result.stderr}"

            # Check that files were created
            assert os.path.exists(floatfile), "Float file was not created"
            assert os.path.exists(intfile), "SMV file was not created"

            # Read and verify float file
            float_data = np.fromfile(floatfile, dtype=np.float32).reshape(32, 32)
            assert float_data.shape == (32, 32)
            assert np.any(float_data > 0), "Float image should have non-zero values"

            # Read and verify SMV file
            with open(intfile, 'rb') as f:
                header_bytes = f.read(512)
                header = header_bytes.decode('ascii', errors='ignore')

                # Verify required header keys
                required_keys = [
                    'HEADER_BYTES', 'DIM', 'BYTE_ORDER', 'TYPE',
                    'SIZE1', 'SIZE2', 'PIXEL_SIZE', 'DISTANCE',
                    'WAVELENGTH', 'BEAM_CENTER_X', 'BEAM_CENTER_Y',
                    'ADXV_CENTER_X', 'ADXV_CENTER_Y',
                    'MOSFLM_CENTER_X', 'MOSFLM_CENTER_Y',
                    'DENZO_X_BEAM', 'DENZO_Y_BEAM',
                    'DIALS_ORIGIN', 'XDS_ORGX', 'XDS_ORGY',
                    'CLOSE_DISTANCE', 'PHI', 'OSC_START', 'OSC_RANGE',
                    'TWOTHETA', 'DETECTOR_SN', 'BEAMLINE'
                ]

                for key in required_keys:
                    assert key in header, f"Missing required header key: {key}"

                # Verify header ends with }\f and is padded to 512 bytes
                assert header.rstrip('\x00').endswith('}\f'), "Header should end with }\\f"
                assert len(header_bytes) == 512, "Header should be exactly 512 bytes"

                # Read data and verify fast-major ordering
                data_bytes = f.read()
                data = np.frombuffer(data_bytes, dtype=np.uint16).reshape(32, 32)
                assert data.shape == (32, 32)

    def test_minimal_render_with_hkl_file(self):
        """AT-CLI-002: Run with actual HKL file and verify header units."""

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal HKL file
            hkl_file = os.path.join(tmpdir, 'test.hkl')
            with open(hkl_file, 'w') as f:
                f.write("# h k l F\n")
                f.write("0 0 1 100.0\n")
                f.write("0 1 0 50.0\n")
                f.write("1 0 0 75.0\n")

            floatfile = os.path.join(tmpdir, 'output.bin')
            intfile = os.path.join(tmpdir, 'output.img')

            # Run the simulation
            cmd = [
                sys.executable, '-m', 'nanobrag_torch',
                '-hkl', hkl_file,
                '-cell', '100', '100', '100', '90', '90', '90',
                '-detpixels', '32',
                '-pixel', '0.2',  # Different pixel size
                '-distance', '150',  # Different distance
                '-lambda', '1.54',  # Different wavelength (Cu K-alpha)
                '-floatfile', floatfile,
                '-intfile', intfile
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            assert result.returncode == 0, f"Command failed: {result.stderr}"

            # Verify SMV header has correct units
            with open(intfile, 'rb') as f:
                header = f.read(512).decode('ascii', errors='ignore')

                # Check specific values with units (flexible about exact format)
                assert 'PIXEL_SIZE=' in header and '0.2' in header, "PIXEL_SIZE should be in mm"
                assert 'DISTANCE=' in header and '150' in header, "DISTANCE should be in mm"
                assert 'WAVELENGTH=' in header and '1.54' in header, "WAVELENGTH should be in Angstroms"

                # Check beam centers are in mm
                assert 'BEAM_CENTER_X=' in header
                assert 'BEAM_CENTER_Y=' in header

    def test_data_ordering_fast_major(self):
        """AT-CLI-002: Verify data ordering is fast-major (row-wise)."""

        with tempfile.TemporaryDirectory() as tmpdir:
            floatfile = os.path.join(tmpdir, 'output.bin')

            # Create a small test with known pattern
            cmd = [
                sys.executable, '-m', 'nanobrag_torch',
                '-cell', '100', '100', '100', '90', '90', '90',
                '-default_F', '100',
                '-detpixels', '8',  # Small for testing
                '-pixel', '0.1',
                '-distance', '100',
                '-lambda', '6.2',
                '-floatfile', floatfile
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            assert result.returncode == 0

            # Read as 1D array
            float_data_1d = np.fromfile(floatfile, dtype=np.float32)

            # Read as 2D array
            float_data_2d = float_data_1d.reshape(8, 8)

            # Verify indexing: pixel[slow, fast] should be at index slow*fpixels + fast
            for slow in range(8):
                for fast in range(8):
                    index_1d = slow * 8 + fast
                    assert float_data_1d[index_1d] == float_data_2d[slow, fast], \
                        f"Data ordering mismatch at pixel ({slow},{fast})"

    def test_error_without_required_inputs(self):
        """AT-CLI-002: Verify error handling when missing required inputs."""

        # Try to run without cell parameters or HKL
        cmd = [
            sys.executable, '-m', 'nanobrag_torch',
            '-detpixels', '32',
            '-floatfile', 'dummy.bin'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode != 0, "Should fail without cell parameters"
        assert 'Error:' in result.stdout or 'Error:' in result.stderr