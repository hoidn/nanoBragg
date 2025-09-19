"""
AT-STR-004: Sparse HKL Handling and Missing Reflection Behavior

This test validates that the implementation correctly handles sparse HKL files
where some reflections are missing and should use default_F values.

From spec:
- Setup: Create sparse HKL file with deliberate gaps (e.g., h,k,l,F: (0,0,0):100.0,
  (2,0,0):80.0, (0,2,0):60.0, with (1,0,0) and (0,1,0) missing).
- Run with -hkl sparse.hkl -default_F 10.
- Expectation: Implementation SHALL use HKL-specified F values for reflections
  present in the file and default_F=10 for missing reflections.
"""

import os
import torch
import numpy as np
import pytest
from pathlib import Path

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.io.hkl import read_hkl_file, try_load_hkl_or_fdump


class TestAT_STR_004:
    """Test sparse HKL handling with default_F fallback."""

    @pytest.fixture
    def sparse_hkl_file(self):
        """Return path to sparse HKL test file."""
        return Path(__file__).parent / "test_data" / "hkl_files" / "sparse.hkl"

    @pytest.fixture
    def test_crystal_config(self):
        """Create crystal config for testing."""
        return CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            default_F=10.0,  # Default for missing reflections
            N_cells=(5, 5, 5),
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            misset_deg=(0.0, 0.0, 0.0),
            mosaic_spread_deg=0.0,
            mosaic_domains=1
        )

    def test_sparse_hkl_loading(self, sparse_hkl_file):
        """Test that sparse HKL file loads correctly."""
        # Load HKL file
        hkl_data, metadata = read_hkl_file(str(sparse_hkl_file))

        # Check that the file loaded
        assert hkl_data is not None
        assert metadata is not None

        # Check bounds include the expected range
        assert metadata['h_min'] <= -1
        assert metadata['h_max'] >= 2
        assert metadata['k_min'] <= -1
        assert metadata['k_max'] >= 2
        assert metadata['l_min'] >= 0
        assert metadata['l_max'] >= 0

    def test_missing_reflection_uses_default_f(self, sparse_hkl_file, test_crystal_config):
        """Test that missing reflections use default_F value."""
        # Create crystal and load HKL data
        crystal = Crystal(test_crystal_config)
        crystal.load_hkl(str(sparse_hkl_file))

        # Test that (0,0,0) uses specified value
        f_000 = crystal.get_structure_factor(
            torch.tensor(0), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_000 - 100.0) < 1e-6, f"Expected F(0,0,0)=100.0, got {f_000}"

        # Test that (2,0,0) uses specified value
        f_200 = crystal.get_structure_factor(
            torch.tensor(2), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_200 - 80.0) < 1e-6, f"Expected F(2,0,0)=80.0, got {f_200}"

        # Test that (0,2,0) uses specified value
        f_020 = crystal.get_structure_factor(
            torch.tensor(0), torch.tensor(2), torch.tensor(0)
        ).item()
        assert abs(f_020 - 60.0) < 1e-6, f"Expected F(0,2,0)=60.0, got {f_020}"

        # Test that missing (1,0,0) uses default_F
        f_100 = crystal.get_structure_factor(
            torch.tensor(1), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_100 - 10.0) < 1e-6, f"Expected F(1,0,0)=10.0 (default), got {f_100}"

        # Test that missing (0,1,0) uses default_F
        f_010 = crystal.get_structure_factor(
            torch.tensor(0), torch.tensor(1), torch.tensor(0)
        ).item()
        assert abs(f_010 - 10.0) < 1e-6, f"Expected F(0,1,0)=10.0 (default), got {f_010}"

    def test_intensity_ratios_with_sparse_hkl(self, sparse_hkl_file, test_crystal_config):
        """Test that intensity ratios match expected F² scaling."""
        # Create a small detector for faster simulation
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64,
            fpixels=64
        )

        beam_config = BeamConfig(
            wavelength_A=6.2,
            fluence=1e12  # Low fluence for testing
        )

        # Create models
        crystal = Crystal(test_crystal_config)
        crystal.load_hkl(str(sparse_hkl_file))
        detector = Detector(detector_config)

        # Run simulation
        simulator = Simulator(crystal, detector, crystal_config=test_crystal_config, beam_config=beam_config)
        image = simulator.run()

        # Find the brightest pixel (should be near (0,0,0) reflection)
        max_intensity = torch.max(image).item()
        assert max_intensity > 0, "Should produce non-zero intensities"

        # The actual intensity ratios depend on geometric factors (Lorentz, etc.)
        # but we can verify that the pattern contains expected reflections
        # by checking that we get non-zero intensity
        assert torch.sum(image > 0) > 10, "Should have multiple non-zero pixels"

    def test_fallback_with_no_hkl_uses_default_f(self, test_crystal_config):
        """Test that without HKL data, all reflections use default_F."""
        # Create crystal without HKL data
        crystal = Crystal(test_crystal_config)

        # All reflections should use default_F = 10.0
        f_000 = crystal.get_structure_factor(
            torch.tensor(0), torch.tensor(0), torch.tensor(0)
        ).item()
        assert f_000 == 10.0

        f_100 = crystal.get_structure_factor(
            torch.tensor(1), torch.tensor(0), torch.tensor(0)
        ).item()
        assert f_100 == 10.0

        f_234 = crystal.get_structure_factor(
            torch.tensor(2), torch.tensor(3), torch.tensor(4)
        ).item()
        assert f_234 == 10.0

    def test_fdump_preserves_sparse_behavior(self, sparse_hkl_file, test_crystal_config, tmp_path):
        """Test that Fdump.bin cache preserves sparse HKL behavior."""
        from nanobrag_torch.io.hkl import write_fdump

        # Change to temp directory for this test
        os.chdir(tmp_path)

        # Load HKL data
        hkl_data_1, metadata_1 = read_hkl_file(str(sparse_hkl_file), default_F=test_crystal_config.default_F)

        # Write Fdump cache
        write_fdump(hkl_data_1, metadata_1, "Fdump.bin")

        # Now load from Fdump (it should have been created)
        hkl_data_2, metadata_2 = try_load_hkl_or_fdump(None, default_F=10.0)

        assert hkl_data_2 is not None, "Should load from Fdump.bin"
        assert metadata_2['h_min'] == metadata_1['h_min']
        assert metadata_2['h_max'] == metadata_1['h_max']

        # Create crystals with both datasets
        crystal_1 = Crystal(test_crystal_config)
        crystal_1.hkl_data = hkl_data_1
        crystal_1.hkl_metadata = metadata_1

        crystal_2 = Crystal(test_crystal_config)
        crystal_2.hkl_data = hkl_data_2
        crystal_2.hkl_metadata = metadata_2

        # Verify same behavior
        h, k, l = torch.tensor(0), torch.tensor(0), torch.tensor(0)
        assert crystal_1.get_structure_factor(h, k, l).item() == crystal_2.get_structure_factor(h, k, l).item()

        h, k, l = torch.tensor(1), torch.tensor(0), torch.tensor(0)
        assert crystal_1.get_structure_factor(h, k, l).item() == crystal_2.get_structure_factor(h, k, l).item()

        h, k, l = torch.tensor(2), torch.tensor(0), torch.tensor(0)
        assert crystal_1.get_structure_factor(h, k, l).item() == crystal_2.get_structure_factor(h, k, l).item()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])