"""
AT-CLI-007: Noise determinism
Setup: Produce -noisefile twice with the same -seed and same inputs over a small ROI.
Expectation: Integer noise images are identical; overload counts match. Changing -seed changes the noise image.
"""

import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np
import pytest

from nanobrag_torch.io.smv import read_smv


class TestATCLI007NoiseDeterminism:
    """Test CLI noise determinism with seeds."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def test_hkl_file(self, temp_dir):
        """Create a minimal HKL file for testing."""
        hkl_path = temp_dir / "test.hkl"
        hkl_path.write_text(
            "0 0 0 100.0\n"
            "1 0 0 50.0\n"
            "0 1 0 50.0\n"
            "0 0 1 50.0\n"
        )
        return hkl_path

    def run_cli_with_seed(self, hkl_file, output_file, seed, roi=None):
        """Run the CLI with specified parameters."""
        cmd = [
            sys.executable, "-m", "nanobrag_torch",
            "-hkl", str(hkl_file),
            "-cell", "100", "100", "100", "90", "90", "90",
            "-detpixels", "32",  # Small detector
            "-pixel", "0.1",
            "-distance", "100",
            "-lambda", "1.0",
            "-default_F", "100",  # Ensure we have some structure factor
            "-fluence", "1e25",  # Higher fluence for non-zero counts
            "-seed", str(seed),
            "-noisefile", str(output_file)
        ]

        # Add ROI if specified
        if roi:
            cmd.extend(["-roi"] + [str(x) for x in roi])

        # Run the command
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            print(f"Command failed: {' '.join(cmd)}")
            print(f"stdout:\n{result.stdout}")
            print(f"stderr:\n{result.stderr}")
            raise RuntimeError(f"CLI failed with return code {result.returncode}")

        return result

    def test_identical_seed_produces_identical_noise(self, temp_dir, test_hkl_file):
        """Test that same seed produces identical noise images."""
        noise1_path = temp_dir / "noise1.img"
        noise2_path = temp_dir / "noise2.img"

        # Use a small ROI for speed
        roi = [10, 20, 10, 20]  # xmin, xmax, ymin, ymax

        # Run twice with same seed
        seed = 42
        result1 = self.run_cli_with_seed(test_hkl_file, noise1_path, seed, roi)
        result2 = self.run_cli_with_seed(test_hkl_file, noise2_path, seed, roi)

        # Read the noise images
        data1, header1 = read_smv(noise1_path)
        data2, header2 = read_smv(noise2_path)

        # Images should be identical
        np.testing.assert_array_equal(data1, data2,
                                       "Noise images with same seed should be identical")

        # Extract overload counts from output
        def extract_overloads(output):
            for line in output.stdout.split('\n'):
                if 'overloads' in line:
                    # Parse: "Wrote noise image to ... (N overloads)"
                    import re
                    match = re.search(r'\((\d+) overloads\)', line)
                    if match:
                        return int(match.group(1))
            return 0

        overloads1 = extract_overloads(result1)
        overloads2 = extract_overloads(result2)

        assert overloads1 == overloads2, \
            f"Overload counts should match: {overloads1} != {overloads2}"

    def test_different_seed_produces_different_noise(self, temp_dir, test_hkl_file):
        """Test that different seeds produce different noise images."""
        noise1_path = temp_dir / "noise1.img"
        noise2_path = temp_dir / "noise2.img"

        # Use a small ROI for speed
        roi = [10, 20, 10, 20]

        # Run with different seeds
        self.run_cli_with_seed(test_hkl_file, noise1_path, seed=42, roi=roi)
        self.run_cli_with_seed(test_hkl_file, noise2_path, seed=123, roi=roi)

        # Read the noise images
        data1, header1 = read_smv(noise1_path)
        data2, header2 = read_smv(noise2_path)

        # Images should be different (with very high probability)
        # Check that at least some pixels differ
        differences = np.sum(data1 != data2)
        total_pixels = data1.size

        assert differences > 0, "Noise images with different seeds should differ"

        # For a reasonable test, expect at least 10% of pixels to differ
        # (Poisson noise with different seeds should easily achieve this)
        diff_fraction = differences / total_pixels
        assert diff_fraction > 0.1, \
            f"Expected >10% pixels to differ, got {diff_fraction*100:.1f}%"

    def test_seed_determinism_without_roi(self, temp_dir, test_hkl_file):
        """Test seed determinism on full detector (no ROI)."""
        noise1_path = temp_dir / "noise1.img"
        noise2_path = temp_dir / "noise2.img"

        # Run twice with same seed, no ROI
        seed = 999
        self.run_cli_with_seed(test_hkl_file, noise1_path, seed, roi=None)
        self.run_cli_with_seed(test_hkl_file, noise2_path, seed, roi=None)

        # Read and compare
        data1, _ = read_smv(noise1_path)
        data2, _ = read_smv(noise2_path)

        np.testing.assert_array_equal(data1, data2,
                                       "Full detector noise should be identical with same seed")

    def test_negative_seed_accepted(self, temp_dir, test_hkl_file):
        """Test that negative seeds work (spec default is negative time)."""
        noise_path = temp_dir / "noise.img"

        # Negative seed should work
        result = self.run_cli_with_seed(test_hkl_file, noise_path, seed=-12345)

        # Should succeed
        assert noise_path.exists(), "Noise file should be created with negative seed"

        # Verify it's reproducible
        noise2_path = temp_dir / "noise2.img"
        self.run_cli_with_seed(test_hkl_file, noise2_path, seed=-12345)

        data1, _ = read_smv(noise_path)
        data2, _ = read_smv(noise2_path)

        np.testing.assert_array_equal(data1, data2,
                                       "Negative seeds should also be deterministic")

    def test_overload_count_determinism(self, temp_dir, test_hkl_file):
        """Test that overload counts are deterministic with seed."""
        noise_path = temp_dir / "noise.img"

        # Use high fluence to ensure some overloads
        cmd = [
            sys.executable, "-m", "nanobrag_torch",
            "-hkl", str(test_hkl_file),
            "-cell", "100", "100", "100", "90", "90", "90",
            "-detpixels", "16",  # Very small
            "-pixel", "0.1",
            "-distance", "50",  # Closer for higher intensity
            "-lambda", "1.0",
            "-fluence", "1e25",  # Very high fluence for overloads
            "-seed", "777",
            "-roi", "5", "10", "5", "10",  # Small ROI
            "-noisefile", str(noise_path)
        ]

        # Run multiple times
        overload_counts = []
        for i in range(3):
            if i > 0:
                noise_path.unlink()  # Remove previous file

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Extract overload count
            for line in result.stdout.split('\n'):
                if 'overloads' in line:
                    import re
                    match = re.search(r'\((\d+) overloads\)', line)
                    if match:
                        overload_counts.append(int(match.group(1)))
                        break

        # All runs should have same overload count
        assert len(overload_counts) == 3, "Should extract overload count from all runs"
        assert len(set(overload_counts)) == 1, \
            f"Overload counts should be identical: {overload_counts}"