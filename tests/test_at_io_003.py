"""Test AT-IO-003: Fdump caching.

From spec-a.md:
- Provide -hkl; verify Fdump.bin is written
- Re-run without -hkl
- Expectation: Implementation SHALL read HKLs from Fdump.bin
- Header and data layout SHALL match spec
- Behavior when -default_F prefills missing points SHALL be preserved
"""

import os
import tempfile
from pathlib import Path
import numpy as np
import torch

from nanobrag_torch.io import read_hkl_file, write_fdump, read_fdump, try_load_hkl_or_fdump


class TestAT_IO_003:
    """Test Fdump binary cache functionality per AT-IO-003."""

    def test_fdump_write_and_read(self):
        """Test that Fdump.bin is written and can be read back correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            hkl_path = tmpdir / "test.hkl"
            fdump_path = tmpdir / "Fdump.bin"

            # Create test HKL file
            hkl_content = """
            0 0 0 100.0
            1 0 0 150.0
            0 1 0 200.0
            0 0 1 250.0
            -1 0 0 50.0
            """
            hkl_path.write_text(hkl_content)

            # Read HKL file
            F_grid_original, metadata_original = read_hkl_file(
                str(hkl_path),
                default_F=10.0
            )

            # Write Fdump cache
            write_fdump(F_grid_original, metadata_original, str(fdump_path))

            # Verify Fdump.bin was created
            assert fdump_path.exists(), "Fdump.bin not created"

            # Read back from Fdump
            F_grid_loaded, metadata_loaded = read_fdump(str(fdump_path))

            # Verify metadata matches
            assert metadata_loaded == metadata_original

            # Verify data matches
            assert torch.allclose(F_grid_loaded, F_grid_original, rtol=1e-9)

    def test_fdump_cache_behavior(self):
        """Test the caching behavior matching C code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            hkl_path = tmpdir / "test.hkl"
            fdump_path = tmpdir / "Fdump.bin"

            # Create test HKL file
            hkl_content = """
            0 0 0 100.0
            1 0 0 150.0
            """
            hkl_path.write_text(hkl_content)

            # First call with HKL path - should write cache
            F_grid1, metadata1 = try_load_hkl_or_fdump(
                hkl_path=str(hkl_path),
                fdump_path=str(fdump_path),
                default_F=5.0,
                write_cache=True
            )

            assert F_grid1 is not None
            assert fdump_path.exists(), "Cache not written"

            # Delete HKL file
            hkl_path.unlink()

            # Second call without HKL path - should read from cache
            F_grid2, metadata2 = try_load_hkl_or_fdump(
                hkl_path=None,
                fdump_path=str(fdump_path),
                default_F=5.0
            )

            assert F_grid2 is not None
            assert torch.allclose(F_grid2, F_grid1, rtol=1e-9)
            assert metadata2 == metadata1

    def test_fdump_no_files_with_default_F(self):
        """Test behavior when no files exist but default_F > 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            fdump_path = tmpdir / "Fdump.bin"

            # Call with no HKL and no existing Fdump, but default_F > 0
            F_grid, metadata = try_load_hkl_or_fdump(
                hkl_path=None,
                fdump_path=str(fdump_path),
                default_F=100.0
            )

            # Per spec, this should return None (program would proceed with default_F only)
            assert F_grid is None
            assert metadata is None

    def test_fdump_no_files_zero_default(self):
        """Test behavior when no files exist and default_F = 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            fdump_path = tmpdir / "Fdump.bin"

            # Call with no HKL and no existing Fdump, and default_F = 0
            F_grid, metadata = try_load_hkl_or_fdump(
                hkl_path=None,
                fdump_path=str(fdump_path),
                default_F=0.0
            )

            # Per spec, this should return None (program should exit)
            assert F_grid is None
            assert metadata is None

    def test_fdump_preserves_default_F(self):
        """Test that Fdump preserves the default_F behavior for missing points."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            hkl_path = tmpdir / "test.hkl"
            fdump_path = tmpdir / "Fdump.bin"

            # Create sparse HKL file
            hkl_content = """
            0 0 0 100.0
            2 2 2 200.0
            """
            hkl_path.write_text(hkl_content)

            # Read with specific default_F
            default_F = 25.0
            F_grid_original, metadata_original = read_hkl_file(
                str(hkl_path),
                default_F=default_F
            )

            # Verify some points have default_F
            assert F_grid_original[0, 0, 0] == 100.0  # Specified point
            assert F_grid_original[2, 2, 2] == 200.0  # Specified point
            assert F_grid_original[1, 1, 1] == default_F  # Unspecified point

            # Write and read back
            write_fdump(F_grid_original, metadata_original, str(fdump_path))
            F_grid_loaded, metadata_loaded = read_fdump(str(fdump_path))

            # Verify default_F values are preserved
            assert F_grid_loaded[1, 1, 1] == default_F
            assert torch.allclose(F_grid_loaded, F_grid_original, rtol=1e-9)

    def test_fdump_header_structure(self):
        """Test that Fdump binary format matches expected structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            fdump_path = tmpdir / "Fdump.bin"

            # Create simple test data
            F_grid = torch.ones((3, 4, 5), dtype=torch.float32) * 42.0
            metadata = {
                'h_min': -1, 'h_max': 1,
                'k_min': -2, 'k_max': 1,
                'l_min': 0, 'l_max': 4,
                'h_range': 3, 'k_range': 4, 'l_range': 5
            }

            write_fdump(F_grid, metadata, str(fdump_path))

            # Read raw binary and check structure
            with open(fdump_path, "rb") as f:
                # Header is ASCII text: "h_min h_max k_min k_max l_min l_max\n\f"
                header_line = f.readline()  # Read until newline
                f.read(1)  # Read form feed character

                # Parse ASCII header
                header_text = header_line.decode('ascii').strip()
                header_values = list(map(int, header_text.split()))

                assert header_values[0] == metadata['h_min']
                assert header_values[1] == metadata['h_max']
                assert header_values[2] == metadata['k_min']
                assert header_values[3] == metadata['k_max']
                assert header_values[4] == metadata['l_min']
                assert header_values[5] == metadata['l_max']

                # Data: should be h_range * k_range * l_range float64 values
                data_size = 3 * 4 * 5 * 8  # dimensions * sizeof(float64)
                data_bytes = f.read(data_size)
                assert len(data_bytes) == data_size

                # Verify a few values
                data = np.frombuffer(data_bytes, dtype=np.float64).reshape(3, 4, 5)
                assert np.allclose(data, 42.0, rtol=1e-6)