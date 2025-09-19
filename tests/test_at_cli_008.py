"""
Test AT-CLI-008: dmin filtering

Setup: Two runs on a small ROI: one without -dmin and one with a moderately strict
-dmin (Å) that removes high-angle contributions for that ROI.

Expectation: The -dmin run produces a strictly lower or equal total intensity sum
over the ROI compared to the run without -dmin; differences are localized toward
higher-angle pixels.
"""
import os
import tempfile
import subprocess
import numpy as np
import pytest
from pathlib import Path

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


class TestATCLI008DminFiltering:
    """Test cases for AT-CLI-008: dmin filtering"""

    def setup_method(self):
        """Create a temporary directory for test outputs"""
        self.test_dir = tempfile.mkdtemp(prefix='test_at_cli_008_')

        # Create a simple HKL file
        self.hkl_file = Path(self.test_dir) / "test.hkl"
        with open(self.hkl_file, 'w') as f:
            # Add structure factors at various resolutions
            # Low-resolution reflections
            f.write("0 0 1 100.0\n")
            f.write("0 1 0 100.0\n")
            f.write("1 0 0 100.0\n")
            # Medium-resolution reflections
            f.write("1 1 0 80.0\n")
            f.write("0 1 1 80.0\n")
            f.write("1 0 1 80.0\n")
            # High-resolution reflections
            f.write("2 0 0 50.0\n")
            f.write("0 2 0 50.0\n")
            f.write("0 0 2 50.0\n")
            f.write("1 1 1 60.0\n")
            f.write("2 1 0 40.0\n")
            f.write("1 2 0 40.0\n")
            f.write("0 2 1 40.0\n")

    def teardown_method(self):
        """Clean up temporary files"""
        import shutil
        if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_dmin_filtering_reduces_intensity(self):
        """Test that dmin filtering reduces total intensity by removing high-angle reflections"""
        # Common parameters for both runs
        common_args = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(self.hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.5',
            '-distance', '100',
            '-detsize', '50',
            '-detpixels', '256',
            '-default_F', '10',
            '-roi', '64', '192', '64', '192',  # Small ROI
            '-nopgm',
            '-N', '3'  # Small crystal for faster simulation
        ]

        # Run 1: Without dmin filtering
        output_no_dmin = Path(self.test_dir) / 'no_dmin.bin'
        args_no_dmin = common_args + ['-floatfile', str(output_no_dmin)]

        result = subprocess.run(args_no_dmin, capture_output=True, text=True)
        assert result.returncode == 0, f"Run without dmin failed: {result.stderr}"

        # Run 2: With dmin filtering at 60.0 Angstroms (to filter reflections with d < 60 Å)
        # This will filter out (1,1,1) at d≈57.7 Å, (2,0,0) at d=50 Å, and higher-order reflections
        output_with_dmin = Path(self.test_dir) / 'with_dmin.bin'
        args_with_dmin = common_args + ['-floatfile', str(output_with_dmin), '-dmin', '60.0']

        result = subprocess.run(args_with_dmin, capture_output=True, text=True)
        assert result.returncode == 0, f"Run with dmin failed: {result.stderr}"

        # Read the output files
        assert output_no_dmin.exists(), "Output without dmin not created"
        assert output_with_dmin.exists(), "Output with dmin not created"

        intensity_no_dmin = np.fromfile(output_no_dmin, dtype=np.float32).reshape(256, 256)
        intensity_with_dmin = np.fromfile(output_with_dmin, dtype=np.float32).reshape(256, 256)

        # Extract ROI (indices 64-192 in both axes)
        roi_no_dmin = intensity_no_dmin[64:193, 64:193]
        roi_with_dmin = intensity_with_dmin[64:193, 64:193]

        # Calculate total intensities
        total_no_dmin = np.sum(roi_no_dmin)
        total_with_dmin = np.sum(roi_with_dmin)

        # Verify expectations
        assert total_with_dmin <= total_no_dmin, \
            f"dmin filtering should reduce total intensity: {total_with_dmin} > {total_no_dmin}"

        assert total_with_dmin < total_no_dmin, \
            f"dmin filtering should actually reduce some intensity: {total_with_dmin} == {total_no_dmin}"

        # Verify that some pixels have reduced intensity
        diff = roi_no_dmin - roi_with_dmin
        pixels_reduced = np.sum(diff > 1e-10)
        assert pixels_reduced > 0, \
            f"At least some pixels should have reduced intensity after dmin filtering"

        # The reduction should be significant for affected pixels
        if pixels_reduced > 0:
            mean_reduction = np.mean(diff[diff > 1e-10])
            assert mean_reduction > 0, \
                f"Mean reduction for affected pixels should be positive: {mean_reduction}"

    def test_dmin_very_strict_removes_most_intensity(self):
        """Test that very strict dmin removes most reflections"""
        common_args = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(self.hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.5',
            '-distance', '100',
            '-detsize', '50',
            '-detpixels', '128',
            '-default_F', '10',
            '-nopgm',
            '-N', '2'
        ]

        # Run with very strict dmin (150 Angstroms - this will filter ALL reflections
        # since even (1,0,0) has d=100 Å)
        output_strict = Path(self.test_dir) / 'strict_dmin.bin'
        args_strict = common_args + ['-floatfile', str(output_strict), '-dmin', '150.0']

        result = subprocess.run(args_strict, capture_output=True, text=True)
        assert result.returncode == 0, f"Run with strict dmin failed: {result.stderr}"

        # Read the output
        intensity = np.fromfile(output_strict, dtype=np.float32).reshape(128, 128)

        # With dmin > 100 Å, all reflections should be filtered out
        # Only background from default_F might remain
        # The intensity should be very low compared to an unfiltered simulation
        total_intensity = np.sum(intensity)
        # Due to default_F=10, there might be some background, but it should be minimal
        assert total_intensity < 1000, \
            f"Very strict dmin should remove essentially all intensity: total={total_intensity}"

    def test_dmin_zero_has_no_effect(self):
        """Test that dmin=0 is equivalent to no dmin filtering"""
        common_args = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(self.hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.5',
            '-distance', '100',
            '-detsize', '30',
            '-detpixels', '64',
            '-default_F', '10',
            '-nopgm',
            '-N', '2'
        ]

        # Run without dmin flag
        output_no_flag = Path(self.test_dir) / 'no_flag.bin'
        args_no_flag = common_args + ['-floatfile', str(output_no_flag)]

        result = subprocess.run(args_no_flag, capture_output=True, text=True)
        assert result.returncode == 0

        # Run with dmin=0
        output_zero_dmin = Path(self.test_dir) / 'zero_dmin.bin'
        args_zero_dmin = common_args + ['-floatfile', str(output_zero_dmin), '-dmin', '0']

        result = subprocess.run(args_zero_dmin, capture_output=True, text=True)
        assert result.returncode == 0

        # Compare outputs
        intensity_no_flag = np.fromfile(output_no_flag, dtype=np.float32)
        intensity_zero_dmin = np.fromfile(output_zero_dmin, dtype=np.float32)

        # Should be identical
        np.testing.assert_array_almost_equal(intensity_no_flag, intensity_zero_dmin, decimal=6,
                                              err_msg="dmin=0 should be equivalent to no dmin filtering")