"""Test for the -show_config debugging feature.

This test ensures that the configuration echo feature works correctly
and displays all important configuration parameters for debugging.
"""

import os
import subprocess
import tempfile
import pytest

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


class TestShowConfig:
    """Test suite for the -show_config CLI feature."""

    def test_show_config_basic(self):
        """Test that -show_config produces configuration output."""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Run with -show_config flag
            result = subprocess.run(
                [
                    'python', '-m', 'nanobrag_torch',
                    '-default_F', '100',
                    '-cell', '100', '100', '100', '90', '90', '90',
                    '-lambda', '1.0',
                    '-distance', '100',
                    '-detpixels', '32',
                    '-show_config',
                    '-floatfile', tmp_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Check that the command succeeded
            assert result.returncode == 0, f"Command failed with: {result.stderr}"

            # Check for configuration header
            assert "CONFIGURATION ECHO" in result.stdout, "Config header not found in output"
            assert "Crystal Configuration" in result.stdout, "Crystal config section missing"
            assert "Detector Configuration" in result.stdout, "Detector config section missing"
            assert "Beam Configuration" in result.stdout, "Beam config section missing"

            # Check for specific parameter values
            assert "Cell: a=100.000" in result.stdout, "Cell parameters not displayed"
            assert "Pixels: 32 x 32" in result.stdout, "Detector pixels not displayed"
            assert "Wavelength: 1.0000 Å" in result.stdout, "Wavelength not displayed"
            assert "Distance: 100.000 mm" in result.stdout, "Distance not displayed"

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_show_config_with_divergence(self):
        """Test that divergence parameters are shown correctly."""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Run with divergence parameters
            result = subprocess.run(
                [
                    'python', '-m', 'nanobrag_torch',
                    '-default_F', '100',
                    '-cell', '100', '100', '100', '90', '90', '90',
                    '-lambda', '1.5',
                    '-distance', '100',
                    '-detpixels', '32',
                    '-hdivrange', '0.5',
                    '-hdivsteps', '5',
                    '-vdivrange', '0.3',
                    '-vdivsteps', '3',
                    '-dispersion', '10',
                    '-dispsteps', '2',
                    '-show_config',
                    '-floatfile', tmp_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Check that the command succeeded
            assert result.returncode == 0, f"Command failed with: {result.stderr}"

            # Check for source information
            assert "Sources:" in result.stdout, "Source count not displayed"

            # The output shows sources were generated
            assert "Generated" in result.stdout and "sources from divergence/dispersion" in result.stdout

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_show_config_with_rotations(self):
        """Test that detector rotations are shown correctly."""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Run with detector rotations
            result = subprocess.run(
                [
                    'python', '-m', 'nanobrag_torch',
                    '-default_F', '100',
                    '-cell', '100', '100', '100', '90', '90', '90',
                    '-lambda', '1.0',
                    '-distance', '100',
                    '-detpixels', '32',
                    '-detector_rotx', '5',
                    '-detector_roty', '3',
                    '-detector_rotz', '2',
                    '-twotheta', '10',
                    '-show_config',
                    '-floatfile', tmp_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Check that the command succeeded
            assert result.returncode == 0, f"Command failed with: {result.stderr}"

            # Check for rotation values
            assert "Rotations: rotx=5.000°" in result.stdout, "Detector rotx not displayed"
            assert "roty=3.000°" in result.stdout, "Detector roty not displayed"
            assert "rotz=2.000°" in result.stdout, "Detector rotz not displayed"
            assert "twotheta=10.000°" in result.stdout, "Two-theta not displayed"

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_echo_config_alias(self):
        """Test that -echo_config works as an alias for -show_config."""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Run with -echo_config alias
            result = subprocess.run(
                [
                    'python', '-m', 'nanobrag_torch',
                    '-default_F', '100',
                    '-cell', '100', '100', '100', '90', '90', '90',
                    '-lambda', '1.0',
                    '-distance', '100',
                    '-detpixels', '32',
                    '-echo_config',  # Using the alias
                    '-floatfile', tmp_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Check that the command succeeded
            assert result.returncode == 0, f"Command failed with: {result.stderr}"

            # Check for configuration header (should work same as -show_config)
            assert "CONFIGURATION ECHO" in result.stdout, "Config header not found with -echo_config"

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)