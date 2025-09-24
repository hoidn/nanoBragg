"""
AT-PARALLEL-028: Performance Parity Requirement
Validates that PyTorch implementation meets performance requirements.

Acceptance Test Requirements (from spec-a-parallel.md, lines 133-137):
- Setup: Cell 100,100,100,90,90,90; -lambda 6.2; -N 5; -default_F 100;
  detector 1024×1024, -pixel 0.1, -distance 100; MOSFLM convention
- Expectation:
  - PyTorch CPU ≥ 50% of C throughput
  - PyTorch GPU ≥ 10x C throughput (when CUDA available)
- Pass Criteria: Throughput = detector_pixels / execution_time
"""

import os
import time
import subprocess
import tempfile
from pathlib import Path
import torch
import pytest
import numpy as np

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


def get_c_binary_path():
    """Find the C nanoBragg binary."""
    # Try environment variable first
    if 'NB_C_BIN' in os.environ:
        return os.environ['NB_C_BIN']

    # Try standard locations
    candidates = [
        './golden_suite_generator/nanoBragg',
        './nanoBragg',
        'nanoBragg'  # On PATH
    ]

    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate

    # No binary found
    return None


def run_c_implementation(output_file: str, verbose: bool = False) -> float:
    """
    Run C implementation and measure execution time.

    Returns:
        Execution time in seconds
    """
    c_bin = get_c_binary_path()
    if not c_bin:
        pytest.skip("C binary not found. Set NB_C_BIN or install nanoBragg C version.")

    # Command matches spec requirements
    cmd = [
        c_bin,
        '-cell', '100', '100', '100', '90', '90', '90',
        '-lambda', '6.2',
        '-N', '5',
        '-default_F', '100',
        '-distance', '100',
        '-detpixels', '1024',
        '-pixel', '0.1',
        '-floatfile', output_file
    ]

    # Add flags to suppress progress output for more accurate timing
    if not verbose:
        cmd.append('-noprogress')

    # Measure execution time
    start_time = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.perf_counter()

    if result.returncode != 0:
        pytest.fail(f"C implementation failed: {result.stderr}")

    return end_time - start_time


def run_pytorch_implementation(device: str = 'cpu') -> float:
    """
    Run PyTorch implementation and measure execution time.

    Args:
        device: 'cpu' or 'cuda'

    Returns:
        Execution time in seconds
    """
    # Setup configuration matching spec requirements
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )

    detector_config = DetectorConfig(
        spixels=1024,
        fpixels=1024,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM
    )

    beam_config = BeamConfig(
        wavelength_A=6.2,
        fluence=1e15  # Standard fluence
    )

    # Create simulator
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)

    # Move to device if GPU requested
    if device == 'cuda':
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available for GPU test")
        crystal = crystal.to('cuda')
        detector = detector.to('cuda')

    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    # Warm-up run (important for both CPU and GPU to avoid including compilation/initialization overhead)
    # torch.compile requires warm-up on CPU as well
    if device == 'cuda':
        _ = simulator.run()
        torch.cuda.synchronize()
    else:
        # CPU also needs warm-up for torch.compile
        _ = simulator.run()

    # Measure execution time
    start_time = time.perf_counter()

    if device == 'cuda':
        # For GPU, ensure synchronization for accurate timing
        image = simulator.run()
        torch.cuda.synchronize()
    else:
        image = simulator.run()

    end_time = time.perf_counter()

    return end_time - start_time


class TestATParallel028PerformanceParity:
    """Test performance parity between C and PyTorch implementations."""

    def calculate_throughput(self, execution_time: float, n_pixels: int = 1024*1024) -> float:
        """Calculate throughput in pixels per second."""
        return n_pixels / execution_time

    @pytest.mark.skipif(
        os.environ.get('NB_RUN_PERFORMANCE') != '1',
        reason="Performance tests disabled by default. Set NB_RUN_PERFORMANCE=1 to run."
    )
    def test_cpu_performance_parity(self):
        """Test that PyTorch CPU achieves ≥50% of C throughput."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run C implementation
            c_output = Path(tmpdir) / 'c_output.bin'
            c_time = run_c_implementation(str(c_output))
            c_throughput = self.calculate_throughput(c_time)

            # Run PyTorch CPU implementation
            pytorch_time = run_pytorch_implementation('cpu')
            pytorch_throughput = self.calculate_throughput(pytorch_time)

            # Calculate ratio
            ratio = pytorch_throughput / c_throughput

            # Report results
            print(f"\n=== CPU Performance Results ===")
            print(f"C implementation: {c_time:.3f}s ({c_throughput:.1e} pixels/s)")
            print(f"PyTorch CPU: {pytorch_time:.3f}s ({pytorch_throughput:.1e} pixels/s)")
            print(f"PyTorch/C ratio: {ratio:.2f}x")
            print(f"Requirement: ≥0.5x")

            # Assert performance requirement
            assert ratio >= 0.5, (
                f"PyTorch CPU throughput ({pytorch_throughput:.1e} pixels/s) "
                f"is less than 50% of C throughput ({c_throughput:.1e} pixels/s). "
                f"Ratio: {ratio:.2f}x < 0.5x required"
            )

    @pytest.mark.skipif(
        not torch.cuda.is_available(),
        reason="CUDA not available"
    )
    @pytest.mark.skipif(
        os.environ.get('NB_RUN_PERFORMANCE') != '1',
        reason="Performance tests disabled by default. Set NB_RUN_PERFORMANCE=1 to run."
    )
    def test_gpu_performance_superiority(self):
        """Test that PyTorch GPU achieves ≥10x C throughput."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run C implementation
            c_output = Path(tmpdir) / 'c_output.bin'
            c_time = run_c_implementation(str(c_output))
            c_throughput = self.calculate_throughput(c_time)

            # Run PyTorch GPU implementation
            pytorch_time = run_pytorch_implementation('cuda')
            pytorch_throughput = self.calculate_throughput(pytorch_time)

            # Calculate ratio
            ratio = pytorch_throughput / c_throughput

            # Report results
            print(f"\n=== GPU Performance Results ===")
            print(f"C implementation: {c_time:.3f}s ({c_throughput:.1e} pixels/s)")
            print(f"PyTorch GPU: {pytorch_time:.3f}s ({pytorch_throughput:.1e} pixels/s)")
            print(f"PyTorch GPU/C ratio: {ratio:.2f}x")
            print(f"Requirement: ≥10x")

            # Assert performance requirement
            assert ratio >= 10.0, (
                f"PyTorch GPU throughput ({pytorch_throughput:.1e} pixels/s) "
                f"is less than 10x C throughput ({c_throughput:.1e} pixels/s). "
                f"Ratio: {ratio:.2f}x < 10x required"
            )

    def test_performance_measurement_validity(self):
        """Test that performance measurements are reproducible and valid."""
        # Run PyTorch CPU multiple times to check consistency
        times = []
        for _ in range(3):
            t = run_pytorch_implementation('cpu')
            times.append(t)

        # Calculate coefficient of variation (should be low)
        mean_time = np.mean(times)
        std_time = np.std(times)
        cv = std_time / mean_time

        print(f"\n=== Measurement Validity ===")
        print(f"Times: {[f'{t:.3f}s' for t in times]}")
        print(f"Mean: {mean_time:.3f}s, Std: {std_time:.4f}s")
        print(f"Coefficient of variation: {cv:.2%}")

        # Assert reasonable consistency (CV < 25% for small workloads)
        # Note: Small simulations can have higher variance due to system noise
        assert cv < 0.25, f"Measurement variability too high (CV={cv:.2%} > 25%)"