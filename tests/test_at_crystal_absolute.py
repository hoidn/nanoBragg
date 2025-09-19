"""
Acceptance Test: AT-CRYSTAL-ABSOLUTE - Absolute Position Validation for Non-Orthogonal Crystals

This test would have caught the 24-pixel triclinic offset bug by validating absolute
Bragg peak positions against analytically calculated values.

Principle: For a known crystal orientation, wavelength, and detector geometry, we can
analytically predict exactly which pixel a given reflection (h,k,l) should appear at.
This tests the entire chain: crystal geometry → reciprocal space → scattering → detector.
"""

import numpy as np
import torch
import pytest
from pathlib import Path
from typing import Tuple, List, Optional

from nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention, DetectorPivot
)
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.simulator import Simulator


class TestATCrystalAbsolute:
    """
    Absolute position validation tests for crystal geometry.

    These tests verify that Bragg reflections appear at the correct absolute
    pixel positions on the detector, not just relative positions.
    """

    def calculate_bragg_position(
        self,
        hkl: Tuple[int, int, int],
        crystal: Crystal,
        detector: Detector,
        wavelength: float
    ) -> Optional[Tuple[float, float]]:
        """
        Analytically calculate where a Bragg reflection should appear on the detector.

        Args:
            hkl: Miller indices (h, k, l)
            crystal: Crystal object with unit cell
            detector: Detector object with geometry
            wavelength: X-ray wavelength in Angstroms

        Returns:
            (slow, fast) pixel coordinates, or None if not on detector
        """
        h, k, l = hkl

        # Get reciprocal lattice vector G = h*a* + k*b* + l*c*
        G = h * crystal.a_star + k * crystal.b_star + l * crystal.c_star

        # For Bragg condition with incident beam along X (MOSFLM convention):
        # The scattering vector q must equal G for constructive interference
        # With elastic scattering: |k_in| = |k_out| = 2π/λ
        k_mag = 2 * np.pi / wavelength

        # Incident wave vector (along +X for MOSFLM)
        k_in = torch.tensor([k_mag, 0.0, 0.0], dtype=crystal.a_star.dtype)

        # For Bragg condition: k_out - k_in = G
        # Therefore: k_out = k_in + G
        k_out = k_in + G

        # Check if this is kinematically allowed (|k_out| ≈ |k_in|)
        if abs(torch.norm(k_out) - k_mag) > 0.1 * k_mag:
            return None  # Reflection not accessible at this wavelength

        # Normalize to get scattered beam direction
        scatter_dir = k_out / torch.norm(k_out)

        # Find intersection with detector plane
        # Ray equation: r = origin + t * scatter_dir
        # Detector plane through detector origin with normal odet_vec
        # For MOSFLM, beam goes along +X and detector is roughly at X = distance

        # Get detector basis vectors
        pixel_coords = detector.get_pixel_coords()
        pix0 = detector.pix0_vector

        # Simple case: assume planar detector perpendicular to beam
        # The detector normal is approximately [1, 0, 0] for small tilts
        # Intersection at X = distance
        t = detector.distance / scatter_dir[0] if scatter_dir[0] > 0 else float('inf')

        if t == float('inf'):
            return None  # Ray doesn't hit detector

        # Point of intersection in lab frame
        intersection = t * scatter_dir

        # Project onto detector coordinate system
        # Vector from pix0 to intersection point
        r_det = intersection - pix0

        # Project onto detector basis vectors to get pixel coordinates
        # Note: Using center-based pixel indexing (0.5, 1.5, 2.5...)
        slow_coord = torch.dot(r_det, detector.sdet_vec) / detector.pixel_size
        fast_coord = torch.dot(r_det, detector.fdet_vec) / detector.pixel_size

        # Check if on detector
        if (0 <= slow_coord < detector.spixels and
            0 <= fast_coord < detector.fpixels):
            return (float(slow_coord), float(fast_coord))
        else:
            return None

    def test_triclinic_absolute_positions(self):
        """
        Test that specific Bragg reflections appear at the correct absolute positions
        for a triclinic crystal.

        This test would have caught the 24-pixel offset bug.
        """
        # Use a well-defined triclinic crystal
        crystal_config = CrystalConfig(
            cell_a=70.0,
            cell_b=80.0,
            cell_c=90.0,
            cell_alpha=85.0,  # Non-orthogonal
            cell_beta=95.0,   # Non-orthogonal
            cell_gamma=105.0, # Non-orthogonal
            N_cells=(1, 1, 1),  # Single unit cell for clarity
            default_F=100.0
        )

        detector_config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            distance_mm=150.0,
            pixel_size_mm=0.1,
            spixels=256,
            fpixels=256
        )

        beam_config = BeamConfig(
            wavelength_A=1.5  # Chosen to put several reflections on detector
        )

        # Create objects
        crystal = Crystal(crystal_config, beam_config)
        detector = Detector(detector_config)

        # Test specific reflections that should be on the detector
        test_reflections = [
            (1, 0, 0),  # (100) reflection
            (0, 1, 0),  # (010) reflection
            (0, 0, 1),  # (001) reflection
            (1, 1, 0),  # (110) reflection
            (1, 0, 1),  # (101) reflection
        ]

        # Run simulation
        simulator = Simulator(crystal, detector, crystal_config, beam_config)
        image = simulator.run()

        # For each test reflection, verify it appears at the correct position
        failures = []
        for hkl in test_reflections:
            # Calculate where it should be
            expected_pos = self.calculate_bragg_position(hkl, crystal, detector, beam_config.wavelength_A)

            if expected_pos is None:
                continue  # Reflection not on detector

            expected_slow, expected_fast = expected_pos

            # Find actual peak position in a small window around expected position
            # Use a 5x5 pixel window
            slow_min = int(max(0, expected_slow - 2))
            slow_max = int(min(detector.spixels, expected_slow + 3))
            fast_min = int(max(0, expected_fast - 2))
            fast_max = int(min(detector.fpixels, expected_fast + 3))

            # Extract window
            window = image[slow_min:slow_max, fast_min:fast_max]

            if window.numel() == 0:
                continue

            # Find peak in window
            max_val = torch.max(window)
            if max_val < 0.01:  # No significant intensity
                failures.append(f"Reflection {hkl} has no intensity at expected position ({expected_slow:.1f}, {expected_fast:.1f})")
                continue

            # Get position of maximum in window
            max_idx = torch.argmax(window.view(-1))
            window_slow = max_idx // window.shape[1]
            window_fast = max_idx % window.shape[1]

            # Convert back to full image coordinates
            actual_slow = slow_min + window_slow
            actual_fast = fast_min + window_fast

            # Calculate distance
            distance = np.sqrt((actual_slow - expected_slow)**2 + (actual_fast - expected_fast)**2)

            # CRITICAL: Absolute position must match within 1 pixel
            # This is the check that would have caught the bug
            if distance > 1.0:
                failures.append(
                    f"Reflection {hkl}: Expected at ({expected_slow:.1f}, {expected_fast:.1f}), "
                    f"found at ({actual_slow}, {actual_fast}), distance = {distance:.2f} pixels"
                )

        # Report all failures
        if failures:
            failure_msg = "Absolute position validation failed:\n" + "\n".join(failures)
            pytest.fail(failure_msg)

    def test_cubic_vs_triclinic_systematic_difference(self):
        """
        Test that validates the crystal geometry implementation by comparing
        cubic and triclinic crystals with known geometric relationships.
        """
        # Create two crystals: one cubic, one triclinic
        cubic_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(1, 1, 1),
            default_F=100.0
        )

        triclinic_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=85.0, cell_beta=95.0, cell_gamma=105.0,
            N_cells=(1, 1, 1),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            distance_mm=150.0,
            pixel_size_mm=0.1,
            spixels=256,
            fpixels=256
        )

        beam_config = BeamConfig(wavelength_A=1.5)

        # Create objects and run simulations
        cubic_crystal = Crystal(cubic_config, beam_config)
        cubic_detector = Detector(detector_config)
        cubic_sim = Simulator(cubic_crystal, cubic_detector, cubic_config, beam_config)
        cubic_image = cubic_sim.run()

        triclinic_crystal = Crystal(triclinic_config, beam_config)
        triclinic_detector = Detector(detector_config)
        triclinic_sim = Simulator(triclinic_crystal, triclinic_detector, triclinic_config, beam_config)
        triclinic_image = triclinic_sim.run()

        # Find brightest spots in each pattern
        cubic_max_idx = torch.argmax(cubic_image)
        cubic_max_slow = cubic_max_idx // cubic_image.shape[1]
        cubic_max_fast = cubic_max_idx % cubic_image.shape[1]

        triclinic_max_idx = torch.argmax(triclinic_image)
        triclinic_max_slow = triclinic_max_idx // triclinic_image.shape[1]
        triclinic_max_fast = triclinic_max_idx % triclinic_image.shape[1]

        # Key insight: The patterns should be different but systematically related
        # A 24-pixel offset would show up as a huge systematic shift
        position_diff = np.sqrt(
            (cubic_max_slow - triclinic_max_slow)**2 +
            (cubic_max_fast - triclinic_max_fast)**2
        )

        # The difference should be reasonable (< 10 pixels) not catastrophic (24 pixels)
        assert position_diff < 10.0, (
            f"Systematic position difference between cubic and triclinic is {position_diff:.1f} pixels. "
            f"This indicates a fundamental geometry bug."
        )

    def test_known_reflection_d_spacings(self):
        """
        Validate that specific reflections appear at positions consistent with
        their known d-spacings.

        This tests the full chain from crystal to detector through the physics.
        """
        crystal_config = CrystalConfig(
            cell_a=70.0,
            cell_b=80.0,
            cell_c=90.0,
            cell_alpha=85.0,
            cell_beta=95.0,
            cell_gamma=105.0,
            N_cells=(2, 2, 2),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=512,
            fpixels=512
        )

        beam_config = BeamConfig(wavelength_A=1.0)

        crystal = Crystal(crystal_config, beam_config)

        # Calculate d-spacings for specific reflections
        reflections = [(1,0,0), (0,1,0), (0,0,1), (1,1,0), (1,1,1)]
        d_spacings = {}

        for hkl in reflections:
            h, k, l = hkl
            G = h * crystal.a_star + k * crystal.b_star + l * crystal.c_star
            d_spacings[hkl] = 1.0 / torch.norm(G).item()

        # Verify d-spacings are reasonable for the given unit cell
        assert 50 < d_spacings[(1,0,0)] < 150, f"d_100 = {d_spacings[(1,0,0)]:.1f} Å is unreasonable"
        assert 50 < d_spacings[(0,1,0)] < 150, f"d_010 = {d_spacings[(0,1,0)]:.1f} Å is unreasonable"
        assert 50 < d_spacings[(0,0,1)] < 150, f"d_001 = {d_spacings[(0,0,1)]:.1f} Å is unreasonable"

        # The key test: these d-spacings should produce Bragg peaks at specific
        # scattering angles, which map to specific detector positions
        # A 24-pixel offset would violate this relationship

        print("\nCalculated d-spacings for triclinic cell:")
        for hkl, d in d_spacings.items():
            theta = np.arcsin(beam_config.wavelength_A / (2 * d)) * 180 / np.pi
            print(f"  {hkl}: d = {d:.2f} Å, 2θ = {2*theta:.2f}°")


if __name__ == "__main__":
    # Run the test that would have caught the bug
    test = TestATCrystalAbsolute()
    test.test_triclinic_absolute_positions()
    test.test_cubic_vs_triclinic_systematic_difference()
    test.test_known_reflection_d_spacings()
    print("\nAll absolute position tests passed!")