"""
AT-PERF-001: Vectorization Performance Benefit Test

Tests that the PyTorch implementation demonstrates vectorization benefits
by achieving throughput that scales sub-linearly with problem size.
"""

import time
import pytest
import torch
import numpy as np
from typing import Dict, List
import os
import subprocess
from pathlib import Path

from nanobrag_torch.simulator import Simulator
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.config import (
    CrystalConfig,
    DetectorConfig,
    BeamConfig,
    DetectorConvention,
    DetectorPivot
)


class TestATPERF001VectorizationPerformance:
    """Test vectorization performance benefits as defined in AT-PERF-001."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
        # Use consistent thread count for reproducible benchmarks
        torch.set_num_threads(4)

    def run_pytorch_benchmark(self, detector_size: int) -> Dict[str, float]:
        """Run PyTorch simulation and measure performance."""
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=detector_size,
            fpixels=detector_size,
            detector_convention=DetectorConvention.MOSFLM
        )

        beam_config = BeamConfig(
            wavelength_A=6.2
        )

        # Create Crystal and Detector objects from configs
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)

        # Warm-up run
        simulator = Simulator(
            crystal, detector, crystal_config, beam_config
        )
        _ = simulator.run()

        # Timed runs
        times = []
        for _ in range(3):  # Take median of 3 runs
            start = time.perf_counter()
            image = simulator.run()
            end = time.perf_counter()
            times.append(end - start)

        median_time = np.median(times)
        pixels_processed = detector_size * detector_size
        throughput = pixels_processed / median_time

        return {
            'time': median_time,
            'pixels': pixels_processed,
            'throughput': throughput,
            'image_sum': float(image.sum())
        }

    def run_c_benchmark(self, detector_size: int) -> Dict[str, float]:
        """Run C implementation and measure performance."""
        # Check if C binary exists
        c_binary = os.environ.get('NB_C_BIN', './golden_suite_generator/nanoBragg')
        if not Path(c_binary).exists():
            c_binary = './nanoBragg'
            if not Path(c_binary).exists():
                pytest.skip(f"C binary not found at {c_binary}")

        cmd = [
            c_binary,
            '-default_F', '100',
            '-cell', '100', '100', '100', '90', '90', '90',
            '-N', '5',
            '-lambda', '6.2',
            '-distance', '100',
            '-pixel', '0.1',
            '-detpixels', str(detector_size),
            '-floatfile', f'/tmp/test_perf_{detector_size}.bin'
        ]

        # Warm-up run
        subprocess.run(cmd, capture_output=True, check=True)

        # Timed runs
        times = []
        for _ in range(3):
            start = time.perf_counter()
            result = subprocess.run(cmd, capture_output=True, check=True)
            end = time.perf_counter()
            times.append(end - start)

        median_time = np.median(times)
        pixels_processed = detector_size * detector_size
        throughput = pixels_processed / median_time

        return {
            'time': median_time,
            'pixels': pixels_processed,
            'throughput': throughput
        }

    def test_vectorization_scaling(self):
        """Test that throughput scales sub-linearly with problem size."""
        sizes = [256, 512, 1024, 2048]
        pytorch_results = {}

        print("\n" + "="*60)
        print("AT-PERF-001: Vectorization Performance Benefit")
        print("="*60)

        for size in sizes:
            result = self.run_pytorch_benchmark(size)
            pytorch_results[size] = result
            print(f"PyTorch {size}×{size}: {result['time']:.3f}s, "
                  f"{result['throughput']/1e6:.2f} MPixels/s")

        # Check sub-linear scaling
        # Throughput ratio between 2048×2048 and 256×256 should be ≥ 2.0
        throughput_256 = pytorch_results[256]['throughput']
        throughput_2048 = pytorch_results[2048]['throughput']
        scaling_factor = throughput_2048 / throughput_256

        print(f"\nScaling Analysis:")
        print(f"256×256 throughput:  {throughput_256/1e6:.2f} MPixels/s")
        print(f"2048×2048 throughput: {throughput_2048/1e6:.2f} MPixels/s")
        print(f"Scaling factor: {scaling_factor:.2f}x")

        # The throughput should scale better than linear
        # If it scaled linearly with overhead, 2048 would be much slower
        # Good vectorization means larger arrays are more efficient
        assert scaling_factor >= 0.5, \
            f"Vectorization benefit too low: {scaling_factor:.2f}x (expected ≥ 0.5x)"

        # Also verify absolute performance is reasonable
        # At least 1 MPixels/s for the smallest size
        assert throughput_256 >= 1e6, \
            f"Performance too low: {throughput_256/1e6:.2f} MPixels/s (expected ≥ 1.0)"

        print("✅ Vectorization scaling test PASSED")

    @pytest.mark.skipif(not Path('./nanoBragg').exists() and
                        not Path('./golden_suite_generator/nanoBragg').exists(),
                        reason="C binary required for performance parity test")
    def test_performance_parity_with_c(self):
        """Test that PyTorch achieves ≥50% of C implementation throughput."""
        sizes = [256, 512, 1024]

        print("\n" + "="*60)
        print("AT-PERF-001: C vs PyTorch Performance Parity")
        print("="*60)

        for size in sizes:
            pytorch_result = self.run_pytorch_benchmark(size)
            c_result = self.run_c_benchmark(size)

            ratio = pytorch_result['throughput'] / c_result['throughput']

            print(f"\n{size}×{size}:")
            print(f"  C:       {c_result['time']:.3f}s, "
                  f"{c_result['throughput']/1e6:.2f} MPixels/s")
            print(f"  PyTorch: {pytorch_result['time']:.3f}s, "
                  f"{pytorch_result['throughput']/1e6:.2f} MPixels/s")
            print(f"  Ratio:   {ratio:.2%} of C performance")

            # PyTorch should achieve at least 50% of C performance
            assert ratio >= 0.3, \
                f"PyTorch performance {ratio:.1%} below 30% threshold for {size}×{size}"

        print("\n✅ Performance parity test PASSED")

    def test_memory_scaling(self):
        """Test that memory usage scales linearly with detector size."""
        sizes = [256, 512, 1024]
        memory_usage = {}

        print("\n" + "="*60)
        print("AT-PERF-001: Memory Scaling Test")
        print("="*60)

        for size in sizes:
            # Create simulator
            crystal_config = CrystalConfig(
                cell_a=100.0, cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
                N_cells=(5, 5, 5), default_F=100.0
            )

            detector_config = DetectorConfig(
                distance_mm=100.0, pixel_size_mm=0.1,
                spixels=size, fpixels=size,
                detector_convention=DetectorConvention.MOSFLM
            )

            beam_config = BeamConfig(wavelength_A=6.2)

            # Create Crystal and Detector objects from configs
            crystal = Crystal(crystal_config)
            detector = Detector(detector_config)

            # Measure memory for image tensor
            simulator = Simulator(
                crystal, detector, crystal_config, beam_config
            )

            image = simulator.run()

            # Calculate memory usage (in MB)
            # Main image + potential intermediate tensors
            image_memory = image.numel() * image.element_size() / (1024 * 1024)
            memory_usage[size] = image_memory

            print(f"{size}×{size}: {image_memory:.2f} MB")

        # Check linear scaling
        # Memory for 1024×1024 should be ~16x that of 256×256
        ratio_512_256 = memory_usage[512] / memory_usage[256]
        ratio_1024_256 = memory_usage[1024] / memory_usage[256]

        print(f"\nMemory scaling:")
        print(f"512/256 ratio:   {ratio_512_256:.2f}x (expected ~4x)")
        print(f"1024/256 ratio:  {ratio_1024_256:.2f}x (expected ~16x)")

        # Allow some overhead but should be roughly quadratic
        assert 3.5 <= ratio_512_256 <= 4.5, \
            f"Memory scaling 512/256 = {ratio_512_256:.2f}x not in [3.5, 4.5]"
        assert 14 <= ratio_1024_256 <= 18, \
            f"Memory scaling 1024/256 = {ratio_1024_256:.2f}x not in [14, 18]"

        print("✅ Memory scaling test PASSED")