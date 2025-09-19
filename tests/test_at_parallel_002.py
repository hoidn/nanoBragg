"""
AT-PARALLEL-002: Pixel Size Independence test

Tests that beam centers and peak positions scale correctly with pixel size.
Fixed 256x256 detector with varying pixel sizes.
"""

import pytest
import torch
import numpy as np
from pathlib import Path

from src.nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention
)
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator


class TestATParallel002:
    """Test pixel size independence per spec AT-PARALLEL-002."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create common test configuration."""
        # We'll use default_F for simple cubic crystal
        pass

    def test_beam_center_scales_with_pixel_size(self):
        """Test that beam center in pixels scales inversely with pixel size.

        AT-PARALLEL-002: With fixed 256x256 detector and beam center at 25.6mm,
        the beam center in pixels SHALL equal 25.6mm / pixel_size_mm ±0.1 pixels.
        """
        pixel_sizes = [0.05, 0.1, 0.2, 0.4]  # mm
        # Use detector center (128 pixels for 256x256 detector)
        fixed_beam_center_pixels = 128  # Center pixel

        for pixel_size in pixel_sizes:
            # Calculate beam center in mm for this pixel size
            beam_center_mm = fixed_beam_center_pixels * pixel_size

            # Create detector config with fixed size and varying pixel size
            detector_config = DetectorConfig(
                detector_convention=DetectorConvention.MOSFLM,
                distance_mm=100.0,
                pixel_size_mm=pixel_size,
                spixels=256,
                fpixels=256,
                beam_center_s=beam_center_mm,
                beam_center_f=beam_center_mm,
            )

            # Verify that the beam center in mm is preserved
            assert abs(detector_config.beam_center_s - beam_center_mm) < 0.001, \
                f"Beam center S (mm) not preserved for pixel_size={pixel_size}mm"
            assert abs(detector_config.beam_center_f - beam_center_mm) < 0.001, \
                f"Beam center F (mm) not preserved for pixel_size={pixel_size}mm"

            # Create detector to verify pixel coordinates
            detector = Detector(detector_config)

            # Calculate expected beam center in pixels
            # MOSFLM convention adds +0.5 pixel offset: beam_center_pixels = beam_center_mm / pixel_size_mm + 0.5
            expected_beam_pixel = beam_center_mm / pixel_size + 0.5

            # The detector internally stores beam centers in pixels (with the +0.5 offset for MOSFLM)
            # Verify the beam center in pixels scales inversely with pixel size
            assert abs(detector.beam_center_s.item() - expected_beam_pixel) < 0.1, \
                f"Beam center S (pixels) mismatch for pixel_size={pixel_size}mm: {detector.beam_center_s.item()} vs {expected_beam_pixel}"
            assert abs(detector.beam_center_f.item() - expected_beam_pixel) < 0.1, \
                f"Beam center F (pixels) mismatch for pixel_size={pixel_size}mm: {detector.beam_center_f.item()} vs {expected_beam_pixel}"

    def test_peak_position_scales_inversely_with_pixel_size(self):
        """Test that peak positions scale inversely with pixel size.

        AT-PARALLEL-002: Peak positions SHALL scale inversely with pixel size.
        """
        pixel_sizes = [0.05, 0.1, 0.2, 0.4]  # mm
        # Keep beam center at the same PHYSICAL location (in mm) for all pixel sizes
        # Use a fixed physical location near the detector center
        fixed_beam_center_mm = 12.8  # mm (center for 0.1mm pixels, 256x256 detector)
        peak_positions = []

        for pixel_size in pixel_sizes:
            # Create configurations
            detector_config = DetectorConfig(
                detector_convention=DetectorConvention.MOSFLM,
                distance_mm=100.0,
                pixel_size_mm=pixel_size,
                spixels=256,
                fpixels=256,
                beam_center_s=fixed_beam_center_mm,
                beam_center_f=fixed_beam_center_mm,
            )

            crystal_config = CrystalConfig(
                cell_a=100.0, cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
                N_cells=(3, 3, 3),
                default_F=100.0
            )

            beam_config = BeamConfig(
                wavelength_A=6.2,
                fluence=1e24  # Use realistic fluence for meaningful intensities
            )

            # Run simulation
            detector = Detector(detector_config)
            crystal = Crystal(crystal_config)
            simulator = Simulator(crystal, detector, crystal_config, beam_config)

            image = simulator.run()

            # Find peak position (maximum intensity)
            max_idx = torch.argmax(image)
            peak_s = max_idx // 256
            peak_f = max_idx % 256

            # Store peak position in mm (physical units)
            peak_position_mm = torch.tensor([
                peak_s.float() * pixel_size,
                peak_f.float() * pixel_size
            ])
            peak_positions.append(peak_position_mm)

        # Verify that peak positions in physical units are consistent
        # They should be approximately the same location in mm
        reference_pos = peak_positions[0]
        for i, pos in enumerate(peak_positions[1:], 1):
            diff_mm = torch.norm(pos - reference_pos)
            assert diff_mm < 2.0, \
                f"Peak position differs by {diff_mm:.2f}mm for pixel_size={pixel_sizes[i]}mm"

    def test_pattern_correlation_across_pixel_sizes(self):
        """Test pattern correlation remains high across different pixel sizes.

        AT-PARALLEL-002: Pattern correlation SHALL be >0.95 across pixel sizes.
        """
        # Use two pixel sizes but adjust detector dimensions to maintain same physical area
        pixel_sizes = [0.1, 0.2]  # mm
        detector_pixels = [256, 128]  # Adjust pixel count to maintain same detector size in mm

        # Fixed physical detector size: 25.6mm x 25.6mm
        fixed_detector_size_mm = 25.6
        # Fixed beam center at physical center: 12.8mm
        fixed_beam_center_mm = 12.8

        images = []

        for pixel_size, n_pixels in zip(pixel_sizes, detector_pixels):
            # Verify we maintain the same physical detector size
            assert abs(n_pixels * pixel_size - fixed_detector_size_mm) < 0.01, \
                f"Detector size mismatch: {n_pixels * pixel_size}mm vs {fixed_detector_size_mm}mm"

            # Create configurations with same physical area but different pixel sizes
            detector_config = DetectorConfig(
                detector_convention=DetectorConvention.MOSFLM,
                distance_mm=100.0,
                pixel_size_mm=pixel_size,
                spixels=n_pixels,
                fpixels=n_pixels,
                beam_center_s=fixed_beam_center_mm,
                beam_center_f=fixed_beam_center_mm,
            )

            crystal_config = CrystalConfig(
                cell_a=100.0, cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
                N_cells=(5, 5, 5),  # Larger crystal for more reflections
                default_F=100.0
            )

            beam_config = BeamConfig(
                wavelength_A=6.2,
                fluence=1e24  # Use realistic fluence for meaningful intensities
            )

            # Run simulation
            detector = Detector(detector_config)
            crystal = Crystal(crystal_config)
            simulator = Simulator(crystal, detector, crystal_config, beam_config)

            image = simulator.run()
            images.append(image)

        # Resample the coarser image (128x128) to match the finer one (256x256)
        # Using bilinear interpolation to upsample
        img_fine = images[0]  # 256x256 with 0.1mm pixels
        img_coarse = images[1]  # 128x128 with 0.2mm pixels

        # Upsample the coarse image to 256x256 for comparison
        # Each coarse pixel maps to 2x2 fine pixels
        img_coarse_upsampled = torch.zeros_like(img_fine)
        for i in range(128):
            for j in range(128):
                # Each coarse pixel expands to a 2x2 block in the fine grid
                img_coarse_upsampled[2*i:2*i+2, 2*j:2*j+2] = img_coarse[i, j]

        # Normalize images for correlation
        img1 = img_fine.flatten()
        img2 = img_coarse_upsampled.flatten()

        # Remove zero/background pixels for better correlation measurement
        # Focus on pixels with significant intensity
        threshold = 0.01 * max(img1.max(), img2.max())
        mask = (img1 > threshold) | (img2 > threshold)

        if mask.sum() > 10:  # Need enough pixels for meaningful correlation
            img1_masked = img1[mask]
            img2_masked = img2[mask]

            # Compute correlation coefficient
            img1_norm = (img1_masked - img1_masked.mean()) / (img1_masked.std() + 1e-10)
            img2_norm = (img2_masked - img2_masked.mean()) / (img2_masked.std() + 1e-10)

            correlation = (img1_norm * img2_norm).mean()
        else:
            # If not enough bright pixels, compare whole images
            img1_norm = (img1 - img1.mean()) / (img1.std() + 1e-10)
            img2_norm = (img2 - img2.mean()) / (img2.std() + 1e-10)
            correlation = (img1_norm * img2_norm).mean()

        # With proper resampling and same physical area, correlation should be high
        assert correlation > 0.95, \
            f"Pattern correlation {correlation:.3f} is below threshold 0.95"

    def test_beam_center_parameter_consistency(self):
        """Test that beam center parameters are handled consistently across pixel sizes.

        Additional test to verify parameter handling.
        """
        pixel_sizes = [0.05, 0.1, 0.2, 0.4]  # mm
        # Use detector center (128 pixels for 256x256 detector)
        fixed_beam_center_pixels = 128  # Center pixel

        for pixel_size in pixel_sizes:
            # Calculate beam center in mm for this pixel size
            beam_center_mm = fixed_beam_center_pixels * pixel_size
            # Calculate beam center in mm for this pixel size
            beam_center_mm = fixed_beam_center_pixels * pixel_size

            # Test that setting beam center in mm is properly converted
            detector_config = DetectorConfig(
                detector_convention=DetectorConvention.MOSFLM,
                distance_mm=100.0,
                pixel_size_mm=pixel_size,
                spixels=256,
                fpixels=256,
                beam_center_s=beam_center_mm,
                beam_center_f=beam_center_mm,
            )

            detector = Detector(detector_config)

            # Verify the detector stores beam centers correctly in pixels
            # MOSFLM convention adds 0.5 pixel offset
            expected_beam_pixel = beam_center_mm / pixel_size + 0.5

            assert abs(detector.beam_center_s.item() - expected_beam_pixel) < 0.01, \
                f"Detector beam_center_s incorrect for pixel_size={pixel_size}mm"
            assert abs(detector.beam_center_f.item() - expected_beam_pixel) < 0.01, \
                f"Detector beam_center_f incorrect for pixel_size={pixel_size}mm"

            # Verify that the distance is correctly calculated
            assert abs(detector.distance_corrected.item() - 0.1) < 1e-6, \
                f"Distance should be 100mm = 0.1m for all pixel sizes"