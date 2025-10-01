"""
Acceptance test AT-CLI-006: Output scaling and PGM

Tests requirements:
- Without -scale, autoscale maps max float pixel to approximately 55,000 counts (within rounding)
- With -scale set, integer pixel = floor(min(65535, float*scale + adc))
- PGM is P5 with header, comment line "# pixels scaled by <pgm_scale>", 255,
  then fast-major bytes equal to min(255, floor(float*pgm_scale))
"""

import subprocess
import tempfile
from pathlib import Path
import numpy as np
import struct
import sys


def run_cli(*args):
    """Run the CLI with given arguments."""
    cmd = [sys.executable, "-m", "nanobrag_torch"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    return result


def read_smv_data(filepath):
    """Read SMV file and return the image data and header."""
    with open(filepath, "rb") as f:
        # Read header (512 bytes)
        header_bytes = f.read(512)
        header = header_bytes.decode("ascii", errors="ignore")

        # Read image data
        # Find dimensions from header
        lines = header.split("\n")
        size1 = None
        size2 = None
        byte_order = None
        for line in lines:
            if line.startswith("SIZE1="):
                size1 = int(line.split("=")[1].strip().rstrip(";"))
            elif line.startswith("SIZE2="):
                size2 = int(line.split("=")[1].strip().rstrip(";"))
            elif line.startswith("BYTE_ORDER="):
                byte_order = line.split("=")[1].strip().rstrip(";")

        # Read image data
        f.seek(512)  # Skip header
        pixel_count = size1 * size2

        # Read as unsigned short (2 bytes per pixel)
        data = np.fromfile(f, dtype=np.uint16, count=pixel_count)
        data = data.reshape((size2, size1))  # Note: SIZE2 is slow, SIZE1 is fast

        return data, header


def read_float_image(filepath, shape):
    """Read binary float image."""
    data = np.fromfile(filepath, dtype=np.float32)
    return data.reshape(shape)


def read_pgm(filepath):
    """Read PGM file and return image data and scale from comment."""
    with open(filepath, "rb") as f:
        # Read header
        magic = f.readline().decode().strip()
        assert magic == "P5", f"Expected P5 magic, got {magic}"

        # Read dimensions
        dims_line = f.readline().decode().strip()
        width, height = map(int, dims_line.split())

        # Read comment line with scale
        comment_line = f.readline().decode().strip()
        assert comment_line.startswith("#"), f"Expected comment line, got {comment_line}"
        # Extract scale from "# pixels scaled by <scale>"
        scale_str = comment_line.split("scaled by")[1].strip()
        scale = float(scale_str)

        # Read max value
        max_val_line = f.readline().decode().strip()
        assert max_val_line == "255", f"Expected max value 255, got {max_val_line}"

        # Read binary data
        data = np.fromfile(f, dtype=np.uint8, count=width*height)
        data = data.reshape((height, width))

        return data, scale


def test_autoscale_without_scale_flag():
    """Test that without -scale, autoscale maps max float to ~55,000 counts."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        floatfile = tmpdir / "test.bin"
        intfile = tmpdir / "test.img"

        # Run simulation without -scale
        result = run_cli(
            "-cell", "50", "50", "50", "90", "90", "90",
            "-default_F", "100",
            "-lambda", "1.0",
            "-N", "1",
            "-distance", "50",
            "-detpixels", "10",
            "-floatfile", str(floatfile),
            "-intfile", str(intfile),
            "-adc", "40"  # Standard ADC offset
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Read float and int images
        float_data = read_float_image(floatfile, (10, 10))
        int_data, _ = read_smv_data(intfile)

        # Find max values
        max_float = float_data.max()
        max_int = int_data.max()

        # Autoscale should map max float to approximately 55,000
        # Allow for rounding errors
        assert 54900 <= max_int <= 55100, f"Max int value {max_int} not near 55,000"

        # Verify the scaling relationship
        # With ADC=40, scale should be (55000 - 40) / max_float
        expected_scale = (55000 - 40) / max_float if max_float > 0 else 1.0

        # Check a few pixels
        for i in range(min(5, float_data.size)):
            flat_idx = i
            float_val = float_data.flat[flat_idx]
            int_val = int_data.flat[flat_idx]

            if float_val > 1e-10:  # Non-zero pixel
                expected_int = min(65535, int(float_val * expected_scale + 40))
                assert abs(int_val - expected_int) <= 1, f"Pixel {i}: expected {expected_int}, got {int_val}"


def test_explicit_scale_flag():
    """Test that with -scale set, integer pixel = floor(min(65535, float*scale + adc))."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        floatfile = tmpdir / "test.bin"
        intfile = tmpdir / "test.img"

        scale_value = 1000.0
        adc_value = 50.0

        # Run simulation with explicit -scale
        result = run_cli(
            "-cell", "50", "50", "50", "90", "90", "90",
            "-default_F", "100",
            "-lambda", "1.0",
            "-N", "1",
            "-distance", "50",
            "-detpixels", "10",
            "-floatfile", str(floatfile),
            "-intfile", str(intfile),
            "-scale", str(scale_value),
            "-adc", str(adc_value)
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Read float and int images
        float_data = read_float_image(floatfile, (10, 10))
        int_data, _ = read_smv_data(intfile)

        # Verify scaling formula: integer pixel = floor(min(65535, float*scale + adc))
        for i in range(10):
            for j in range(10):
                float_val = float_data[i, j]
                int_val = int_data[i, j]

                if float_val > 1e-10:  # Non-zero pixel
                    expected = min(65535, int(float_val * scale_value + adc_value))
                    assert int_val == expected, f"Pixel ({i},{j}): expected {expected}, got {int_val}"
                else:
                    # Zero pixels should remain zero (ROI behavior)
                    assert int_val == 0, f"Zero pixel ({i},{j}) has non-zero int value {int_val}"


def test_pgm_without_pgmscale():
    """Test PGM output without -pgmscale (default scale=1.0)."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        floatfile = tmpdir / "test.bin"
        pgmfile = tmpdir / "test.pgm"

        # Run simulation without -pgmscale
        result = run_cli(
            "-cell", "50", "50", "50", "90", "90", "90",
            "-default_F", "100",
            "-lambda", "1.0",
            "-N", "1",
            "-distance", "50",
            "-detpixels", "10",
            "-floatfile", str(floatfile),
            "-pgmfile", str(pgmfile)
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Read float and PGM images
        float_data = read_float_image(floatfile, (10, 10))
        pgm_data, scale = read_pgm(pgmfile)

        # Without -pgmscale, default should be 1.0
        assert scale == 1.0, f"Expected default pgmscale=1.0, got {scale}"

        # Verify PGM formula: min(255, floor(float*pgmscale))
        for i in range(10):
            for j in range(10):
                float_val = float_data[i, j]
                pgm_val = pgm_data[i, j]

                expected = min(255, int(float_val * scale))
                assert pgm_val == expected, f"Pixel ({i},{j}): expected {expected}, got {pgm_val}"


def test_pgm_with_explicit_pgmscale():
    """Test PGM output with explicit -pgmscale."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        floatfile = tmpdir / "test.bin"
        pgmfile = tmpdir / "test.pgm"

        pgmscale_value = 10000.0

        # Run simulation with -pgmscale
        result = run_cli(
            "-cell", "50", "50", "50", "90", "90", "90",
            "-default_F", "100",
            "-lambda", "1.0",
            "-N", "1",
            "-distance", "50",
            "-detpixels", "10",
            "-floatfile", str(floatfile),
            "-pgmfile", str(pgmfile),
            "-pgmscale", str(pgmscale_value)
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Read float and PGM images
        float_data = read_float_image(floatfile, (10, 10))
        pgm_data, scale = read_pgm(pgmfile)

        # Check scale in comment
        assert scale == pgmscale_value, f"Expected pgmscale={pgmscale_value}, got {scale}"

        # Verify PGM formula: min(255, floor(float*pgmscale))
        for i in range(10):
            for j in range(10):
                float_val = float_data[i, j]
                pgm_val = pgm_data[i, j]

                expected = min(255, int(float_val * pgmscale_value))
                assert pgm_val == expected, f"Pixel ({i},{j}): expected {expected}, got {pgm_val}"


def test_pgm_format_compliance():
    """Test that PGM file format is compliant with P5 specification."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        pgmfile = tmpdir / "test.pgm"

        pgmscale_value = 100.0

        # Run simulation with PGM output
        result = run_cli(
            "-cell", "50", "50", "50", "90", "90", "90",
            "-default_F", "100",
            "-lambda", "1.0",
            "-N", "1",
            "-distance", "50",
            "-detpixels", "10",
            "-pgmfile", str(pgmfile),
            "-pgmscale", str(pgmscale_value)
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Read and verify PGM format
        with open(pgmfile, "rb") as f:
            # Line 1: Magic number
            line1 = f.readline().decode().strip()
            assert line1 == "P5", f"Expected P5 magic, got {line1}"

            # Line 2: Width Height
            line2 = f.readline().decode().strip()
            width, height = map(int, line2.split())
            assert width == 10 and height == 10, f"Expected 10x10, got {width}x{height}"

            # Line 3: Comment with scale
            line3 = f.readline().decode().strip()
            expected_comment = f"# pixels scaled by {pgmscale_value}"
            assert line3 == expected_comment, f"Expected '{expected_comment}', got '{line3}'"

            # Line 4: Max value
            line4 = f.readline().decode().strip()
            assert line4 == "255", f"Expected max value 255, got {line4}"

            # Rest is binary data
            data = f.read()
            assert len(data) == width * height, f"Expected {width*height} bytes, got {len(data)}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])