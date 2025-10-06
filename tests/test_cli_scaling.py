"""
CLI Scaling Tests for CLI-FLAGS-003 Phase K

Tests the SQUARE lattice factor (F_latt) calculation correctness after fixing
the (h-h0) bug. Validates that PyTorch matches C for F_latt and I_before_scaling.

Evidence base: reports/2025-10-cli-flags/phase_k/f_latt_fix/
Plan reference: plans/active/cli-noise-pix0/plan.md Phase K1-K3
"""
import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
import pytest
import numpy as np

# Set required environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def get_c_binary():
    """Resolve C binary path from env or fallback."""
    c_bin = os.environ.get('NB_C_BIN')
    if c_bin:
        c_path = Path(c_bin)
        if c_path.exists():
            return str(c_path)
        pytest.skip(f"NB_C_BIN={c_bin} does not exist")

    # Fallback order: golden_suite_generator/nanoBragg → ./nanoBragg
    for candidate in ['./golden_suite_generator/nanoBragg', './nanoBragg']:
        c_path = Path(candidate)
        if c_path.exists():
            return str(c_path.resolve())

    pytest.skip("No C binary found (set NB_C_BIN or ensure ./golden_suite_generator/nanoBragg exists)")


def is_parallel_enabled():
    """Check if parallel validation is enabled."""
    return os.environ.get('NB_RUN_PARALLEL', '0') == '1'


def read_float_image(path, shape):
    """Read a raw float binary image."""
    data = np.fromfile(path, dtype=np.float32)
    if data.size != shape[0] * shape[1]:
        raise ValueError(f"Expected {shape[0]}×{shape[1]}={shape[0]*shape[1]} floats, got {data.size}")
    return data.reshape(shape)


@pytest.mark.skipif(not is_parallel_enabled(), reason="NB_RUN_PARALLEL=1 required for C↔PyTorch parity")
class TestFlattSquareMatchesC:
    """Test that SQUARE lattice factor matches C implementation."""

    def test_f_latt_square_matches_c(self):
        """
        Verify F_latt and I_before_scaling match between C and PyTorch for SQUARE shape.

        This test runs a minimal SQUARE crystal simulation and compares final intensities.
        The ratio should be within 1e-3 (Phase K3 exit criterion).

        CRITICAL FIX: This test validates that F_latt uses sincg(π·h, Na) instead of
        the incorrect sincg(π·(h-h0), Na) which caused a 463× error (Attempt #28).
        """
        if not is_parallel_enabled():
            pytest.skip("NB_RUN_PARALLEL=1 required")

        c_bin = get_c_binary()
        py_cli = f"{sys.executable} -m nanobrag_torch"

        # Shared parameters (simple cubic, SQUARE shape)
        common_args = [
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '300',
            '-N', '10',
            '-lambda', '1.0',
            '-distance', '100',
            '-detpixels', '512',
            '-pixel', '0.1',
            '-oversample', '1',
            '-phisteps', '1',
            '-mosaic_dom', '1'
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            c_out = tmpdir / 'c_image.bin'
            py_out = tmpdir / 'py_image.bin'

            # Run C
            c_cmd = [c_bin] + common_args + ['-floatfile', str(c_out)]
            result_c = subprocess.run(c_cmd, capture_output=True, text=True)
            if result_c.returncode != 0:
                pytest.fail(f"C simulation failed:\n{result_c.stderr}")

            # Run PyTorch
            py_cmd = py_cli.split() + common_args + ['-floatfile', str(py_out)]
            result_py = subprocess.run(py_cmd, capture_output=True, text=True)
            if result_py.returncode != 0:
                pytest.fail(f"PyTorch simulation failed:\n{result_py.stderr}")

            # Load images
            shape = (512, 512)
            c_img = read_float_image(c_out, shape)
            py_img = read_float_image(py_out, shape)

            # Compute metrics
            c_sum = np.sum(c_img)
            py_sum = np.sum(py_img)
            sum_ratio = py_sum / c_sum if c_sum > 0 else float('inf')

            c_max = np.max(c_img)
            py_max = np.max(py_img)
            max_ratio = py_max / c_max if c_max > 0 else float('inf')

            # Correlation
            c_flat = c_img.flatten()
            py_flat = py_img.flatten()
            correlation = np.corrcoef(c_flat, py_flat)[0, 1] if np.std(c_flat) > 0 and np.std(py_flat) > 0 else 0.0

            # Phase K3 exit criteria: ratios within 1e-3
            # (sum_ratio and max_ratio should be ~1.0)
            tolerance = 1e-3

            # Report metrics
            metrics = {
                'c_sum': float(c_sum),
                'py_sum': float(py_sum),
                'sum_ratio': float(sum_ratio),
                'c_max': float(c_max),
                'py_max': float(py_max),
                'max_ratio': float(max_ratio),
                'correlation': float(correlation)
            }

            # Save metrics on failure for debugging
            if abs(sum_ratio - 1.0) > tolerance or abs(max_ratio - 1.0) > tolerance or correlation < 0.999:
                report_dir = Path('reports/2025-10-cli-flags/phase_k/f_latt_fix')
                report_dir.mkdir(parents=True, exist_ok=True)
                metrics_path = report_dir / 'test_metrics_failure.json'
                with open(metrics_path, 'w') as f:
                    json.dump(metrics, f, indent=2)

                # Save images for inspection
                np.save(report_dir / 'c_image.npy', c_img)
                np.save(report_dir / 'py_image.npy', py_img)

            # Assertions
            assert correlation >= 0.999, \
                f"Correlation {correlation:.6f} < 0.999. Metrics: {json.dumps(metrics, indent=2)}"

            assert abs(sum_ratio - 1.0) <= tolerance, \
                f"Sum ratio {sum_ratio:.6f} deviates by {abs(sum_ratio - 1.0):.6f} (> {tolerance}). " \
                f"C sum={c_sum:.6g}, PyTorch sum={py_sum:.6g}. Metrics: {json.dumps(metrics, indent=2)}"

            assert abs(max_ratio - 1.0) <= tolerance, \
                f"Max ratio {max_ratio:.6f} deviates by {abs(max_ratio - 1.0):.6f} (> {tolerance}). " \
                f"C max={c_max:.6g}, PyTorch max={py_max:.6g}. Metrics: {json.dumps(metrics, indent=2)}"
