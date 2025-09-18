"""Test for AT-ROI-001: ROI and mask behavior.

From spec:
- AT-ROI-001 ROI and mask behavior
  - Setup: Provide -roi limiting to a sub-rectangle and a -mask with zeros in a subset.
  - Expectation: Pixels outside ROI or with mask value 0 SHALL be skipped in rendering
    and excluded from statistics.
"""

import os
import torch
import pytest

from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.io.mask import create_circular_mask, create_rectangle_mask


class TestAT_ROI_001:
    """Test suite for AT-ROI-001: ROI and mask behavior."""

    def test_roi_bounds_default_to_full_detector(self):
        """Test that unspecified ROI defaults to full detector."""
        config = DetectorConfig(
            spixels=100,
            fpixels=120,
            distance_mm=100.0,
            pixel_size_mm=0.1,
        )

        # Check defaults were set correctly
        assert config.roi_xmin == 0
        assert config.roi_xmax == 119  # fpixels - 1
        assert config.roi_ymin == 0
        assert config.roi_ymax == 99   # spixels - 1

    def test_roi_bounds_validation(self):
        """Test that invalid ROI bounds raise errors."""
        # Test negative bounds
        with pytest.raises(ValueError, match="roi_xmin must be in"):
            DetectorConfig(
                spixels=100,
                fpixels=120,
                roi_xmin=-1,
            )

        # Test bounds exceeding detector size
        with pytest.raises(ValueError, match="roi_xmax must be in"):
            DetectorConfig(
                spixels=100,
                fpixels=120,
                roi_xmax=120,  # Should be max 119
            )

        # Test min > max
        with pytest.raises(ValueError, match="roi_xmin must be <= roi_xmax"):
            DetectorConfig(
                spixels=100,
                fpixels=120,
                roi_xmin=50,
                roi_xmax=40,
            )

    def test_roi_limits_rendering_area(self):
        """Test that ROI correctly limits the rendering area."""
        # Set environment variable to prevent MKL issues
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        # Create small detector with limited ROI
        detector_config = DetectorConfig(
            spixels=50,
            fpixels=60,
            distance_mm=100.0,
            pixel_size_mm=0.1,
            roi_xmin=20,  # Fast axis: only pixels 20-39
            roi_xmax=39,
            roi_ymin=10,  # Slow axis: only pixels 10-29
            roi_ymax=29,
        )

        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            default_F=100.0,
            N_cells=(5, 5, 5),
        )

        beam_config = BeamConfig(
            wavelength_A=6.2,
            fluence=1e24,
        )

        # Create simulator
        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation
        intensity = simulator.run()

        # Check that pixels outside ROI are zero
        # Outside ROI vertically (slow axis)
        assert torch.all(intensity[:10, :] == 0), "Pixels below ROI ymin should be zero"
        assert torch.all(intensity[30:, :] == 0), "Pixels above ROI ymax should be zero"

        # Outside ROI horizontally (fast axis)
        assert torch.all(intensity[:, :20] == 0), "Pixels left of ROI xmin should be zero"
        assert torch.all(intensity[:, 40:] == 0), "Pixels right of ROI xmax should be zero"

        # Inside ROI should have some non-zero values (at least at beam center)
        roi_region = intensity[10:30, 20:40]
        assert torch.any(roi_region > 0), "ROI region should have some non-zero intensities"

    def test_mask_array_filtering(self):
        """Test that mask array correctly filters pixels."""
        # Set environment variable to prevent MKL issues
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        # Create detector with circular mask
        spixels, fpixels = 50, 60
        mask = create_circular_mask(
            spixels=spixels,
            fpixels=fpixels,
            center_s=25.0,
            center_f=30.0,
            radius=15.0
        )

        detector_config = DetectorConfig(
            spixels=spixels,
            fpixels=fpixels,
            distance_mm=100.0,
            pixel_size_mm=0.1,
            mask_array=mask,
        )

        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            default_F=100.0,
            N_cells=(5, 5, 5),
        )

        beam_config = BeamConfig(
            wavelength_A=6.2,
            fluence=1e24,
        )

        # Create simulator
        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation
        intensity = simulator.run()

        # Check that masked pixels (mask==0) have zero intensity
        masked_pixels = (mask == 0)
        assert torch.all(intensity[masked_pixels] == 0), "Masked pixels should have zero intensity"

        # Check that unmasked pixels in the center have some intensity
        center_region = intensity[20:30, 25:35]
        center_mask = mask[20:30, 25:35]
        unmasked_center = center_region[center_mask > 0]
        assert torch.any(unmasked_center > 0), "Unmasked center pixels should have non-zero intensity"

    def test_roi_and_mask_combination(self):
        """Test that ROI and mask are properly combined (both must be enabled)."""
        # Set environment variable to prevent MKL issues
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        spixels, fpixels = 50, 60

        # Create rectangular ROI mask
        roi_xmin, roi_xmax = 15, 44
        roi_ymin, roi_ymax = 10, 39

        # Create circular mask that partially overlaps ROI
        circular_mask = create_circular_mask(
            spixels=spixels,
            fpixels=fpixels,
            center_s=20.0,  # Center within ROI
            center_f=25.0,
            radius=10.0
        )

        detector_config = DetectorConfig(
            spixels=spixels,
            fpixels=fpixels,
            distance_mm=100.0,
            pixel_size_mm=0.1,
            roi_xmin=roi_xmin,
            roi_xmax=roi_xmax,
            roi_ymin=roi_ymin,
            roi_ymax=roi_ymax,
            mask_array=circular_mask,
        )

        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            default_F=100.0,
            N_cells=(5, 5, 5),
        )

        beam_config = BeamConfig(
            wavelength_A=6.2,
            fluence=1e24,
        )

        # Create simulator
        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation
        intensity = simulator.run()

        # Create expected combined mask
        roi_mask = create_rectangle_mask(
            spixels, fpixels,
            roi_xmin, roi_xmax,
            roi_ymin, roi_ymax
        )
        combined_mask = roi_mask * circular_mask

        # Check that pixels outside combined mask are zero
        outside_combined = (combined_mask == 0)
        assert torch.all(intensity[outside_combined] == 0), \
            "Pixels outside combined ROI+mask should be zero"

        # Check that some pixels inside combined mask have intensity
        inside_combined = (combined_mask > 0)
        if torch.any(inside_combined):
            inside_intensities = intensity[inside_combined]
            assert torch.any(inside_intensities > 0), \
                "Some pixels inside combined ROI+mask should have non-zero intensity"

    def test_mask_array_dimension_validation(self):
        """Test that mask array with wrong dimensions raises error."""
        wrong_mask = torch.ones(10, 10)  # Wrong size

        with pytest.raises(ValueError, match="Mask array shape"):
            DetectorConfig(
                spixels=50,
                fpixels=60,
                mask_array=wrong_mask,
            )

    def test_statistics_exclude_masked_pixels(self):
        """Test that statistics calculations exclude masked/ROI-filtered pixels.

        Note: This test is a placeholder for when statistics are implemented.
        The spec requires that masked pixels be excluded from statistics.
        """
        # This will be implemented when statistics calculation is added
        # For now, we just verify that the masking infrastructure is in place
        pass