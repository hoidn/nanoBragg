#!/usr/bin/env python3
"""
Detector Absorption Baseline Benchmark

Measures current detector absorption performance with layering to establish
a baseline before Phase F vectorization work.

Follows nanoBragg tooling standards (testing_strategy.md §6):
- Located in scripts/benchmarks/
- Honors KMP_DUPLICATE_LIB_OK environment variable
- Saves outputs to reports/2025-10-vectorization/phase_a/
- Device/dtype neutral (CPU and CUDA support)

References:
- specs/spec-a-core.md (Detector absorption)
- arch.md ADR-09 (Detector Absorption Implementation)
- plans/active/vectorization.md Phase A task A3
- nanoBragg.c lines 3375-3450 (detector absorption loop)
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

# Ensure environment is set per project standards
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import after environment setup
import torch
import numpy as np

# Add src to path if needed
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention, CrystalShape
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator


def benchmark_absorption(size, repeats, device, dtype, thicksteps=5):
    """
    Benchmark detector absorption for a given detector size.

    Args:
        size: Detector size (square detector size x size)
        repeats: Number of timing repeats
        device: torch.device or string ('cpu', 'cuda')
        dtype: torch.dtype (typically float32 or float64)
        thicksteps: Number of detector thickness layers (default: 5)

    Returns:
        dict with timing results and metadata
    """
    device_obj = torch.device(device)

    # Configure detector with absorption enabled
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=size,
        fpixels=size,
        detector_abs_um=500.0,      # 500 μm attenuation depth
        detector_thick_um=100.0,    # 100 μm thickness
        detector_thicksteps=thicksteps,
        detector_convention=DetectorConvention.MOSFLM,
        oversample=1,
        oversample_thick=True  # Use accumulation semantics to exercise all layers
    )

    # Simple crystal config
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
        shape=CrystalShape.SQUARE
    )

    beam_config = BeamConfig(wavelength_A=6.2)

    # Create objects
    detector = Detector(detector_config, device=device_obj, dtype=dtype)
    crystal = Crystal(crystal_config, device=device_obj, dtype=dtype)
    simulator = Simulator(crystal, detector, crystal_config, beam_config, device=device_obj)

    # Warm-up runs (especially important for GPU and torch.compile)
    if device_obj.type == 'cuda':
        for _ in range(3):
            _ = simulator.run()
        torch.cuda.synchronize()

    # Cold timing (first run after warm-up)
    if device_obj.type == 'cuda':
        torch.cuda.synchronize()

    start_cold = time.perf_counter()
    result_cold = simulator.run()

    if device_obj.type == 'cuda':
        torch.cuda.synchronize()

    time_cold = time.perf_counter() - start_cold

    # Warm timings (subsequent runs)
    warm_times = []
    for i in range(repeats):
        if device_obj.type == 'cuda':
            torch.cuda.synchronize()

        start = time.perf_counter()
        result = simulator.run()

        if device_obj.type == 'cuda':
            torch.cuda.synchronize()

        warm_times.append(time.perf_counter() - start)

    # Verify result is non-trivial
    assert result.shape == (size, size), f"Expected shape ({size}, {size}), got {result.shape}"
    assert torch.all(torch.isfinite(result)), "Result contains non-finite values"
    assert torch.sum(result > 0) > 0, "Result is all zeros"

    # Collect results
    results = {
        'size': size,
        'device': str(device_obj),
        'dtype': str(dtype),
        'thicksteps': thicksteps,
        'pixels': size * size,
        'detector_abs_um': float(detector_config.detector_abs_um),
        'detector_thick_um': float(detector_config.detector_thick_um),
        'oversample_thick': detector_config.oversample_thick,
        'cold_time_s': float(time_cold),
        'warm_times_s': [float(t) for t in warm_times],
        'mean_warm_s': float(np.mean(warm_times)),
        'median_warm_s': float(np.median(warm_times)),
        'std_warm_s': float(np.std(warm_times)),
        'min_warm_s': float(np.min(warm_times)),
        'max_warm_s': float(np.max(warm_times)),
        'throughput_pixels_per_sec': float(size * size / np.mean(warm_times)),
        'mean_intensity': float(torch.mean(result).item()),
        'max_intensity': float(torch.max(result).item()),
    }

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark detector absorption baseline performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # CPU baseline with default sizes
  python absorption_baseline.py --sizes 256 512 --repeats 5

  # GPU baseline
  python absorption_baseline.py --sizes 256 512 --device cuda --repeats 10

  # Test different thickness layer counts
  python absorption_baseline.py --sizes 256 --thicksteps 3 5 10 --repeats 5
        """
    )

    parser.add_argument('--sizes', type=int, nargs='+', default=[256, 512],
                        help='Detector sizes to benchmark (default: 256 512)')
    parser.add_argument('--repeats', type=int, default=5,
                        help='Number of warm-run repeats per size (default: 5)')
    parser.add_argument('--device', type=str, default='cpu',
                        choices=['cpu', 'cuda'],
                        help='Device to run on (default: cpu)')
    parser.add_argument('--dtype', type=str, default='float32',
                        choices=['float32', 'float64'],
                        help='Floating point precision (default: float32)')
    parser.add_argument('--thicksteps', type=int, nargs='+', default=[5],
                        help='Number of thickness layers to test (default: 5)')
    parser.add_argument('--outdir', type=str,
                        default='reports/2025-10-vectorization/phase_a',
                        help='Output directory for results')

    args = parser.parse_args()

    # Convert dtype string to torch dtype
    dtype_map = {'float32': torch.float32, 'float64': torch.float64}
    dtype = dtype_map[args.dtype]

    # Check device availability
    if args.device == 'cuda' and not torch.cuda.is_available():
        print("WARNING: CUDA requested but not available. Falling back to CPU.")
        device = 'cpu'
    else:
        device = args.device

    # Create output directory
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Collect environment info
    env_info = {
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'torch_version': torch.__version__,
        'cuda_available': torch.cuda.is_available(),
        'device_requested': args.device,
        'device_actual': device,
        'dtype': str(dtype),
    }

    if torch.cuda.is_available():
        env_info['cuda_device_count'] = torch.cuda.device_count()
        env_info['cuda_device_name'] = torch.cuda.get_device_name(0)

    print(f"=== Detector Absorption Baseline Benchmark ===")
    print(f"Device: {device}")
    print(f"Dtype: {dtype}")
    print(f"Sizes: {args.sizes}")
    print(f"Thicksteps: {args.thicksteps}")
    print(f"Repeats: {args.repeats}")
    print()

    # Run benchmarks for all combinations of size and thicksteps
    all_results = []
    for size in args.sizes:
        for thicksteps in args.thicksteps:
            print(f"Benchmarking size {size}x{size} with {thicksteps} layers...")
            result = benchmark_absorption(size, args.repeats, device, dtype, thicksteps)
            all_results.append(result)

            print(f"  Cold run: {result['cold_time_s']:.6f} s")
            print(f"  Warm runs: {result['mean_warm_s']:.6f} ± {result['std_warm_s']:.6f} s")
            print(f"  Throughput: {result['throughput_pixels_per_sec']:.1f} pixels/sec")
            print(f"  Mean intensity: {result['mean_intensity']:.2e}")
            print()

    # Save results
    output_data = {
        'environment': env_info,
        'benchmark_config': {
            'sizes': args.sizes,
            'thicksteps': args.thicksteps,
            'repeats': args.repeats,
        },
        'results': all_results,
    }

    # Save JSON
    json_path = outdir / 'absorption_baseline_results.json'
    with open(json_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Results saved to: {json_path}")

    # Save markdown summary
    md_path = outdir / 'absorption_baseline.md'
    with open(md_path, 'w') as f:
        f.write(f"# Detector Absorption Baseline Results\n\n")
        f.write(f"**Date:** {env_info['timestamp']}\n\n")
        f.write(f"**Device:** {device}\n\n")
        f.write(f"**Dtype:** {dtype}\n\n")
        f.write(f"## Environment\n\n")
        f.write(f"- Python: {sys.version.split()[0]}\n")
        f.write(f"- PyTorch: {torch.__version__}\n")
        f.write(f"- CUDA Available: {torch.cuda.is_available()}\n")
        if torch.cuda.is_available():
            f.write(f"- GPU: {torch.cuda.get_device_name(0)}\n")
        f.write(f"\n## Configuration\n\n")
        f.write(f"- Attenuation Depth: 500 μm\n")
        f.write(f"- Detector Thickness: 100 μm\n")
        f.write(f"- Oversample Thick: True (accumulation mode)\n")
        f.write(f"\n## Results\n\n")
        f.write(f"| Size | Layers | Pixels | Cold (s) | Warm Mean (s) | Warm Std (s) | Throughput (px/s) | Mean Intensity |\n")
        f.write(f"|------|--------|--------|----------|---------------|--------------|-------------------|----------------|\n")
        for r in all_results:
            f.write(f"| {r['size']}x{r['size']} | {r['thicksteps']} | {r['pixels']} | "
                   f"{r['cold_time_s']:.6f} | {r['mean_warm_s']:.6f} | "
                   f"{r['std_warm_s']:.6f} | {r['throughput_pixels_per_sec']:.1f} | "
                   f"{r['mean_intensity']:.2e} |\n")
        f.write(f"\n## Command\n\n")
        f.write(f"```bash\n")
        f.write(f"PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python {' '.join(sys.argv)}\n")
        f.write(f"```\n")
        f.write(f"\n## Notes\n\n")
        f.write(f"- Absorption parameters: attenuation depth = {all_results[0]['detector_abs_um']} μm, ")
        f.write(f"thickness = {all_results[0]['detector_thick_um']} μm\n")
        f.write(f"- Layer semantics: oversample_thick=True (accumulation mode exercises all layers)\n")
        f.write(f"- Performance bottleneck: Python loop over `thicksteps` in current implementation\n")

    print(f"Summary saved to: {md_path}")
    print("\n✅ Detector absorption baseline benchmark complete!")


if __name__ == '__main__':
    main()
