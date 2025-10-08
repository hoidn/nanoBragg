"""
Test custom detector basis vectors (CLI integration)

This tests that custom detector basis vectors specified via CLI
are properly passed through to the detector configuration.
"""

import os
import numpy as np
import subprocess
import sys
import pytest
import torch
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nanobrag_torch.config import DetectorConfig, DetectorConvention
from nanobrag_torch.models.detector import Detector


class TestCustomVectors:
    """Test custom detector basis vectors functionality"""

    def test_custom_vectors_in_detector_config(self):
        """Test that custom vectors can be set in DetectorConfig"""
        config = DetectorConfig(
            detector_convention=DetectorConvention.CUSTOM,
            custom_fdet_vector=(1.0, 0.0, 0.0),
            custom_sdet_vector=(0.0, 1.0, 0.0),
            custom_odet_vector=(0.0, 0.0, 1.0)
        )

        assert config.detector_convention == DetectorConvention.CUSTOM
        assert config.custom_fdet_vector == (1.0, 0.0, 0.0)
        assert config.custom_sdet_vector == (0.0, 1.0, 0.0)
        assert config.custom_odet_vector == (0.0, 0.0, 1.0)

    def test_custom_vectors_in_detector(self):
        """Test that Detector properly uses custom vectors"""
        config = DetectorConfig(
            detector_convention=DetectorConvention.CUSTOM,
            custom_fdet_vector=(0.5, 0.5, 0.707107),  # Non-standard vectors
            custom_sdet_vector=(-0.5, 0.5, 0.707107),
            custom_odet_vector=(-0.707107, 0.0, 0.707107)
        )

        detector = Detector(config)

        # The Detector should accept the custom vectors without error
        assert detector.config.detector_convention == DetectorConvention.CUSTOM
        assert detector.config.custom_fdet_vector == (0.5, 0.5, 0.707107)
        assert detector.config.custom_sdet_vector == (-0.5, 0.5, 0.707107)
        assert detector.config.custom_odet_vector == (-0.707107, 0.0, 0.707107)

        # Get pixel coordinates - this will use the custom vectors internally
        pixel_coords = detector.get_pixel_coords()

        # Should return valid pixel coordinates
        assert pixel_coords.shape[0] == config.spixels
        assert pixel_coords.shape[1] == config.fpixels
        assert pixel_coords.shape[2] == 3  # x, y, z coordinates

    def test_cli_custom_vectors(self):
        """Test that custom vectors from CLI are properly parsed"""
        # Create a minimal test command
        cmd = [
            sys.executable, "-m", "nanobrag_torch",
            "-cell", "100", "100", "100", "90", "90", "90",
            "-default_F", "100",
            "-lambda", "1.0",
            "-distance", "100",
            "-detpixels", "64",
            "-fdet_vector", "1", "0", "0",
            "-sdet_vector", "0", "1", "0",
            "-odet_vector", "0", "0", "1",
            "-floatfile", "/tmp/test_custom_vectors.bin",
            "-oversample", "1"
        ]

        # Set environment variable
        env = os.environ.copy()
        env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        # Check that it runs without errors
        if result.returncode != 0:
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")

        assert result.returncode == 0, f"Command failed with return code {result.returncode}"

        # Check that CUSTOM convention was detected
        assert "Convention: CUSTOM" in result.stdout or "detector_convention=DetectorConvention.CUSTOM" in result.stdout or "CUSTOM" in result.stderr

        # Clean up
        if os.path.exists("/tmp/test_custom_vectors.bin"):
            os.remove("/tmp/test_custom_vectors.bin")

    def test_custom_convention_detection(self):
        """Test that providing custom vectors automatically sets CUSTOM convention"""
        # Test with just fdet_vector
        cmd = [
            sys.executable, "-m", "nanobrag_torch",
            "-cell", "100", "100", "100", "90", "90", "90",
            "-default_F", "100",
            "-lambda", "1.0",
            "-distance", "100",
            "-detpixels", "32",
            "-fdet_vector", "0", "1", "0",  # Non-standard fast vector
            "-oversample", "1",
            "-printout"  # Enable verbose output
        ]

        env = os.environ.copy()
        env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        # Should run successfully
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Should detect CUSTOM convention (check various possible output formats)
        output = result.stdout + result.stderr
        custom_detected = (
            "Convention: CUSTOM" in output or
            "convention='CUSTOM'" in output or
            "detector_convention=DetectorConvention.CUSTOM" in output
        )
        assert custom_detected, "CUSTOM convention not detected when custom vectors provided"

    def test_custom_spindle_axis(self):
        """Test that custom spindle axis is properly handled"""
        cmd = [
            sys.executable, "-m", "nanobrag_torch",
            "-cell", "100", "100", "100", "90", "90", "90",
            "-default_F", "100",
            "-lambda", "1.0",
            "-distance", "100",
            "-detpixels", "32",
            "-spindle_axis", "1", "0", "0",  # X-axis spindle
            "-phi", "30",
            "-osc", "1",
            "-oversample", "1",
            "-printout"
        ]

        env = os.environ.copy()
        env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        # Should run successfully
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Should also set CUSTOM convention
        output = result.stdout + result.stderr
        custom_detected = (
            "Convention: CUSTOM" in output or
            "convention='CUSTOM'" in output or
            "detector_convention=DetectorConvention.CUSTOM" in output
        )
        assert custom_detected, "CUSTOM convention not detected when spindle_axis provided"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])