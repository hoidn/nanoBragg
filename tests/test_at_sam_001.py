"""
Acceptance Test AT-SAM-001: Steps normalization

Per spec:
- AT-SAM-001 Steps normalization
  - Setup: sources=1; mosaic_domains=1; oversample=1; phisteps=2 with identical
    physics across steps (e.g., zero mosaic and symmetric phi so F_cell and F_latt
    identical); disable thickness/polar/omega oversample toggles.
  - Expectation: Final per-pixel scale SHALL divide by steps=2 so intensity matches
    the single-step case (within numeric tolerance).
"""

import torch
import numpy as np
import pytest
from src.nanobrag_torch.config import CrystalConfig, DetectorConfig
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.simulator import Simulator


def test_at_sam_001_steps_normalization():
    """Test that intensity is properly normalized by the number of steps."""

    # Setup: Create crystal and detector
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=10,
        fpixels=10,
        beam_center_s=5.0,
        beam_center_f=5.0
    )
    detector = Detector(detector_config)

    # Create a simple cubic crystal with known structure factors
    crystal_config_base = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )
    crystal = Crystal(config=crystal_config_base)

    # Test with phi_steps=1 (single step)
    config_1step = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
        phi_steps=1,
        phi_start_deg=0.0,
        osc_range_deg=0.0,  # No oscillation
        misset_deg=(0.0, 0.0, 0.0),
        mosaic_domains=1,
        mosaic_spread_deg=0.0  # No mosaic spread
    )

    simulator_1step = Simulator(
        crystal=crystal,
        detector=detector,
        crystal_config=config_1step
    )

    # Run simulation with single step
    intensity_1step = simulator_1step.run()

    # Test with phi_steps=2 (two steps) with symmetric phi
    # With zero oscillation and zero mosaic, both steps should give identical physics
    config_2step = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
        phi_steps=2,
        phi_start_deg=0.0,
        osc_range_deg=0.0,  # No oscillation (both steps at same angle)
        misset_deg=(0.0, 0.0, 0.0),
        mosaic_domains=1,
        mosaic_spread_deg=0.0  # No mosaic spread
    )

    simulator_2step = Simulator(
        crystal=crystal,
        detector=detector,
        crystal_config=config_2step
    )

    # Run simulation with two steps
    intensity_2step = simulator_2step.run()

    # With proper normalization, intensity_2step should equal intensity_1step
    # because both steps contribute identical physics and should be divided by steps=2

    # Check that intensities are approximately equal
    assert torch.allclose(intensity_1step, intensity_2step, rtol=1e-6), \
        f"Intensity with 2 steps should match 1 step after normalization. " \
        f"Max relative difference: {(torch.abs(intensity_2step - intensity_1step) / intensity_1step.max()).max().item()}"

    # Also test with phi_steps=4
    config_4step = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
        phi_steps=4,
        phi_start_deg=0.0,
        osc_range_deg=0.0,  # No oscillation
        misset_deg=(0.0, 0.0, 0.0),
        mosaic_domains=1,
        mosaic_spread_deg=0.0
    )

    simulator_4step = Simulator(
        crystal=crystal,
        detector=detector,
        crystal_config=config_4step
    )

    intensity_4step = simulator_4step.run()

    # Should also match the single-step case
    assert torch.allclose(intensity_1step, intensity_4step, rtol=1e-6), \
        f"Intensity with 4 steps should match 1 step after normalization. " \
        f"Max relative difference: {(torch.abs(intensity_4step - intensity_1step) / intensity_1step.max()).max().item()}"

    # Verify that without normalization, 2 steps would give double the intensity
    # This is a sanity check to ensure our test is meaningful
    # We'll manually check this by temporarily disabling normalization

    # For now, we expect the test to fail until normalization is implemented
    # Once implemented, the assertions above should pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])