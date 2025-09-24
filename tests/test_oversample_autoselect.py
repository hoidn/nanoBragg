"""Test oversample auto-selection behavior to match C implementation.

This test verifies that the PyTorch implementation auto-selects oversample
values in the same way as the C code when oversample=-1 (auto mode).

The C formula is:
    xtalsize_max = max(|a|*Na, |b|*Nb, |c|*Nc)
    reciprocal_pixel_size = λ*distance/pixel_size
    recommended_oversample = ceil(3.0 * xtalsize_max / reciprocal_pixel_size)
"""

import pytest
import torch
import math
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


class TestOversampleAutoSelect:
    """Test suite for oversample auto-selection behavior."""

    def test_auto_select_formula(self):
        """Test that auto-selection follows the C formula exactly."""
        # Test parameters
        cell_a, cell_b, cell_c = 100.0, 100.0, 100.0  # Angstroms
        Na, Nb, Nc = 5, 5, 5
        wavelength_A = 6.2
        distance_mm = 100.0
        pixel_size_mm = 0.1

        # Create configurations
        crystal_config = CrystalConfig(
            cell_a=cell_a, cell_b=cell_b, cell_c=cell_c,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(Na, Nb, Nc),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=distance_mm,
            pixel_size_mm=pixel_size_mm,
            spixels=256, fpixels=256,
            oversample=-1  # Auto-select mode
        )

        beam_config = BeamConfig(wavelength_A=wavelength_A)

        # Calculate expected oversample using C formula
        xtalsize_max = max(
            cell_a * 1e-10 * Na,
            cell_b * 1e-10 * Nb,
            cell_c * 1e-10 * Nc
        )
        wavelength_m = wavelength_A * 1e-10
        distance_m = distance_mm / 1000.0
        pixel_size_m = pixel_size_mm / 1000.0
        reciprocal_pixel_size = wavelength_m * distance_m / pixel_size_m
        expected_oversample = max(1, math.ceil(3.0 * xtalsize_max / reciprocal_pixel_size))

        # Create models and simulator
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal=crystal, detector=detector, beam_config=beam_config)

        # Run simulation to trigger auto-selection (capture print output)
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            result = simulator.run(oversample=None)  # Use detector config value
        output = f.getvalue()

        # Check that auto-selection occurred
        assert "auto-selected" in output, "Auto-selection message not printed"

        # Extract the selected value from output
        import re
        match = re.search(r"auto-selected (\d+)-fold oversampling", output)
        assert match, "Could not parse auto-selection message"
        actual_oversample = int(match.group(1))

        # Verify it matches expected
        assert actual_oversample == expected_oversample, \
            f"Expected oversample={expected_oversample}, got {actual_oversample}"

    def test_different_crystal_sizes(self):
        """Test auto-selection with different crystal sizes."""
        test_cases = [
            # (Na, Nb, Nc, expected_oversample)
            (1, 1, 1, 1),    # Very small crystal
            (5, 5, 5, 1),    # Medium crystal
            (10, 10, 10, 1), # Larger crystal
            (20, 20, 20, 1), # Large crystal
            (50, 50, 50, 3), # Very large crystal
        ]

        for Na, Nb, Nc, expected in test_cases:
            crystal_config = CrystalConfig(
                cell_a=100.0, cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
                N_cells=(Na, Nb, Nc),
                default_F=100.0
            )

            detector_config = DetectorConfig(
                distance_mm=100.0,
                pixel_size_mm=0.1,
                spixels=128, fpixels=128,
                oversample=-1  # Auto-select
            )

            beam_config = BeamConfig(wavelength_A=6.2)

            crystal = Crystal(crystal_config)
            detector = Detector(detector_config)
            simulator = Simulator(crystal=crystal, detector=detector, beam_config=beam_config)

            # Capture output
            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                result = simulator.run(oversample=None)
            output = f.getvalue()

            # Extract selected value
            import re
            match = re.search(r"auto-selected (\d+)-fold oversampling", output)
            assert match, f"No auto-selection for N=({Na},{Nb},{Nc})"
            actual = int(match.group(1))

            assert actual == expected, \
                f"For N=({Na},{Nb},{Nc}): expected oversample={expected}, got {actual}"

    def test_explicit_oversample_overrides_auto(self):
        """Test that explicit oversample value overrides auto-selection."""
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(10, 10, 10),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=128, fpixels=128,
            oversample=-1  # Auto-select in config
        )

        beam_config = BeamConfig(wavelength_A=6.2)

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal=crystal, detector=detector, beam_config=beam_config)

        # Run with explicit oversample=4
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            result = simulator.run(oversample=4)  # Override with explicit value
        output = f.getvalue()

        # Should NOT see auto-selection message
        assert "auto-selected" not in output, "Auto-selection occurred when explicit value provided"

    def test_different_wavelengths(self):
        """Test auto-selection with different wavelengths."""
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(10, 10, 10),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=128, fpixels=128,
            oversample=-1
        )

        # Test with different wavelengths
        # Longer wavelength = larger reciprocal pixel size = smaller oversample needed
        for wavelength, expected_oversample in [(1.0, 3), (3.0, 1), (6.2, 1), (12.0, 1)]:
            beam_config = BeamConfig(wavelength_A=wavelength)

            crystal = Crystal(crystal_config)
            detector = Detector(detector_config)
            simulator = Simulator(crystal=crystal, detector=detector, beam_config=beam_config)

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                result = simulator.run(oversample=None)
            output = f.getvalue()

            import re
            match = re.search(r"auto-selected (\d+)-fold oversampling", output)
            assert match, f"No auto-selection for wavelength={wavelength}"
            actual = int(match.group(1))

            # Allow some tolerance as the exact value depends on the formula
            assert abs(actual - expected_oversample) <= 1, \
                f"For λ={wavelength}Å: expected ~{expected_oversample}, got {actual}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])