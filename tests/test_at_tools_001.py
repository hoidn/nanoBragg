"""
test_at_tools_001.py

Acceptance tests for AT-TOOLS-001: Dual-Runner Comparison Script

Tests the nb-compare utility that runs C and PyTorch implementations
side-by-side and computes comparison metrics.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

from scripts.nb_compare import (
    compute_metrics,
    find_c_binary,
    find_peaks,
    find_py_binary,
    load_float_image,
    resample_image,
)

# Set environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


class TestAT_TOOLS_001_DualRunnerComparison:
    """Test the dual-runner comparison utility per AT-TOOLS-001."""

    def test_find_c_binary_resolution(self):
        """Test C binary resolution order."""
        # Test with explicit path
        with tempfile.NamedTemporaryFile(suffix='_nanoBragg', delete=False) as f:
            f.write(b"dummy")
            temp_path = f.name

        try:
            result = find_c_binary(temp_path)
            assert result == Path(temp_path).resolve()
        finally:
            Path(temp_path).unlink()

        # Test with environment variable
        os.environ['NB_C_BIN'] = temp_path
        with tempfile.NamedTemporaryFile(suffix='_nanoBragg', delete=False) as f:
            f.write(b"dummy")
            temp_path = f.name

        try:
            os.environ['NB_C_BIN'] = temp_path
            result = find_c_binary()
            assert result == Path(temp_path).resolve()
        finally:
            del os.environ['NB_C_BIN']
            Path(temp_path).unlink()

        # Test error case
        with pytest.raises(FileNotFoundError):
            find_c_binary("nonexistent_binary")

    def test_find_py_binary_resolution(self):
        """Test PyTorch binary resolution order."""
        # Test with explicit path
        result = find_py_binary("custom_script.py")
        assert result == ['python', 'custom_script.py']

        result = find_py_binary("custom_binary")
        assert result == ['custom_binary']

        # Test with environment variable
        os.environ['NB_PY_BIN'] = 'env_script.py'
        result = find_py_binary()
        assert result == ['python', 'env_script.py']
        del os.environ['NB_PY_BIN']

        # Test default fallback
        result = find_py_binary()
        assert result in [['nanoBragg'], ['python', '-m', 'nanobrag_torch']]

    def test_load_float_image(self):
        """Test float image loading."""
        # Create test image
        test_data = np.random.rand(256, 256).astype(np.float32)

        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            test_data.tofile(f.name)
            temp_path = f.name

        try:
            loaded = load_float_image(temp_path)
            assert loaded.shape == (256, 256)
            np.testing.assert_array_almost_equal(loaded, test_data)
        finally:
            Path(temp_path).unlink()

        # Test non-existent file
        with pytest.raises(FileNotFoundError):
            load_float_image("nonexistent.bin")

    def test_resample_image(self):
        """Test image resampling."""
        # Create test image
        img = np.random.rand(128, 128)

        # Test upsampling
        resampled = resample_image(img, (256, 256))
        assert resampled.shape == (256, 256)

        # Test downsampling
        resampled = resample_image(img, (64, 64))
        assert resampled.shape == (64, 64)

    def test_compute_metrics(self):
        """Test metric computation between two images."""
        # Create test images
        np.random.seed(42)
        img1 = np.random.rand(128, 128)
        img2 = img1 + np.random.randn(128, 128) * 0.01  # Add small noise

        metrics = compute_metrics(img1, img2)

        # Check required metrics
        assert 'correlation' in metrics
        assert 'mse' in metrics
        assert 'rmse' in metrics
        assert 'max_abs_diff' in metrics
        assert 'c_sum' in metrics
        assert 'py_sum' in metrics
        assert 'sum_ratio' in metrics

        # Check reasonable values
        assert 0.9 < metrics['correlation'] < 1.0
        assert metrics['rmse'] < 0.1
        assert 0.95 < metrics['sum_ratio'] < 1.05

        # Test with ROI
        roi = (32, 96, 32, 96)
        roi_metrics = compute_metrics(img1, img2, roi)
        assert roi_metrics['c_sum'] < metrics['c_sum']  # ROI should have less sum

    def test_find_peaks(self):
        """Test peak finding algorithm."""
        # Create image with known peaks
        img = np.zeros((128, 128))
        peak_positions = [(30, 30), (60, 60), (90, 90)]
        for y, x in peak_positions:
            img[y, x] = 100.0
            # Add some surrounding intensity
            img[y-1:y+2, x-1:x+2] = 50.0
            img[y, x] = 100.0  # Restore peak

        peaks = find_peaks(img, 3)

        # Should find the peaks
        assert len(peaks) <= 3
        for peak in peaks:
            assert any(np.linalg.norm(np.array(peak) - np.array(p)) < 2
                      for p in peak_positions)

    @pytest.mark.skipif(
        not Path("./nanoBragg").exists() and not Path("./golden_suite_generator/nanoBragg").exists(),
        reason="Requires C binary for integration test"
    )
    def test_script_integration(self):
        """Test the full script execution."""
        # Run with minimal arguments
        cmd = [
            'python', 'scripts/nb_compare.py',
            '--outdir', 'test_comparison',
            '--',
            '-default_F', '100',
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-distance', '100',
            '-detpixels', '64',
            '-floatfile', 'test.bin'
        ]

        # Run the script
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check that it ran without critical errors
        # (May still fail comparison if implementations differ)
        assert result.returncode in [0, 1]  # 0=pass, 1=fail comparison

        # Check that output files were created
        outdir = Path('test_comparison')
        if outdir.exists():
            assert (outdir / 'summary.json').exists()

            # Load and check summary
            with open(outdir / 'summary.json', 'r') as f:
                summary = json.load(f)

            assert 'correlation' in summary
            assert 'c_runtime_s' in summary
            assert 'py_runtime_s' in summary

            # Clean up
            import shutil
            shutil.rmtree(outdir)

    def test_metrics_with_identical_images(self):
        """Test metrics when images are identical."""
        img = np.random.rand(128, 128)
        metrics = compute_metrics(img, img)

        assert metrics['correlation'] == pytest.approx(1.0)
        assert metrics['mse'] == pytest.approx(0.0)
        assert metrics['rmse'] == pytest.approx(0.0)
        assert metrics['max_abs_diff'] == pytest.approx(0.0)
        assert metrics['sum_ratio'] == pytest.approx(1.0)

    def test_metrics_with_scaled_images(self):
        """Test metrics when one image is a scaled version of the other."""
        img1 = np.random.rand(128, 128)
        img2 = img1 * 2.0

        metrics = compute_metrics(img1, img2)

        assert metrics['correlation'] == pytest.approx(1.0)  # Perfect correlation
        assert metrics['sum_ratio'] == pytest.approx(2.0)  # 2x scaling