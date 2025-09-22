#!/usr/bin/env python3
"""
Profile PyTorch implementation to identify performance bottlenecks.
"""

import os
import time
import torch
import numpy as np
import cProfile
import pstats
from io import StringIO

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
sys.path.insert(0, '/Users/ollie/Documents/nanoBragg/src')

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, CrystalShape, DetectorConvention
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

def run_simulation(size=1024):
    """Run a simulation and return timing breakdown."""

    # Setup configs
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=[5, 5, 5],
        default_F=100.0,
        shape=CrystalShape.SQUARE
    )

    detector_config = DetectorConfig(
        spixels=size,
        fpixels=size,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        oversample=1
    )

    beam_config = BeamConfig(wavelength_A=6.2)

    # Time each component
    timings = {}

    # Model creation
    start = time.time()
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    timings['model_creation'] = time.time() - start

    # Simulator setup
    start = time.time()
    simulator = Simulator(crystal, detector, crystal_config, beam_config)
    timings['simulator_setup'] = time.time() - start

    # Get pixel coordinates (often cached)
    start = time.time()
    pixel_coords = detector.get_pixel_coords()
    timings['pixel_coords'] = time.time() - start

    # Run simulation with detailed timing
    total_start = time.time()

    # The main run() method
    with torch.no_grad():  # Disable gradient tracking for fair comparison
        image = simulator.run()

    timings['total_simulation'] = time.time() - total_start

    return timings, image

def profile_detailed():
    """Run detailed profiling of the simulation."""

    print("=" * 70)
    print("PyTorch Implementation Profiling")
    print("=" * 70)

    # Check PyTorch settings
    print(f"\nPyTorch Configuration:")
    print(f"  Version: {torch.__version__}")
    print(f"  Threads: {torch.get_num_threads()}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    print(f"  MKL available: {torch.backends.mkl.is_available()}")

    # Test different sizes
    sizes = [256, 512, 1024]

    for size in sizes:
        print(f"\n{'='*50}")
        print(f"Detector size: {size}x{size}")
        print('-'*50)

        # Warm-up run
        print("Warm-up run...")
        _, _ = run_simulation(size)

        # Timed run
        print("Timed run...")
        timings, image = run_simulation(size)

        print(f"  Model creation: {timings['model_creation']*1000:.2f} ms")
        print(f"  Simulator setup: {timings['simulator_setup']*1000:.2f} ms")
        print(f"  Pixel coords: {timings['pixel_coords']*1000:.2f} ms")
        print(f"  Total simulation: {timings['total_simulation']*1000:.2f} ms")
        print(f"  Throughput: {(size*size/timings['total_simulation'])/1e6:.2f} MPixels/s")

    # Profile the main simulation
    print(f"\n{'='*70}")
    print("Detailed Profiling (1024x1024)")
    print('='*70)

    profiler = cProfile.Profile()
    profiler.enable()

    # Run simulation
    run_simulation(1024)

    profiler.disable()

    # Get stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)

    print("\nTop 20 functions by cumulative time:")
    print(s.getvalue())

    # Now let's check specific operations
    print(f"\n{'='*70}")
    print("Tensor Operation Analysis")
    print('='*70)

    # Create test tensors
    size = 1024
    test_tensor = torch.randn(size, size)

    # Test different operations
    operations = [
        ("Tensor creation", lambda: torch.zeros(size, size)),
        ("Matrix multiply", lambda: torch.matmul(test_tensor, test_tensor)),
        ("Element-wise multiply", lambda: test_tensor * test_tensor),
        ("Exponential", lambda: torch.exp(test_tensor)),
        ("Sine", lambda: torch.sin(test_tensor)),
        ("Broadcasting add", lambda: test_tensor + torch.randn(1, size)),
        ("Reduction (sum)", lambda: test_tensor.sum()),
        ("meshgrid", lambda: torch.meshgrid(torch.arange(size), torch.arange(size), indexing='ij')),
    ]

    for name, op in operations:
        # Warm-up
        for _ in range(5):
            op()

        # Time
        start = time.time()
        for _ in range(10):
            result = op()
        elapsed = (time.time() - start) / 10

        print(f"  {name:25} {elapsed*1000:.2f} ms")

    # Check for common bottlenecks
    print(f"\n{'='*70}")
    print("Bottleneck Analysis")
    print('='*70)

    # Test with and without gradient tracking
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=[5, 5, 5],
        default_F=100.0
    )

    detector_config = DetectorConfig(
        spixels=512, fpixels=512,
        pixel_size_mm=0.1, distance_mm=100.0
    )

    beam_config = BeamConfig(wavelength_A=6.2)

    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    # With gradient tracking
    start = time.time()
    image_grad = simulator.run()
    time_with_grad = time.time() - start

    # Without gradient tracking
    with torch.no_grad():
        start = time.time()
        image_no_grad = simulator.run()
        time_no_grad = time.time() - start

    print(f"  With gradient tracking: {time_with_grad*1000:.2f} ms")
    print(f"  Without gradient tracking: {time_no_grad*1000:.2f} ms")
    print(f"  Overhead from gradients: {((time_with_grad/time_no_grad - 1)*100):.1f}%")

    # Check memory layout
    print(f"\n  Checking tensor memory layout:")
    test_coords = detector.get_pixel_coords()
    print(f"    Pixel coords contiguous: {test_coords.is_contiguous()}")
    print(f"    Pixel coords dtype: {test_coords.dtype}")
    print(f"    Pixel coords device: {test_coords.device}")

if __name__ == "__main__":
    profile_detailed()