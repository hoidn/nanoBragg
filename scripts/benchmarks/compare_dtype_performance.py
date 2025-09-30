#!/usr/bin/env python3
"""
Compare FP32 vs FP64 performance to quantify precision impact.

Follows nanoBragg tooling standards.
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np

from nanobrag_torch.config import (
    CrystalConfig, DetectorConfig, BeamConfig,
    CrystalShape, DetectorConvention
)
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def benchmark_dtype(detpixels, dtype, device='cuda', n_runs=3):
    """Run simulation with specified dtype and measure performance."""
    device_obj = torch.device(device)

    # Setup configs
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=[5, 5, 5],
        default_F=100.0,
        shape=CrystalShape.SQUARE
    )

    detector_config = DetectorConfig(
        spixels=detpixels,
        fpixels=detpixels,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        oversample=1
    )

    beam_config = BeamConfig(wavelength_A=6.2)

    # Create models with specified dtype
    crystal = Crystal(crystal_config, device=device_obj, dtype=dtype)
    detector = Detector(detector_config, device=device_obj, dtype=dtype)
    simulator = Simulator(crystal, detector, crystal_config, beam_config, device=device_obj, dtype=dtype)

    # Warm-up run
    _ = simulator.run()
    if device_obj.type == 'cuda':
        torch.cuda.synchronize()

    # Timed runs
    times = []
    for _ in range(n_runs):
        start = time.time()
        image = simulator.run()
        if device_obj.type == 'cuda':
            torch.cuda.synchronize()
        elapsed = time.time() - start
        times.append(elapsed)

    return {
        'dtype': str(dtype),
        'mean_time': np.mean(times),
        'std_time': np.std(times),
        'min_time': np.min(times),
        'image': image
    }


def main():
    if not torch.cuda.is_available():
        print("ERROR: CUDA not available. This benchmark requires GPU.")
        sys.exit(1)

    print("=" * 80)
    print("FP32 vs FP64 Performance Comparison")
    print("=" * 80)
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_dir = Path('reports/benchmarks') / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    test_size = 1024
    print(f"\nDetector size: {test_size}x{test_size}")

    # Benchmark FP64
    print("\nRunning FP64 (float64) benchmark...")
    fp64_results = benchmark_dtype(test_size, torch.float64, device='cuda')
    print(f"  Mean time: {fp64_results['mean_time']:.3f}s ± {fp64_results['std_time']:.3f}s")

    # Benchmark FP32
    print("\nRunning FP32 (float32) benchmark...")
    fp32_results = benchmark_dtype(test_size, torch.float32, device='cuda')
    print(f"  Mean time: {fp32_results['mean_time']:.3f}s ± {fp32_results['std_time']:.3f}s")

    # Compute speedup
    speedup = fp64_results['mean_time'] / fp32_results['mean_time']

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"FP64 time: {fp64_results['mean_time']:.3f}s")
    print(f"FP32 time: {fp32_results['mean_time']:.3f}s")
    print(f"Speedup: {speedup:.2f}x (FP32 is {speedup:.2f}x faster)")

    # Check numerical agreement
    fp64_image = fp64_results['image'].cpu().numpy()
    fp32_image = fp32_results['image'].cpu().numpy()

    # Compute correlation
    correlation = np.corrcoef(fp64_image.flatten(), fp32_image.flatten())[0, 1]

    # Compute relative error
    rel_error = np.abs(fp64_image - fp32_image) / (fp64_image + 1e-10)
    mean_rel_error = np.mean(rel_error)
    max_rel_error = np.max(rel_error)

    print(f"\nNumerical Agreement:")
    print(f"  Correlation: {correlation:.6f}")
    print(f"  Mean relative error: {mean_rel_error:.6f}")
    print(f"  Max relative error: {max_rel_error:.6f}")

    # Save results
    results = {
        'test_size': test_size,
        'fp64_time': fp64_results['mean_time'],
        'fp32_time': fp32_results['mean_time'],
        'speedup': speedup,
        'correlation': float(correlation),
        'mean_rel_error': float(mean_rel_error),
        'max_rel_error': float(max_rel_error),
    }

    import json
    results_file = output_dir / 'dtype_comparison.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()