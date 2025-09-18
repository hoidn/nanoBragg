"""Test AT-STA-001: Float-image statistics calculation.

This test validates the statistics computation on the float image per the spec:
- max_I: maximum float image pixel value and its fast/slow subpixel coordinates
- mean = sum(pixel)/N
- RMS = sqrt(sum(pixel^2)/(N − 1))
- RMSD from mean = sqrt(sum((pixel − mean)^2)/(N − 1))
- N counts only pixels inside the ROI and unmasked
"""

import torch
import numpy as np
import pytest

from src.nanobrag_torch.simulator import Simulator
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.config import (
    DetectorConfig,
    CrystalConfig,
    BeamConfig,
    DetectorConvention,
    DetectorPivot,
)


class TestAT_STA_001:
    """Test suite for AT-STA-001: Float-image statistics."""

    def test_statistics_basic(self):
        """Test basic statistics calculation on a simple pattern."""
        # Create a simple test image
        float_image = torch.tensor([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ], dtype=torch.float64)

        # Create minimal detector config
        config = DetectorConfig(
            pixel_size_mm=0.1,
            distance_mm=100.0,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            roi_xmin=None,  # No ROI restriction
            roi_xmax=None,
            roi_ymin=None,
            roi_ymax=None,
        )

        # Create detector and crystal (minimal)
        detector = Detector(config)
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
        )
        crystal = Crystal(crystal_config)

        # Create simulator
        beam_config = BeamConfig(wavelength_A=1.0)
        simulator = Simulator(crystal, detector, beam_config=beam_config)

        # Compute statistics
        stats = simulator.compute_statistics(float_image)

        # Verify results
        assert stats["N"] == 9  # All 9 pixels counted
        assert stats["max_I"] == 9.0
        assert stats["max_I_fast"] == 2
        assert stats["max_I_slow"] == 2

        # Mean should be 5.0 (1+2+3+4+5+6+7+8+9)/9
        assert abs(stats["mean"] - 5.0) < 1e-10

        # RMS = sqrt(sum(pixel^2)/(N-1))
        # sum(pixel^2) = 1+4+9+16+25+36+49+64+81 = 285
        # RMS = sqrt(285/8) = sqrt(35.625) ≈ 5.9687
        expected_rms = np.sqrt(285.0 / 8.0)
        assert abs(stats["RMS"] - expected_rms) < 1e-6

        # RMSD = sqrt(sum((pixel-mean)^2)/(N-1))
        # deviations from mean(5): -4, -3, -2, -1, 0, 1, 2, 3, 4
        # sum of squares: 16+9+4+1+0+1+4+9+16 = 60
        # RMSD = sqrt(60/8) = sqrt(7.5) ≈ 2.7386
        expected_rmsd = np.sqrt(60.0 / 8.0)
        assert abs(stats["RMSD"] - expected_rmsd) < 1e-6

    def test_statistics_with_roi(self):
        """Test statistics calculation with ROI limiting."""
        # Create test image
        float_image = torch.tensor([
            [1.0, 2.0, 3.0, 4.0],
            [5.0, 6.0, 7.0, 8.0],
            [9.0, 10.0, 11.0, 12.0],
            [13.0, 14.0, 15.0, 16.0]
        ], dtype=torch.float64)

        # Create detector config with ROI limiting to center 2x2 region
        config = DetectorConfig(
            pixel_size_mm=0.1,
            distance_mm=100.0,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            roi_xmin=1,  # Fast axis: pixels 1-2
            roi_xmax=2,
            roi_ymin=1,  # Slow axis: pixels 1-2
            roi_ymax=2,
        )

        # Create detector and crystal
        detector = Detector(config)
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
        )
        crystal = Crystal(crystal_config)

        # Create simulator
        beam_config = BeamConfig(wavelength_A=1.0)
        simulator = Simulator(crystal, detector, beam_config=beam_config)

        # Compute statistics
        stats = simulator.compute_statistics(float_image)

        # Verify results - should only include center 2x2: [6, 7, 10, 11]
        assert stats["N"] == 4
        assert stats["max_I"] == 11.0
        assert stats["max_I_fast"] == 2  # Column 2
        assert stats["max_I_slow"] == 2  # Row 2

        # Mean = (6+7+10+11)/4 = 34/4 = 8.5
        assert abs(stats["mean"] - 8.5) < 1e-10

    def test_statistics_with_mask(self):
        """Test statistics calculation with external mask."""
        # Create test image
        float_image = torch.tensor([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ], dtype=torch.float64)

        # Create mask (0 = skip, 1 = include)
        mask = torch.tensor([
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1]
        ], dtype=torch.float64)

        # Create detector config with mask
        config = DetectorConfig(
            pixel_size_mm=0.1,
            distance_mm=100.0,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            spixels=3,  # Match test image size
            fpixels=3,  # Match test image size
            roi_xmin=None,  # No ROI restriction
            roi_xmax=None,
            roi_ymin=None,
            roi_ymax=None,
            mask_array=mask,
        )

        # Create detector and crystal
        detector = Detector(config)
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
        )
        crystal = Crystal(crystal_config)

        # Create simulator
        beam_config = BeamConfig(wavelength_A=1.0)
        simulator = Simulator(crystal, detector, beam_config=beam_config)

        # Compute statistics
        stats = simulator.compute_statistics(float_image)

        # Verify results - should include [1, 3, 5, 7, 9]
        assert stats["N"] == 5
        assert stats["max_I"] == 9.0
        assert stats["max_I_fast"] == 2
        assert stats["max_I_slow"] == 2

        # Mean = (1+3+5+7+9)/5 = 25/5 = 5.0
        assert abs(stats["mean"] - 5.0) < 1e-10

    def test_statistics_empty_roi(self):
        """Test statistics with empty ROI (all pixels excluded)."""
        # Create test image
        float_image = torch.ones((3, 3), dtype=torch.float64)

        # Create detector config with ROI that excludes everything
        config = DetectorConfig(
            pixel_size_mm=0.1,
            distance_mm=100.0,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            roi_xmin=10,  # Outside image bounds
            roi_xmax=20,
            roi_ymin=10,
            roi_ymax=20,
        )

        # Create detector and crystal
        detector = Detector(config)
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
        )
        crystal = Crystal(crystal_config)

        # Create simulator
        beam_config = BeamConfig(wavelength_A=1.0)
        simulator = Simulator(crystal, detector, beam_config=beam_config)

        # Compute statistics
        stats = simulator.compute_statistics(float_image)

        # Verify empty results
        assert stats["N"] == 0
        assert stats["max_I"] == 0.0
        assert stats["mean"] == 0.0
        assert stats["RMS"] == 0.0
        assert stats["RMSD"] == 0.0

    def test_statistics_last_max_location(self):
        """Test that max location reports the last occurrence when multiple pixels have max value."""
        # Create test image with duplicate max values
        float_image = torch.tensor([
            [9.0, 2.0, 3.0],
            [4.0, 9.0, 6.0],
            [7.0, 8.0, 9.0]
        ], dtype=torch.float64)

        # Create minimal detector config
        config = DetectorConfig(
            pixel_size_mm=0.1,
            distance_mm=100.0,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            roi_xmin=None,
            roi_xmax=None,
            roi_ymin=None,
            roi_ymax=None,
        )

        # Create detector and crystal
        detector = Detector(config)
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
        )
        crystal = Crystal(crystal_config)

        # Create simulator
        beam_config = BeamConfig(wavelength_A=1.0)
        simulator = Simulator(crystal, detector, beam_config=beam_config)

        # Compute statistics
        stats = simulator.compute_statistics(float_image)

        # Should report the last occurrence of 9.0, which is at (2, 2)
        assert stats["max_I"] == 9.0
        assert stats["max_I_fast"] == 2
        assert stats["max_I_slow"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])