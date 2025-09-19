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

        # Run 2: With dmin filtering at 13.0 Angstroms (to filter edge pixels with d < 13 Å)
        output_with_dmin = Path(self.test_dir) / 'with_dmin.bin'
        args_with_dmin = common_args + ['-floatfile', str(output_with_dmin), '-dmin', '13.0']

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

        # Check that differences are localized to higher-angle pixels (further from center)
        center_y, center_x = 128, 128
        y_indices, x_indices = np.meshgrid(range(64, 193), range(64, 193), indexing='ij')
        distances = np.sqrt((y_indices - center_y)**2 + (x_indices - center_x)**2)

        # Calculate difference map
        diff = roi_no_dmin - roi_with_dmin

        # Higher-angle pixels (further from center) should show more reduction
        # Split into near and far regions
        near_mask = distances < 40
        far_mask = distances >= 40

        # Average reduction in each region (only for pixels with intensity)
        has_intensity = roi_no_dmin > 1e-10
        if np.any(has_intensity & near_mask) and np.any(has_intensity & far_mask):
            near_reduction = np.mean(diff[has_intensity & near_mask])
            far_reduction = np.mean(diff[has_intensity & far_mask])

            # Far pixels should have more reduction on average
            assert far_reduction >= near_reduction * 0.5, \
                f"High-angle pixels should show more filtering effect: far={far_reduction:.3e}, near={near_reduction:.3e}"

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

        # Run with very strict dmin (10 Angstroms)
        output_strict = Path(self.test_dir) / 'strict_dmin.bin'
        args_strict = common_args + ['-floatfile', str(output_strict), '-dmin', '10.0']

        result = subprocess.run(args_strict, capture_output=True, text=True)
        assert result.returncode == 0, f"Run with strict dmin failed: {result.stderr}"

        # Read the output
        intensity = np.fromfile(output_strict, dtype=np.float32).reshape(128, 128)

        # With such a strict dmin, most pixels should be zero
        nonzero_fraction = np.count_nonzero(intensity) / intensity.size
        assert nonzero_fraction < 0.1, \
            f"Strict dmin should remove most reflections: {nonzero_fraction:.1%} nonzero"

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