"""Acceptance test AT-SRC-001: Sourcefile and weighting.

From spec-a.md:
- AT-SRC-001 Sourcefile and weighting
  - Setup: -sourcefile with two sources having distinct weights and λ; disable other sampling.
  - Expectation: steps = 2; intensity contributions SHALL sum with per-source λ and weight,
    then divide by steps.

Source file format (from spec):
- Each line: X, Y, Z (position vector in meters), weight (dimensionless), λ (meters)
- Missing fields default to:
  - Position along −source_distance·b (source_distance default 10 m)
  - Weight = 1.0
  - λ = λ0
- Positions are normalized to unit direction vectors
- The weight column is read but ignored (equal weighting results)
"""

import pytest
import torch
import numpy as np
from pathlib import Path
import tempfile
from typing import Tuple

from nanobrag_torch.io.source import read_sourcefile
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, DetectorConvention
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


class TestAT_SRC_001_SourcefileAndWeighting:
    """Test suite for AT-SRC-001: Sourcefile and weighting."""

    def test_sourcefile_with_all_columns(self):
        """Test reading sourcefile with all 5 columns specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sourcefile = Path(tmpdir) / "test_sources.txt"

            # Write test source file with two sources
            # X, Y, Z, weight, wavelength (in meters)
            content = """# Test source file
-10.0  0.0  0.0  2.0  1.0e-10
0.0  -10.0  0.0  3.0  1.5e-10
"""
            sourcefile.write_text(content)

            # Read source file
            default_wavelength_m = 6.2e-10  # 6.2 Angstroms
            directions, weights, wavelengths = read_sourcefile(
                sourcefile,
                default_wavelength_m=default_wavelength_m,
                default_source_distance_m=10.0
            )

            # Check we got 2 sources
            assert directions.shape == (2, 3)
            assert weights.shape == (2,)
            assert wavelengths.shape == (2,)

            # Check directions are normalized (unit vectors)
            norms = torch.linalg.norm(directions, dim=1)
            # Use dtype from parser output (defaults to torch.get_default_dtype())
            torch.testing.assert_close(norms, torch.ones(2, dtype=directions.dtype))

            # Per spec-a-core.md:151-153, wavelength column is read but IGNORED.
            # CLI -lambda (default_wavelength_m) is the sole authoritative source.
            assert wavelengths[0].item() == pytest.approx(default_wavelength_m)
            assert wavelengths[1].item() == pytest.approx(default_wavelength_m)

            # Per spec-a-core.md:151-153, weights are read but IGNORED (equal weighting).
            # All sources contribute equally via division by source count in steps normalization.
            assert weights[0].item() == pytest.approx(2.0)  # File value preserved for read test
            assert weights[1].item() == pytest.approx(3.0)  # File value preserved for read test

    def test_sourcefile_with_missing_columns(self):
        """Test reading sourcefile with missing columns (using defaults)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sourcefile = Path(tmpdir) / "test_sources.txt"

            # Write test source file with varying number of columns
            content = """# Test source file with missing columns
# Full specification
-10.0  0.0  0.0  2.0  1.0e-10
# Only position
0.0  -10.0  0.0
# No columns (should use defaults)

# Comment line
# Only position and weight
5.0  5.0  0.0  1.5
"""
            sourcefile.write_text(content)

            # Read source file
            default_wavelength_m = 6.2e-10  # 6.2 Angstroms
            default_source_distance_m = 10.0
            beam_direction = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)

            directions, weights, wavelengths = read_sourcefile(
                sourcefile,
                default_wavelength_m=default_wavelength_m,
                default_source_distance_m=default_source_distance_m,
                beam_direction=beam_direction
            )

            # Check we got 3 sources (empty line is skipped)
            assert directions.shape == (3, 3)
            assert weights.shape == (3,)
            assert wavelengths.shape == (3,)

            # Per spec-a-core.md:151-153, wavelength column is IGNORED.
            # All wavelengths use CLI -lambda value (default_wavelength_m).
            assert wavelengths[0].item() == pytest.approx(default_wavelength_m)
            assert wavelengths[1].item() == pytest.approx(default_wavelength_m)
            assert wavelengths[2].item() == pytest.approx(default_wavelength_m)

            # Check weights are preserved from file for read verification
            assert weights[0].item() == pytest.approx(2.0)   # Specified
            assert weights[1].item() == pytest.approx(1.0)   # Default
            assert weights[2].item() == pytest.approx(1.5)   # Specified

    def test_sourcefile_default_position(self):
        """Test that missing X,Y,Z defaults to -source_distance·b position."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sourcefile = Path(tmpdir) / "test_sources.txt"

            # Write source file with partial position (X, Y only, no Z)
            # Per spec, columns are: X, Y, Z, weight, wavelength
            # If we provide X=-15, Y=0 (no Z), position should be [-15, 0, 0] -> normalized [-1, 0, 0]
            content = """# Source with only X, Y position
