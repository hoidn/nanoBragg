#!/usr/bin/env python3
"""Investigate torch.compile cross-instance caching behavior.

This script tests whether torch.compile automatically reuses compiled kernels
across different simulator instances when calling the same pure function.

PERF-PYTORCH-004 Phase 2 prerequisite investigation.
"""

import os
import sys
import time
import torch

# Set required environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from nanobrag_torch.simulator import Simulator, compute_physics_for_position
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, CrystalShape
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector


def benchmark_compile_times(n_instances=10, size=256, device='cpu', dtype=torch.float64):
    """Benchmark compilation times across multiple simulator instances.

    Tests:
    1. Are compile times decreasing after first instance?
    2. Does torch.compile cache compiled kernels across instances?
    3. What is the speedup from warm cache vs cold?

    Args:
        n_instances: Number of simulator instances to create
        size: Detector size (square)
        device: Device to run on ('cpu' or 'cuda')
        dtype: Data type for tensors
    """
    print("=" * 80)
    print("torch.compile Cross-Instance Caching Investigation")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Instances: {n_instances}")
    print(f"  Detector size: {size}x{size}")
    print(f"  Device: {device}")
    print(f"  Dtype: {dtype}")
    print(f"  PyTorch version: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")

    # Common configuration for all instances
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
        mosaic_domains=1,
        phi_steps=1
    )

    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=size,
        fpixels=size
    )

    beam_config = BeamConfig(
        wavelength_A=6.2
    )

    construction_times = []
    first_run_times = []
    second_run_times = []

    print("\n" + "=" * 80)
    print("Creating and running simulators...")
    print("=" * 80)

    for i in range(n_instances):
        print(f"\nInstance {i+1}/{n_instances}:")

        # Measure construction time (includes Crystal and Detector creation)
        t0 = time.perf_counter()

        # Create Crystal and Detector objects
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)

        # Create Simulator
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            beam_config=beam_config,
            device=device,
            dtype=dtype
        )
        t_construct = time.perf_counter() - t0
        construction_times.append(t_construct)
        print(f"  Construction: {t_construct*1000:.2f} ms")

        # Measure first run (includes compilation)
        t0 = time.perf_counter()
        image1 = simulator.run()
        t_first = time.perf_counter() - t0
        first_run_times.append(t_first)
        print(f"  First run: {t_first*1000:.2f} ms")

        # Measure second run (should be warm)
        t0 = time.perf_counter()
        image2 = simulator.run()
        t_second = time.perf_counter() - t0
        second_run_times.append(t_second)
        print(f"  Second run: {t_second*1000:.2f} ms")
        print(f"  Speedup (first→second): {t_first/t_second:.2f}x")

        # Verify correctness
        assert torch.allclose(image1, image2, rtol=1e-10), "Runs should be identical!"

        # Clean up to avoid memory buildup
        del simulator, image1, image2
        if device == 'cuda':
            torch.cuda.empty_cache()

    # Analysis
    print("\n" + "=" * 80)
    print("Analysis")
    print("=" * 80)

    print("\n1. Construction times:")
    print(f"   First: {construction_times[0]*1000:.2f} ms")
    if len(construction_times) > 1:
        print(f"   Mean (2-{n_instances}): {sum(construction_times[1:])/len(construction_times[1:])*1000:.2f} ms")
        print(f"   Reduction: {construction_times[0]/construction_times[-1]:.2f}x")

    print("\n2. First run times (includes compilation):")
    print(f"   First: {first_run_times[0]*1000:.2f} ms")
    if len(first_run_times) > 1:
        print(f"   Mean (2-{n_instances}): {sum(first_run_times[1:])/len(first_run_times[1:])*1000:.2f} ms")
        reduction = first_run_times[0] / first_run_times[-1] if first_run_times[-1] > 0 else float('inf')
        print(f"   Speedup: {reduction:.2f}x")

    print("\n3. Second run times (warm):")
    print(f"   First: {second_run_times[0]*1000:.2f} ms")
    if len(second_run_times) > 1:
        print(f"   Mean (2-{n_instances}): {sum(second_run_times[1:])/len(second_run_times[1:])*1000:.2f} ms")

    # Key metric: Does torch.compile cache work across instances?
    if len(first_run_times) > 1:
        print("\n" + "=" * 80)
        print("KEY FINDING: Cross-Instance Caching")
        print("=" * 80)

        cache_speedup = first_run_times[0] / (sum(first_run_times[1:]) / len(first_run_times[1:]))

        if cache_speedup > 2.0:
            print(f"✅ torch.compile DOES cache across instances!")
            print(f"   Speedup: {cache_speedup:.2f}x (instances 2-{n_instances} vs instance 1)")
            print(f"\n   CONCLUSION: Phase 2-4 (explicit cache) may be UNNECESSARY.")
            print(f"   torch.compile's internal cache is already working effectively.")
        elif cache_speedup > 1.2:
            print(f"⚠️  torch.compile provides PARTIAL cross-instance caching.")
            print(f"   Speedup: {cache_speedup:.2f}x (instances 2-{n_instances} vs instance 1)")
            print(f"\n   CONCLUSION: Investigate further. May benefit from explicit cache.")
        else:
            print(f"❌ torch.compile does NOT cache effectively across instances.")
            print(f"   Speedup: {cache_speedup:.2f}x (instances 2-{n_instances} vs instance 1)")
            print(f"\n   CONCLUSION: Phase 2-4 (explicit cache) IS NECESSARY.")
            print(f"   torch.compile recompiles for each new instance.")

    # Return results for further analysis
    return {
        'construction_times': construction_times,
        'first_run_times': first_run_times,
        'second_run_times': second_run_times,
        'config': {
            'n_instances': n_instances,
            'size': size,
            'device': device,
            'dtype': str(dtype)
        }
    }


