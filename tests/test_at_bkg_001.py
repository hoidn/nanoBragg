"""
Test for AT-BKG-001: Water background term.

From spec:
- AT-BKG-001 Water background term
  - Setup: -water set to a finite µm; otherwise zero contributions (e.g., default_F=0);
    compute one pixel.
  - Expectation: I_bg = (F_bg^2) · r_e^2 · fluence · (water_size^3) · 1e6 · Avogadro / water_MW
    with F_bg = 2.57, Avogadro = 6.02214179e23, water_MW = 18. This adds a constant to all pixels.
"""

import torch
import pytest
from src.nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.simulator import Simulator


class TestAT_BKG_001:
    """Test suite for AT-BKG-001: Water background term calculation."""

    def test_water_background_calculation(self):
        """Test that water background adds expected constant to all pixels."""
        # Create minimal configuration with water background
        crystal_config = CrystalConfig(
            phi_steps=1,
            mosaic_domains=1,
            N_cells=(1, 1, 1),
            default_F=0.0,  # Zero structure factor to isolate background
        )

        # Create detector with small grid for testing
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            fpixels=10,
            spixels=10,
        )

        # Configure beam with water background
        water_size_um = 10.0  # 10 micrometers
        beam_config = BeamConfig(
            wavelength_A=6.2,
            water_size_um=water_size_um,
        )

        # Create objects
        crystal = Crystal(crystal_config, device="cpu", dtype=torch.float64)
        detector = Detector(detector_config, device="cpu", dtype=torch.float64)

        # Create simulator
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=crystal_config,
            beam_config=beam_config,
            device="cpu",
            dtype=torch.float64,
        )

        # Run simulation
        image = simulator.run()

        # Calculate expected background value
        F_bg = 2.57
        Avogadro = 6.02214179e23  # mol^-1
        water_MW = 18.0  # g/mol
        r_e_sqr = 7.94079248018965e-30  # m^2
        fluence = simulator.fluence
        water_size_m = water_size_um * 1e-6

        expected_I_bg = (
            F_bg * F_bg
            * r_e_sqr
            * fluence
            * (water_size_m ** 3)
            * 1e6  # Unit inconsistency factor from spec
            * Avogadro
            / water_MW
        )

        # Check that all pixels have the expected background value
        # (Since default_F=0, the only contribution should be the background)
        assert torch.allclose(image, torch.full_like(image, expected_I_bg), rtol=1e-10)

    def test_water_background_zero(self):
        """Test that zero water size produces no background."""
        # Create minimal configuration without water background
        crystal_config = CrystalConfig(
            phi_steps=1,
            mosaic_domains=1,
            N_cells=(1, 1, 1),
            default_F=0.0,  # Zero structure factor
        )

        # Create detector
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            fpixels=10,
            spixels=10,
        )

        # Configure beam with NO water background
        beam_config = BeamConfig(
            wavelength_A=6.2,
            water_size_um=0.0,  # No water
        )

        # Create objects
        crystal = Crystal(crystal_config, device="cpu", dtype=torch.float64)
        detector = Detector(detector_config, device="cpu", dtype=torch.float64)

        # Create simulator
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=crystal_config,
            beam_config=beam_config,
            device="cpu",
            dtype=torch.float64,
        )

        # Run simulation
        image = simulator.run()

        # Check that all pixels are zero (no background, no diffraction)
        assert torch.allclose(image, torch.zeros_like(image), atol=1e-20)

    def test_water_background_additive(self):
        """Test that water background adds to existing diffraction pattern."""
        # Create configuration with both diffraction and background
        crystal_config = CrystalConfig(
            phi_steps=1,
            mosaic_domains=1,
            N_cells=(1, 1, 1),
            default_F=100.0,  # Non-zero structure factor
        )

        # Create detector
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            fpixels=10,
            spixels=10,
        )

        # Configure beam with water background
        water_size_um = 5.0
        beam_config_with_water = BeamConfig(
            wavelength_A=6.2,
            water_size_um=water_size_um,
        )

        beam_config_no_water = BeamConfig(
            wavelength_A=6.2,
            water_size_um=0.0,
        )

        # Create objects
        crystal = Crystal(crystal_config, device="cpu", dtype=torch.float64)
        detector = Detector(detector_config, device="cpu", dtype=torch.float64)

        # Create simulators with and without water
        simulator_with_water = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=crystal_config,
            beam_config=beam_config_with_water,
            device="cpu",
            dtype=torch.float64,
        )

        simulator_no_water = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=crystal_config,
            beam_config=beam_config_no_water,
            device="cpu",
            dtype=torch.float64,
        )

        # Run simulations
        image_with_water = simulator_with_water.run()
        image_no_water = simulator_no_water.run()

        # Calculate expected background
        F_bg = 2.57
        Avogadro = 6.02214179e23
        water_MW = 18.0
        r_e_sqr = 7.94079248018965e-30
        fluence = simulator_with_water.fluence
        water_size_m = water_size_um * 1e-6

        expected_I_bg = (
            F_bg * F_bg
            * r_e_sqr
            * fluence
            * (water_size_m ** 3)
            * 1e6
            * Avogadro
            / water_MW
        )

        # The difference should be the constant background value
        difference = image_with_water - image_no_water
        assert torch.allclose(
            difference,
            torch.full_like(difference, expected_I_bg),
            rtol=1e-10
        )

        # Also verify that with water image = no water image + background
        assert torch.allclose(
            image_with_water,
            image_no_water + expected_I_bg,
            rtol=1e-10
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])