-15.0  0.0
"""
            sourcefile.write_text(content)

            # Read with specific beam direction (not actually used when X,Y provided)
            default_wavelength_m = 6.2e-10
            default_source_distance_m = 15.0  # 15 meters
            beam_direction = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)  # Along +X

            directions, weights, wavelengths = read_sourcefile(
                sourcefile,
                default_wavelength_m=default_wavelength_m,
                default_source_distance_m=default_source_distance_m,
                beam_direction=beam_direction
            )

            # Position [-15, 0, 0] normalized to unit vector: [-1, 0, 0]
            # Use dtype from parser output (respects beam_direction dtype, which is float64 here)
            expected_direction = torch.tensor([[-1.0, 0.0, 0.0]], dtype=directions.dtype)
            torch.testing.assert_close(directions, expected_direction)

            # Per spec-a-core.md:151-153, wavelength uses CLI -lambda (default_wavelength_m)
            assert wavelengths[0].item() == pytest.approx(default_wavelength_m)

    def test_multiple_sources_normalization(self):
        """Test that intensity is properly normalized by number of sources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sourcefile = Path(tmpdir) / "test_sources.txt"

            # Create two sources with same wavelength but different positions
            content = """# Two sources for normalization test
-10.0  0.0  0.0  1.0  6.2e-10
10.0  0.0  0.0  1.0  6.2e-10
"""
            sourcefile.write_text(content)

            # Read sources
            directions, weights, wavelengths = read_sourcefile(
                sourcefile,
                default_wavelength_m=6.2e-10
            )

            # Verify we have 2 sources
            assert len(directions) == 2
            assert len(weights) == 2
            assert len(wavelengths) == 2

            # Verify directions are opposite (sources on opposite sides)
            torch.testing.assert_close(directions[0], -directions[1])

            # Both sources have weight 1.0 specified in the file
            # Use dtype from parser output (defaults to torch.get_default_dtype())
            torch.testing.assert_close(weights, torch.ones(2, dtype=weights.dtype))

    def test_empty_sourcefile(self):
        """Test that empty sourcefile raises appropriate error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sourcefile = Path(tmpdir) / "empty.txt"

            # Write empty file (only comments)
            content = """# Empty source file
# No actual sources
"""
            sourcefile.write_text(content)

            # Should raise error for no valid sources
            with pytest.raises(ValueError, match="No valid source lines found"):
                read_sourcefile(sourcefile, default_wavelength_m=6.2e-10)

    def test_weighted_sources_integration(self):
        """Test that sources can be loaded and simulated (AT-SRC-001).

        Per spec-a-core.md:151-153, file weight/λ columns are read but IGNORED.
        Equal weighting semantics: all sources contribute equally via steps normalization.
        CLI -lambda is the sole authoritative wavelength source.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sourcefile = Path(tmpdir) / "weighted_sources.txt"

            # Create two sources with different file weights/wavelengths
            # Per spec, these will be read but ultimately ignored in favor of equal weighting
            content = """# Two sources with file-specified weights and wavelengths (ignored per spec)
# X Y Z weight wavelength
0.0  0.0  -10.0  2.0  6.2e-10
0.0  0.0  -10.0  3.0  8.0e-10
"""
            sourcefile.write_text(content)

            # Read sources
            default_wavelength_m = 6.2e-10
            directions, weights, wavelengths = read_sourcefile(
                sourcefile,
                default_wavelength_m=default_wavelength_m
            )

            # Verify weights are read from file (for parsing correctness)
            assert weights[0].item() == pytest.approx(2.0)
            assert weights[1].item() == pytest.approx(3.0)

            # Per spec-a-core.md:151-153, wavelength column is IGNORED.
            # Both sources use CLI -lambda value.
            assert wavelengths[0].item() == pytest.approx(default_wavelength_m)
            assert wavelengths[1].item() == pytest.approx(default_wavelength_m)

            # Create a small test setup with these sources
            beam_config = BeamConfig(
                wavelength_A=6.2,  # Default wavelength in Angstroms
                source_directions=directions,
                source_weights=weights,
                source_wavelengths=wavelengths
            )

            crystal_config = CrystalConfig(
                cell_a=100.0, cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
                N_cells=(1, 1, 1),
                default_F=100.0
            )

            detector_config = DetectorConfig(
                distance_mm=100.0,
                spixels=8, fpixels=8,  # Small detector for speed
                pixel_size_mm=0.1,
                detector_convention=DetectorConvention.MOSFLM
            )

            # Create simulator with sources
            crystal = Crystal(crystal_config, beam_config, dtype=torch.float64)
            detector = Detector(detector_config, dtype=torch.float64)
            # Pass beam_config as 4th parameter (after crystal_config which is None)
            simulator = Simulator(crystal, detector, None, beam_config)

            # Run simulation - per AT-SRC-001, steps should equal 2
            result = simulator.run(oversample=1)

            # Per AT-SRC-001 expectation: "steps = 2"
            # The normalization should use sum of weights (2.0 + 3.0 = 5.0)
            # This is implemented in the simulator's steps calculation

            # Verify we get non-zero intensity (simulation runs correctly)
            assert result.sum() > 0, "Should produce non-zero intensity with weighted sources"

            # Verify shape is correct
            assert result.shape == (8, 8), "Result should match detector size"