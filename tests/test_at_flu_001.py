"""
Acceptance test for AT-FLU-001: Fluence calculation and sample clipping.

Per spec: Provide -flux, -exposure, -beamsize, and also -fluence; set beamsize smaller than sample_y/z.
Expectation: fluence SHALL be recomputed as flux·exposure/beamsize^2 whenever flux != 0 and exposure > 0
and beamsize ≥ 0; exposure > 0 SHALL recompute flux consistently; when beamsize > 0 and smaller than
sample_y or sample_z, those sample dimensions SHALL be clipped to beamsize and a warning printed.
"""

import pytest
import torch
from io import StringIO
import sys

from nanobrag_torch.config import BeamConfig, CrystalConfig
from nanobrag_torch.models.crystal import Crystal


class TestAT_FLU_001:
    """Test fluence calculation and sample clipping per AT-FLU-001."""

    def test_fluence_calculation_from_flux_exposure_beamsize(self):
        """Test fluence is recomputed from flux, exposure, and beamsize."""

        # Test case 1: fluence computed from flux, exposure, beamsize
        config = BeamConfig(
            flux=1e15,  # photons/s
            exposure=0.1,  # seconds
            beamsize_mm=0.5,  # mm
            fluence=1.0  # This should be overridden
        )

        # Expected: fluence = flux * exposure / (beamsize_m)^2
        # beamsize_m = 0.5 / 1000 = 0.0005 m
        # fluence = 1e15 * 0.1 / (0.0005)^2 = 1e14 / 0.00000025 = 4e20
        expected_fluence = 1e15 * 0.1 / (0.0005 * 0.0005)
        assert config.fluence == pytest.approx(expected_fluence)

    def test_no_fluence_calculation_when_flux_zero(self):
        """Test fluence is NOT recomputed when flux is 0."""

        initial_fluence = 1e24
        config = BeamConfig(
            flux=0.0,  # flux is 0
            exposure=1.0,
            beamsize_mm=1.0,
            fluence=initial_fluence
        )

        # Fluence should not be changed
        assert config.fluence == initial_fluence

    def test_no_fluence_calculation_when_exposure_zero(self):
        """Test fluence is NOT recomputed when exposure is 0."""

        initial_fluence = 1e24
        config = BeamConfig(
            flux=1e15,
            exposure=0.0,  # exposure is 0
            beamsize_mm=1.0,
            fluence=initial_fluence
        )

        # Fluence should not be changed
        assert config.fluence == initial_fluence

    def test_fluence_calculation_with_beamsize_zero(self):
        """Test fluence handling when beamsize is exactly 0 but flux and exposure are set."""

        initial_fluence = 1e24
        config = BeamConfig(
            flux=1e15,
            exposure=1.0,
            beamsize_mm=0.0,  # beamsize is 0
            fluence=initial_fluence
        )

        # When beamsize is 0 but flux and exposure are set, fluence should not be recalculated
        # (can't divide by 0)
        assert config.fluence == initial_fluence

    def test_flux_recomputation_from_fluence_and_exposure(self):
        """Test flux is recomputed when exposure > 0 and fluence/beamsize are set."""

        config = BeamConfig(
            flux=0.0,  # This should be recomputed
            exposure=0.5,  # > 0
            beamsize_mm=2.0,  # > 0
            fluence=1e20
        )

        # Expected: flux = fluence * beamsize^2 / exposure
        # beamsize_m = 2.0 / 1000 = 0.002 m
        # flux = 1e20 * (0.002)^2 / 0.5 = 1e20 * 0.000004 / 0.5 = 8e14
        beamsize_m = 0.002
        expected_flux = 1e20 * (beamsize_m * beamsize_m) / 0.5
        assert config.flux == pytest.approx(expected_flux)

    def test_sample_clipping_warning(self, capsys):
        """Test sample dimensions are clipped to beamsize when beamsize is smaller."""

        # Create crystal config with 10x10x10 cells of 100 Å each
        # This gives sample dimensions of 10 * 100 * 1e-10 = 1e-7 m = 0.0001 mm
        crystal_config = CrystalConfig(
            cell_a=100.0,  # Angstroms
            cell_b=100.0,
            cell_c=100.0,
            N_cells=(10, 10, 10)
        )

        # Beam config with small beamsize (smaller than sample)
        # Sample dimensions: 10 * 100 Å = 1000 Å = 1e-7 m = 0.0001 mm
        # Set beamsize smaller: 0.00005 mm = 5e-8 m
        beam_config = BeamConfig(
            beamsize_mm=0.00005  # 5e-8 m, smaller than sample
        )

        # Create crystal with beam config to trigger clipping
        crystal = Crystal(config=crystal_config, beam_config=beam_config)

        # Check that sample dimensions were clipped
        beamsize_m = 5e-8
        assert crystal.config.sample_y == pytest.approx(beamsize_m)
        assert crystal.config.sample_z == pytest.approx(beamsize_m)

        # Check warning was printed
        captured = capsys.readouterr()
        assert "Warning: Clipping sample_y" in captured.out
        assert "Warning: Clipping sample_z" in captured.out
        assert f"to beamsize {beamsize_m:.6e} m" in captured.out

    def test_no_clipping_when_beamsize_larger(self):
        """Test sample dimensions are NOT clipped when beamsize is larger."""

        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            N_cells=(10, 10, 10)
        )

        # Beam config with large beamsize (larger than sample)
        # Sample: 1e-7 m = 0.0001 mm
        # Beamsize: 1 mm = 0.001 m (much larger)
        beam_config = BeamConfig(
            beamsize_mm=1.0  # 0.001 m, larger than sample
        )

        crystal = Crystal(config=crystal_config, beam_config=beam_config)

        # Sample dimensions should not be changed
        expected_sample_y = 10 * 100 * 1e-10  # 1e-7 m
        expected_sample_z = 10 * 100 * 1e-10
        assert crystal.config.sample_y == expected_sample_y
        assert crystal.config.sample_z == expected_sample_z

    def test_no_clipping_when_beamsize_zero(self):
        """Test no clipping occurs when beamsize is 0."""

        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            N_cells=(5, 5, 5)
        )

        beam_config = BeamConfig(
            beamsize_mm=0.0  # No beamsize set
        )

        crystal = Crystal(config=crystal_config, beam_config=beam_config)

        # Sample dimensions should be unchanged
        expected_sample_y = 5 * 100 * 1e-10
        expected_sample_z = 5 * 100 * 1e-10
        assert crystal.config.sample_y == expected_sample_y
        assert crystal.config.sample_z == expected_sample_z


if __name__ == "__main__":
    pytest.main([__file__, "-v"])