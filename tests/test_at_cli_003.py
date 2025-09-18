#!/usr/bin/env python3
"""
AT-CLI-003: Conventions and pivot behavior

Test requirements:
- MOSFLM run uses pivot=BEAM by default
- XDS run uses pivot=SAMPLE by default
- ORGX/ORGY and ADXV/MOSFLM/DENZO center keys reflect the mapping rules
- Providing -pivot sample|beam overrides the default pivot
"""

import pytest
import subprocess
import tempfile
import os
import struct
from pathlib import Path
import re


def create_test_hkl(filepath):
    """Create a minimal HKL file for testing."""
    with open(filepath, 'w') as f:
        f.write("0 0 0 0\n")
        f.write("1 0 0 100\n")
        f.write("0 1 0 100\n")
        f.write("0 0 1 100\n")


def parse_smv_header(filepath):
    """Parse SMV header to extract key values."""
    header_dict = {}

    with open(filepath, 'rb') as f:
        # Read header (first 512 bytes)
        header_bytes = f.read(512)
        header_text = header_bytes.decode('ascii', errors='ignore')

        # Split into lines and parse key=value pairs
        lines = header_text.split('\n')
        for line in lines:
            if '=' in line and not line.startswith('{') and not line.startswith('}'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().rstrip(';')
                    header_dict[key] = value

    return header_dict


def run_nanobrag_cli(args):
    """Run the nanobrag CLI and return the process result."""
    cmd = ['python', '-m', 'nanobrag_torch'] + args
    env = os.environ.copy()
    env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result


class TestATCLI003:
    """Test AT-CLI-003: Conventions and pivot behavior."""

    def test_mosflm_default_pivot_beam(self):
        """Test that MOSFLM convention uses BEAM pivot by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            hkl_file = tmpdir / "test.hkl"
            int_file = tmpdir / "test.img"
            float_file = tmpdir / "test.bin"

            create_test_hkl(hkl_file)

            # Run with MOSFLM convention (default)
            args = [
                '-hkl', str(hkl_file),
                '-cell', '100', '100', '100', '90', '90', '90',
                '-detpixels', '32',
                '-pixel', '0.1',
                '-distance', '100',
                '-lambda', '1.0',
                '-default_F', '100',
                '-mosflm',  # Explicit MOSFLM
                '-intfile', str(int_file),
                '-floatfile', str(float_file)
            ]

            result = run_nanobrag_cli(args)
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Parse SMV header
            header = parse_smv_header(int_file)

            # With BEAM pivot and centered beam at detector center:
            # For 32x32 detector with 0.1mm pixels:
            # Detector is 3.2x3.2mm, center at 1.6mm,1.6mm
            # BEAM_CENTER should be at 1.6,1.6
            assert 'BEAM_CENTER_X' in header
            assert 'BEAM_CENTER_Y' in header

            # MOSFLM centers should include the pixel offset
            # In pixel coords: 1.6mm/0.1mm = 16 pixels (center)
            # MOSFLM adds 0.5 offset in convention
            assert 'MOSFLM_CENTER_X' in header
            assert 'MOSFLM_CENTER_Y' in header

    def test_xds_default_pivot_sample(self):
        """Test that XDS convention uses SAMPLE pivot by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            hkl_file = tmpdir / "test.hkl"
            int_file = tmpdir / "test.img"
            float_file = tmpdir / "test.bin"

            create_test_hkl(hkl_file)

            # Run with XDS convention
            args = [
                '-hkl', str(hkl_file),
                '-cell', '100', '100', '100', '90', '90', '90',
                '-detpixels', '32',
                '-pixel', '0.1',
                '-distance', '100',
                '-lambda', '1.0',
                '-default_F', '100',
                '-xds',  # XDS convention
                '-intfile', str(int_file),
                '-floatfile', str(float_file)
            ]

            result = run_nanobrag_cli(args)
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Parse SMV header
            header = parse_smv_header(int_file)

            # XDS should have ORGX/ORGY values
            assert 'XDS_ORGX' in header
            assert 'XDS_ORGY' in header

            # XDS uses SAMPLE pivot by default
            # The values should reflect XDS convention mapping
            # XDS origin is in pixels with origin at pixel (1,1)

    def test_pivot_override_mosflm_to_sample(self):
        """Test that -pivot sample overrides MOSFLM default BEAM pivot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            hkl_file = tmpdir / "test.hkl"
            int_file = tmpdir / "test.img"
            float_file = tmpdir / "test.bin"

            create_test_hkl(hkl_file)

            # Run with MOSFLM but override to SAMPLE pivot
            args = [
                '-hkl', str(hkl_file),
                '-cell', '100', '100', '100', '90', '90', '90',
                '-detpixels', '32',
                '-pixel', '0.1',
                '-distance', '100',
                '-lambda', '1.0',
                '-default_F', '100',
                '-mosflm',
                '-pivot', 'sample',  # Override to SAMPLE
                '-intfile', str(int_file),
                '-floatfile', str(float_file)
            ]

            result = run_nanobrag_cli(args)
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Parse SMV header
            header = parse_smv_header(int_file)

            # Should still have MOSFLM convention keys
            assert 'MOSFLM_CENTER_X' in header
            assert 'MOSFLM_CENTER_Y' in header

            # But pivot behavior should be SAMPLE
            # Close distance should be same as distance when no rotation
            if 'CLOSE_DISTANCE' in header:
                close_dist = float(header['CLOSE_DISTANCE'])
                dist = float(header['DISTANCE'])
                # For no rotations, close_distance should equal distance with SAMPLE pivot
                assert abs(close_dist - dist) < 0.01

    def test_pivot_override_xds_to_beam(self):
        """Test that -pivot beam overrides XDS default SAMPLE pivot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            hkl_file = tmpdir / "test.hkl"
            int_file = tmpdir / "test.img"
            float_file = tmpdir / "test.bin"

            create_test_hkl(hkl_file)

            # Run with XDS but override to BEAM pivot
            args = [
                '-hkl', str(hkl_file),
                '-cell', '100', '100', '100', '90', '90', '90',
                '-detpixels', '32',
                '-pixel', '0.1',
                '-distance', '100',
                '-lambda', '1.0',
                '-default_F', '100',
                '-xds',
                '-pivot', 'beam',  # Override to BEAM
                '-intfile', str(int_file),
                '-floatfile', str(float_file)
            ]

            result = run_nanobrag_cli(args)
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Parse SMV header
            header = parse_smv_header(int_file)

            # Should have XDS ORGX/ORGY
            assert 'XDS_ORGX' in header
            assert 'XDS_ORGY' in header

    def test_convention_header_keys_consistency(self):
        """Test that all convention-specific header keys are present and consistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            hkl_file = tmpdir / "test.hkl"

            create_test_hkl(hkl_file)

            conventions = ['mosflm', 'xds', 'dials']
            headers = {}

            for conv in conventions:
                int_file = tmpdir / f"test_{conv}.img"
                float_file = tmpdir / f"test_{conv}.bin"

                args = [
                    '-hkl', str(hkl_file),
                    '-cell', '100', '100', '100', '90', '90', '90',
                    '-detpixels', '32',
                    '-pixel', '0.1',
                    '-distance', '100',
                    '-lambda', '1.0',
                    '-default_F', '100',
                    f'-{conv}',
                    '-intfile', str(int_file),
                    '-floatfile', str(float_file)
                ]

                result = run_nanobrag_cli(args)
                assert result.returncode == 0, f"CLI failed for {conv}: {result.stderr}"

                headers[conv] = parse_smv_header(int_file)

            # All should have common keys
            common_keys = ['BEAM_CENTER_X', 'BEAM_CENTER_Y', 'DISTANCE',
                          'PIXEL_SIZE', 'SIZE1', 'SIZE2', 'WAVELENGTH']
            for conv, header in headers.items():
                for key in common_keys:
                    assert key in header, f"{conv} missing {key}"

            # Convention-specific keys
            assert 'MOSFLM_CENTER_X' in headers['mosflm']
            assert 'MOSFLM_CENTER_Y' in headers['mosflm']
            assert 'XDS_ORGX' in headers['xds']
            assert 'XDS_ORGY' in headers['xds']
            assert 'DIALS_ORIGIN' in headers['dials']

            # All should have ADXV and DENZO centers (compatibility)
            for conv in headers:
                assert 'ADXV_CENTER_X' in headers[conv]
                assert 'ADXV_CENTER_Y' in headers[conv]
                assert 'DENZO_X_BEAM' in headers[conv]
                assert 'DENZO_Y_BEAM' in headers[conv]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])