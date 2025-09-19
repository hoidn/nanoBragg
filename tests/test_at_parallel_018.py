"""
AT-PARALLEL-018: Crystal Boundary Conditions

Tests crystal behavior at singular orientations, aligned axes, and zero-angle cases.
Ensures no division by zero errors and graceful handling of degenerate cases.
"""

import numpy as np
import pytest
import torch
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


class TestATParallel018CrystalBoundaryConditions:
    """Test suite for crystal boundary conditions and edge cases."""

    def test_cubic_crystal_aligned_axes(self):
        """Test cubic crystal with axes aligned to lab frame (90° angles)."""
        # Perfect cubic crystal - all angles at 90 degrees
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(3, 3, 3),
            default_F=100.0,
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64, fpixels=64
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e12
        )

        # Create crystal and verify no errors
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation - should not crash
        image = simulator.run()

        # Verify results are finite
        assert torch.isfinite(image).all(), "Image contains NaN or Inf values"
        assert (image >= 0).all(), "Image contains negative values"

    def test_zero_angle_rotations(self):
        """Test crystal with zero-angle rotations (no misset, no phi)."""
        crystal_config = CrystalConfig(
            cell_a=70.0, cell_b=80.0, cell_c=90.0,
            cell_alpha=75.0, cell_beta=85.0, cell_gamma=95.0,
            N_cells=(3, 3, 3),
            default_F=100.0,
            misset_deg=(0.0, 0.0, 0.0),  # Zero misset
            phi_start_deg=0.0,  # Zero phi
            osc_range_deg=0.0,  # No oscillation
            phi_steps=1,
            mosaic_spread_deg=0.0,  # No mosaic
            mosaic_domains=1
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64, fpixels=64,
            detector_rotx_deg=0.0,  # No detector rotations
            detector_roty_deg=0.0,
            detector_rotz_deg=0.0,
            detector_twotheta_deg=0.0
        )

        beam_config = BeamConfig(
            wavelength_A=1.5,
            fluence=1e12
        )

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        image = simulator.run()

        assert torch.isfinite(image).all(), "Image contains NaN or Inf with zero rotations"
        assert (image >= 0).all(), "Image contains negative values"

    def test_near_singular_cell_angles(self):
        """Test crystal with near-singular cell angles (close to 0° or 180°)."""
        # Test case 1: Very acute angle (close to 0°)
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=1.0,  # Very acute gamma angle
            N_cells=(3, 3, 3),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64, fpixels=64
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e12
        )

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        image = simulator.run()

        assert torch.isfinite(image).all(), "Image contains NaN or Inf with acute angle"
        assert (image >= 0).all(), "Image contains negative values"

        # Test case 2: Very obtuse angle (close to 180°)
        crystal_config2 = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=179.0,  # Very obtuse gamma angle
            N_cells=(3, 3, 3),
            default_F=100.0
        )

        crystal2 = Crystal(crystal_config2)
        simulator2 = Simulator(crystal2, detector, crystal_config2, beam_config)

        image2 = simulator2.run()

        assert torch.isfinite(image2).all(), "Image contains NaN or Inf with obtuse angle"
        assert (image2 >= 0).all(), "Image contains negative values"

    def test_aligned_spindle_and_beam(self):
        """Test case where spindle axis is aligned with beam direction."""
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(3, 3, 3),
            default_F=100.0,
            spindle_axis=(1.0, 0.0, 0.0),  # Aligned with X (beam direction in MOSFLM)
            phi_start_deg=0.0,
            osc_range_deg=45.0,
            phi_steps=5
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64, fpixels=64,
            detector_convention=DetectorConvention.MOSFLM  # Beam along X
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e12
        )

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        image = simulator.run()

        assert torch.isfinite(image).all(), "Image contains NaN or Inf with aligned spindle"
        assert (image >= 0).all(), "Image contains negative values"

    def test_very_small_unit_cell(self):
        """Test crystal with very small unit cell dimensions."""
        crystal_config = CrystalConfig(
            cell_a=1.0, cell_b=1.0, cell_c=1.0,  # Very small cell
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(10, 10, 10),  # More cells to compensate
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64, fpixels=64
        )

        beam_config = BeamConfig(
            wavelength_A=0.1,  # Short wavelength for small cell
            fluence=1e12
        )

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        image = simulator.run()

        assert torch.isfinite(image).all(), "Image contains NaN or Inf with small cell"
        assert (image >= 0).all(), "Image contains negative values"

    def test_very_large_unit_cell(self):
        """Test crystal with very large unit cell dimensions."""
        crystal_config = CrystalConfig(
            cell_a=1000.0, cell_b=1000.0, cell_c=1000.0,  # Very large cell
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(1, 1, 1),  # Single cell
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=1000.0,  # Larger distance for large cell
            pixel_size_mm=0.1,
            spixels=64, fpixels=64
        )

        beam_config = BeamConfig(
            wavelength_A=6.2,  # Longer wavelength for large cell
            fluence=1e12
        )

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        image = simulator.run()

        assert torch.isfinite(image).all(), "Image contains NaN or Inf with large cell"
        assert (image >= 0).all(), "Image contains negative values"

    def test_continuity_near_90_degrees(self):
        """Test that results are continuous near 90° angles."""
        angles_to_test = [89.9, 89.99, 89.999, 90.0, 90.001, 90.01, 90.1]
        max_intensities = []

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64, fpixels=64
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e12
        )

        for angle in angles_to_test:
            crystal_config = CrystalConfig(
                cell_a=100.0, cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=angle,
                N_cells=(3, 3, 3),
                default_F=100.0
            )

            crystal = Crystal(crystal_config)
            detector = Detector(detector_config)
            simulator = Simulator(crystal, detector, crystal_config, beam_config)

            image = simulator.run()
            max_intensity = image.max().item()
            max_intensities.append(max_intensity)

            assert torch.isfinite(image).all(), f"Image contains NaN or Inf at angle {angle}"

        # Check continuity - intensities should not jump dramatically
        for i in range(1, len(max_intensities)):
            ratio = max_intensities[i] / max_intensities[i-1] if max_intensities[i-1] > 0 else 1.0
            assert 0.5 < ratio < 2.0, f"Discontinuous jump at angle {angles_to_test[i]}: {ratio:.4f}"

    def test_identity_misset_matrix(self):
        """Test that identity misset (0,0,0) produces valid results."""
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(3, 3, 3),
            default_F=100.0,
            misset_deg=(0.0, 0.0, 0.0)  # Identity misset
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64, fpixels=64
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e12
        )

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        image = simulator.run()

        assert torch.isfinite(image).all(), "Image contains NaN or Inf with identity misset"
        assert (image >= 0).all(), "Image contains negative values"
        assert image.max() > 0, "No intensity with identity misset"


if __name__ == "__main__":
    # Run tests
    test_suite = TestATParallel018CrystalBoundaryConditions()

    print("Testing cubic crystal with aligned axes...")
    test_suite.test_cubic_crystal_aligned_axes()
    print("✓ Passed")

    print("Testing zero-angle rotations...")
    test_suite.test_zero_angle_rotations()
    print("✓ Passed")

    print("Testing near-singular cell angles...")
    test_suite.test_near_singular_cell_angles()
    print("✓ Passed")

    print("Testing aligned spindle and beam...")
    test_suite.test_aligned_spindle_and_beam()
    print("✓ Passed")

    print("Testing very small unit cell...")
    test_suite.test_very_small_unit_cell()
    print("✓ Passed")

    print("Testing very large unit cell...")
    test_suite.test_very_large_unit_cell()
    print("✓ Passed")

    print("Testing continuity near 90 degrees...")
    test_suite.test_continuity_near_90_degrees()
    print("✓ Passed")

    print("Testing identity misset matrix...")
    test_suite.test_identity_misset_matrix()
    print("✓ Passed")

    print("\n✅ All AT-PARALLEL-018 tests passed!")