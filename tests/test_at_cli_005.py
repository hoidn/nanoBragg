"""
Test AT-CLI-005: ROI bounding

From spec-a.md lines 810-812:
"- AT-CLI-005 ROI bounding
 - Setup: Render with -roi xmin xmax ymin ymax strictly inside the detector.
 - Expectation: Only pixels within the ROI rectangle have non-zero values in the float/int/noise outputs; pixels outside remain zero."
"""

import os
import sys
import subprocess
import tempfile
import numpy as np
from pathlib import Path

# Set environment variable for MKL
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def read_float_image(filepath):
    """Read binary float image."""
    with open(filepath, 'rb') as f:
        data = np.frombuffer(f.read(), dtype=np.float32)
    return data


def read_smv_image(filepath, width, height):
    """Read SMV format image data."""
    with open(filepath, 'rb') as f:
        # Skip header (512 bytes)
        f.seek(512)
        # Read data
        data = np.frombuffer(f.read(width*height*2), dtype=np.uint16)
    return data.reshape(height, width)


def test_cli_roi_basic():
    """Test basic ROI functionality - pixels outside ROI are zero."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a simple HKL file
        hkl_file = tmpdir / 'test.hkl'
        with open(hkl_file, 'w') as f:
            f.write("   0   0   1  100.0\n")
            f.write("   0   1   0  100.0\n")
            f.write("   1   0   0  100.0\n")

        float_out = tmpdir / 'test.bin'
        int_out = tmpdir / 'test.img'

        # Run with ROI 10-20 x 10-20 on a 32x32 detector
        cmd = [
            sys.executable, '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-N', '5',
            '-detpixels', '32',
            '-pixel', '0.1',
            '-distance', '100',
            '-floatfile', str(float_out),
            '-intfile', str(int_out),
            '-roi', '10', '20', '10', '20',  # ROI from pixel 10-20 in both dimensions
            '-default_F', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Check that output files exist
        assert float_out.exists()
        assert int_out.exists()

        # Read float image
        float_data = read_float_image(float_out).reshape(32, 32)

        # Check pixels outside ROI are zero
        # Before ROI (rows 0-9)
        assert np.all(float_data[0:10, :] == 0), "Pixels before ROI should be zero"
        # After ROI (rows 21-31)
        assert np.all(float_data[21:32, :] == 0), "Pixels after ROI should be zero"
        # Before ROI (cols 0-9)
        assert np.all(float_data[:, 0:10] == 0), "Pixels before ROI should be zero"
        # After ROI (cols 21-31)
        assert np.all(float_data[:, 21:32] == 0), "Pixels after ROI should be zero"

        # Check that some pixels inside ROI are non-zero
        roi_data = float_data[10:21, 10:21]
        assert np.any(roi_data > 0), "At least some pixels in ROI should be non-zero"

        # Read SMV image and perform same checks
        int_data = read_smv_image(int_out, 32, 32)

        # Check pixels outside ROI are zero
        assert np.all(int_data[0:10, :] == 0), "INT: Pixels before ROI should be zero"
        assert np.all(int_data[21:32, :] == 0), "INT: Pixels after ROI should be zero"
        assert np.all(int_data[:, 0:10] == 0), "INT: Pixels before ROI should be zero"
        assert np.all(int_data[:, 21:32] == 0), "INT: Pixels after ROI should be zero"


def test_cli_roi_with_noise():
    """Test ROI with noise output - noise should also respect ROI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a simple HKL file
        hkl_file = tmpdir / 'test.hkl'
        with open(hkl_file, 'w') as f:
            f.write("   0   0   1  100.0\n")

        noise_out = tmpdir / 'noise.img'

        # Run with ROI and noise output
        cmd = [
            sys.executable, '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-N', '5',
            '-detpixels', '32',
            '-pixel', '0.1',
            '-distance', '100',
            '-noisefile', str(noise_out),
            '-roi', '8', '23', '8', '23',  # ROI 16x16 in center
            '-default_F', '100',
            '-seed', '42'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Check that output file exists
        assert noise_out.exists()

        # Read noise image
        noise_data = read_smv_image(noise_out, 32, 32)

        # Check pixels outside ROI are zero
        assert np.all(noise_data[0:8, :] == 0), "Noise: Pixels before ROI should be zero"
        assert np.all(noise_data[24:32, :] == 0), "Noise: Pixels after ROI should be zero"
        assert np.all(noise_data[:, 0:8] == 0), "Noise: Pixels before ROI should be zero"
        assert np.all(noise_data[:, 24:32] == 0), "Noise: Pixels after ROI should be zero"

        # Check that some pixels inside ROI are non-zero (with noise)
        roi_data = noise_data[8:24, 8:24]
        assert np.any(roi_data > 0), "At least some pixels in ROI should be non-zero"


def test_cli_roi_edge_cases():
    """Test ROI edge cases - single pixel, full detector."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a simple HKL file
        hkl_file = tmpdir / 'test.hkl'
        with open(hkl_file, 'w') as f:
            f.write("   0   0   1  100.0\n")

        # Test 1: Single pixel ROI
        float_out = tmpdir / 'single.bin'
        cmd = [
            sys.executable, '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-N', '5',
            '-detpixels', '32',
            '-pixel', '0.1',
            '-distance', '100',
            '-floatfile', str(float_out),
            '-roi', '15', '15', '15', '15',  # Single pixel at (15,15)
            '-default_F', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        float_data = read_float_image(float_out).reshape(32, 32)

        # Count non-zero pixels
        non_zero_count = np.count_nonzero(float_data)
        assert non_zero_count <= 1, f"Only single pixel should be non-zero, got {non_zero_count}"

        # Test 2: Full detector ROI (should be same as no ROI)
        float_out2 = tmpdir / 'full.bin'
        cmd = [
            sys.executable, '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-N', '5',
            '-detpixels', '32',
            '-pixel', '0.1',
            '-distance', '100',
            '-floatfile', str(float_out2),
            '-roi', '0', '31', '0', '31',  # Full detector
            '-default_F', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        float_data2 = read_float_image(float_out2).reshape(32, 32)

        # Should have many non-zero pixels
        non_zero_count2 = np.count_nonzero(float_data2)
        assert non_zero_count2 > 100, f"Full ROI should have many non-zero pixels, got {non_zero_count2}"


def test_cli_roi_different_conventions():
    """Test ROI works with different detector conventions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a simple HKL file
        hkl_file = tmpdir / 'test.hkl'
        with open(hkl_file, 'w') as f:
            f.write("   0   0   1  100.0\n")

        for convention in ['-mosflm', '-xds']:
            float_out = tmpdir / f'{convention[1:]}.bin'
            cmd = [
                sys.executable, '-m', 'nanobrag_torch',
                '-hkl', str(hkl_file),
                '-cell', '100', '100', '100', '90', '90', '90',
                '-lambda', '1.0',
                '-N', '5',
                '-detpixels', '32',
                '-pixel', '0.1',
                '-distance', '100',
                '-floatfile', str(float_out),
                '-roi', '5', '26', '5', '26',
                '-default_F', '100',
                convention
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            assert result.returncode == 0, f"Command failed with {convention}: {result.stderr}"

            float_data = read_float_image(float_out).reshape(32, 32)

            # Check ROI boundaries respected
            assert np.all(float_data[0:5, :] == 0), f"{convention}: Before ROI should be zero"
            assert np.all(float_data[27:32, :] == 0), f"{convention}: After ROI should be zero"
            assert np.all(float_data[:, 0:5] == 0), f"{convention}: Before ROI should be zero"
            assert np.all(float_data[:, 27:32] == 0), f"{convention}: After ROI should be zero"

            # Check some pixels in ROI are non-zero
            roi_data = float_data[5:27, 5:27]
            assert np.any(roi_data > 0), f"{convention}: ROI should have non-zero pixels"


if __name__ == "__main__":
    test_cli_roi_basic()
    test_cli_roi_with_noise()
    test_cli_roi_edge_cases()
    test_cli_roi_different_conventions()
    print("All AT-CLI-005 tests passed!")