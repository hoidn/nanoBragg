#!/usr/bin/env python3
"""
Microbenchmark for rotated-vector regeneration cost (PERF-PYTORCH-004 Phase C9).

Measures the cost of Crystal.get_rotated_real_vectors() calls under 4096² benchmark config.
Results inform whether caching rotated vectors (Plan D6) is justified.
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

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal

def profile_rotated_vectors(device='cpu', dtype=torch.float32, phi_steps=1, mosaic_domains=1):
    """Profile get_rotated_real_vectors call costs."""

    # Create crystal with 4096² benchmark config parameters
    config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        phi_start_deg=0.0,
        osc_range_deg=0.0,
        phi_steps=phi_steps,
        mosaic_spread_deg=0.0,
        mosaic_domains=mosaic_domains,
        default_F=100.0,
        spindle_axis=(0.0, -1.0, 0.0)
    )

    crystal = Crystal(config, device=device, dtype=dtype)

    # Warm-up run
    for _ in range(3):
        _ = crystal.get_rotated_real_vectors(config)

    # Timed runs
    num_iterations = 100
    times = []

    for _ in range(num_iterations):
        start = time.perf_counter()
        vectors = crystal.get_rotated_real_vectors(config)
        end = time.perf_counter()
        times.append(end - start)

    times_ms = [t * 1000 for t in times]
    mean_ms = sum(times_ms) / len(times_ms)
    min_ms = min(times_ms)
    max_ms = max(times_ms)
    std_ms = (sum((t - mean_ms)**2 for t in times_ms) / len(times_ms)) ** 0.5

    # vectors is a tuple of (a, b, c) tensors
    vector_shapes = [tuple(v.shape) if hasattr(v, 'shape') else str(v) for v in vectors]

    return {
        'mean_ms': mean_ms,
        'min_ms': min_ms,
        'max_ms': max_ms,
        'std_ms': std_ms,
        'iterations': num_iterations,
        'phi_steps': phi_steps,
        'mosaic_domains': mosaic_domains,
        'device': str(device),
        'dtype': str(dtype),
        'vector_shapes': vector_shapes
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Profile rotated vector regeneration cost')
    parser.add_argument('--device', default='cpu', choices=['cpu', 'cuda'], help='Device to run on')
    parser.add_argument('--dtype', default='float32', choices=['float32', 'float64'], help='Precision')
    parser.add_argument('--phi-steps', type=int, default=1, help='Number of phi steps')
    parser.add_argument('--mosaic-domains', type=int, default=1, help='Number of mosaic domains')
    parser.add_argument('--outdir', type=str, default=None, help='Output directory')

    args = parser.parse_args()

    dtype = torch.float32 if args.dtype == 'float32' else torch.float64

    if args.device == 'cuda' and not torch.cuda.is_available():
        print("ERROR: CUDA requested but not available", file=sys.stderr)
        sys.exit(1)

    print(f"Profiling rotated vector regeneration...")
    print(f"Device: {args.device}, Dtype: {args.dtype}")
    print(f"phi_steps: {args.phi_steps}, mosaic_domains: {args.mosaic_domains}")
    print()

    results = profile_rotated_vectors(
        device=args.device,
        dtype=dtype,
        phi_steps=args.phi_steps,
        mosaic_domains=args.mosaic_domains
    )

    # Print results
    print("Results:")
    print(f"  Mean time:   {results['mean_ms']:.6f} ms")
    print(f"  Std dev:     {results['std_ms']:.6f} ms")
    print(f"  Min time:    {results['min_ms']:.6f} ms")
    print(f"  Max time:    {results['max_ms']:.6f} ms")
    print(f"  Iterations:  {results['iterations']}")
    print(f"  Vector shapes: {results['vector_shapes']}")

    # Estimate cost for 4096² simulation
    # For 4096² detector at 4096² oversample=1, we have phi_steps × mosaic_domains calls
    total_calls = args.phi_steps * args.mosaic_domains
    estimated_total_ms = results['mean_ms'] * total_calls
    print(f"\nEstimated total cost for {args.phi_steps} phi × {args.mosaic_domains} mosaic: {estimated_total_ms:.3f} ms")

    # Save results
    if args.outdir:
        outdir = Path(args.outdir)
    else:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        outdir = Path('reports/profiling') / f'{timestamp}-rotated-vector-cost'

    outdir.mkdir(parents=True, exist_ok=True)

    # Write JSON results
    import json
    with open(outdir / 'timings.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Write markdown summary
    with open(outdir / 'C9_diagnostic_summary.md', 'w') as f:
        f.write(f"# Phase C9: Rotated Vector Regeneration Cost\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Configuration\n")
        f.write(f"- Device: {results['device']}\n")
        f.write(f"- Dtype: {results['dtype']}\n")
        f.write(f"- phi_steps: {results['phi_steps']}\n")
        f.write(f"- mosaic_domains: {results['mosaic_domains']}\n")
        f.write(f"- Crystal: 100Å cubic, N=(5,5,5)\n\n")
        f.write(f"## Results\n")
        f.write(f"- **Mean time per call:** {results['mean_ms']:.6f} ms\n")
        f.write(f"- **Std deviation:** {results['std_ms']:.6f} ms\n")
        f.write(f"- **Min/Max:** {results['min_ms']:.6f} / {results['max_ms']:.6f} ms\n")
        f.write(f"- **Iterations:** {results['iterations']}\n")
        f.write(f"- **Vector shapes:** {results['vector_shapes']}\n\n")
        f.write(f"## Cost Estimate for 4096² Simulation\n")
        f.write(f"- Total calls: {args.phi_steps} phi × {args.mosaic_domains} mosaic = {total_calls}\n")
        f.write(f"- **Estimated total cost:** {estimated_total_ms:.3f} ms\n\n")

        # Interpret results relative to target warm time (~600ms)
        target_warm_ms = 600.0
        percentage = (estimated_total_ms / target_warm_ms) * 100
        f.write(f"## Analysis\n")
        f.write(f"For 4096² detector with baseline config (phi_steps={args.phi_steps}, mosaic={args.mosaic_domains}):\n")
        f.write(f"- Rotated vector regeneration: ~{estimated_total_ms:.1f} ms ({percentage:.1f}% of {target_warm_ms:.0f}ms target)\n\n")

        if percentage < 5:
            f.write(f"**Recommendation:** Rotated vector regeneration is NOT a significant bottleneck (<5% of warm time). ")
            f.write(f"Caching (Plan D6) would provide minimal ROI (~{estimated_total_ms:.1f}ms savings).\n")
        elif percentage < 10:
            f.write(f"**Recommendation:** Minor bottleneck (5-10% of warm time). ")
            f.write(f"Caching (Plan D6) is OPTIONAL - consider only if other optimizations are exhausted.\n")
        else:
            f.write(f"**Recommendation:** Significant bottleneck (>10% of warm time). ")
            f.write(f"Caching (Plan D6) is JUSTIFIED and should improve warm speedup by ~{percentage:.1f}%.\n")

    print(f"\nResults saved to: {outdir}")
    print(f"  - timings.json")
    print(f"  - C9_diagnostic_summary.md")

if __name__ == '__main__':
    main()
