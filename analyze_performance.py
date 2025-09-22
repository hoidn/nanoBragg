#!/usr/bin/env python3
"""
Analyze why PyTorch is slower and identify optimization opportunities.
"""

import os
import time
import torch
import numpy as np

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
sys.path.insert(0, '/Users/ollie/Documents/nanoBragg/src')

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, CrystalShape
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

def analyze_bottlenecks():
    """Identify key performance issues."""

    print("=" * 70)
    print("Performance Analysis: Why is PyTorch Slower?")
    print("=" * 70)

    # 1. Threading comparison
    print("\n1. THREADING ANALYSIS")
    print("-" * 50)
    print(f"PyTorch threads: {torch.get_num_threads()}")
    print(f"PyTorch inter-op threads: {torch.get_num_interop_threads()}")

    # Try different thread settings
    for num_threads in [1, 2, 4, 8]:
        torch.set_num_threads(num_threads)

        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=[5, 5, 5], default_F=100.0
        )

        detector_config = DetectorConfig(
            spixels=512, fpixels=512,
            pixel_size_mm=0.1, distance_mm=100.0
        )

        beam_config = BeamConfig(wavelength_A=6.2)

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Warm-up
        with torch.no_grad():
            _ = simulator.run()

        # Time
        start = time.time()
        with torch.no_grad():
            _ = simulator.run()
        elapsed = time.time() - start

        print(f"  Threads={num_threads}: {elapsed*1000:.2f} ms")

    # Reset to default
    torch.set_num_threads(4)

    # 2. Memory layout and dtype
    print("\n2. MEMORY LAYOUT & DTYPE ANALYSIS")
    print("-" * 50)

    # Test float32 vs float64
    for dtype in [torch.float32, torch.float64]:
        print(f"\nTesting dtype: {dtype}")

        # Create test tensors
        size = 1024
        a = torch.randn(size, size, dtype=dtype)
        b = torch.randn(size, size, dtype=dtype)

        # Time operations
        ops = [
            ("Element multiply", lambda: a * b),
            ("Sin", lambda: torch.sin(a)),
            ("Exp", lambda: torch.exp(a * 0.001)),  # Scale to avoid overflow
            ("Sum", lambda: a.sum()),
        ]

        for name, op in ops:
            # Warm-up
            for _ in range(5):
                _ = op()

            start = time.time()
            for _ in range(10):
                _ = op()
            elapsed = (time.time() - start) / 10

            print(f"    {name:20} {elapsed*1000:.2f} ms")

    # 3. Vectorization analysis
    print("\n3. VECTORIZATION ANALYSIS")
    print("-" * 50)
    print("Comparing loop vs vectorized operations")

    size = 1024 * 1024

    # Loop version (simulating C-style)
    def loop_version():
        result = 0.0
        for i in range(size):
            result += np.sin(i * 0.001) * np.exp(-i * 0.0001)
        return result

    # Vectorized version
    def vector_version():
        x = torch.arange(size, dtype=torch.float32)
        return (torch.sin(x * 0.001) * torch.exp(-x * 0.0001)).sum()

    # NumPy vectorized
    def numpy_version():
        x = np.arange(size, dtype=np.float32)
        return (np.sin(x * 0.001) * np.exp(-x * 0.0001)).sum()

    # Time loop (sample only)
    start = time.time()
    loop_result = loop_version()
    loop_time = time.time() - start

    # Time vectorized
    start = time.time()
    vector_result = vector_version()
    vector_time = time.time() - start

    # Time numpy
    start = time.time()
    numpy_result = numpy_version()
    numpy_time = time.time() - start

    print(f"  Loop version: {loop_time*1000:.2f} ms")
    print(f"  NumPy vectorized: {numpy_time*1000:.2f} ms")
    print(f"  PyTorch vectorized: {vector_time*1000:.2f} ms")
    print(f"  Speedup over loop: {loop_time/vector_time:.2f}x")

    # 4. Check actual simulator operations
    print("\n4. SIMULATOR OPERATION BREAKDOWN")
    print("-" * 50)

    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=[5, 5, 5], default_F=100.0
    )

    detector_config = DetectorConfig(
        spixels=256, fpixels=256,
        pixel_size_mm=0.1, distance_mm=100.0
    )

    beam_config = BeamConfig(wavelength_A=6.2)

    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)

    # Get shapes for analysis
    pixel_coords = detector.get_pixel_coords()
    S, F, _ = pixel_coords.shape
    print(f"  Pixels: {S}x{F} = {S*F:,}")

    # The issue: We're doing operations on EVERY pixel
    print(f"\n  Operations per pixel:")
    print(f"    - 3 dot products (for h,k,l)")
    print(f"    - 3 sincg calls (with sin operations)")
    print(f"    - Multiple tensor operations")

    total_ops = S * F * 3 * 2  # Simplified estimate
    print(f"  Estimated operations: {total_ops:,}")

    # 5. The REAL issue: Python overhead
    print("\n5. KEY INSIGHTS")
    print("-" * 50)
    print("WHY C is faster:")
    print("  1. OpenMP parallelization across pixels")
    print("  2. Direct memory access without tensor overhead")
    print("  3. Compiled loop with minimal function calls")
    print("  4. No Python interpreter overhead")
    print("  5. Cache-friendly memory access patterns")

    print("\nWHY PyTorch is slower (on CPU):")
    print("  1. Python function call overhead")
    print("  2. Tensor creation and management overhead")
    print("  3. Generic BLAS operations not optimized for this specific pattern")
    print("  4. Broadcasting creates intermediate tensors")
    print("  5. float64 by default (2x memory bandwidth)")

    print("\nPOTENTIAL OPTIMIZATIONS:")
    print("  1. Use torch.compile() (PyTorch 2.0+)")
    print("  2. Switch to float32 throughout")
    print("  3. Fuse operations to reduce intermediates")
    print("  4. Use torch.jit.script for hot paths")
    print("  5. GPU would completely change the picture")

    # 6. Test torch.compile if available
    print("\n6. TORCH.COMPILE TEST")
    print("-" * 50)

    if hasattr(torch, 'compile'):
        print("torch.compile is available!")

        # Create a simple test function
        def compute_intensity(pixel_coords, a, b, c):
            # Simplified version of the core computation
            h = (pixel_coords * a.unsqueeze(0).unsqueeze(0)).sum(dim=-1)
            k = (pixel_coords * b.unsqueeze(0).unsqueeze(0)).sum(dim=-1)
            l = (pixel_coords * c.unsqueeze(0).unsqueeze(0)).sum(dim=-1)
            return h + k + l

        # Compile it
        compiled_fn = torch.compile(compute_intensity)

        test_coords = torch.randn(256, 256, 3)
        test_a = torch.randn(3)
        test_b = torch.randn(3)
        test_c = torch.randn(3)

        # Warm-up
        _ = compute_intensity(test_coords, test_a, test_b, test_c)
        _ = compiled_fn(test_coords, test_a, test_b, test_c)

        # Time original
        start = time.time()
        for _ in range(100):
            _ = compute_intensity(test_coords, test_a, test_b, test_c)
        original_time = (time.time() - start) / 100

        # Time compiled
        start = time.time()
        for _ in range(100):
            _ = compiled_fn(test_coords, test_a, test_b, test_c)
        compiled_time = (time.time() - start) / 100

        print(f"  Original: {original_time*1000:.2f} ms")
        print(f"  Compiled: {compiled_time*1000:.2f} ms")
        print(f"  Speedup: {original_time/compiled_time:.2f}x")
    else:
        print("torch.compile not available in this PyTorch version")

if __name__ == "__main__":
    analyze_bottlenecks()