#!/usr/bin/env python3
"""
Microbenchmark for mosaic rotation RNG cost (PERF-PYTORCH-004 Phase C10).

Measures the cost of _generate_mosaic_rotations() calls under 4096² benchmark config.
Results inform whether caching mosaic rotation matrices (Plan D7) is justified.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import torch
import time
from pathlib import Path
from datetime import datetime

# Ensure module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import CrystalConfig

def profile_mosaic_rotations(device='cpu', dtype=torch.float32, mosaic_domains=10, mosaic_spread_deg=1.0):
    """Profile _generate_mosaic_rotations call costs."""

    # Create config and crystal instance
    config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        mosaic_domains=mosaic_domains,
        mosaic_spread_deg=mosaic_spread_deg,
        default_F=100.0
    )

    crystal = Crystal(config, device=device, dtype=dtype)

    # Warm-up run
    for _ in range(3):
        _ = crystal._generate_mosaic_rotations(config)

    # Timed runs
    num_iterations = 100
    times = []

    for _ in range(num_iterations):
        start = time.perf_counter()
        matrices = crystal._generate_mosaic_rotations(config)
        end = time.perf_counter()
        times.append(end - start)

    times_ms = [t * 1000 for t in times]
    mean_ms = sum(times_ms) / len(times_ms)
    min_ms = min(times_ms)
    max_ms = max(times_ms)
    std_ms = (sum((t - mean_ms)**2 for t in times_ms) / len(times_ms)) ** 0.5

    return {
        'mean_ms': mean_ms,
        'min_ms': min_ms,
        'max_ms': max_ms,
        'std_ms': std_ms,
        'iterations': num_iterations,
        'mosaic_domains': mosaic_domains,
        'mosaic_spread_deg': mosaic_spread_deg,
        'device': str(device),
        'dtype': str(dtype),
        'matrix_shape': tuple(matrices.shape) if hasattr(matrices, 'shape') else str(type(matrices))
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Profile mosaic rotation RNG cost')
    parser.add_argument('--device', default='cpu', choices=['cpu', 'cuda'], help='Device to run on')
    parser.add_argument('--dtype', default='float32', choices=['float32', 'float64'], help='Precision')
    parser.add_argument('--mosaic-domains', type=int, default=10, help='Number of mosaic domains')
    parser.add_argument('--mosaic-spread', type=float, default=1.0, help='Mosaic spread in degrees')
    parser.add_argument('--outdir', type=str, default=None, help='Output directory')

    args = parser.parse_args()

    dtype = torch.float32 if args.dtype == 'float32' else torch.float64

    if args.device == 'cuda' and not torch.cuda.is_available():
        print("ERROR: CUDA requested but not available", file=sys.stderr)
        sys.exit(1)

    print(f"Profiling mosaic rotation RNG...")
    print(f"Device: {args.device}, Dtype: {args.dtype}")
    print(f"mosaic_domains: {args.mosaic_domains}, mosaic_spread: {args.mosaic_spread}°")
    print()

    results = profile_mosaic_rotations(
        device=args.device,
        dtype=dtype,
        mosaic_domains=args.mosaic_domains,
        mosaic_spread_deg=args.mosaic_spread
    )

    # Print results
    print("Results:")
    print(f"  Mean time:   {results['mean_ms']:.6f} ms")
    print(f"  Std dev:     {results['std_ms']:.6f} ms")
    print(f"  Min time:    {results['min_ms']:.6f} ms")
    print(f"  Max time:    {results['max_ms']:.6f} ms")
    print(f"  Iterations:  {results['iterations']}")
    print(f"  Matrix shape: {results['matrix_shape']}")

    # Estimate cost for 4096² simulation
    # For 4096² detector, mosaic rotation matrices are generated once per run
    # (they're used across all pixels)
    estimated_total_ms = results['mean_ms']
    print(f"\nEstimated total cost per simulation run: {estimated_total_ms:.3f} ms")

    # Save results
    if args.outdir:
        outdir = Path(args.outdir)
    else:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        outdir = Path('reports/profiling') / f'{timestamp}-mosaic-rotation-cost'

    outdir.mkdir(parents=True, exist_ok=True)

    # Write JSON results
    import json
    with open(outdir / 'timings.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Write markdown summary
    with open(outdir / 'C10_diagnostic_summary.md', 'w') as f:
        f.write(f"# Phase C10: Mosaic Rotation RNG Cost\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Configuration\n")
        f.write(f"- Device: {results['device']}\n")
        f.write(f"- Dtype: {results['dtype']}\n")
        f.write(f"- mosaic_domains: {results['mosaic_domains']}\n")
        f.write(f"- mosaic_spread: {results['mosaic_spread_deg']}°\n")
        f.write(f"- Crystal: 100Å cubic (standard benchmark params)\n\n")
        f.write(f"## Results\n")
        f.write(f"- **Mean time per call:** {results['mean_ms']:.6f} ms\n")
        f.write(f"- **Std deviation:** {results['std_ms']:.6f} ms\n")
        f.write(f"- **Min/Max:** {results['min_ms']:.6f} / {results['max_ms']:.6f} ms\n")
        f.write(f"- **Iterations:** {results['iterations']}\n")
        f.write(f"- **Matrix shape:** {results['matrix_shape']}\n\n")
        f.write(f"## Cost Estimate for 4096² Simulation\n")
        f.write(f"- Mosaic rotations generated once per run\n")
        f.write(f"- **Estimated total cost:** {estimated_total_ms:.3f} ms\n\n")

        # Interpret results relative to target warm time (~600ms)
        target_warm_ms = 600.0
        percentage = (estimated_total_ms / target_warm_ms) * 100
        f.write(f"## Analysis\n")
        f.write(f"For 4096² detector with {args.mosaic_domains} mosaic domains:\n")
        f.write(f"- Mosaic rotation RNG: ~{estimated_total_ms:.1f} ms ({percentage:.1f}% of {target_warm_ms:.0f}ms target)\n\n")

        if percentage < 5:
            f.write(f"**Recommendation:** Mosaic rotation RNG is NOT a significant bottleneck (<5% of warm time). ")
            f.write(f"Caching (Plan D7) would provide minimal ROI (~{estimated_total_ms:.1f}ms savings).\n")
        elif percentage < 10:
            f.write(f"**Recommendation:** Minor bottleneck (5-10% of warm time). ")
            f.write(f"Caching (Plan D7) is OPTIONAL - consider only if other optimizations are exhausted.\n")
        else:
            f.write(f"**Recommendation:** Significant bottleneck (>10% of warm time). ")
            f.write(f"Caching (Plan D7) is JUSTIFIED and should improve warm speedup by ~{percentage:.1f}%.\n")

    print(f"\nResults saved to: {outdir}")
    print(f"  - timings.json")
    print(f"  - C10_diagnostic_summary.md")

if __name__ == '__main__':
    main()
