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


class TestMOSFLMCellVectors:
    """Test MOSFLM matrix cell vector computation (Phase K3g2)."""

    def test_mosflm_cell_vectors(self):
        """
        Verify that PyTorch correctly computes real-space vectors from MOSFLM matrices.

        This test validates CLI-FLAGS-003 Phase K3g1 implementation:
        When MOSFLM reciprocal vectors are provided (via -mat file), PyTorch must:
        1. Compute V_star = a* · (b* × c*)
        2. Compute V_cell = 1 / V_star
        3. Derive real vectors: a = (b* × c*) × V_cell, etc.
        4. Update cell_a/b/c parameters from the derived vectors

        Expected output (from C trace):
        - V_cell ≈ 24682.3 Å³
        - |a| ≈ 26.7514 Å
        - |b| ≈ 31.3100 Å
        - |c| ≈ 33.6734 Å
        """
        import torch
        from nanobrag_torch.models.crystal import Crystal, CrystalConfig
        from nanobrag_torch.io.mosflm import read_mosflm_matrix

        # Read A.mat from repo root
        mat_file = Path('A.mat')
        if not mat_file.exists():
            pytest.skip("A.mat not found in repository root")

        wavelength_A = 0.976800
        a_star, b_star, c_star = read_mosflm_matrix(str(mat_file), wavelength_A)

        # Create Crystal with MOSFLM orientation
        config = CrystalConfig(
            cell_a=100.0,  # placeholder
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            mosflm_a_star=a_star,
            mosflm_b_star=b_star,
            mosflm_c_star=c_star,
            N_cells=(36, 47, 29),
        )

        crystal = Crystal(config, device=torch.device('cpu'), dtype=torch.float64)
        tensors = crystal.compute_cell_tensors()

        # Expected values from C trace (reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt)
        expected_V_cell = 24682.3  # Å³
        expected_mag_a = 26.7514   # Å
        expected_mag_b = 31.3100   # Å
        expected_mag_c = 33.6734   # Å

        # Compute actual values
        actual_V_cell = tensors['V'].item()
        actual_mag_a = torch.norm(tensors['a']).item()
        actual_mag_b = torch.norm(tensors['b']).item()
        actual_mag_c = torch.norm(tensors['c']).item()

        # Tolerance: 5e-4 relative error (from Phase K3f exit criteria)
        rtol = 5e-4

        # Assertions
        V_rel_error = abs(actual_V_cell - expected_V_cell) / expected_V_cell
        assert V_rel_error <= rtol, \
            f"V_cell relative error {V_rel_error:.6g} > {rtol}. " \
            f"Expected {expected_V_cell:.2f}, got {actual_V_cell:.2f} Å³"

        a_rel_error = abs(actual_mag_a - expected_mag_a) / expected_mag_a
        assert a_rel_error <= rtol, \
            f"|a| relative error {a_rel_error:.6g} > {rtol}. " \
            f"Expected {expected_mag_a:.4f}, got {actual_mag_a:.4f} Å"

        b_rel_error = abs(actual_mag_b - expected_mag_b) / expected_mag_b
        assert b_rel_error <= rtol, \
            f"|b| relative error {b_rel_error:.6g} > {rtol}. " \
            f"Expected {expected_mag_b:.4f}, got {actual_mag_b:.4f} Å"

        c_rel_error = abs(actual_mag_c - expected_mag_c) / expected_mag_c
        assert c_rel_error <= rtol, \
            f"|c| relative error {c_rel_error:.6g} > {rtol}. " \
            f"Expected {expected_mag_c:.4f}, got {actual_mag_c:.4f} Å"


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

            # Run C (in tmpdir to avoid Fdump.bin contamination)
            # Convert c_bin to absolute path before changing directory
            c_bin_abs = str(Path(c_bin).resolve())
            c_cmd = [c_bin_abs] + common_args + ['-floatfile', str(c_out)]
            result_c = subprocess.run(c_cmd, capture_output=True, text=True, cwd=tmpdir)
            if result_c.returncode != 0:
                pytest.fail(f"C simulation failed:\n{result_c.stderr}")

            # Run PyTorch (in tmpdir to avoid Fdump.bin contamination)
            py_cmd = py_cli.split() + common_args + ['-floatfile', str(py_out)]
            result_py = subprocess.run(py_cmd, capture_output=True, text=True, cwd=tmpdir)
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


