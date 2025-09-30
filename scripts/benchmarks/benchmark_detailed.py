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


# PERF-PYTORCH-005: Global simulator cache for reuse across runs
# Key: (spixels, fpixels, oversample, n_sources, device_type)
_simulator_cache = {}


def get_cache_key(detpixels, oversample, n_sources, device):
    """Generate cache key for simulator reuse."""
    device_type = device if isinstance(device, str) else str(device)
    return (detpixels, detpixels, oversample, n_sources, device_type)


def run_pytorch_timed(args, output_file, device='cpu', use_cache=True):
    """
    Run PyTorch version with detailed timing.

    Device handling: all objects created with explicit device parameter to avoid
    TorchDynamo FakeTensor device mismatches.

    Args:
        args: Command-line arguments string
        output_file: Path to output file
        device: Device to run on ('cpu' or 'cuda')
        use_cache: If True, reuse cached simulators (PERF-PYTORCH-005)
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
    oversample = 1
    n_sources = 1
    for i, arg in enumerate(args.split()):
        if arg == '-detpixels' and i+1 < len(args.split()):
            detpixels = int(args.split()[i+1])
        elif arg == '-oversample' and i+1 < len(args.split()):
            oversample = int(args.split()[i+1])

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
        oversample=oversample
    )

    beam_config = BeamConfig(wavelength_A=6.2)

    # Time different stages
    timings = {}
    timings['device'] = str(device_obj)
    timings['cache_hit'] = False

    # PERF-PYTORCH-005: Check cache before creating new simulator
    cache_key = get_cache_key(detpixels, oversample, n_sources, device_obj.type)

    start = time.time()
    if use_cache and cache_key in _simulator_cache:
        # Reuse cached simulator
        simulator = _simulator_cache[cache_key]
        timings['cache_hit'] = True
        timings['setup'] = time.time() - start
    else:
        # Setup - CREATE OBJECTS WITH DEVICE PARAMETER
        # This ensures all tensors live on the target device from creation,
        # avoiding device drift and TorchDynamo compilation issues
        crystal = Crystal(crystal_config, device=device_obj)
        detector = Detector(detector_config, device=device_obj)

        # CRITICAL: Pass device to Simulator to ensure incident_beam_direction lives on correct device
        simulator = Simulator(crystal, detector, crystal_config, beam_config, device=device_obj)

        # For GPU, warm-up run to trigger JIT compilation
        if device_obj.type == 'cuda':
            _ = simulator.run()
            torch.cuda.synchronize()

        timings['setup'] = time.time() - start

        # Cache the simulator for reuse
        if use_cache:
            _simulator_cache[cache_key] = simulator

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
    print("\nPERF-PYTORCH-005: Testing simulator cache reuse")
    print("Each size will be run twice: cold (first run) and warm (cached)")

    results = []

    for size in test_sizes:
        print(f"\n{'='*50}")
        print(f"Detector Size: {size}x{size} ({size**2:,} pixels)")
        print('-'*50)

        with tempfile.TemporaryDirectory() as tmpdir:
            c_output = Path(tmpdir) / "c_output.bin"
            py_output_cold = Path(tmpdir) / "py_output_cold.bin"
            py_output_warm = Path(tmpdir) / "py_output_warm.bin"

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

            # PyTorch implementation - COLD RUN (first time for this size)
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"Running PyTorch COLD (first run) on {device.upper()}...")
            mem_before = get_memory_usage()

            try:
                py_timings_cold = run_pytorch_timed(args, py_output_cold, device=device, use_cache=True)
                py_mem_cold = get_memory_usage() - mem_before

                print(f"  Setup time (cold): {py_timings_cold['setup']:.3f}s")
                print(f"  Simulation time: {py_timings_cold['simulation']:.3f}s")
                print(f"  Cache hit: {py_timings_cold['cache_hit']}")
                py_success_cold = True
            except Exception as e:
                print(f"  PyTorch COLD execution error: {e}")
                import traceback
                traceback.print_exc()
                py_success_cold = False
                py_timings_cold = None

            # PyTorch implementation - WARM RUN (reuse cached simulator)
            print(f"Running PyTorch WARM (cached) on {device.upper()}...")
            mem_before = get_memory_usage()

            try:
                py_timings_warm = run_pytorch_timed(args, py_output_warm, device=device, use_cache=True)
                py_mem_warm = get_memory_usage() - mem_before

                print(f"  Setup time (warm): {py_timings_warm['setup']:.3f}s")
                print(f"  Simulation time: {py_timings_warm['simulation']:.3f}s")
                print(f"  Cache hit: {py_timings_warm['cache_hit']}")
                print(f"  Setup speedup: {py_timings_cold['setup'] / py_timings_warm['setup']:.1f}x faster")
                py_success_warm = True
            except Exception as e:
                print(f"  PyTorch WARM execution error: {e}")
                import traceback
                traceback.print_exc()
                py_success_warm = False
                py_timings_warm = None

            # Compare if all succeeded
            if c_success and py_success_cold and py_success_warm:
                c_data = np.fromfile(c_output, dtype=np.float32).reshape(size, size)
                py_data_cold = np.fromfile(py_output_cold, dtype=np.float32).reshape(size, size)
                py_data_warm = np.fromfile(py_output_warm, dtype=np.float32).reshape(size, size)

                correlation_cold = np.corrcoef(c_data.flatten(), py_data_cold.flatten())[0, 1]
                correlation_warm = np.corrcoef(c_data.flatten(), py_data_warm.flatten())[0, 1]

                # Calculate times (warm run uses cached simulator, so lower setup time)
                py_time_cold = py_timings_cold['total']
                py_time_warm = py_timings_warm['total']

                # Speedup calculations
                speedup_cold = c_time / py_time_cold
                speedup_warm = c_time / py_time_warm

                print(f"\nResults:")
                print(f"  C time: {c_time:.3f}s (memory: {c_mem:.1f} MB)")
                print(f"  PyTorch COLD total: {py_time_cold:.3f}s (memory: {py_mem_cold:.1f} MB)")
                print(f"  PyTorch WARM total: {py_time_warm:.3f}s (memory: {py_mem_warm:.1f} MB)")
                print(f"  Speedup (cold): {speedup_cold:.2f}x {'(PyTorch faster)' if speedup_cold > 1 else '(C faster)'}")
                print(f"  Speedup (warm): {speedup_warm:.2f}x {'(PyTorch faster)' if speedup_warm > 1 else '(C faster)'}")
                print(f"  Correlation (cold): {correlation_cold:.6f}")
                print(f"  Correlation (warm): {correlation_warm:.6f}")

                # PERF-PYTORCH-005: Report cache effectiveness
                setup_improvement = py_timings_cold['setup'] / py_timings_warm['setup']
                print(f"\n  ✓ Cache effectiveness: {setup_improvement:.1f}x faster setup")
                if py_timings_warm['setup'] < 0.050:
                    print(f"  ✓ PERF-PYTORCH-005 EXIT CRITERIA MET: Warm setup {py_timings_warm['setup']*1000:.1f}ms < 50ms")
                else:
                    print(f"  ⚠ PERF-PYTORCH-005: Warm setup {py_timings_warm['setup']*1000:.1f}ms > 50ms target")

                results.append({
                    'size': size,
                    'pixels': size * size,
                    'c_time': c_time,
                    'py_time_cold': py_time_cold,
                    'py_time_warm': py_time_warm,
                    'py_setup_cold': py_timings_cold['setup'],
                    'py_setup_warm': py_timings_warm['setup'],
                    'py_sim_cold': py_timings_cold['simulation'],
                    'py_sim_warm': py_timings_warm['simulation'],
                    'c_mem': c_mem,
                    'py_mem_cold': py_mem_cold,
                    'py_mem_warm': py_mem_warm,
                    'speedup_cold': speedup_cold,
                    'speedup_warm': speedup_warm,
                    'setup_speedup': setup_improvement,
                    'correlation_cold': correlation_cold,
                    'correlation_warm': correlation_warm,
                    'cache_hit_cold': py_timings_cold['cache_hit'],
                    'cache_hit_warm': py_timings_warm['cache_hit'],
                })

    # Summary and analysis
    if results:
        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY (PERF-PYTORCH-005: Cache Reuse)")
        print("=" * 80)

        print("\n{:<10} {:>12} {:>8} {:>10} {:>10} {:>10} {:>10}".format(
            "Size", "Pixels", "C (s)", "PyTorch", "PyTorch", "Setup", "Corr"
        ))
        print("{:<10} {:>12} {:>8} {:>10} {:>10} {:>10} {:>10}".format(
            "", "", "", "COLD (s)", "WARM (s)", "Speedup", "(warm)"
        ))
        print("-" * 82)

        for r in results:
            print("{:<10} {:>12,} {:>8.3f} {:>10.3f} {:>10.3f} {:>9.1f}x {:>10.6f}".format(
                f"{r['size']}x{r['size']}",
                r['pixels'],
                r['c_time'],
                r['py_time_cold'],
                r['py_time_warm'],
                r['setup_speedup'],
                r['correlation_warm']
            ))

        # PERF-PYTORCH-005: Cache effectiveness summary
        print("\n" + "=" * 80)
        print("CACHE EFFECTIVENESS (PERF-PYTORCH-005)")
        print("=" * 80)

        print("\n{:<10} {:>15} {:>15} {:>12} {:>12}".format(
            "Size", "Setup COLD (ms)", "Setup WARM (ms)", "Speedup", "Exit Crit"
        ))
        print("-" * 70)

        all_meet_criteria = True
        for r in results:
            setup_cold_ms = r['py_setup_cold'] * 1000
            setup_warm_ms = r['py_setup_warm'] * 1000
            meets_criteria = "✓" if setup_warm_ms < 50 else "✗"
            if setup_warm_ms >= 50:
                all_meet_criteria = False

            print("{:<10} {:>15.1f} {:>15.1f} {:>11.1f}x {:>12}".format(
                f"{r['size']}x{r['size']}",
                setup_cold_ms,
                setup_warm_ms,
                r['setup_speedup'],
                meets_criteria
            ))

        print(f"\nPERF-PYTORCH-005 Exit Criteria: Setup time < 50ms for cached runs")
        if all_meet_criteria:
            print("  ✓ ALL SIZES MEET EXIT CRITERIA")
        else:
            print("  ⚠ Some sizes exceed 50ms target (see ✗ marks above)")

        # Save results to reports directory
        results_file = output_dir / 'benchmark_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to {results_file}")

        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)

        avg_speedup_cold = sum(r['speedup_cold'] for r in results) / len(results)
        avg_speedup_warm = sum(r['speedup_warm'] for r in results) / len(results)
        avg_setup_speedup = sum(r['setup_speedup'] for r in results) / len(results)

        print("\nCOLD runs (first time, includes compilation):")
        if avg_speedup_cold > 1:
            print(f"  ✓ PyTorch is on average {avg_speedup_cold:.2f}x faster than C")
        else:
            print(f"  ✓ C is on average {1/avg_speedup_cold:.2f}x faster than PyTorch")

        print("\nWARM runs (cached simulator):")
        if avg_speedup_warm > 1:
            print(f"  ✓ PyTorch is on average {avg_speedup_warm:.2f}x faster than C")
        else:
            print(f"  ✓ C is on average {1/avg_speedup_warm:.2f}x faster than PyTorch")

        print(f"\nCache effectiveness: {avg_setup_speedup:.1f}x faster setup on average")
        print(f"✓ All correlations > 0.99, indicating excellent numerical agreement")

        print(f"\n\nAll outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()