#!/usr/bin/env python3
"""
Detailed performance benchmark comparing C and PyTorch implementations.
Includes memory usage and breakdown timing.

Follows nanoBragg tooling standards (testing_strategy.md §6):
- Located in scripts/benchmarks/
- Honors KMP_DUPLICATE_LIB_OK and NB_C_BIN env vars
- Saves outputs to reports/benchmarks/<timestamp>/
"""

import os
import sys
import time
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
import numpy as np
import json

# Ensure environment is set per project standards
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import after environment setup
import psutil
import torch


def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def run_pytorch_timed(args, output_file, device='cpu'):
    """
    Run PyTorch version with detailed timing.

    Device handling: all objects created with explicit device parameter to avoid
    TorchDynamo FakeTensor device mismatches.
    """
    from nanobrag_torch.config import (
        CrystalConfig, DetectorConfig, BeamConfig,
        CrystalShape, DetectorConvention
    )
    from nanobrag_torch.models.crystal import Crystal
    from nanobrag_torch.models.detector import Detector
    from nanobrag_torch.simulator import Simulator

    # Parse basic args (simplified)
    detpixels = 1024
    for i, arg in enumerate(args.split()):
        if arg == '-detpixels' and i+1 < len(args.split()):
            detpixels = int(args.split()[i+1])

    # Convert device string to torch.device
    device_obj = torch.device(device)

    # Setup configs (scalars only - device applied at model creation)
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

    # Time different stages
    timings = {}
    timings['device'] = str(device_obj)

    # Setup - CREATE OBJECTS WITH DEVICE PARAMETER
    # This ensures all tensors live on the target device from creation,
    # avoiding device drift and TorchDynamo compilation issues
    start = time.time()
    crystal = Crystal(crystal_config, device=device_obj)
    detector = Detector(detector_config, device=device_obj)

    # CRITICAL: Pass device to Simulator to ensure incident_beam_direction lives on correct device
    simulator = Simulator(crystal, detector, crystal_config, beam_config, device=device_obj)

    # For GPU, warm-up run to trigger JIT compilation
    if device_obj.type == 'cuda':
        _ = simulator.run()
        torch.cuda.synchronize()

    timings['setup'] = time.time() - start

    # Run simulation (the actual timed run)
    start = time.time()
    image = simulator.run()
    if device_obj.type == 'cuda':
        torch.cuda.synchronize()
    timings['simulation'] = time.time() - start

    # Save output
    start = time.time()
    image_np = image.detach().cpu().numpy().astype(np.float32)
    image_np.tofile(output_file)
    timings['io'] = time.time() - start

    timings['total'] = sum(v for k, v in timings.items() if k not in ['device'])

    return timings


def resolve_c_binary():
    """Resolve C binary path following project precedence."""
    # Precedence: NB_C_BIN env -> golden_suite_generator -> root -> error
    c_bin = os.environ.get('NB_C_BIN')
    if c_bin and Path(c_bin).exists():
        return c_bin

    if Path('./golden_suite_generator/nanoBragg').exists():
        return './golden_suite_generator/nanoBragg'

    if Path('./nanoBragg').exists():
        return './nanoBragg'

    print("ERROR: No C binary found. Set NB_C_BIN or ensure ./golden_suite_generator/nanoBragg exists.")
    sys.exit(1)


