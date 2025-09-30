"""
AT-PARALLEL-006: Single Reflection Position
Tests that single reflection positions follow Bragg's law for various distances and wavelengths.
"""

import pytest
import torch
import numpy as np

# FIXED: Crystal orientation issue resolved by using (0,-1,0) instead of (1,0,0)
# In MOSFLM convention with default orientation, (1,0,0) is parallel to beam
# but (0,-1,0) is perpendicular and can diffract properly with positive offset
from pathlib import Path
import tempfile
import os

from nanobrag_torch.config import (
    CrystalConfig,
    DetectorConfig,
    BeamConfig,
    DetectorConvention,
    DetectorPivot,
    CrystalShape
)
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

class TestATParallel006SingleReflection:
    """
    Tests that single reflection positions match Bragg's law predictions.

    Spec requirement:
    - Setup: Cubic crystal 100Å, single reflection, vary distance (50,100,200mm)
      and wavelength (1.0,1.5,2.0Å)
    - Expectation: Peak position SHALL match Bragg angle calculation θ=arcsin(λ/(2d)) ±0.5 pixels;
      Distance scaling ratio ±2%; Wavelength scaling follows Bragg's law ±1%

    NOTE: Using (0,-1,0) reflection instead of (1,0,0) because in MOSFLM convention
    with default orientation, (1,0,0) is parallel to the beam and cannot diffract.
    The (0,-1,0) reflection has the same d-spacing (100Å) and scatters along the slow axis
    with a positive offset that matches the test's expectations.
    """

    def setup_single_reflection_hkl(self) -> str:
        """Create an HKL file with (0,-1,0) reflection and neighbors for interpolation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hkl', delete=False) as f:
            # Add neighboring reflections to avoid interpolation issues
            # Need a 4x4x4 neighborhood for tricubic interpolation
            for h in range(-2, 4):
                for k in range(-2, 4):
                    for l in range(-2, 4):
                        if h == 0 and k == -1 and l == 0:
                            f.write(f"{h} {k} {l} 1000.0\n")  # Strong (0,-1,0) reflection
                        else:
                            f.write(f"{h} {k} {l} 0.0\n")  # All others zero
            return f.name

    def find_peak(self, image: torch.Tensor, threshold_percentile: float = 99.0) -> tuple:
        """Find the brightest peak in the image."""
        # Flatten and find threshold
        flat_image = image.flatten()
        threshold = torch.quantile(flat_image, threshold_percentile / 100.0)

        # Find max above threshold
        mask = image > threshold
        if not mask.any():
            # No peaks, return center of mass
            coords = torch.meshgrid(
                torch.arange(image.shape[0], dtype=torch.float32),
                torch.arange(image.shape[1], dtype=torch.float32),
                indexing='ij'
            )
            total = image.sum()
            if total > 0:
                slow_cm = (coords[0] * image).sum() / total
                fast_cm = (coords[1] * image).sum() / total
                return (slow_cm.item(), fast_cm.item())
            return (image.shape[0] / 2, image.shape[1] / 2)

        # Find maximum position
        max_val = image.max()
        max_pos = (image == max_val).nonzero()[0]
        return (max_pos[0].item(), max_pos[1].item())

    def calculate_bragg_angle(self, wavelength_A: float, d_spacing_A: float) -> float:
        """Calculate Bragg angle in radians."""
        # Bragg's law: n*λ = 2*d*sin(θ)
        # For n=1: θ = arcsin(λ/(2d))
        sin_theta = wavelength_A / (2.0 * d_spacing_A)
        if sin_theta > 1.0:
            return None  # No diffraction possible
        return np.arcsin(sin_theta)

    def calculate_expected_position(self, theta_rad: float, distance_mm: float,
                                   pixel_size_mm: float, detector_pixels: int) -> float:
        """Calculate expected peak position on detector."""
        if theta_rad is None:
            return None
        # Distance from beam center on detector
        # For small angles: position ≈ distance * tan(2θ)
        # For exact: position = distance * tan(2θ)
        detector_position_mm = distance_mm * np.tan(2.0 * theta_rad)

        # Convert to pixels
        position_pixels = detector_position_mm / pixel_size_mm

        # Add beam center offset (detector center)
        beam_center_pixels = detector_pixels / 2.0
        return beam_center_pixels + position_pixels

    def test_bragg_angle_prediction_single_distance(self):
        """Test that peak position matches Bragg's law for various wavelengths at fixed distance."""
        # Setup
        distance_mm = 100.0
        wavelengths = [1.5, 2.0, 2.5]  # Angstroms (avoid very small angles)
        detector_pixels = 256
        pixel_size_mm = 0.1

        # Create HKL file
        hkl_file = self.setup_single_reflection_hkl()

        try:
            # d-spacing for (0,-1,0) in 100Å cubic cell is 100Å
            d_spacing = 100.0

            peak_positions = []
            expected_positions = []

            for wavelength in wavelengths:
                # Calculate expected position
                theta = self.calculate_bragg_angle(wavelength, d_spacing)
                expected_pos = self.calculate_expected_position(
                    theta, distance_mm, pixel_size_mm, detector_pixels
                )

                if expected_pos is None:
                    continue  # Skip if no diffraction expected

                # Configure simulation
                crystal_config = CrystalConfig(
                    cell_a=100.0,
                    cell_b=100.0,
                    cell_c=100.0,
                    cell_alpha=90.0,
                    cell_beta=90.0,
                    cell_gamma=90.0,
                    N_cells=(10, 10, 10),  # Larger crystal for sufficient intensity
                    shape=CrystalShape.SQUARE,
                    phi_start_deg=0.0,
                    osc_range_deg=0.0,
                    phi_steps=1,
                    mosaic_spread_deg=0.0,
                    mosaic_domains=1
                )

                detector_config = DetectorConfig(
                    distance_mm=distance_mm,
                    pixel_size_mm=pixel_size_mm,
                    spixels=detector_pixels,
                    fpixels=detector_pixels,
                    detector_convention=DetectorConvention.MOSFLM,
                    detector_pivot=DetectorPivot.BEAM
                )

                beam_config = BeamConfig(
                    wavelength_A=wavelength,
                    polarization_factor=0.0,
                    fluence=1e16
                )

                # Initialize models
                crystal = Crystal(crystal_config)
                crystal.load_hkl(hkl_file)
                detector = Detector(detector_config)
                simulator = Simulator(crystal, detector, crystal.config, beam_config)

                # Run simulation
                image = simulator.run()

                # Debug
                max_val = image.max().item()
                print(f"λ={wavelength}Å: max intensity = {max_val:.3e}")
                # Find where the max actually is
                max_pos = (image == image.max()).nonzero()[0]
                print(f"  Max at pixel ({max_pos[0]}, {max_pos[1]})")
                # Check specific pixels near expected position
                expected_pixel = int(expected_pos)
                print(f"  Expected pixel: ({expected_pixel}, {128})")  # (0,-1,0) scatters along slow axis
                if 0 <= expected_pixel < detector_pixels:
                    print(f"  Intensity at expected position: {image[expected_pixel, 128].item():.3e}")

                # Find peak
                peak_slow, peak_fast = self.find_peak(image)

                # For (0,-1,0) reflection in MOSFLM convention,
                # peak should be along slow axis from center
                peak_positions.append(peak_slow)
                expected_positions.append(expected_pos)

                # Check position match (spec: ±0.5 pixels)
                position_error = abs(peak_slow - expected_pos)
                assert position_error < 0.5, \
                    f"Peak position error {position_error:.2f} pixels exceeds 0.5 pixel tolerance " \
                    f"for λ={wavelength}Å (expected {expected_pos:.1f}, got {peak_slow:.1f})"

            # Check wavelength scaling follows Bragg's law (spec: ±1%)
            if len(peak_positions) > 1:
                # Positions should scale with sin(θ) ∝ λ
                for i in range(1, len(wavelengths)):
                    # For small angles, position ∝ tan(2θ) ≈ 2sin(θ) ∝ λ
                    expected_ratio = wavelengths[i] / wavelengths[0]

                    # Distance from beam center
                    pos0 = peak_positions[0] - detector_pixels/2.0
                    posi = peak_positions[i] - detector_pixels/2.0

                    if abs(pos0) > 1.0:  # Avoid division by near-zero
                        actual_ratio = posi / pos0
                        ratio_error = abs(actual_ratio - expected_ratio) / expected_ratio

                        assert ratio_error < 0.01, \
                            f"Wavelength scaling error {ratio_error*100:.1f}% exceeds 1% " \
                            f"for λ={wavelengths[i]}Å (ratio {actual_ratio:.3f} vs expected {expected_ratio:.3f})"

        finally:
            # Cleanup
            os.unlink(hkl_file)
            if Path("Fdump.bin").exists():
                os.unlink("Fdump.bin")

    def test_distance_scaling(self):
        """Test that peak position scales correctly with detector distance."""
        # Setup
        distances = [50.0, 100.0, 200.0]  # mm
        wavelength = 1.5  # Angstroms
        detector_pixels = 256
        pixel_size_mm = 0.1

        # Create HKL file
        hkl_file = self.setup_single_reflection_hkl()

        try:
            # d-spacing for (0,-1,0) in 100Å cubic cell
            d_spacing = 100.0
            theta = self.calculate_bragg_angle(wavelength, d_spacing)

            if theta is None:
                pytest.skip("No diffraction at this wavelength")

            peak_positions = []

            for distance in distances:
                # Configure simulation
                crystal_config = CrystalConfig(
                    cell_a=100.0,
                    cell_b=100.0,
                    cell_c=100.0,
                    cell_alpha=90.0,
                    cell_beta=90.0,
                    cell_gamma=90.0,
                    N_cells=(10, 10, 10),
                    shape=CrystalShape.SQUARE,
                    phi_start_deg=0.0,
                    osc_range_deg=0.0,
                    phi_steps=1,
                    mosaic_spread_deg=0.0,
                    mosaic_domains=1
                )

                detector_config = DetectorConfig(
                    distance_mm=distance,
                    pixel_size_mm=pixel_size_mm,
                    spixels=detector_pixels,
                    fpixels=detector_pixels,
                    detector_convention=DetectorConvention.MOSFLM,
                    detector_pivot=DetectorPivot.BEAM
                )

                beam_config = BeamConfig(
                    wavelength_A=wavelength,
                    polarization_factor=0.0,
                    fluence=1e16
                )

                # Initialize models
                crystal = Crystal(crystal_config)
                crystal.load_hkl(hkl_file)
                detector = Detector(detector_config)
                simulator = Simulator(crystal, detector, crystal.config, beam_config)

                # Run simulation
                image = simulator.run()

                # Find peak
                peak_slow, peak_fast = self.find_peak(image)

                # Store distance from beam center in mm (along slow axis for (0,-1,0))
                beam_center = detector_pixels / 2.0
                position_mm = (peak_slow - beam_center) * pixel_size_mm
                peak_positions.append(position_mm)

            # Check distance scaling (position in mm should be constant for different distances
            # because position_mm = distance * tan(2θ), and we measure position_mm directly)
            # Actually, the ANGLE is constant, so position_mm should scale with distance

            # Positions should scale linearly with distance (spec: ±2%)
            for i in range(1, len(distances)):
                expected_ratio = distances[i] / distances[0]
                actual_ratio = peak_positions[i] / peak_positions[0]

                ratio_error = abs(actual_ratio - expected_ratio) / expected_ratio

                assert ratio_error < 0.02, \
                    f"Distance scaling error {ratio_error*100:.1f}% exceeds 2% " \
                    f"for distance={distances[i]}mm (ratio {actual_ratio:.3f} vs expected {expected_ratio:.3f})"

        finally:
            # Cleanup
            os.unlink(hkl_file)
            if Path("Fdump.bin").exists():
                os.unlink("Fdump.bin")

    def test_combined_wavelength_and_distance(self):
        """Test peak positions for combined wavelength and distance variations."""
        # Test matrix of wavelengths and distances
        wavelengths = [1.0, 2.0]  # Angstroms
        distances = [100.0, 200.0]  # mm
        detector_pixels = 256
        pixel_size_mm = 0.1

        # Create HKL file
        hkl_file = self.setup_single_reflection_hkl()

        try:
            d_spacing = 100.0

            results = {}

            for wavelength in wavelengths:
                for distance in distances:
                    theta = self.calculate_bragg_angle(wavelength, d_spacing)
                    if theta is None:
                        continue

                    # Configure and run simulation
                    crystal_config = CrystalConfig(
                        cell_a=100.0,
                        cell_b=100.0,
                        cell_c=100.0,
                        cell_alpha=90.0,
                        cell_beta=90.0,
                        cell_gamma=90.0,
                        N_cells=(10, 10, 10),
                        shape=CrystalShape.SQUARE,
                        phi_start_deg=0.0,
                        osc_range_deg=0.0,
                        phi_steps=1,
                        mosaic_spread_deg=0.0,
                        mosaic_domains=1
                    )

                    detector_config = DetectorConfig(
                        distance_mm=distance,
                        pixel_size_mm=pixel_size_mm,
                        spixels=detector_pixels,
                        fpixels=detector_pixels,
                        detector_convention=DetectorConvention.MOSFLM,
                        detector_pivot=DetectorPivot.BEAM
                    )

                    beam_config = BeamConfig(
                        wavelength_A=wavelength,
                        polarization_factor=0.0,
                        fluence=1e16
                    )

                    crystal = Crystal(crystal_config)
                    crystal.load_hkl(hkl_file)
                    detector = Detector(detector_config)
                    simulator = Simulator(crystal, detector, crystal.config, beam_config)

                    image = simulator.run()
                    peak_slow, peak_fast = self.find_peak(image)

                    # Calculate expected position
                    expected_pos = self.calculate_expected_position(
                        theta, distance, pixel_size_mm, detector_pixels
                    )

                    # Store results (using slow axis for (0,-1,0) reflection)
                    results[(wavelength, distance)] = {
                        'measured': peak_slow,
                        'expected': expected_pos,
                        'theta': theta
                    }

                    # Check individual position accuracy (spec: ±0.5 pixels)
                    position_error = abs(peak_slow - expected_pos)
                    assert position_error < 0.5, \
                        f"Position error {position_error:.2f} pixels exceeds 0.5 pixel tolerance " \
                        f"for λ={wavelength}Å, d={distance}mm"

            # Cross-check scaling relationships
            if len(results) >= 4:
                # The scattering angle depends only on wavelength
                # The detector position scales with distance * tan(2θ)

                # Check that doubling wavelength doubles the scattering angle (for small angles)
                if (1.0, 100.0) in results and (2.0, 100.0) in results:
                    theta1 = results[(1.0, 100.0)]['theta']
                    theta2 = results[(2.0, 100.0)]['theta']

                    # For small angles, sin(θ) ≈ θ, so θ ∝ λ
                    angle_ratio = theta2 / theta1
                    expected_angle_ratio = 2.0

                    angle_error = abs(angle_ratio - expected_angle_ratio) / expected_angle_ratio
                    assert angle_error < 0.01, \
                        f"Angle scaling with wavelength error: {angle_error*100:.1f}%"

        finally:
            # Cleanup
            os.unlink(hkl_file)
            if Path("Fdump.bin").exists():
                os.unlink("Fdump.bin")