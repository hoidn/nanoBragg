#!/usr/bin/env python3
"""
Acceptance Tests for CLI interface (AT-CLI-* from spec-a-cli.md).

These tests verify the CLI binding profile requirements from the spec.
"""

import os
import subprocess
import sys
import tempfile
import numpy as np
import pytest
import struct


class TestCLIAcceptance:
    """Test suite for CLI acceptance criteria from spec-a-cli.md."""

    def test_at_cli_001_presence_and_help(self):
        """
        AT-CLI-001: CLI presence and help

        Verify that nanoBragg CLI responds to help flag and prints required options.
        """
        # Test both -h and --help
        for help_flag in ['-h', '--help']:
            result = subprocess.run(
                [sys.executable, '-m', 'nanobrag_torch', help_flag],
                capture_output=True,
                text=True,
                env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
            )

            # Check exit code indicates success
            assert result.returncode == 0, f"Help command failed with code {result.returncode}"

            # Check for required options in help text
            required_options = [
                '-hkl', '-mat', '-cell', '-pixel', '-detpixels', '-distance',
                '-lambda', '-energy', '-floatfile', '-intfile', '-noisefile',
                '-pgmfile', '-scale', '-adc', '-mosflm', '-xds', '-adxv',
                '-denzo', '-dials', '-roi'
            ]

            help_text = result.stdout + result.stderr
            missing_options = []

            for option in required_options:
                if option not in help_text:
                    missing_options.append(option)

            assert len(missing_options) == 0, \
                f"Help text missing required options: {missing_options}"

            # Verify it's actually help text (contains usage info)
            assert 'usage:' in help_text.lower() or 'Usage:' in help_text, \
                "Help text doesn't contain usage information"

    def test_at_cli_002_minimal_render_and_headers(self):
        """
        AT-CLI-002: Minimal render and headers

        Run with small geometry and verify output files are created with correct headers.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            float_file = os.path.join(tmpdir, 'output.bin')
            int_file = os.path.join(tmpdir, 'output.img')

            # Run minimal simulation
            cmd = [
                sys.executable, '-m', 'nanobrag_torch',
                '-detpixels', '32',
                '-pixel', '0.1',
                '-distance', '100',
                '-default_F', '10',
                '-cell', '100', '100', '100', '90', '90', '90',
                '-lambda', '1.0',
                '-N', '1',
                '-floatfile', float_file,
                '-intfile', int_file
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
            )

            # Check command succeeded
            assert result.returncode == 0, \
                f"Simulation failed with code {result.returncode}\nSTDERR: {result.stderr}"

            # Check float file exists
            assert os.path.exists(float_file), "Float file was not created"

            # Check float file has correct size (32x32 pixels * 4 bytes)
            float_size = os.path.getsize(float_file)
            expected_size = 32 * 32 * 4
            assert float_size == expected_size, \
                f"Float file size {float_size} != expected {expected_size}"

            # Check SMV file exists
            assert os.path.exists(int_file), "SMV file was not created"

            # Read and validate SMV header
            with open(int_file, 'rb') as f:
                header_bytes = f.read(512)
                # Don't strip() as it removes the form feed character
                header_text = header_bytes.decode('ascii', errors='ignore')

                # Check for required header keys
                required_keys = [
                    'HEADER_BYTES=512',
                    'DIM=2',
                    'BYTE_ORDER',
                    'TYPE=unsigned_short',
                    'SIZE1=32',  # fpixels
                    'SIZE2=32',  # spixels
                    'PIXEL_SIZE',  # in mm
                    'DISTANCE',    # in mm
                    'WAVELENGTH',  # in Å
                    'BEAM_CENTER_X',  # in mm
                    'BEAM_CENTER_Y',  # in mm
                    'ADXV_CENTER',
                    'MOSFLM_CENTER',
                    'DENZO_X_BEAM',
                    'DENZO_Y_BEAM',
                    'DIALS_ORIGIN',
                    'XDS_ORGX',  # in pixels
                    'XDS_ORGY',  # in pixels
                    'CLOSE_DISTANCE',
                    'PHI',
                    'OSC_START',
                    'OSC_RANGE',
                    'TWOTHETA',
                    'DETECTOR_SN',
                    'BEAMLINE'
                ]

                missing_keys = []
                for key in required_keys:
                    # Check if key exists (handling partial matches for compound keys)
                    key_base = key.split('=')[0]
                    if key_base not in header_text:
                        missing_keys.append(key_base)

                assert len(missing_keys) == 0, \
                    f"SMV header missing required keys: {missing_keys}\nHeader: {header_text.strip()[:500]}"

                # Verify header starts with { and ends with }\f
                # Note: Need to check on stripped version for startswith but original for form feed
                assert header_text.strip().startswith('{'), "SMV header doesn't start with '{'"
                assert '}\f' in header_text or '}\x0c' in header_text, \
                    "SMV header doesn't end with '}\\f'"

                # Check data section exists and has correct size
                # Skip header and read data
                f.seek(512)
                data = f.read()
                # Data should be 32x32 pixels * 2 bytes (uint16)
                expected_data_size = 32 * 32 * 2
                assert len(data) == expected_data_size, \
                    f"SMV data size {len(data)} != expected {expected_data_size}"

                # Verify data ordering (fast-major) by checking it can be reshaped
                data_array = np.frombuffer(data, dtype=np.uint16)
                assert data_array.shape[0] == 32 * 32, \
                    f"Data array size {data_array.shape[0]} != expected {32*32}"

    def test_at_cli_002_header_units(self):
        """
        Additional test for AT-CLI-002: Verify header units are correct.

        Tests that PIXEL_SIZE is in mm, DISTANCE in mm, WAVELENGTH in Å.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            int_file = os.path.join(tmpdir, 'output.img')

            # Run with specific values to check unit conversion
            cmd = [
                sys.executable, '-m', 'nanobrag_torch',
                '-detpixels', '16',
                '-pixel', '0.2',  # 0.2 mm
                '-distance', '150.5',  # 150.5 mm
                '-default_F', '10',
                '-cell', '100', '100', '100', '90', '90', '90',
                '-lambda', '2.5',  # 2.5 Å
                '-N', '1',
                '-intfile', int_file
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
            )

            assert result.returncode == 0, f"Command failed: {result.stderr}"

            with open(int_file, 'rb') as f:
                header = f.read(512).decode('ascii', errors='ignore')

                # Extract and verify specific values
                import re

                # PIXEL_SIZE should be 0.2 mm
                pixel_match = re.search(r'PIXEL_SIZE=([0-9.]+)', header)
                assert pixel_match, "PIXEL_SIZE not found in header"
                pixel_size = float(pixel_match.group(1))
                assert abs(pixel_size - 0.2) < 0.001, \
                    f"PIXEL_SIZE {pixel_size} != expected 0.2 mm"

                # DISTANCE should be 150.5 mm
                dist_match = re.search(r'DISTANCE=([0-9.]+)', header)
                assert dist_match, "DISTANCE not found in header"
                distance = float(dist_match.group(1))
                assert abs(distance - 150.5) < 0.001, \
                    f"DISTANCE {distance} != expected 150.5 mm"

                # WAVELENGTH should be 2.5 Å
                wave_match = re.search(r'WAVELENGTH=([0-9.]+)', header)
                assert wave_match, "WAVELENGTH not found in header"
                wavelength = float(wave_match.group(1))
                assert abs(wavelength - 2.5) < 0.001, \
                    f"WAVELENGTH {wavelength} != expected 2.5 Å"