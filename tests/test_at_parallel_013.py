"""
AT-PARALLEL-013: Cross-Platform Consistency
Tests that PyTorch implementation produces consistent results across platforms.

Acceptance Test Requirements (from spec-a-parallel.md):
- Constraints: CPU, float64, deterministic Torch mode; identical seeds; no GPU
- Setup: Use triclinic_P1 case from AT-PARALLEL-012
- Pass criteria:
  - PyTorch vs PyTorch (machine A vs B): allclose with rtol ≤ 1e-7, atol ≤ 1e-12 and correlation ≥ 0.999
  - C vs PyTorch: allclose with rtol ≤ 1e-5, atol ≤ 1e-6 and correlation ≥ 0.995
"""

import os
import sys
import platform

# Set environment variables BEFORE importing torch to avoid device query issues
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TORCHDYNAMO_DISABLE'] = '1'
os.environ['NANOBRAGG_DISABLE_COMPILE'] = '1'

import numpy as np
import torch
import pytest
from pathlib import Path
from scipy.stats import pearsonr

from nanobrag_torch.config import (
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
    CrystalConfig,
    BeamConfig,
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator

# Import C reference runner if available
try:
    from scripts.c_reference_utils import run_c_nanobrag
except ImportError:
    run_c_nanobrag = None


def set_deterministic_mode():
    """Set PyTorch to deterministic mode for reproducibility.

    Note: CUDA_VISIBLE_DEVICES, TORCHDYNAMO_DISABLE, and NANOBRAGG_DISABLE_COMPILE
    are set at module level before torch import to prevent device query issues.
    """
    # Set seeds
    torch.manual_seed(42)
    np.random.seed(42)

    # Force CPU only
    torch.set_default_device('cpu')

    # Enable deterministic algorithms
    torch.use_deterministic_algorithms(True, warn_only=True)

    # Set default dtype to float64
    torch.set_default_dtype(torch.float64)

    # Try to set threading for reproducibility, but don't fail if already set
    try:
        torch.set_num_threads(1)
    except RuntimeError:
        pass  # Already set

    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass  # Already set

    # Set MKL threads if using MKL
    if 'MKL_NUM_THREADS' not in os.environ:
        os.environ['MKL_NUM_THREADS'] = '1'
    if 'OMP_NUM_THREADS' not in os.environ:
        os.environ['OMP_NUM_THREADS'] = '1'

    # Reset dynamo state after toggling so other tests resume with defaults
    try:
        torch._dynamo.reset()
    except Exception:
        pass  # Dynamo may not be available or already reset


def get_platform_fingerprint():
    """Get platform information for logging."""
    return {
        'platform': platform.platform(),
        'python_version': sys.version,
        'torch_version': torch.__version__,
        'numpy_version': np.__version__,
        'processor': platform.processor(),
        'machine': platform.machine(),
    }


def run_simulation_deterministic(seed: int = 42):
    """
    Run simulation in deterministic mode with triclinic_P1 configuration.

    Args:
        seed: Random seed for reproducibility

    Returns:
        np.ndarray: Simulated diffraction pattern
    """
    # Reset and set deterministic mode
    torch.manual_seed(seed)
    np.random.seed(seed)
    set_deterministic_mode()

    # Setup configuration matching triclinic_P1 from AT-PARALLEL-012
    # From spec: -misset -89.968546 -31.328953 177.753396
    # -cell 70 80 90 75 85 95 -default_F 100 -N 5 -lambda 1.0 -detpixels 512
    crystal_config = CrystalConfig(
        cell_a=70.0, cell_b=80.0, cell_c=90.0,
        cell_alpha=75.0, cell_beta=85.0, cell_gamma=95.0,
        N_cells=(5, 5, 5),
        misset_deg=(-89.968546, -31.328953, 177.753396),
        default_F=100.0
    )

    detector_config = DetectorConfig(
        spixels=512,
        fpixels=512,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM
    )

    beam_config = BeamConfig(
        wavelength_A=1.0,
        fluence=1e15
    )

    # Create models in deterministic mode
    crystal = Crystal(crystal_config, dtype=torch.float64)
    detector = Detector(detector_config, dtype=torch.float64)
    simulator = Simulator(crystal, detector, crystal_config, beam_config, dtype=torch.float64)

    # Run simulation on CPU with float64
    result = simulator.run()

    # Ensure result is on CPU and convert to numpy
    return result.cpu().numpy()


class TestATParallel013CrossPlatformConsistency:
    """Test cross-platform consistency and determinism."""

    def test_pytorch_determinism_same_seed(self):
        """Test that PyTorch produces identical results with same seed."""
        # Run simulation twice with same seed
        result1 = run_simulation_deterministic(seed=42)
        result2 = run_simulation_deterministic(seed=42)

        # Should be exactly identical (bit-for-bit)
        assert np.array_equal(result1, result2), (
            "PyTorch not deterministic - results differ with same seed"
        )

        # Also check with allclose for numerical precision
        np.testing.assert_allclose(
            result1, result2,
            rtol=1e-7,
            atol=1e-12,
            err_msg="PyTorch determinism: tolerance check failed"
        )

        # Correlation should be perfect (1.0)
        corr, _ = pearsonr(result1.flatten(), result2.flatten())
        assert corr >= 0.9999999, f"Correlation {corr} < 0.9999999 for same-seed runs"

        # Log platform info for debugging
        platform_info = get_platform_fingerprint()
        print(f"Platform: {platform_info['platform']}")
        print(f"PyTorch version: {platform_info['torch_version']}")

    def test_pytorch_determinism_different_seeds(self):
        """Test that PyTorch produces different results with different seeds."""
        # Note: This test configuration uses fixed misset angles and no mosaic/noise,
        # so different seeds won't affect the result. We expect identical results.

        # Run simulation with different seeds
        result1 = run_simulation_deterministic(seed=42)
        result2 = run_simulation_deterministic(seed=123)

        # With no random components (fixed misset, no mosaic, no noise),
        # results should be identical regardless of seed
        np.testing.assert_allclose(
            result1, result2,
            rtol=1e-7,
            atol=1e-12,
            err_msg="Results differ despite no random components"
        )

        # Correlation should be perfect
        corr, _ = pearsonr(result1.flatten(), result2.flatten())
        assert corr >= 0.9999999, f"Correlation {corr} < 0.9999999 for identical physics"

    def test_pytorch_consistency_across_runs(self):
        """Test PyTorch consistency across multiple runs."""
        # Run simulation multiple times
        n_runs = 5
        results = []

        for i in range(n_runs):
            # Each run with same seed should be identical
            result = run_simulation_deterministic(seed=42)
            results.append(result)

        # All runs should be identical to first
        reference = results[0]
        for i, result in enumerate(results[1:], 1):
            np.testing.assert_allclose(
                reference, result,
                rtol=1e-7,
                atol=1e-12,
                err_msg=f"Run {i+1} differs from reference"
            )

            # Check correlation
            corr, _ = pearsonr(reference.flatten(), result.flatten())
            assert corr >= 0.999, f"Run {i+1} correlation {corr} < 0.999"

    @pytest.mark.skipif(
        run_c_nanobrag is None or os.getenv("NB_RUN_PARALLEL") != "1",
        reason="Requires NB_RUN_PARALLEL=1 and C binary"
    )
    def test_c_pytorch_equivalence(self):
        """Test equivalence between C and PyTorch implementations."""
        # Get C binary path
        c_binary = os.getenv("NB_C_BIN", "./golden_suite_generator/nanoBragg")
        if not os.path.exists(c_binary):
            pytest.skip(f"C binary not found at {c_binary}")

        # Run PyTorch simulation in deterministic mode
        pytorch_result = run_simulation_deterministic(seed=42)

        # Run C simulation with matching parameters
        c_params = [
            "-misset", "-89.968546", "-31.328953", "177.753396",
            "-cell", "70", "80", "90", "75", "85", "95",
            "-default_F", "100",
            "-N", "5",
            "-lambda", "1.0",
            "-detpixels", "512",
            "-distance", "100",
            "-pixel", "0.1",
            "-floatfile", "test_c_output.bin"
        ]

        # Run C code
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "test_c_output.bin")
            c_params[-1] = output_file

            result = subprocess.run(
                [c_binary] + c_params,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                pytest.fail(f"C code failed: {result.stderr}")

            # Load C result
            import struct
            with open(output_file, 'rb') as f:
                data = f.read()
                n_floats = len(data) // 4
                assert n_floats == 512 * 512, f"Expected {512*512} floats, got {n_floats}"
                floats = struct.unpack(f'{n_floats}f', data)
                c_result = np.array(floats).reshape(512, 512)

        # Compare C and PyTorch results
        np.testing.assert_allclose(
            c_result, pytorch_result,
            rtol=1e-5,
            atol=1e-6,
            err_msg="C vs PyTorch equivalence failed"
        )

        # Check correlation
        corr, _ = pearsonr(c_result.flatten(), pytorch_result.flatten())
        assert corr >= 0.995, f"C-PyTorch correlation {corr} < 0.995 requirement"

    def test_platform_fingerprint(self):
        """Test that platform fingerprint is captured correctly."""
        fingerprint = get_platform_fingerprint()

        # Verify all expected fields are present
        expected_fields = [
            'platform', 'python_version', 'torch_version',
            'numpy_version', 'processor', 'machine'
        ]

        for field in expected_fields:
            assert field in fingerprint, f"Missing platform field: {field}"
            assert fingerprint[field], f"Empty platform field: {field}"

        # Log fingerprint for record
        print("\n=== Platform Fingerprint ===")
        for key, value in fingerprint.items():
            print(f"{key}: {value}")

    def test_numerical_precision_float64(self):
        """Test that float64 precision is maintained throughout."""
        set_deterministic_mode()

        # Create test configuration
        crystal_config = CrystalConfig(
            cell_a=70.0, cell_b=80.0, cell_c=90.0,
            cell_alpha=75.0, cell_beta=85.0, cell_gamma=95.0,
            N_cells=(5, 5, 5),
            default_F=100.0
        )

        # Verify float64 is used
        crystal = Crystal(crystal_config, dtype=torch.float64)

        # Check that internal tensors are float64
        assert crystal.cell_a.dtype == torch.float64, "Crystal cell_a not float64"
        assert crystal.cell_b.dtype == torch.float64, "Crystal cell_b not float64"
        assert crystal.cell_c.dtype == torch.float64, "Crystal cell_c not float64"

        # Run small simulation to verify precision maintained
        detector_config = DetectorConfig(
            spixels=64,  # Small for quick test
            fpixels=64,
            pixel_size_mm=0.1,
            distance_mm=100.0
        )

        detector = Detector(detector_config, dtype=torch.float64)
        beam_config = BeamConfig(wavelength_A=1.0, fluence=1e15)
        simulator = Simulator(crystal, detector, crystal_config, beam_config, dtype=torch.float64)

        result = simulator.run()
        assert result.dtype == torch.float64, "Simulation result not float64"

        # Check for numerical stability (no NaNs or Infs)
        assert not torch.isnan(result).any(), "NaNs in simulation result"
        assert not torch.isinf(result).any(), "Infs in simulation result"