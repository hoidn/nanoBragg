#!/usr/bin/env python3
"""Investigate torch.compile cross-instance caching behavior.

This script tests whether torch.compile automatically reuses compiled kernels
across different simulator instances when calling the same pure function.

PERF-PYTORCH-004 Phase 2 prerequisite investigation.
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import torch

# Set required environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from nanobrag_torch.simulator import Simulator, compute_physics_for_position
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, CrystalShape
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector


def benchmark_compile_times(n_instances=10, size=256, device='cpu', dtype=torch.float64, n_sources=1):
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
        n_sources: Number of X-ray sources (1 or 3 for multi-source testing)
    """
    print("=" * 80)
    print("torch.compile Cross-Instance Caching Investigation")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Instances: {n_instances}")
    print(f"  Detector size: {size}x{size}")
    print(f"  Device: {device}")
    print(f"  Dtype: {dtype}")
    print(f"  Sources: {n_sources}")
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

    # Configure beam with multiple sources if requested
    if n_sources == 1:
        beam_config = BeamConfig(
            wavelength_A=6.2
        )
    else:
        # Create multiple source directions for vectorization testing
        source_directions = torch.tensor([
            [0.0, 0.0, 1.0],  # Primary beam along +Z
            [0.01, 0.0, 0.9999],  # Slightly off-axis
            [0.0, 0.01, 0.9999]   # Another off-axis
        ][:n_sources], device=device, dtype=dtype)

        # source_wavelengths needs to be in meters, not Angstroms
        wavelengths_m = torch.tensor([6.2e-10] * n_sources, device=device, dtype=dtype)
        weights = torch.ones(n_sources, device=device, dtype=dtype) / n_sources

        beam_config = BeamConfig(
            source_directions=source_directions,
            source_weights=weights,
            source_wavelengths=wavelengths_m
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

    # Calculate cache speedup for JSON output
    cache_speedup = None
    if len(first_run_times) > 1:
        cache_speedup = first_run_times[0] / (sum(first_run_times[1:]) / len(first_run_times[1:]))

    # Return results for further analysis
    return {
        'construction_times': construction_times,
        'first_run_times': first_run_times,
        'second_run_times': second_run_times,
        'cache_speedup': cache_speedup,
        'config': {
            'n_instances': n_instances,
            'size': size,
            'device': device,
            'dtype': str(dtype),
            'n_sources': n_sources
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

    parser = argparse.ArgumentParser(
        description='Investigate torch.compile caching across devices, dtypes, and source counts (PERF-PYTORCH-004 Phase 2)'
    )
    parser.add_argument('--instances', type=int, default=5, help='Number of instances')
    parser.add_argument('--size', type=int, default=128, help='Detector size')
    parser.add_argument('--devices', type=str, default='cpu', help='Comma-separated list of devices (cpu,cuda)')
    parser.add_argument('--dtypes', type=str, default='float64', help='Comma-separated list of dtypes (float32,float64)')
    parser.add_argument('--sources', type=str, default='1', help='Comma-separated list of source counts (1,3)')
    parser.add_argument('--outdir', type=str, default=None, help='Output directory (default: reports/benchmarks/<timestamp>-compile-cache)')

    args = parser.parse_args()

    # Parse comma-separated lists
    devices = [d.strip() for d in args.devices.split(',')]
    dtypes_str = [d.strip() for d in args.dtypes.split(',')]
    source_counts = [int(s.strip()) for s in args.sources.split(',')]

    # Convert dtype strings to torch dtypes
    dtype_map = {
        'float32': torch.float32,
        'float64': torch.float64
    }
    dtypes = [dtype_map[d] for d in dtypes_str]

    # Setup output directory
    if args.outdir is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        outdir = Path(__file__).parent.parent.parent / 'reports' / 'benchmarks' / f'{timestamp}-compile-cache'
    else:
        outdir = Path(args.outdir)

    outdir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {outdir}")

    # Collect all results
    all_results = []

    # Run pure function test first (single time, on CPU float64)
    print("\n" + "=" * 80)
    print("Running pure function caching test...")
    print("=" * 80)
    test_pure_function_caching()

    # Run benchmarks for all combinations
    total_runs = len(devices) * len(dtypes) * len(source_counts)
    run_num = 0

    for device in devices:
        # Check device availability
        if device == 'cuda' and not torch.cuda.is_available():
            print(f"\nWARNING: CUDA requested but not available, skipping CUDA tests")
            continue

        for dtype, dtype_str in zip(dtypes, dtypes_str):
            for n_sources in source_counts:
                run_num += 1
                print(f"\n\n{'=' * 80}")
                print(f"Run {run_num}/{total_runs}: device={device}, dtype={dtype_str}, sources={n_sources}")
                print('=' * 80)

                # Run benchmark
                results = benchmark_compile_times(
                    n_instances=args.instances,
                    size=args.size,
                    device=device,
                    dtype=dtype,
                    n_sources=n_sources
                )

                # Add metadata
                results['run_metadata'] = {
                    'timestamp': datetime.now().isoformat(),
                    'pytorch_version': torch.__version__,
                    'cuda_available': torch.cuda.is_available()
                }

                all_results.append(results)

    # Write JSON summary
    summary_file = outdir / 'cache_validation_summary.json'
    with open(summary_file, 'w') as f:
        json.dump({
            'all_runs': all_results,
            'summary': {
                'total_configurations': len(all_results),
                'min_cache_speedup': min([r['cache_speedup'] for r in all_results if r['cache_speedup'] is not None], default=None),
                'max_cache_speedup': max([r['cache_speedup'] for r in all_results if r['cache_speedup'] is not None], default=None),
                'mean_cache_speedup': sum([r['cache_speedup'] for r in all_results if r['cache_speedup'] is not None]) / len([r for r in all_results if r['cache_speedup'] is not None]) if len([r for r in all_results if r['cache_speedup'] is not None]) > 0 else None
            }
        }, f, indent=2)

    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal configurations tested: {len(all_results)}")
    if len(all_results) > 0:
        speedups = [r['cache_speedup'] for r in all_results if r['cache_speedup'] is not None]
        if speedups:
            print(f"Cache speedup range: {min(speedups):.2f}x - {max(speedups):.2f}x")
            print(f"Mean cache speedup: {sum(speedups)/len(speedups):.2f}x")

            if min(speedups) >= 50.0:
                print("\n✅ ALL configurations exceed 50x cache speedup threshold")
            elif min(speedups) >= 2.0:
                print(f"\n⚠️  Some configurations below 50x threshold (min: {min(speedups):.2f}x)")
            else:
                print(f"\n❌ Cache not effective (min: {min(speedups):.2f}x)")

    print(f"\nResults written to: {summary_file}")

    print("\n" + "=" * 80)
    print("Investigation Complete")
    print("=" * 80)
