#!/usr/bin/env python3
"""
Tricubic Interpolation Baseline Benchmark

Measures current (non-vectorized) tricubic interpolation performance to establish
a baseline before Phase B/C vectorization work.

Follows nanoBragg tooling standards (testing_strategy.md §6):
- Located in scripts/benchmarks/
- Honors KMP_DUPLICATE_LIB_OK environment variable
- Saves outputs to reports/2025-10-vectorization/phase_a/
- Device/dtype neutral (CPU and CUDA support)

References:
- specs/spec-a-core.md §4 (Structure factor sampling)
- specs/spec-a-parallel.md §2.3 (Tricubic acceptance tests)
- plans/active/vectorization.md Phase A task A2
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
import tempfile

# Ensure environment is set per project standards
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import after environment setup
import torch
import numpy as np

# Add src to path if needed
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal


def create_test_hkl_file():
    """
    Create a temporary HKL file with smooth variation for tricubic interpolation testing.

    Returns a 9x9x9 grid with a smooth cubic function suitable for interpolation benchmarking.
    """
    hkl_content = []

    # Generate a grid with values that vary smoothly
    # Using a cubic polynomial: F = 100 + 10*h + 5*k + 2*l + 0.5*h*k + 0.3*k*l + 0.2*h*l
    for h in range(-4, 5):
        for k in range(-4, 5):
            for l in range(-4, 5):
                F = (100.0 + 10.0 * h + 5.0 * k + 2.0 * l +
                     0.5 * h * k + 0.3 * k * l + 0.2 * h * l)
                hkl_content.append(f"{h} {k} {l} {F:.6f}\n")

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.hkl', delete=False) as f:
        f.writelines(hkl_content)
        return f.name


def benchmark_tricubic(size, repeats, device, dtype):
    """
    Benchmark tricubic interpolation for a given detector size.

    Args:
        size: Detector size (square detector size x size)
        repeats: Number of timing repeats
        device: torch.device or string ('cpu', 'cuda')
        dtype: torch.dtype (typically float32 or float64)

    Returns:
        dict with timing results and metadata
    """
    device_obj = torch.device(device)

    # Create HKL file (shared across repeats)
    hkl_file = create_test_hkl_file()

    try:
        # Configure crystal to auto-enable tricubic (N_cells <= 2)
        config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(2, 2, 2),  # Small crystal to auto-enable interpolation
            default_F=100.0
        )

        # Create crystal and load HKL
        crystal = Crystal(config, device=device_obj, dtype=dtype)
        crystal.load_hkl(hkl_file)

        # Verify interpolation is enabled
        assert crystal.interpolate, "Tricubic interpolation should be auto-enabled for N=2"

        # Create a set of fractional Miller indices to interpolate
        # NOTE: Current implementation only supports scalar calls, so we time
        # the overhead of calling get_structure_factor() many times with scalar inputs.
        # This is the baseline that vectorization will improve upon.
        num_samples = min(100, size)  # Limit to 100 scalar calls for reasonable runtime
        h_samples = torch.linspace(-2.5, 2.5, num_samples, device=device_obj, dtype=dtype)
        k_samples = torch.linspace(-2.5, 2.5, num_samples, device=device_obj, dtype=dtype)
        l_samples = torch.ones(num_samples, device=device_obj, dtype=dtype) * 0.5

        # Warm-up run (especially important for GPU)
        if device_obj.type == 'cuda':
            for _ in range(3):
                for j in range(min(10, num_samples)):
                    _ = crystal.get_structure_factor(h_samples[j], k_samples[j], l_samples[j])
            torch.cuda.synchronize()

        # Cold timing (first run after warm-up)
        if device_obj.type == 'cuda':
            torch.cuda.synchronize()

        start_cold = time.perf_counter()
        results_cold = []
        for j in range(num_samples):
            results_cold.append(crystal.get_structure_factor(h_samples[j], k_samples[j], l_samples[j]))

        if device_obj.type == 'cuda':
            torch.cuda.synchronize()

        time_cold = time.perf_counter() - start_cold

        # Warm timings (subsequent runs)
        warm_times = []
        for i in range(repeats):
            if device_obj.type == 'cuda':
                torch.cuda.synchronize()

            start = time.perf_counter()
            results_warm = []
            for j in range(num_samples):
                results_warm.append(crystal.get_structure_factor(h_samples[j], k_samples[j], l_samples[j]))

            if device_obj.type == 'cuda':
                torch.cuda.synchronize()

            warm_times.append(time.perf_counter() - start)

        # Verify results are non-trivial
        result = torch.stack(results_cold)
        assert result.numel() == num_samples, f"Expected {num_samples} elements, got {result.numel()}"
        assert torch.all(torch.isfinite(result)), "Result contains non-finite values"

        # Collect results
        results = {
            'size': size,
            'device': str(device_obj),
            'dtype': str(dtype),
            'interpolation_enabled': crystal.interpolate,
            'scalar_calls': num_samples,
            'note': 'Current implementation only supports scalar interpolation',
            'cold_time_s': float(time_cold),
            'warm_times_s': [float(t) for t in warm_times],
            'mean_warm_s': float(np.mean(warm_times)),
            'median_warm_s': float(np.median(warm_times)),
            'std_warm_s': float(np.std(warm_times)),
            'min_warm_s': float(np.min(warm_times)),
            'max_warm_s': float(np.max(warm_times)),
            'time_per_call_us': float(np.mean(warm_times) / num_samples * 1e6),
            'throughput_calls_per_sec': float(num_samples / np.mean(warm_times)),
        }

        return results

    finally:
        # Clean up temp file
        if os.path.exists(hkl_file):
            os.unlink(hkl_file)


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark tricubic interpolation baseline performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # CPU baseline with default sizes
  python tricubic_baseline.py --sizes 256 512 --repeats 5

  # GPU baseline
  python tricubic_baseline.py --sizes 256 512 --device cuda --repeats 10

  # High-precision CPU baseline
  python tricubic_baseline.py --sizes 128 256 --dtype float64 --repeats 5
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

    print(f"=== Tricubic Interpolation Baseline Benchmark ===")
    print(f"Device: {device}")
    print(f"Dtype: {dtype}")
    print(f"Sizes: {args.sizes}")
    print(f"Repeats: {args.repeats}")
    print()

    # Run benchmarks
    all_results = []
    for size in args.sizes:
        print(f"Benchmarking size {size}x{size}...")
        result = benchmark_tricubic(size, args.repeats, device, dtype)
        all_results.append(result)

        print(f"  Scalar calls: {result['scalar_calls']}")
        print(f"  Cold run: {result['cold_time_s']:.6f} s")
        print(f"  Warm runs: {result['mean_warm_s']:.6f} ± {result['std_warm_s']:.6f} s")
        print(f"  Time/call: {result['time_per_call_us']:.2f} μs")
        print(f"  Throughput: {result['throughput_calls_per_sec']:.1f} calls/sec")
        print()

    # Save results
    output_data = {
        'environment': env_info,
        'benchmark_config': {
            'sizes': args.sizes,
            'repeats': args.repeats,
        },
        'results': all_results,
    }

    # Save JSON
    json_path = outdir / 'tricubic_baseline_results.json'
    with open(json_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Results saved to: {json_path}")

    # Save markdown summary
    md_path = outdir / 'tricubic_baseline.md'
    with open(md_path, 'w') as f:
        f.write(f"# Tricubic Interpolation Baseline Results\n\n")
        f.write(f"**Date:** {env_info['timestamp']}\n\n")
        f.write(f"**Device:** {device}\n\n")
        f.write(f"**Dtype:** {dtype}\n\n")
        f.write(f"## Environment\n\n")
        f.write(f"- Python: {sys.version.split()[0]}\n")
        f.write(f"- PyTorch: {torch.__version__}\n")
        f.write(f"- CUDA Available: {torch.cuda.is_available()}\n")
        if torch.cuda.is_available():
            f.write(f"- GPU: {torch.cuda.get_device_name(0)}\n")
        f.write(f"\n## Results\n\n")
        f.write(f"**Note:** Current implementation only supports scalar interpolation calls. ")
        f.write(f"Benchmarks measure overhead of {all_results[0]['scalar_calls']} scalar ")
        f.write(f"get_structure_factor() calls in a loop.\n\n")
        f.write(f"| Size Param | Scalar Calls | Cold (s) | Warm Mean (s) | Warm Std (s) | Time/Call (μs) | Calls/sec |\n")
        f.write(f"|------------|--------------|----------|---------------|--------------|----------------|----------|\n")
        for r in all_results:
            f.write(f"| {r['size']} | {r['scalar_calls']} | "
                   f"{r['cold_time_s']:.6f} | {r['mean_warm_s']:.6f} | "
                   f"{r['std_warm_s']:.6f} | {r['time_per_call_us']:.2f} | "
                   f"{r['throughput_calls_per_sec']:.1f} |\n")
        f.write(f"\n## Command\n\n")
        f.write(f"```bash\n")
        f.write(f"PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python {' '.join(sys.argv)}\n")
        f.write(f"```\n")

    print(f"Summary saved to: {md_path}")
    print("\n✅ Tricubic baseline benchmark complete!")


if __name__ == '__main__':
    main()
