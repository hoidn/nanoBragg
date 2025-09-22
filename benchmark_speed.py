#!/usr/bin/env python3
"""
Benchmark script to compare C and PyTorch nanoBragg performance on large test cases.
"""

import os
import time
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import json

# Ensure environment is set
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def run_benchmark(command, label="Test"):
    """Run a command and measure execution time."""
    print(f"Running {label}...")
    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        elapsed = time.time() - start_time

        # Extract statistics from output if available
        lines = result.stdout.split('\n')
        max_intensity = None
        for line in lines:
            if 'Max intensity:' in line:
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'intensity:':
                            max_intensity = float(parts[i+1])
                            break
                except:
                    pass

        return {
            'success': True,
            'time': elapsed,
            'max_intensity': max_intensity,
            'error': None
        }
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        return {
            'success': False,
            'time': elapsed,
            'max_intensity': None,
            'error': str(e)
        }

def compare_outputs(file1, file2, size):
    """Compare two binary output files."""
    try:
        data1 = np.fromfile(file1, dtype=np.float32)
        data2 = np.fromfile(file2, dtype=np.float32)

        if len(data1) != size * size or len(data2) != size * size:
            return {'error': 'Size mismatch'}

        img1 = data1.reshape(size, size)
        img2 = data2.reshape(size, size)

        correlation = np.corrcoef(img1.flatten(), img2.flatten())[0, 1]
        rmse = np.sqrt(np.mean((img1 - img2)**2))
        max_diff = np.abs(img1 - img2).max()

        return {
            'correlation': float(correlation),
            'rmse': float(rmse),
            'max_diff': float(max_diff)
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    print("=" * 70)
    print("nanoBragg C vs PyTorch Performance Benchmark")
    print("=" * 70)

    # Check for C binary
    c_bin = os.environ.get('NB_C_BIN', './golden_suite_generator/nanoBragg')
    if not Path(c_bin).exists():
        c_bin = './nanoBragg'
        if not Path(c_bin).exists():
            print(f"Error: C binary not found. Please set NB_C_BIN or compile nanoBragg")
            return

    print(f"Using C binary: {c_bin}")

    # Define test cases
    test_cases = [
        {
            'name': 'Large Detector (2048x2048)',
            'args': '-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -distance 100',
            'detpixels': 2048
        },
        {
            'name': 'Very Large Detector (4096x4096)',
            'args': '-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 3 -distance 100',
            'detpixels': 4096
        },
        {
            'name': 'Large Crystal (10x10x10 cells)',
            'args': '-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 10 -distance 100',
            'detpixels': 1024
        },
        {
            'name': 'Complex Case (triclinic, mosaic, large)',
            'args': '-default_F 100 -cell 70 80 90 85 95 105 -lambda 1.5 -N 8 -distance 100 '
                   '-misset 10 5 3 -mosaic 0.5 -mosaic_domains 10',
            'detpixels': 1024
        },
        {
            'name': 'Multiple Phi Steps',
            'args': '-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -distance 100 '
                   '-phi 0 -osc 5 -phisteps 10',
            'detpixels': 512
        }
    ]

    results = []

    for test in test_cases:
        print(f"\n{'='*70}")
        print(f"Test: {test['name']}")
        print(f"Detector: {test['detpixels']}x{test['detpixels']} pixels")
        print(f"Total pixels: {test['detpixels']**2:,}")
        print('-' * 70)

        with tempfile.TemporaryDirectory() as tmpdir:
            c_output = Path(tmpdir) / "c_output.bin"
            py_output = Path(tmpdir) / "py_output.bin"

            base_args = f"{test['args']} -detpixels {test['detpixels']}"

            # Run C version
            c_cmd = f"{c_bin} {base_args} -floatfile {c_output}"
            c_result = run_benchmark(c_cmd, "C implementation")

            # Run PyTorch version
            py_cmd = f"python3 -m nanobrag_torch {base_args} -floatfile {py_output}"
            py_result = run_benchmark(py_cmd, "PyTorch implementation")

            # Compare outputs if both succeeded
            comparison = None
            if c_result['success'] and py_result['success']:
                comparison = compare_outputs(c_output, py_output, test['detpixels'])

            # Calculate speedup
            speedup = None
            if c_result['success'] and py_result['success']:
                speedup = c_result['time'] / py_result['time']

            # Store results
            test_result = {
                'test': test['name'],
                'detpixels': test['detpixels'],
                'c_time': c_result['time'] if c_result['success'] else None,
                'pytorch_time': py_result['time'] if py_result['success'] else None,
                'speedup': speedup,
                'comparison': comparison,
                'c_success': c_result['success'],
                'pytorch_success': py_result['success']
            }
            results.append(test_result)

            # Print results
            if c_result['success']:
                print(f"C time: {c_result['time']:.2f} seconds")
            else:
                print(f"C failed: {c_result['error']}")

            if py_result['success']:
                print(f"PyTorch time: {py_result['time']:.2f} seconds")
            else:
                print(f"PyTorch failed: {py_result['error']}")

            if speedup:
                if speedup > 1:
                    print(f"PyTorch is {speedup:.2f}x faster")
                else:
                    print(f"C is {1/speedup:.2f}x faster")

            if comparison and 'correlation' in comparison:
                print(f"Correlation: {comparison['correlation']:.6f}")
                print(f"RMSE: {comparison['rmse']:.6f}")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)

    print("\nPerformance Results:")
    print(f"{'Test':<40} {'C (s)':<10} {'PyTorch (s)':<12} {'Speedup':<10} {'Correlation':<12}")
    print("-" * 90)

    for r in results:
        if r['c_success'] and r['pytorch_success']:
            corr = r['comparison']['correlation'] if r['comparison'] and 'correlation' in r['comparison'] else 'N/A'
            speedup_str = f"{r['speedup']:.2f}x" if r['speedup'] else 'N/A'
            if r['speedup'] and r['speedup'] < 1:
                speedup_str = f"-{1/r['speedup']:.2f}x"

            print(f"{r['test']:<40} {r['c_time']:<10.2f} {r['pytorch_time']:<12.2f} {speedup_str:<10} {corr:<12.6f}")

    # Calculate average speedup
    valid_speedups = [r['speedup'] for r in results if r['speedup'] is not None]
    if valid_speedups:
        avg_speedup = sum(valid_speedups) / len(valid_speedups)
        print(f"\nAverage speedup: {avg_speedup:.2f}x")
        if avg_speedup > 1:
            print(f"PyTorch is on average {avg_speedup:.2f}x faster than C")
        else:
            print(f"C is on average {1/avg_speedup:.2f}x faster than PyTorch")

    # Save detailed results
    with open('benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to benchmark_results.json")

if __name__ == "__main__":
    main()