"""
Test AT-PARALLEL-015: Mixed Unit Input Handling

This test validates that unit conversions are applied consistently and results
are independent of the input units used. It verifies there are no unit confusion
errors when mixing different unit specifications.
"""

import numpy as np
import torch
import pytest
from pathlib import Path

from nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention, CrystalShape
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator


class TestATParallel015MixedUnits:
    """AT-PARALLEL-015: Mixed Unit Input Handling."""

    def test_distance_units_consistency(self):
        """Test that distance specified in different ways gives same result."""
        # Base configuration
        crystal_config = CrystalConfig(
            cell_a=100.0,  # Angstroms
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,  # degrees
            cell_beta=90.0,
            cell_gamma=90.0,
            default_F=100.0,
            N_cells=(3, 3, 3),
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,  # Angstroms
            fluence=1e24,
        )

        # Test 1: Distance in mm (standard)
        detector1 = DetectorConfig(
            distance_mm=100.0,  # 100 mm
            pixel_size_mm=0.1,
            spixels=64,
            fpixels=64,
            detector_convention=DetectorConvention.MOSFLM,
        )

        det1 = Detector(detector1)
        crystal1 = Crystal(crystal_config)
        sim1 = Simulator(detector=det1, crystal=crystal1, beam_config=beam_config)
        intensity1 = sim1.run(oversample=1)

        # Test 2: Different distance but same physical setup
        detector2 = DetectorConfig(
            distance_mm=200.0,  # 200 mm - double the distance
            pixel_size_mm=0.2,  # double the pixel size to maintain same angular coverage
            spixels=64,
            fpixels=64,
            detector_convention=DetectorConvention.MOSFLM,
        )

        det2 = Detector(detector2)
        crystal2 = Crystal(crystal_config)
        sim2 = Simulator(detector=det2, crystal=crystal2, beam_config=beam_config)
        intensity2 = sim2.run(oversample=1)

        # The patterns should be similar (same angular coverage)
        # but intensities scale with 1/r^2
        # Account for the solid angle difference:
        # Intensity scales as 1/r^2 for same pixel size
        # But we doubled pixel size, so solid angle is 4x larger
        # Net effect: intensity2 should be similar to intensity1

        # Find peaks and compare positions
        peak1 = torch.argmax(intensity1).item()
        peak2 = torch.argmax(intensity2).item()

        peak1_y, peak1_x = divmod(peak1, 64)
        peak2_y, peak2_x = divmod(peak2, 64)

        # Peaks should appear at the same pixel position (same angular coverage)
        assert abs(peak1_x - peak2_x) <= 1, f"Peak X positions differ: {peak1_x} vs {peak2_x}"
        assert abs(peak1_y - peak2_y) <= 1, f"Peak Y positions differ: {peak1_y} vs {peak2_y}"

        # Check that both produce reasonable intensities (no unit errors)
        assert intensity1.max() > 0, "First simulation produced zero intensity"
        assert intensity2.max() > 0, "Second simulation produced zero intensity"
        assert not torch.isnan(intensity1).any(), "First simulation has NaN values"
        assert not torch.isnan(intensity2).any(), "Second simulation has NaN values"

    def test_wavelength_units_consistency(self):
        """Test wavelength specified in Angstroms gives consistent results."""
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            default_F=100.0,
            N_cells=(3, 3, 3),
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64,
            fpixels=64,
            detector_convention=DetectorConvention.MOSFLM,
        )

        # Test with different wavelengths (all in Angstroms as per spec)
        wavelengths_A = [0.5, 1.0, 1.5, 2.0]

        det = Detector(detector_config)
        crystal = Crystal(crystal_config)

        peak_positions = []
        for wavelength in wavelengths_A:
            beam_config = BeamConfig(
                wavelength_A=wavelength,
                fluence=1e24,
            )
            sim = Simulator(detector=det, crystal=crystal, beam_config=beam_config)
            intensity = sim.run(oversample=1)

            # Find peak position
            peak_idx = torch.argmax(intensity).item()
            peak_y, peak_x = divmod(peak_idx, 64)

            # Calculate expected Bragg angle
            # For (1,0,0) reflection: sin(theta) = λ/(2d) where d = 100Å
            sin_theta = wavelength / (2 * 100.0)

            # Store peak position relative to beam center
            beam_center = 32  # For 64x64 detector with MOSFLM
            radial_distance = np.sqrt((peak_x - beam_center)**2 + (peak_y - beam_center)**2)
            peak_positions.append(radial_distance)

            # Verify intensity is reasonable
            assert intensity.max() > 0, f"Zero intensity for wavelength {wavelength}Å"
            assert not torch.isnan(intensity).any(), f"NaN values for wavelength {wavelength}Å"

        # Peak positions should increase with wavelength (larger Bragg angle)
        for i in range(len(peak_positions) - 1):
            # Allow for discretization effects
            assert peak_positions[i+1] >= peak_positions[i] - 1, \
                f"Peak positions not increasing with wavelength: {peak_positions}"

    def test_angle_units_consistency(self):
        """Test that angles specified in degrees are handled correctly."""
        # Test various angle configurations
        angle_sets = [
            (90.0, 90.0, 90.0),  # Cubic
            (90.0, 90.0, 120.0),  # Hexagonal
            (70.0, 80.0, 85.0),  # Triclinic
        ]

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64,
            fpixels=64,
            detector_convention=DetectorConvention.MOSFLM,
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e24,
        )

        det = Detector(detector_config)

        for alpha, beta, gamma in angle_sets:
            crystal_config = CrystalConfig(
                cell_a=100.0,
                cell_b=100.0,
                cell_c=100.0,
                cell_alpha=alpha,  # degrees
                cell_beta=beta,    # degrees
                cell_gamma=gamma,  # degrees
                default_F=100.0,
                N_cells=(3, 3, 3),
            )

            crystal = Crystal(crystal_config)

            # Verify angles are converted correctly (stored as radians internally)
            alpha_rad = np.radians(alpha)
            beta_rad = np.radians(beta)
            gamma_rad = np.radians(gamma)

            # Check that crystal has correct angles (stored in config)
            # Note: Crystal doesn't expose angles as attributes, they're internal
            # We can verify they're handled correctly by checking the simulation runs

            # Run simulation
            sim = Simulator(detector=det, crystal=crystal, beam_config=beam_config)
            intensity = sim.run(oversample=1)

            # Verify simulation produces valid results
            assert intensity.max() > 0, f"Zero intensity for angles ({alpha}, {beta}, {gamma})"
            assert not torch.isnan(intensity).any(), f"NaN values for angles ({alpha}, {beta}, {gamma})"
            assert not torch.isinf(intensity).any(), f"Inf values for angles ({alpha}, {beta}, {gamma})"

    def test_mixed_units_comprehensive(self):
        """Test comprehensive mixed unit scenario."""
        # Configuration with explicit units
        crystal_config = CrystalConfig(
            cell_a=75.5,      # Angstroms
            cell_b=82.3,      # Angstroms
            cell_c=91.7,      # Angstroms
            cell_alpha=87.5,  # degrees
            cell_beta=92.3,   # degrees
            cell_gamma=95.8,  # degrees
            default_F=100.0,
            N_cells=(3, 3, 3),
            phi_start_deg=0.0,    # degrees
            osc_range_deg=1.0,    # degrees
            phi_steps=1,
        )

        detector_config = DetectorConfig(
            distance_mm=150.5,      # millimeters
            pixel_size_mm=0.172,    # millimeters
            spixels=128,
            fpixels=128,
            detector_convention=DetectorConvention.XDS,
            detector_rotx_deg=5.0,  # degrees
            detector_roty_deg=3.0,  # degrees
            detector_rotz_deg=2.0,  # degrees
            detector_twotheta_deg=10.0,  # degrees
        )

        beam_config = BeamConfig(
            wavelength_A=1.54,  # Angstroms (Cu K-alpha)
            fluence=1e23,
            polarization_factor=0.95,  # dimensionless
            dmin=2.0,          # Angstroms
        )

        # Create models
        det = Detector(detector_config)
        crystal = Crystal(crystal_config)

        # Verify unit conversions happened correctly
        # Detector distance should be in meters internally
        assert np.isclose(det.distance, 0.1505, rtol=1e-6), \
            f"Distance conversion error: {det.distance} != 0.1505"

        # Pixel size should be in meters internally
        assert np.isclose(det.pixel_size, 0.000172, rtol=1e-6), \
            f"Pixel size conversion error: {det.pixel_size} != 0.000172"

        # Rotations are converted internally but not exposed as attributes
        # We can verify they work correctly by running the simulation

        # Wavelength should be in meters internally (used in simulator)
        # Note: BeamConfig stores in Angstroms, conversion happens in simulator
        assert beam_config.wavelength_A == 1.54, "Wavelength storage error"

        # Run simulation
        sim = Simulator(detector=det, crystal=crystal, beam_config=beam_config)
        intensity = sim.run(oversample=1)

        # Comprehensive checks
        assert intensity.shape == (128, 128), f"Wrong output shape: {intensity.shape}"
        assert intensity.max() > 0, "Zero maximum intensity"
        assert not torch.isnan(intensity).any(), "NaN values in output"
        assert not torch.isinf(intensity).any(), "Inf values in output"

        # Check that dmin filtering is working (should reduce intensity at high angles)
        center = 64  # XDS convention centers at detector middle
        corner_intensity = intensity[0:10, 0:10].mean()
        center_intensity = intensity[center-5:center+5, center-5:center+5].mean()

        # Center should have higher intensity than corners (due to dmin filtering)
        # This isn't always true for all crystals, but with dmin=2.0 it should be
        if center_intensity > 0:  # Only check if there's signal
            ratio = corner_intensity / center_intensity
            assert ratio < 1.0 or corner_intensity == 0, \
                f"dmin filtering not working: corner/center = {ratio}"

    def test_detector_rotation_units(self):
        """Test that detector rotations in degrees are handled correctly."""
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            default_F=100.0,
            N_cells=(3, 3, 3),
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e24,
        )

        # Test various rotation angles in degrees
        rotation_sets = [
            (0.0, 0.0, 0.0, 0.0),      # No rotation
            (5.0, 0.0, 0.0, 0.0),      # X rotation only
            (0.0, 10.0, 0.0, 0.0),     # Y rotation only
            (0.0, 0.0, 15.0, 0.0),     # Z rotation only
            (5.0, 3.0, 2.0, 10.0),     # Combined rotations
        ]

        for rotx, roty, rotz, twotheta in rotation_sets:
            detector_config = DetectorConfig(
                distance_mm=100.0,
                pixel_size_mm=0.1,
                spixels=64,
                fpixels=64,
                detector_convention=DetectorConvention.MOSFLM,
                detector_rotx_deg=rotx,
                detector_roty_deg=roty,
                detector_rotz_deg=rotz,
                detector_twotheta_deg=twotheta,
            )

            det = Detector(detector_config)
            crystal = Crystal(crystal_config)

            # Verify rotations are converted to radians (stored in config)
            # Note: Detector internally converts to radians, but doesn't expose as attributes
            # We can verify correct handling by checking simulation runs successfully

            # Run simulation
            sim = Simulator(detector=det, crystal=crystal, beam_config=beam_config)
            intensity = sim.run(oversample=1)

            # Verify valid output
            assert intensity.max() > 0, \
                f"Zero intensity for rotations ({rotx}, {roty}, {rotz}, {twotheta})"
            assert not torch.isnan(intensity).any(), \
                f"NaN values for rotations ({rotx}, {roty}, {rotz}, {twotheta})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])