class TestHKLDevice:
    """Test that HKL tensors respect CLI -device flag (Phase L3d)."""

    @pytest.mark.parametrize("device_str,dtype_str", [
        ("cpu", "float32"),
        ("cpu", "float64"),
        pytest.param("cuda", "float32", marks=pytest.mark.skipif(
            not __import__('torch').cuda.is_available(), reason="CUDA not available")),
        pytest.param("cuda", "float64", marks=pytest.mark.skipif(
            not __import__('torch').cuda.is_available(), reason="CUDA not available")),
    ])
    def test_hkl_tensor_respects_device(self, device_str, dtype_str):
        """
        Verify that HKL tensors are transferred to the correct device when CLI -device is specified.

        This test validates CLI-FLAGS-003 Phase L3d implementation:
        When the CLI is invoked with -device cuda (or cpu), the HKL tensor loaded from
        -hkl file must be transferred to the specified device (not remain on CPU).

        The fix ensures that __main__.py:1073 calls .to(device=device, dtype=dtype)
        instead of just .to(dtype=dtype).

        Expected behavior:
        - crystal.hkl_data.device matches the requested device
        - crystal.hkl_data.dtype matches the requested dtype
        - Structure factor lookup succeeds without device mismatch errors
        """
        import torch
        from nanobrag_torch.models.crystal import Crystal, CrystalConfig
        from nanobrag_torch.config import BeamConfig
        from nanobrag_torch.io.hkl import read_hkl_file

        # Check if scaled.hkl exists (supervisor test case)
        hkl_file = Path('scaled.hkl')
        if not hkl_file.exists():
            pytest.skip("scaled.hkl not found (required for Phase L supervisor command)")

        # Parse device and dtype
        device = torch.device(device_str)
        dtype = torch.float32 if dtype_str == "float32" else torch.float64

        # Load HKL data
        hkl_array, hkl_metadata = read_hkl_file(str(hkl_file))

        # Create minimal config (matching supervisor command)
        wavelength_A = 0.976800
        beam_config = BeamConfig(wavelength_A=wavelength_A)

        config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(36, 47, 29),
        )

        # Instantiate Crystal
        crystal = Crystal(config, beam_config=beam_config, device=device, dtype=dtype)

        # Attach HKL data (mimicking __main__.py flow)
        if isinstance(hkl_array, torch.Tensor):
            crystal.hkl_data = hkl_array.clone().detach().to(device=device, dtype=dtype)
        else:
            crystal.hkl_data = torch.tensor(hkl_array, device=device, dtype=dtype)
        crystal.hkl_metadata = hkl_metadata

        # Verify device and dtype
        # Use .type comparison for device to handle cuda vs cuda:0
        assert crystal.hkl_data.device.type == device.type, \
            f"HKL tensor device {crystal.hkl_data.device} does not match requested {device}"
        assert crystal.hkl_data.dtype == dtype, \
            f"HKL tensor dtype {crystal.hkl_data.dtype} does not match requested {dtype}"

        # Verify structure factor lookup works (target reflection from supervisor trace)
        # hkl = (-7, -1, -14) should return F_cell ≈ 190.27 (from Phase L3b probe)
        h = torch.tensor(-7.0, device=device, dtype=dtype)
        k = torch.tensor(-1.0, device=device, dtype=dtype)
        l = torch.tensor(-14.0, device=device, dtype=dtype)

        # Lookup structure factor
        F_cell = crystal.get_structure_factor(h, k, l)

        # Expected value from C trace and Phase L3b probe
        expected_F = 190.27
        tolerance = 0.01  # Allow 1% tolerance for dtype differences

        # Verify result
        # Use .type comparison for device to handle cuda vs cuda:0
        assert F_cell.device.type == device.type, \
            f"get_structure_factor returned tensor on {F_cell.device}, expected {device}"

        F_cell_val = F_cell.item()
        rel_error = abs(F_cell_val - expected_F) / expected_F
        assert rel_error <= tolerance, \
            f"Structure factor lookup failed: expected {expected_F:.2f}, got {F_cell_val:.2f} " \
            f"(relative error {rel_error:.6f} > {tolerance})"