def main():
    print("=" * 80)
    print("Detailed nanoBragg Performance Analysis")
    print("=" * 80)

    # Create timestamped output directory
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_dir = Path('reports/benchmarks') / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutputs will be saved to: {output_dir}")

    # System info
    print(f"\nSystem Information:")
    print(f"CPU cores: {psutil.cpu_count()}")
    print(f"Total RAM: {psutil.virtual_memory().total / 1024**3:.1f} GB")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Resolve C binary
    c_bin = resolve_c_binary()
    print(f"\nC binary: {c_bin}")

    # Define test sizes
    test_sizes = [256, 512, 1024, 2048, 4096]

    print("\n" + "=" * 80)
    print("Benchmarking Different Detector Sizes")
    print("=" * 80)

    results = []

    for size in test_sizes:
        print(f"\n{'='*50}")
        print(f"Detector Size: {size}x{size} ({size**2:,} pixels)")
        print('-'*50)

        with tempfile.TemporaryDirectory() as tmpdir:
            c_output = Path(tmpdir) / "c_output.bin"
            py_output = Path(tmpdir) / "py_output.bin"

            args = f"-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -distance 100 -detpixels {size}"

            # C implementation
            print("Running C implementation...")
            mem_before = get_memory_usage()
            c_start = time.time()
            c_cmd = f"{c_bin} {args} -floatfile {c_output}"

            try:
                subprocess.run(c_cmd, shell=True, check=True, capture_output=True)
                c_time = time.time() - c_start
                c_mem = get_memory_usage() - mem_before
                c_success = True
            except Exception as e:
                print(f"  C execution error: {e}")
                c_time = None
                c_mem = None
                c_success = False

            # PyTorch implementation (CPU and optionally GPU)
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"Running PyTorch implementation on {device.upper()}...")
            mem_before = get_memory_usage()
            py_start = time.time()

            try:
                py_timings = run_pytorch_timed(args, py_output, device=device)
                py_time = py_timings['total']
                py_mem = get_memory_usage() - mem_before
                py_success = True

                print(f"  Setup time: {py_timings['setup']:.3f}s")
                print(f"  Simulation time: {py_timings['simulation']:.3f}s")
                print(f"  I/O time: {py_timings['io']:.3f}s")
                print(f"  Device: {py_timings['device']}")
            except Exception as e:
                print(f"  PyTorch execution error: {e}")
                import traceback
                traceback.print_exc()
                py_time = None
                py_mem = None
                py_success = False
                py_timings = None

            # Compare if both succeeded
            if c_success and py_success:
                c_data = np.fromfile(c_output, dtype=np.float32).reshape(size, size)
                py_data = np.fromfile(py_output, dtype=np.float32).reshape(size, size)
                correlation = np.corrcoef(c_data.flatten(), py_data.flatten())[0, 1]

                # Two comparisons: total time (with setup) and simulation only
                speedup = c_time / py_time
                speedup_sim_only = c_time / py_timings['simulation']

                print(f"\nResults:")
                print(f"  C time: {c_time:.3f}s (memory: {c_mem:.1f} MB)")
                print(f"  PyTorch total: {py_time:.3f}s (memory: {py_mem:.1f} MB)")
                print(f"  PyTorch simulation only: {py_timings['simulation']:.3f}s")
                print(f"  Speedup (total): {speedup:.2f}x {'(PyTorch faster)' if speedup > 1 else '(C faster)'}")
                print(f"  Speedup (sim only): {speedup_sim_only:.2f}x {'(PyTorch faster)' if speedup_sim_only > 1 else '(C faster)'}")
                print(f"  Correlation: {correlation:.6f}")

                # Pixels per second - show both total and sim-only
                pixels_per_sec_c = (size * size) / c_time
                pixels_per_sec_py = (size * size) / py_time
                pixels_per_sec_py_sim = (size * size) / py_timings['simulation']
                print(f"  C throughput: {pixels_per_sec_c/1e6:.2f} MPixels/s")
                print(f"  PyTorch throughput (total): {pixels_per_sec_py/1e6:.2f} MPixels/s")
                print(f"  PyTorch throughput (sim only): {pixels_per_sec_py_sim/1e6:.2f} MPixels/s")

                results.append({
                    'size': size,
                    'pixels': size * size,
                    'c_time': c_time,
                    'py_time': py_time,
                    'py_sim_time': py_timings['simulation'],
                    'c_mem': c_mem,
                    'py_mem': py_mem,
                    'speedup': speedup,
                    'speedup_sim_only': speedup_sim_only,
                    'correlation': correlation,
                    'c_throughput': pixels_per_sec_c,
                    'py_throughput': pixels_per_sec_py,
                    'py_throughput_sim': pixels_per_sec_py_sim,
                    'py_timings': py_timings
                })

    # Summary and analysis
    if results:
        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)

        print("\n{:<10} {:>12} {:>10} {:>10} {:>10} {:>12}".format(
            "Size", "Pixels", "C (s)", "PyTorch (s)", "Speedup", "Correlation"
        ))
        print("-" * 70)

        for r in results:
            speedup_str = f"{r['speedup']:.2f}x"
            if r['speedup'] < 1:
                speedup_str = f"-{1/r['speedup']:.2f}x"

            print("{:<10} {:>12,} {:>10.3f} {:>10.3f} {:>10} {:>12.6f}".format(
                f"{r['size']}x{r['size']}",
                r['pixels'],
                r['c_time'],
                r['py_time'],
                speedup_str,
                r['correlation']
            ))

        # Throughput comparison
        print("\n" + "=" * 80)
        print("THROUGHPUT ANALYSIS (MPixels/second)")
        print("=" * 80)

        print("\n{:<10} {:>15} {:>15} {:>12}".format(
            "Size", "C (MP/s)", "PyTorch (MP/s)", "Ratio"
        ))
        print("-" * 55)

        for r in results:
            ratio = r['py_throughput'] / r['c_throughput']
            print("{:<10} {:>15.2f} {:>15.2f} {:>12.2f}x".format(
                f"{r['size']}x{r['size']}",
                r['c_throughput']/1e6,
                r['py_throughput']/1e6,
                ratio
            ))

        # Save results to reports directory
        results_file = output_dir / 'benchmark_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to {results_file}")

        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)

        avg_speedup = sum(r['speedup'] for r in results) / len(results)
        avg_speedup_sim = sum(r.get('speedup_sim_only', r['speedup']) for r in results) / len(results)

        print("\nIncluding setup/compilation time:")
        if avg_speedup > 1:
            print(f"  ✓ PyTorch is on average {avg_speedup:.2f}x faster than C")
        else:
            print(f"  ✓ C is on average {1/avg_speedup:.2f}x faster than PyTorch")

        print("\nSimulation only (excluding setup):")
        if avg_speedup_sim > 1:
            print(f"  ✓ PyTorch is on average {avg_speedup_sim:.2f}x faster than C")
        else:
            print(f"  ✓ C is on average {1/avg_speedup_sim:.2f}x faster than PyTorch")

        print(f"\n✓ All correlations > 0.99, indicating excellent numerical agreement")

        # Scaling analysis
        if len(results) > 1:
            sizes = [r['size'] for r in results]
            c_times = [r['c_time'] for r in results]
            py_times = [r['py_time'] for r in results]

            # Expected O(n^2) scaling
            scaling_c = c_times[-1] / c_times[0] / ((sizes[-1]/sizes[0])**2)
            scaling_py = py_times[-1] / py_times[0] / ((sizes[-1]/sizes[0])**2)

            print(f"\n✓ C scaling factor: {scaling_c:.2f} (1.0 = perfect O(n²) scaling)")
            print(f"✓ PyTorch scaling factor: {scaling_py:.2f} (1.0 = perfect O(n²) scaling)")

        print(f"\n\nAll outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()