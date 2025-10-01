"""Test AT-IO-002: PGM writer.

From spec-a.md:
- File SHALL be P5 with width, height, one comment line "# pixels scaled by <pgm_scale>",
  255, followed by width*height bytes with values = floor(min(255, float_pixel * pgm_scale)).
"""

import os
import tempfile
from pathlib import Path
import numpy as np
import torch

from nanobrag_torch.io import write_pgm


class TestAT_IO_002:
    """Test PGM file format writing per AT-IO-002."""

    def test_pgm_header_format(self):
        """Test that PGM header follows P5 format specification."""
        with tempfile.NamedTemporaryFile(suffix='.pgm', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Create test data
            image_data = np.random.rand(64, 48) * 100

            # Write PGM with specific scale
            pgm_scale = 2.5
            write_pgm(
                filepath=tmp_path,
                image_data=image_data,
                pgm_scale=pgm_scale,
            )

            # Read and verify header
            with open(tmp_path, "rb") as f:
                # Read header lines
                magic = f.readline().decode("ascii").strip()
                dims = f.readline().decode("ascii").strip()
                comment = f.readline().decode("ascii").strip()
                maxval = f.readline().decode("ascii").strip()

                # Check P5 magic number
                assert magic == "P5", f"Expected P5, got {magic}"

                # Check dimensions (width height)
                width_str, height_str = dims.split()
                assert int(width_str) == 48, f"Width {width_str} != 48"
                assert int(height_str) == 64, f"Height {height_str} != 64"

                # Check comment line
                expected_comment = f"# pixels scaled by {pgm_scale}"
                assert comment == expected_comment, f"Comment '{comment}' != '{expected_comment}'"

                # Check max value
                assert maxval == "255", f"Max value {maxval} != 255"

                # Check binary data size
                remaining = f.read()
                expected_size = 64 * 48  # height * width bytes
                assert len(remaining) == expected_size, f"Data size {len(remaining)} != {expected_size}"

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_pgm_pixel_scaling(self):
        """Test PGM pixel scaling formula: floor(min(255, float_pixel * pgm_scale))."""
        with tempfile.NamedTemporaryFile(suffix='.pgm', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Create test data with known values
            image_data = np.array([
                [10.0, 50.0, 100.0, 150.0],
                [200.0, 250.0, 300.0, 400.0],
            ], dtype=np.float32)

            pgm_scale = 1.5

            write_pgm(
                filepath=tmp_path,
                image_data=image_data,
                pgm_scale=pgm_scale,
            )

            # Read binary data
            with open(tmp_path, "rb") as f:
                # Skip header (4 lines)
                for _ in range(4):
                    f.readline()

                # Read pixel data
                pixel_bytes = f.read()
                pixels = np.frombuffer(pixel_bytes, dtype=np.uint8).reshape(2, 4)

                # Verify scaling formula
                for i in range(2):
                    for j in range(4):
                        expected = int(np.floor(min(255, image_data[i, j] * pgm_scale)))
                        actual = pixels[i, j]
                        assert actual == expected, (
                            f"Pixel [{i},{j}]: expected {expected}, got {actual}"
                        )

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_pgm_with_default_scale(self):
        """Test PGM writing with default scale=1.0."""
        with tempfile.NamedTemporaryFile(suffix='.pgm', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Create test data
            image_data = np.array([[100, 200], [50, 255]], dtype=np.float32)

            # Write without specifying scale (should default to 1.0)
            write_pgm(filepath=tmp_path, image_data=image_data)

            # Read and verify comment line shows scale=1.0
            with open(tmp_path, "rb") as f:
                f.readline()  # Skip P5
                f.readline()  # Skip dimensions
                comment = f.readline().decode("ascii").strip()

                assert comment == "# pixels scaled by 1.0"

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_pgm_torch_tensor_input(self):
        """Test that PGM writer accepts torch tensors."""
        with tempfile.NamedTemporaryFile(suffix='.pgm', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Create torch tensor
            image_tensor = torch.randn(32, 32) * 50 + 128

            write_pgm(
                filepath=tmp_path,
                image_data=image_tensor,
                pgm_scale=0.5,
            )

            # Verify file was created with correct structure
            assert os.path.exists(tmp_path)
            with open(tmp_path, "rb") as f:
                magic = f.readline().decode("ascii").strip()
                assert magic == "P5"

                dims = f.readline().decode("ascii").strip()
                assert dims == "32 32"

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_pgm_clipping_behavior(self):
        """Test that values are properly clipped to 255."""
        with tempfile.NamedTemporaryFile(suffix='.pgm', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Create data with values that will exceed 255 after scaling
            image_data = np.array([
                [100, 200],
                [300, 500]
            ], dtype=np.float32)

            pgm_scale = 2.0

            write_pgm(
                filepath=tmp_path,
                image_data=image_data,
                pgm_scale=pgm_scale,
            )

            # Read pixel data
            with open(tmp_path, "rb") as f:
                # Skip header
                for _ in range(4):
                    f.readline()

                pixels = np.frombuffer(f.read(), dtype=np.uint8).reshape(2, 2)

                # Check clipping
                assert pixels[0, 0] == 200  # 100 * 2.0 = 200 (no clipping)
                assert pixels[0, 1] == 255  # 200 * 2.0 = 400 -> clipped to 255
                assert pixels[1, 0] == 255  # 300 * 2.0 = 600 -> clipped to 255
                assert pixels[1, 1] == 255  # 500 * 2.0 = 1000 -> clipped to 255

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)