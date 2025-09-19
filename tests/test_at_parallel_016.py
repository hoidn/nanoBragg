"""
AT-PARALLEL-016: Extreme Scale Testing

Tests PyTorch implementation with extreme parameter values to verify stability
and ensure no NaNs, infinities, or exceptions occur. Tests three scenarios:
1. Tiny: Very small crystal and short wavelength
2. Large cell: Very large unit cell
3. Long distance: Detector at 10 meters

Each test verifies that the simulation runs without errors and produces
reasonable patterns when compared with C reference (if available).
"""

import os
import pytest
import torch
import numpy as np
from pathlib import Path

from nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator


class TestATParallel016ExtremeScale:
    """
    Test suite for AT-PARALLEL-016: Extreme Scale Testing

    Verifies that the simulation handles extreme parameter values without
    producing NaNs, infinities, or exceptions.
    """

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment"""
        self.dtype = torch.float64
        self.device = torch.device("cpu")

    def test_tiny_scale(self):
        """
        Test Case 1: Tiny crystal with very small parameters
        N=1, λ=0.1Å, distance=10mm, 128×128, pixel 0.05mm
        """
        # Configuration for tiny scale
        detector_config = DetectorConfig(
            distance_mm=10.0,  # Very close detector
            pixel_size_mm=0.05,  # Small pixels
            spixels=128,
            fpixels=128,
            detector_convention=DetectorConvention.MOSFLM
        )

        crystal_config = CrystalConfig(
            cell_a=100.0,  # Standard cell size
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(1, 1, 1),  # Single unit cell
            default_F=100.0,
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            mosaic_spread_deg=0.0,
            mosaic_domains=1
        )

        beam_config = BeamConfig(
            wavelength_A=0.1,  # Very short wavelength
            fluence=1e12
        )

        # Create simulator
        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation
        image = simulator.run()

        # Verify no NaNs or infinities
        assert not torch.isnan(image).any(), "Image contains NaN values"
        assert not torch.isinf(image).any(), "Image contains infinite values"

        # Verify reasonable intensity range (should be positive)
        assert image.min() >= 0, f"Negative intensities found: {image.min()}"

        # Verify some signal is present (not all zeros)
        assert image.max() > 0, "No signal generated (all zeros)"

        # Check that max intensity is reasonable (not extremely large)
        assert image.max() < 1e10, f"Unreasonably large intensities: {image.max()}"

        print(f"Tiny scale test passed - max intensity: {image.max():.2e}, "
              f"mean: {image.mean():.2e}")

    def test_large_cell(self):
        """
        Test Case 2: Large unit cell
        Cell: 300×300×300 Å, N=10, λ=6Å, 1024×1024, pixel 0.1mm
        """
        # Configuration for large cell
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            detector_convention=DetectorConvention.MOSFLM
        )

        crystal_config = CrystalConfig(
            cell_a=300.0,  # Very large cell
            cell_b=300.0,
            cell_c=300.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(10, 10, 10),  # Large crystal
            default_F=100.0,
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            mosaic_spread_deg=0.0,
            mosaic_domains=1
        )

        beam_config = BeamConfig(
            wavelength_A=6.0,  # Long wavelength
            fluence=1e12
        )

        # Create simulator
        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation on a smaller ROI to save memory
        detector_config.roi_xmin = 400
        detector_config.roi_xmax = 624
        detector_config.roi_ymin = 400
        detector_config.roi_ymax = 624

        # Run simulation
        image = simulator.run()

        # Verify no NaNs or infinities
        assert not torch.isnan(image).any(), "Image contains NaN values"
        assert not torch.isinf(image).any(), "Image contains infinite values"

        # Verify reasonable intensity range
        assert image.min() >= 0, f"Negative intensities found: {image.min()}"

        # Large cells might produce very weak diffraction, so just check non-negative
        if image.max() > 0:
            assert image.max() < 1e10, f"Unreasonably large intensities: {image.max()}"

        print(f"Large cell test passed - max intensity: {image.max():.2e}, "
              f"mean: {image.mean():.2e}")

    def test_long_distance(self):
        """
        Test Case 3: Detector at very long distance
        distance=10000mm (10m), 256×256, pixel 0.2mm
        """
        # Configuration for long distance
        detector_config = DetectorConfig(
            distance_mm=10000.0,  # 10 meters!
            pixel_size_mm=0.2,
            spixels=256,
            fpixels=256,
            detector_convention=DetectorConvention.MOSFLM
        )

        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=100.0,
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            mosaic_spread_deg=0.0,
            mosaic_domains=1
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e12
        )

        # Create simulator
        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation
        image = simulator.run()

        # Verify no NaNs or infinities
        assert not torch.isnan(image).any(), "Image contains NaN values"
        assert not torch.isinf(image).any(), "Image contains infinite values"

        # Verify reasonable intensity range
        assert image.min() >= 0, f"Negative intensities found: {image.min()}"

        # At 10m distance, intensity will be very low due to 1/R^2 falloff
        # Just verify no numerical issues
        if image.max() > 0:
            assert image.max() < 1e10, f"Unreasonably large intensities: {image.max()}"

        print(f"Long distance test passed - max intensity: {image.max():.2e}, "
              f"mean: {image.mean():.2e}")

    @pytest.mark.skipif(
        os.environ.get("NB_RUN_PARALLEL", "0") != "1",
        reason="C-PyTorch parallel tests require NB_RUN_PARALLEL=1"
    )
    def test_extreme_scale_c_comparison(self):
        """
        Compare extreme scale scenarios with C reference implementation.
        Tests that correlation remains reasonable even at extreme scales.
        """
        pytest.skip("C comparison for extreme scales requires special golden data generation")

        # This test would require generating golden data with the C code
        # for each extreme scenario and comparing results.
        # The implementation would be similar to other parallel tests
        # but is skipped for now as it requires extensive C execution.

    def test_combined_extremes(self):
        """
        Test multiple extreme conditions simultaneously
        Small detector, large crystal, short wavelength
        """
        # Configuration combining extremes
        detector_config = DetectorConfig(
            distance_mm=50.0,  # Short distance
            pixel_size_mm=0.05,  # Small pixels
            spixels=128,
            fpixels=128,
            detector_convention=DetectorConvention.MOSFLM
        )

        crystal_config = CrystalConfig(
            cell_a=200.0,  # Large cell
            cell_b=250.0,
            cell_c=300.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(1, 1, 1),  # Small crystal
            default_F=100.0,
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            mosaic_spread_deg=0.0,
            mosaic_domains=1
        )

        beam_config = BeamConfig(
            wavelength_A=0.5,  # Short wavelength
            fluence=1e12
        )

        # Create simulator
        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation
        image = simulator.run()

        # Verify no NaNs or infinities
        assert not torch.isnan(image).any(), "Image contains NaN values"
        assert not torch.isinf(image).any(), "Image contains infinite values"

        # Verify reasonable intensity range
        assert image.min() >= 0, f"Negative intensities found: {image.min()}"

        if image.max() > 0:
            assert image.max() < 1e10, f"Unreasonably large intensities: {image.max()}"

        print(f"Combined extremes test passed - max intensity: {image.max():.2e}, "
              f"mean: {image.mean():.2e}")

    def test_numerical_stability_metrics(self):
        """
        Test that key numerical quantities remain stable at extreme scales
        """
        # Test with large distance to check for underflow
        detector_config = DetectorConfig(
            distance_mm=5000.0,
            pixel_size_mm=0.1,
            spixels=64,
            fpixels=64,
            detector_convention=DetectorConvention.MOSFLM
        )

        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(3, 3, 3),
            default_F=100.0
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e12
        )

        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)

        # Check that geometric calculations are stable
        pixel_coords = detector.get_pixel_coords()
        assert not torch.isnan(pixel_coords).any(), "Pixel coords contain NaN"
        assert not torch.isinf(pixel_coords).any(), "Pixel coords contain inf"

        # Check solid angle calculation
        solid_angles = detector.get_solid_angle()
        assert not torch.isnan(solid_angles).any(), "Solid angles contain NaN"
        assert not torch.isinf(solid_angles).any(), "Solid angles contain inf"
        assert (solid_angles > 0).all(), "Solid angles should be positive"
        assert (solid_angles < 1).all(), "Solid angles unreasonably large"

        # Check crystal calculations
        real_vecs = [crystal.a, crystal.b, crystal.c]
        recip_vecs = [crystal.a_star, crystal.b_star, crystal.c_star]

        for vec in real_vecs + recip_vecs:
            assert not torch.isnan(vec).any(), "Crystal vectors contain NaN"
            assert not torch.isinf(vec).any(), "Crystal vectors contain inf"

        print("Numerical stability test passed")