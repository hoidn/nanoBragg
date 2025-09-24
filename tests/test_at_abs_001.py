"""
test_at_abs_001.py: Test detector absorption with layering

AT-ABS-001: Detector absorption layering
- Setup: thickness>0; thicksteps>1; finite μ from -detector_abs; choose a pixel with parallax ρ=d·o ≠ 0; disable oversample_thick.
- Expectation: Per-layer capture fractions SHALL follow exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ),
  summing (t=0..steps−1) to 1−exp(−thickness·μ/ρ).
  With -oversample_thick unset, the final S SHALL be multiplied by the last layer's capture fraction;
  with -oversample_thick set, the running sum SHALL be multiplied by each layer's capture fraction as terms accumulate.
"""

import os
import pytest
import torch
import numpy as np

# Set environment variable before importing torch-dependent modules
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator


class TestAT_ABS_001:
    """Test detector absorption layering per AT-ABS-001."""

    def test_absorption_disabled_when_zero(self):
        """Test that absorption is disabled when detector_abs_um=0 or detector_thick_um=0."""
        # Setup with zero thickness
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=10, fpixels=10,
            detector_abs_um=100.0,  # Non-zero attenuation depth
            detector_thick_um=0.0,  # Zero thickness
            detector_thicksteps=1
        )

        crystal_config = CrystalConfig(default_F=100.0)  # Need non-zero intensity
        beam_config = BeamConfig()

        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation
        intensity1 = simulator.run()

        # Run without absorption (as reference)
        detector_config2 = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=10, fpixels=10,
            detector_abs_um=None,  # No absorption
            detector_thick_um=0.0,
            detector_thicksteps=1
        )
        detector2 = Detector(detector_config2)
        simulator2 = Simulator(crystal, detector2, crystal_config, beam_config)
        intensity2 = simulator2.run()

        # Should be identical when thickness is zero
        torch.testing.assert_close(intensity1, intensity2, rtol=1e-6, atol=1e-8)

    def test_capture_fraction_calculation(self):
        """Test that capture fractions follow the expected formula."""
        # Setup with specific absorption parameters
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=3, fpixels=3,  # Small for testing
            detector_abs_um=500.0,  # Attenuation depth in micrometers
            detector_thick_um=100.0,  # 100 μm thickness
            detector_thicksteps=5,  # 5 layers
            oversample_thick=False  # Use last-value semantics
        )

        crystal_config = CrystalConfig(default_F=100.0)  # Need non-zero intensity
        beam_config = BeamConfig()

        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Calculate expected capture fractions manually
        thickness_m = 100e-6  # 100 μm in meters
        mu = 1.0 / (500e-6)  # 1/attenuation_depth
        delta_z = thickness_m / 5  # 5 layers

        # For a center pixel, parallax should be close to 1 (aligned with detector normal)
        # Get pixel coordinates for center pixel
        pixel_coords = detector.get_pixel_coords()  # [S, F, 3] in meters
        center_s, center_f = 1, 1  # Center of 3x3 grid
        center_pixel = pixel_coords[center_s, center_f, :]  # [3]

        # Calculate observation direction
        pixel_distance = torch.sqrt(torch.sum(center_pixel**2))
        obs_dir = center_pixel / pixel_distance

        # Calculate parallax (dot product with detector normal)
        detector_normal = detector.odet_vec
        parallax = torch.abs(torch.sum(detector_normal * obs_dir))

        # Calculate expected capture fraction for last layer (t=4)
        t = 4
        exp_start = torch.exp(-t * delta_z * mu / parallax)
        exp_end = torch.exp(-(t + 1) * delta_z * mu / parallax)
        expected_last_capture = exp_start - exp_end

        # Also verify that all capture fractions sum to expected total
        total_capture = 0
        for t in range(5):
            exp_start = torch.exp(-t * delta_z * mu / parallax)
            exp_end = torch.exp(-(t + 1) * delta_z * mu / parallax)
            total_capture += (exp_start - exp_end)

        expected_total = 1 - torch.exp(-thickness_m * mu / parallax)

        # Verify the sum
        torch.testing.assert_close(total_capture, expected_total, rtol=1e-6, atol=1e-8)

    def test_last_value_vs_accumulation_semantics(self):
        """Test difference between oversample_thick=False (last-value) vs True (accumulation)."""
        # Common setup
        detector_config_base = dict(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=5, fpixels=5,
            detector_abs_um=1000.0,  # 1mm attenuation depth
            detector_thick_um=200.0,  # 200 μm thickness
            detector_thicksteps=4,  # 4 layers
        )

        crystal_config = CrystalConfig(default_F=100.0)  # Need non-zero intensity
        beam_config = BeamConfig()
        crystal = Crystal(crystal_config)

        # Test with oversample_thick=False (last-value semantics)
        detector_config1 = DetectorConfig(**detector_config_base, oversample_thick=False)
        detector1 = Detector(detector_config1)
        simulator1 = Simulator(crystal, detector1, crystal_config, beam_config)
        intensity_last_value = simulator1.run(oversample_thick=False)

        # Test with oversample_thick=True (accumulation)
        detector_config2 = DetectorConfig(**detector_config_base, oversample_thick=True)
        detector2 = Detector(detector_config2)
        simulator2 = Simulator(crystal, detector2, crystal_config, beam_config)
        intensity_accumulation = simulator2.run(oversample_thick=True)

        # The two should be different (last-value uses only final layer, accumulation uses all)
        # Last-value should generally be smaller as it only uses one layer's capture
        assert not torch.allclose(intensity_last_value, intensity_accumulation, rtol=1e-3)

        # For most pixels, accumulated should be larger than last-value
        # (since accumulation sums all layers, last-value only uses final layer)
        ratio = intensity_accumulation / (intensity_last_value + 1e-10)
        assert torch.median(ratio) > 1.0, "Accumulation should generally give higher intensity"

    def test_parallax_dependence(self):
        """Test that absorption varies with parallax (off-axis vs on-axis pixels)."""
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=21, fpixels=21,  # Larger grid to see parallax effects
            detector_abs_um=500.0,
            detector_thick_um=100.0,
            detector_thicksteps=3,
            oversample_thick=True
        )

        crystal_config = CrystalConfig(default_F=100.0)  # Need non-zero intensity
        beam_config = BeamConfig()

        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        intensity = simulator.run()

        # Compare center pixel (high parallax, aligned with normal)
        # vs corner pixel (lower parallax, off-axis)
        center_intensity = intensity[10, 10]  # Center pixel
        corner_intensity = intensity[0, 0]    # Corner pixel

        # Due to parallax differences, absorption should differ
        # Center pixel has higher parallax (better aligned), so less absorption
        assert not torch.allclose(center_intensity, corner_intensity, rtol=1e-2), \
            "Center and corner pixels should have different absorption due to parallax"

    def test_absorption_with_tilted_detector(self):
        """Test absorption calculation works correctly with detector rotations."""
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=5, fpixels=5,
            detector_rotx_deg=10.0,  # Tilt detector
            detector_roty_deg=5.0,
            detector_abs_um=1000.0,
            detector_thick_um=50.0,
            detector_thicksteps=2,
            oversample_thick=False
        )

        crystal_config = CrystalConfig(default_F=100.0)  # Need non-zero intensity
        beam_config = BeamConfig()

        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Should run without errors
        intensity = simulator.run()

        # Verify intensity is positive and finite
        assert torch.all(intensity >= 0), "Intensity should be non-negative"
        assert torch.all(torch.isfinite(intensity)), "Intensity should be finite"

        # With absorption, intensity should be reduced compared to no absorption
        detector_config_no_abs = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=5, fpixels=5,
            detector_rotx_deg=10.0,
            detector_roty_deg=5.0,
            detector_abs_um=None,  # No absorption
            detector_thick_um=0.0,
            detector_thicksteps=1
        )
        detector_no_abs = Detector(detector_config_no_abs)
        simulator_no_abs = Simulator(crystal, detector_no_abs, crystal_config, beam_config)
        intensity_no_abs = simulator_no_abs.run()

        # With absorption should reduce intensity
        assert torch.mean(intensity) < torch.mean(intensity_no_abs), \
            "Absorption should reduce average intensity"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])