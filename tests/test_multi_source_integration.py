"""Integration test for multi-source support in simulator.

This test verifies that when multiple sources are provided through divergence/dispersion
or source files, the simulator actually uses them and the intensity is properly normalized.
"""

import torch
import numpy as np
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, DetectorConvention, CrystalShape
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def test_multi_source_intensity_normalization():
    """Test that intensity is properly normalized with multiple sources."""

    # Create minimal configuration
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
        mosaic_domains=1,
        shape=CrystalShape.SQUARE
    )

    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=64,
        fpixels=64,
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s=3.2,  # mm
        beam_center_f=3.2   # mm
    )

    # Test 1: Single source (reference)
    beam_config_single = BeamConfig(
        wavelength_A=6.2,
        fluence=1e12
    )

    crystal_single = Crystal(crystal_config, beam_config=beam_config_single)
    detector_single = Detector(detector_config)

    # Debug: check crystal config
    print(f"Crystal config type: {type(crystal_single.config)}")
    print(f"Crystal config has phi_steps: {hasattr(crystal_single.config, 'phi_steps')}")
    if hasattr(crystal_single.config, 'phi_steps'):
        print(f"Crystal config phi_steps: {crystal_single.config.phi_steps}")

    # Pass beam_config as keyword argument, not positional
    simulator_single = Simulator(crystal_single, detector_single, beam_config=beam_config_single)

    # Run simulation with single source
    image_single = simulator_single.run(oversample=1)
    intensity_single = torch.sum(image_single).item()
    max_single = torch.max(image_single).item()

    print(f"Single source - Total intensity: {intensity_single:.2e}, Max: {max_single:.2e}")

    # Test 2: Multiple sources (2 sources with same wavelength and direction)
    # Create two identical sources to test normalization
    n_sources = 2
    source_directions = torch.tensor([
        [-1.0, 0.0, 0.0],  # Source 1: along -X (MOSFLM beam direction)
        [-1.0, 0.0, 0.0]   # Source 2: identical to source 1
    ], dtype=torch.float64)

    # Normalize directions
    source_directions = source_directions / torch.norm(source_directions, dim=1, keepdim=True)

    source_wavelengths = torch.tensor([6.2e-10, 6.2e-10], dtype=torch.float64)  # meters
    source_weights = torch.ones(n_sources, dtype=torch.float64)  # Equal weights per spec

    beam_config_multi = BeamConfig(
        wavelength_A=6.2,
        fluence=1e12,
        source_directions=source_directions,
        source_wavelengths=source_wavelengths,
        source_weights=source_weights
    )

    crystal_multi = Crystal(crystal_config, beam_config=beam_config_multi)
    detector_multi = Detector(detector_config)
    # Pass beam_config as keyword argument, not positional
    simulator_multi = Simulator(crystal_multi, detector_multi, beam_config=beam_config_multi)

    # Run simulation with multiple sources
    image_multi = simulator_multi.run(oversample=1)
    intensity_multi = torch.sum(image_multi).item()
    max_multi = torch.max(image_multi).item()

    print(f"Multi source - Total intensity: {intensity_multi:.2e}, Max: {max_multi:.2e}")

    # Test 3: Verify normalization
    # With 2 nearly-identical sources, intensity should be similar but not exactly double
    # (due to the slightly different incident angles affecting the scattering)
    # The normalization by steps should prevent doubling of intensity

    # Check that total intensity is within reasonable bounds
    # It should NOT be double the single-source case due to normalization by n_sources
    intensity_ratio = intensity_multi / intensity_single
    print(f"Intensity ratio (multi/single): {intensity_ratio:.3f}")

    # The ratio should be exactly 1.0 (not 2.0) due to normalization
    # Since sources are identical, patterns should be identical
    assert 0.99 < intensity_ratio < 1.01, f"Intensity ratio {intensity_ratio} out of expected range [0.99, 1.01]"

    # Max intensity should also be comparable
    max_ratio = max_multi / max_single
    print(f"Max intensity ratio (multi/single): {max_ratio:.3f}")
    assert 0.99 < max_ratio < 1.01, f"Max ratio {max_ratio} out of expected range [0.99, 1.01]"

    # Test 4: Verify different directions affect the pattern
    # Create two sources with more significant angular separation
    angle_mrad = 5.0  # 5 milliradians divergence
    source_directions_diff = torch.tensor([
        [-1.0, 0.0, 0.0],     # Source 1: along -X (standard)
        [-torch.cos(torch.tensor(angle_mrad/1000)), torch.sin(torch.tensor(angle_mrad/1000)), 0.0]  # Source 2: 5 mrad off
    ], dtype=torch.float64)
    source_directions_diff = source_directions_diff / torch.norm(source_directions_diff, dim=1, keepdim=True)

    source_wavelengths_same = torch.tensor([6.2e-10, 6.2e-10], dtype=torch.float64)  # Same wavelengths

    beam_config_diff = BeamConfig(
        wavelength_A=6.2,  # Central wavelength
        fluence=1e12,
        source_directions=source_directions_diff,
        source_wavelengths=source_wavelengths_same,
        source_weights=source_weights
    )

    crystal_diff = Crystal(crystal_config, beam_config=beam_config_diff)
    detector_diff = Detector(detector_config)
    # Pass beam_config as keyword argument, not positional
    simulator_diff = Simulator(crystal_diff, detector_diff, beam_config=beam_config_diff)

    # Run simulation with different wavelengths
    image_diff = simulator_diff.run(oversample=1)

    # The pattern should be different from the same-wavelength case
    # Calculate correlation between patterns
    corr = torch.corrcoef(torch.stack([image_multi.flatten(), image_diff.flatten()]))[0, 1].item()
    print(f"Correlation between same-wavelength and different-wavelength patterns: {corr:.3f}")

    # Patterns should be somewhat different due to direction variation
    # With 5 mrad divergence, expect some decorrelation but still high similarity
    assert corr < 0.999, f"Patterns too similar (correlation={corr:.3f}), direction variation not working"
    assert corr > 0.90, f"Patterns too different (correlation={corr:.3f}), unexpected behavior"

    print("\n✓ All multi-source integration tests passed!")


if __name__ == "__main__":
    test_multi_source_intensity_normalization()