"""Test AT-PARALLEL-001: Beam Center Scales with Detector Size

Purpose: Catch hardcoded beam center issues
Setup:
- Fixed beam center ratio (0.5, 0.5) relative to detector
- Test detector sizes: 64x64, 128x128, 256x256, 512x512, 1024x1024
- Pixel size: 0.1mm
- Crystal: 100Å cubic, N=3

From spec-a.md lines 827-860:
- Expected Behavior:
  - Beam center (mm) = detector_pixels/2 × pixel_size_mm
  - Peak should appear at (detector_pixels/2, detector_pixels/2) ± 2 pixels
  - Intensity scaling should be proportional to solid angle
- Pass Criteria:
  - Beam center position accuracy: ±0.05mm
  - Peak position accuracy: ±2 pixels from center
  - Cross-size correlation: >0.95 when normalized
- Fail Criteria:
  - Beam center fixed at 51.2mm regardless of detector size
  - Peak always at same absolute pixel position
  - Intensity ratios inconsistent with geometric scaling
"""

import os
import sys
import subprocess
import tempfile
import numpy as np
import pytest
import torch
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig, NoiseConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator
# from src.nanobrag_torch.io.hkl import create_simple_hkl_data  # Not needed for these tests


class TestATParallel001:
    """Test suite for AT-PARALLEL-001: Beam Center Scaling"""

    def setup_method(self):
        """Set up test environment."""
        # Set environment variable for PyTorch
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

    @pytest.mark.parametrize("detector_pixels", [64, 128, 256, 512, 1024])
    def test_beam_center_scales_with_detector_size(self, detector_pixels):
        """Test that beam centers scale correctly with detector size.

        This is the critical test that catches the hardcoded 51.2mm bug.
        """
        pixel_size_mm = 0.1

        # Create detector config with specific detector size
        # Do NOT explicitly set beam centers - let defaults be calculated
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=pixel_size_mm,
            spixels=detector_pixels,
            fpixels=detector_pixels,
            detector_convention=DetectorConvention.MOSFLM
        )

        # Expected beam center in DetectorConfig (geometric center in mm, NO offset yet)
        # The MOSFLM +0.5 pixel offset is applied later in Detector.__init__
        expected_detsize_s = detector_pixels * pixel_size_mm
        expected_detsize_f = detector_pixels * pixel_size_mm
        expected_beam_center_s = expected_detsize_s / 2.0  # Geometric center
        expected_beam_center_f = expected_detsize_f / 2.0  # Geometric center

        # Verify beam centers are calculated correctly in DetectorConfig
        assert abs(detector_config.beam_center_s - expected_beam_center_s) < 0.001, \
            f"Beam center S incorrect for {detector_pixels}x{detector_pixels}: " \
            f"got {detector_config.beam_center_s}, expected {expected_beam_center_s}"
        assert abs(detector_config.beam_center_f - expected_beam_center_f) < 0.001, \
            f"Beam center F incorrect for {detector_pixels}x{detector_pixels}: " \
            f"got {detector_config.beam_center_f}, expected {expected_beam_center_f}"

        # Verify this is NOT the hardcoded 51.2mm bug
        if detector_pixels != 1024:
            assert detector_config.beam_center_s != 51.2, \
                f"CRITICAL BUG: Beam center S is hardcoded at 51.2mm for {detector_pixels}x{detector_pixels} detector!"
            assert detector_config.beam_center_f != 51.2, \
                f"CRITICAL BUG: Beam center F is hardcoded at 51.2mm for {detector_pixels}x{detector_pixels} detector!"

    def test_peak_position_at_beam_center(self):
        """Test that diffraction peak appears at the calculated beam center."""
        # Use a small detector for faster testing
        detector_pixels = 64
        pixel_size_mm = 0.1

        # Set up configuration
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=pixel_size_mm,
            spixels=detector_pixels,
            fpixels=detector_pixels,
            detector_convention=DetectorConvention.MOSFLM
        )

        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(3, 3, 3),  # Small crystal for clear peak
            default_F=100.0
        )

        beam_config = BeamConfig(
            wavelength_A=6.2,
            fluence=1e24
        )

        # Create models
        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation
        image = simulator.run()

        # Find peak position (maximum intensity)
        peak_idx = torch.argmax(image)
        peak_slow = peak_idx // detector_pixels
        peak_fast = peak_idx % detector_pixels

        # Expected peak position at beam center (in pixels)
        # MOSFLM convention adds 0.5 pixel offset
        expected_center_slow = detector_pixels // 2
        expected_center_fast = detector_pixels // 2

        # Check peak is within ±2 pixels of center (per spec)
        assert abs(peak_slow.item() - expected_center_slow) <= 2, \
            f"Peak slow position {peak_slow.item()} not at center {expected_center_slow} ±2"
        assert abs(peak_fast.item() - expected_center_fast) <= 2, \
            f"Peak fast position {peak_fast.item()} not at center {expected_center_fast} ±2"

    def test_cli_beam_center_calculation(self, tmp_path):
        """Test that CLI correctly calculates beam centers for different detector sizes."""
        # Create a simple HKL file
        hkl_file = tmp_path / "test.hkl"
        with open(hkl_file, 'w') as f:
            f.write("0 0 0 100.0\n")
            f.write("1 0 0 50.0\n")

        for detector_pixels in [64, 128, 256]:
            output_file = tmp_path / f"output_{detector_pixels}.bin"

            # Run CLI without specifying beam centers
            cmd = [
                sys.executable, '-m', 'nanobrag_torch',
                '-hkl', str(hkl_file),
                '-cell', '100', '100', '100', '90', '90', '90',
                '-lambda', '6.2',
                '-N', '3',
                '-distance', '100',
                '-detpixels', str(detector_pixels),
                '-pixel', '0.1',
                '-default_F', '100',
                '-floatfile', str(output_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            # Check that the command succeeded
            assert result.returncode == 0, \
                f"CLI failed for {detector_pixels}x{detector_pixels}: {result.stderr}"

            # Verify output file was created
            assert output_file.exists(), f"Output file not created for {detector_pixels}x{detector_pixels}"

            # Load and check the image
            with open(output_file, 'rb') as f:
                data = np.frombuffer(f.read(), dtype=np.float32)
                image = data.reshape(detector_pixels, detector_pixels)

            # Find peak position
            peak_idx = np.unravel_index(np.argmax(image), image.shape)
            center = detector_pixels // 2

            # Peak should be near center (within 2 pixels)
            assert abs(peak_idx[0] - center) <= 2, \
                f"Peak not centered for {detector_pixels}x{detector_pixels}: at {peak_idx}, expected near {center}"
            assert abs(peak_idx[1] - center) <= 2, \
                f"Peak not centered for {detector_pixels}x{detector_pixels}: at {peak_idx}, expected near {center}"

    def test_intensity_scaling_with_solid_angle(self):
        """Test that intensity scales correctly with detector size (solid angle)."""
        pixel_size_mm = 0.1
        distance_mm = 100.0
        intensities = {}

        for detector_pixels in [64, 128]:
            # Set up configuration
            detector_config = DetectorConfig(
                distance_mm=distance_mm,
                pixel_size_mm=pixel_size_mm,
                spixels=detector_pixels,
                fpixels=detector_pixels,
                detector_convention=DetectorConvention.MOSFLM
            )

            crystal_config = CrystalConfig(
                cell_a=100.0, cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
                N_cells=(3, 3, 3),
                default_F=100.0
            )

            beam_config = BeamConfig(
                wavelength_A=6.2,
                fluence=1e24
            )

            # Create models and simulate
            detector = Detector(detector_config)
            crystal = Crystal(crystal_config)
            simulator = Simulator(crystal, detector, crystal_config, beam_config)
            image = simulator.run()

            # Store max intensity for comparison
            intensities[detector_pixels] = torch.max(image).item()

        # Intensities should be similar (solid angle effect is per-pixel)
        # The peak intensity should not vary drastically with detector size
        ratio = intensities[128] / intensities[64]
        assert 0.8 < ratio < 1.25, \
            f"Intensity scaling incorrect: 128px={intensities[128]:.2f}, 64px={intensities[64]:.2f}, ratio={ratio:.2f}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
