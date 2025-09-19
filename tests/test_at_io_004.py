"""
AT-IO-004: HKL Format Validation Suite

This test validates that the implementation correctly parses different HKL
file formats and produces identical results regardless of extra columns.

From spec:
- Setup: Provide test HKL files in different valid formats: minimal.hkl (h,k,l,F four columns),
  with_phase.hkl (h,k,l,F,phase five columns), with_sigma.hkl (h,k,l,F,sigma,phase six columns),
  negative_indices.hkl (including negative Miller indices).
- Expectation: All format variants SHALL produce identical diffraction patterns when
  phase/sigma columns are ignored. Implementation SHALL correctly parse all columns
  present but use only h,k,l,F for intensity calculations.
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
from nanobrag_torch.io.hkl import read_hkl_file, write_fdump, try_load_hkl_or_fdump


class TestAT_IO_004:
    """Test HKL format validation and parsing compatibility."""

    @pytest.fixture
    def hkl_files_dir(self):
        """Return path to HKL test files directory."""
        return Path(__file__).parent / "test_data" / "hkl_files"

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
            default_F=0.0,  # No default - all values from file
            N_cells=(5, 5, 5),
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            misset_deg=(0.0, 0.0, 0.0),
            mosaic_spread_deg=0.0,
            mosaic_domains=1
        )

    def test_minimal_hkl_format(self, hkl_files_dir, test_crystal_config):
        """Test reading minimal 4-column HKL format."""
        hkl_file = hkl_files_dir / "minimal.hkl"

        # Load HKL data
        hkl_data, metadata = read_hkl_file(str(hkl_file))

        # Check that file loaded
        assert hkl_data is not None
        assert metadata is not None

        # Create crystal and check specific reflections
        crystal = Crystal(test_crystal_config)
        crystal.hkl_data = hkl_data
        crystal.hkl_metadata = metadata

        # Test specific values from the file
        f_000 = crystal.get_structure_factor(
            torch.tensor(0), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_000 - 100.0) < 1e-6

        f_100 = crystal.get_structure_factor(
            torch.tensor(1), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_100 - 50.0) < 1e-6

    def test_five_column_with_phase(self, hkl_files_dir, test_crystal_config):
        """Test reading 5-column HKL format with phase (phase should be ignored)."""
        hkl_file = hkl_files_dir / "with_phase.hkl"

        # Load HKL data
        hkl_data, metadata = read_hkl_file(str(hkl_file))

        # Create crystal and check that values match minimal format
        crystal = Crystal(test_crystal_config)
        crystal.hkl_data = hkl_data
        crystal.hkl_metadata = metadata

        # Should still get same F values, ignoring phase
        f_000 = crystal.get_structure_factor(
            torch.tensor(0), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_000 - 100.0) < 1e-6

        f_100 = crystal.get_structure_factor(
            torch.tensor(1), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_100 - 50.0) < 1e-6

    def test_six_column_with_sigma_and_phase(self, hkl_files_dir, test_crystal_config):
        """Test reading 6-column HKL format with sigma and phase (both should be ignored)."""
        hkl_file = hkl_files_dir / "with_sigma.hkl"

        # Load HKL data
        hkl_data, metadata = read_hkl_file(str(hkl_file))

        # Create crystal and check that values match minimal format
        crystal = Crystal(test_crystal_config)
        crystal.hkl_data = hkl_data
        crystal.hkl_metadata = metadata

        # Should still get same F values, ignoring sigma and phase
        f_000 = crystal.get_structure_factor(
            torch.tensor(0), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_000 - 100.0) < 1e-6

        f_100 = crystal.get_structure_factor(
            torch.tensor(1), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_100 - 50.0) < 1e-6

    def test_negative_indices_handling(self, hkl_files_dir, test_crystal_config):
        """Test that negative Miller indices are handled correctly."""
        hkl_file = hkl_files_dir / "negative_indices.hkl"

        # Load HKL data
        hkl_data, metadata = read_hkl_file(str(hkl_file))

        # Check that bounds include negative indices
        assert metadata['h_min'] < 0
        assert metadata['k_min'] < 0

        # Create crystal
        crystal = Crystal(test_crystal_config)
        crystal.hkl_data = hkl_data
        crystal.hkl_metadata = metadata

        # Test positive and negative indices have appropriate values
        f_100 = crystal.get_structure_factor(
            torch.tensor(1), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_100 - 50.0) < 1e-6

        f_m100 = crystal.get_structure_factor(
            torch.tensor(-1), torch.tensor(0), torch.tensor(0)
        ).item()
        assert abs(f_m100 - 50.0) < 1e-6  # Should be same as (1,0,0) per Friedel's law

    def test_all_formats_produce_same_pattern(self, hkl_files_dir, test_crystal_config):
        """Test that all format variants produce identical diffraction patterns."""
        # Create small detector for testing
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=32,
            fpixels=32
        )

        beam_config = BeamConfig(
            wavelength_A=6.2,
            fluence=1e12
        )

        # Load all formats
        formats = ["minimal.hkl", "with_phase.hkl", "with_sigma.hkl"]
        images = []

        for hkl_filename in formats:
            hkl_file = hkl_files_dir / hkl_filename

            # Create crystal with this HKL file
            crystal = Crystal(test_crystal_config)
            crystal.load_hkl(str(hkl_file))

            # Create detector and simulator
            detector = Detector(detector_config)
            simulator = Simulator(crystal, detector, crystal_config=test_crystal_config, beam_config=beam_config)

            # Run simulation
            image = simulator.run()
            images.append(image)

        # All images should be identical (within numerical precision)
        for i in range(1, len(images)):
            diff = torch.abs(images[0] - images[i])
            max_diff = torch.max(diff).item()
            assert max_diff < 1e-10, f"Format {formats[i]} produces different pattern than {formats[0]}"

    def test_fdump_caching_for_all_formats(self, hkl_files_dir, test_crystal_config, tmp_path):
        """Test that Fdump caching works correctly for all formats."""
        formats = ["minimal.hkl", "with_phase.hkl", "with_sigma.hkl", "negative_indices.hkl"]

        for hkl_filename in formats:
            # Create a new temp directory for each format
            format_dir = tmp_path / hkl_filename.replace(".hkl", "")
            format_dir.mkdir()
            os.chdir(format_dir)

            hkl_file = hkl_files_dir / hkl_filename

            # Load HKL and create Fdump
            hkl_data_1, metadata_1 = read_hkl_file(str(hkl_file))
            write_fdump(hkl_data_1, metadata_1, "Fdump.bin")

            # Load from Fdump
            hkl_data_2, metadata_2 = try_load_hkl_or_fdump(None, default_F=0.0)

            assert hkl_data_2 is not None, f"Failed to load Fdump for {hkl_filename}"

            # Check that metadata matches
            assert metadata_2['h_min'] == metadata_1['h_min']
            assert metadata_2['h_max'] == metadata_1['h_max']
            assert metadata_2['k_min'] == metadata_1['k_min']
            assert metadata_2['k_max'] == metadata_1['k_max']
            assert metadata_2['l_min'] == metadata_1['l_min']
            assert metadata_2['l_max'] == metadata_1['l_max']

            # Check that data shapes match
            assert hkl_data_2.shape == hkl_data_1.shape

    def test_comment_and_blank_line_handling(self, tmp_path):
        """Test that comments and blank lines are correctly ignored."""
        # Create a test HKL file with comments and blank lines
        test_hkl = tmp_path / "test_comments.hkl"
        test_hkl.write_text("""# This is a comment
# Another comment
0 0 0 100.0

1 0 0 50.0
# Comment in the middle
0 1 0 60.0

# Final comment
""")

        # Load the file
        hkl_data, metadata = read_hkl_file(str(test_hkl))

        # Check that only data lines were processed
        assert metadata['h_min'] == 0
        assert metadata['h_max'] == 1
        assert metadata['k_min'] == 0
        assert metadata['k_max'] == 1
        assert metadata['l_min'] == 0
        assert metadata['l_max'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])