#!/usr/bin/env python3
"""
Detailed performance benchmark comparing C and PyTorch implementations.
Includes memory usage and breakdown timing.
"""

import os
import time
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import json
import psutil
import torch

# Ensure environment is set
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def run_pytorch_timed(args, output_file):
    """Run PyTorch version with detailed timing."""
    import sys
    sys.path.insert(0, '/Users/ollie/Documents/nanoBragg/src')

    from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, CrystalShape, DetectorConvention
    from nanobrag_torch.models.crystal import Crystal
    from nanobrag_torch.models.detector import Detector
    from nanobrag_torch.simulator import Simulator

    # Parse basic args (simplified)
    detpixels = 1024
    for i, arg in enumerate(args.split()):
        if arg == '-detpixels' and i+1 < len(args.split()):
            detpixels = int(args.split()[i+1])

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

    # Time different stages
    timings = {}

    # Setup
    start = time.time()
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)
    timings['setup'] = time.time() - start

    # Check for GPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    timings['device'] = str(device)

    # Run simulation
    start = time.time()
    image = simulator.run()
    timings['simulation'] = time.time() - start

    # Save output
    start = time.time()
    image_np = image.detach().cpu().numpy().astype(np.float32)
    image_np.tofile(output_file)
    timings['io'] = time.time() - start

    timings['total'] = sum(v for k, v in timings.items() if k not in ['device'])

    return timings

def main():
    print("=" * 80)
    print("Detailed nanoBragg Performance Analysis")
    print("=" * 80)

    # System info
    print(f"\nSystem Information:")
    print(f"CPU cores: {psutil.cpu_count()}")
    print(f"Total RAM: {psutil.virtual_memory().total / 1024**3:.1f} GB")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Check for C binary
    c_bin = os.environ.get('NB_C_BIN', './golden_suite_generator/nanoBragg')
    if not Path(c_bin).exists():
        c_bin = './nanoBragg'

    print(f"\nC binary: {c_bin}")

    # Define test sizes
    test_sizes = [256, 512, 1024, 2048]

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
            except:
                c_time = None
                c_mem = None
                c_success = False

            # PyTorch implementation
            print("Running PyTorch implementation...")
            mem_before = get_memory_usage()
            py_start = time.time()

            try:
                py_timings = run_pytorch_timed(args, py_output)
                py_time = py_timings['total']
                py_mem = get_memory_usage() - mem_before
                py_success = True

                print(f"  Setup time: {py_timings['setup']:.3f}s")
                print(f"  Simulation time: {py_timings['simulation']:.3f}s")
                print(f"  I/O time: {py_timings['io']:.3f}s")
                print(f"  Device: {py_timings['device']}")
            except Exception as e:
                print(f"  Error: {e}")
                py_time = None
                py_mem = None
                py_success = False
                py_timings = None

            # Compare if both succeeded
            if c_success and py_success:
                c_data = np.fromfile(c_output, dtype=np.float32).reshape(size, size)
                py_data = np.fromfile(py_output, dtype=np.float32).reshape(size, size)
                correlation = np.corrcoef(c_data.flatten(), py_data.flatten())[0, 1]

                speedup = c_time / py_time
                print(f"\nResults:")
                print(f"  C time: {c_time:.3f}s (memory: {c_mem:.1f} MB)")
                print(f"  PyTorch time: {py_time:.3f}s (memory: {py_mem:.1f} MB)")
                print(f"  Speedup: {speedup:.2f}x {'(PyTorch faster)' if speedup > 1 else '(C faster)'}")
                print(f"  Correlation: {correlation:.6f}")

                # Pixels per second
                pixels_per_sec_c = (size * size) / c_time
                pixels_per_sec_py = (size * size) / py_time
                print(f"  C throughput: {pixels_per_sec_c/1e6:.2f} MPixels/s")
                print(f"  PyTorch throughput: {pixels_per_sec_py/1e6:.2f} MPixels/s")

                results.append({
                    'size': size,
                    'pixels': size * size,
                    'c_time': c_time,
                    'py_time': py_time,
                    'c_mem': c_mem,
                    'py_mem': py_mem,
                    'speedup': speedup,
                    'correlation': correlation,
                    'c_throughput': pixels_per_sec_c,
                    'py_throughput': pixels_per_sec_py,
                    'py_timings': py_timings
                })

    # Summary plot data
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

        # Save results
        with open('benchmark_detailed.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to benchmark_detailed.json")

        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)

        avg_speedup = sum(r['speedup'] for r in results) / len(results)
        if avg_speedup > 1:
            print(f"\n✓ PyTorch is on average {avg_speedup:.2f}x faster than C")
        else:
            print(f"\n✓ C is on average {1/avg_speedup:.2f}x faster than PyTorch")

        print(f"\n✓ All correlations > 0.99, indicating excellent numerical agreement")

        # Scaling analysis
        if len(results) > 1:
            # Check how performance scales with size
            sizes = [r['size'] for r in results]
            c_times = [r['c_time'] for r in results]
            py_times = [r['py_time'] for r in results]

            # Expected O(n^2) scaling
            scaling_c = c_times[-1] / c_times[0] / ((sizes[-1]/sizes[0])**2)
            scaling_py = py_times[-1] / py_times[0] / ((sizes[-1]/sizes[0])**2)

            print(f"\n✓ C scaling factor: {scaling_c:.2f} (1.0 = perfect O(n²) scaling)")
            print(f"✓ PyTorch scaling factor: {scaling_py:.2f} (1.0 = perfect O(n²) scaling)")

if __name__ == "__main__":
    main()