def test_pure_function_caching():
    """Test if pure function caching works at the function level.

    This isolates the torch.compile behavior from the Simulator class.
    """
    print("\n" + "=" * 80)
    print("Pure Function Caching Test")
    print("=" * 80)

    # Create a simple pure function
    @torch.compile
    def simple_pure_function(x, y):
        return x @ y + torch.sin(x)

    # Test across multiple "instances" (different input tensors of same shape)
    device = 'cpu'
    dtype = torch.float64

    times = []
    for i in range(5):
        # Create fresh inputs each time
        x = torch.randn(100, 100, device=device, dtype=dtype)
        y = torch.randn(100, 100, device=device, dtype=dtype)

        t0 = time.perf_counter()
        result = simple_pure_function(x, y)
        t = time.perf_counter() - t0
        times.append(t)

        print(f"Call {i+1}: {t*1000:.2f} ms")

    print(f"\nFirst call: {times[0]*1000:.2f} ms")
    print(f"Mean (2-5): {sum(times[1:])/len(times[1:])*1000:.2f} ms")
    print(f"Speedup: {times[0]/times[-1]:.2f}x")

    if times[0] / times[-1] > 2.0:
        print("✅ Pure function caching WORKS")
    else:
        print("❌ Pure function caching DOES NOT WORK as expected")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Investigate torch.compile caching')
    parser.add_argument('--instances', type=int, default=5, help='Number of instances')
    parser.add_argument('--size', type=int, default=128, help='Detector size')
    parser.add_argument('--device', type=str, default='cpu', choices=['cpu', 'cuda'])
    parser.add_argument('--dtype', type=str, default='float64', choices=['float32', 'float64'])

    args = parser.parse_args()

    dtype = torch.float32 if args.dtype == 'float32' else torch.float64

    # Check device availability
    if args.device == 'cuda' and not torch.cuda.is_available():
        print("WARNING: CUDA requested but not available, falling back to CPU")
        args.device = 'cpu'

    # Run pure function test first
    test_pure_function_caching()

    # Run full simulator test
    results = benchmark_compile_times(
        n_instances=args.instances,
        size=args.size,
        device=args.device,
        dtype=dtype
    )

    print("\n" + "=" * 80)
    print("Investigation Complete")
    print("=" * 80)
