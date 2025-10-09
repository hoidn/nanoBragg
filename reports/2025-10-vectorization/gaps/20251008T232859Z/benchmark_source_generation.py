#!/usr/bin/env python3
"""
Benchmark source generation after vectorization.

This script measures the performance of generate_sources_from_divergence_dispersion
to verify the vectorization speedup for PERF-PYTORCH-004.
"""

import time
import torch
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.utils.auto_selection import (
    SamplingParams,
    generate_sources_from_divergence_dispersion,
)


def benchmark_source_generation():
    """Benchmark the vectorized source generation."""

    # Test case from input.md: 25×25 divergence grid × 9 dispersion points
    hdiv_params = SamplingParams(count=25, range=2.0, step=2.0/24)
    vdiv_params = SamplingParams(count=25, range=2.0, step=2.0/24)
    disp_params = SamplingParams(count=9, range=0.1, step=0.1/8)

    central_wavelength_m = 1e-10  # 1 Angstrom

    # Warmup
    for _ in range(3):
        directions, weights, wavelengths = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=central_wavelength_m,
            round_div=True,
        )

    # Benchmark
    n_iterations = 100
    start_time = time.perf_counter()

    for _ in range(n_iterations):
        directions, weights, wavelengths = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=central_wavelength_m,
            round_div=True,
        )

    end_time = time.perf_counter()
    elapsed = end_time - start_time
    avg_time_ms = (elapsed / n_iterations) * 1000

    print(f"Vectorized Source Generation Benchmark")
    print(f"=" * 50)
    print(f"Configuration: {hdiv_params.count}×{vdiv_params.count} divergence, {disp_params.count} dispersion")
    print(f"Total sources generated: {len(directions)}")
    print(f"Iterations: {n_iterations}")
    print(f"Total time: {elapsed:.3f} s")
    print(f"Average time per call: {avg_time_ms:.3f} ms")
    print(f"Throughput: {n_iterations/elapsed:.1f} calls/sec")
    print()
    print(f"Results:")
    print(f"  Directions shape: {directions.shape}")
    print(f"  Weights shape: {weights.shape}")
    print(f"  Wavelengths shape: {wavelengths.shape}")

    # Store results
    results = {
        "avg_time_ms": avg_time_ms,
        "n_sources": len(directions),
        "n_iterations": n_iterations,
        "total_time_s": elapsed,
    }

    return results


if __name__ == "__main__":
    results = benchmark_source_generation()

    # Target: should be << 120ms (the old baseline from input.md)
    baseline_ms = 120.0
    speedup = baseline_ms / results['avg_time_ms']

    print()
    print(f"Performance vs baseline ({baseline_ms} ms):")
    print(f"  Speedup: {speedup:.1f}×")

    if speedup >= 10:
        print(f"  ✅ Target achieved (≥10× speedup)")
    else:
        print(f"  ⚠️  Below target (need ≥10×, got {speedup:.1f}×)")
