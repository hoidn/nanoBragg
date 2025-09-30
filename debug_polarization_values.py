#!/usr/bin/env python3
"""
Debug script to compare polarization calculations between C and PyTorch.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import numpy as np
import subprocess
import tempfile
import torch
from pathlib import Path

def run_c_reference(args_list):
    """Run C reference with given arguments."""
    c_bin = os.environ.get('NB_C_BIN', './golden_suite_generator/nanoBragg')
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
        floatfile = f.name

    cmd = [c_bin] + args_list + ['-floatfile', floatfile]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"C binary failed: {result.stderr}")
        return None

    # Read the output
    with open(floatfile, 'rb') as f:
        data = np.fromfile(f, dtype=np.float32)

    os.unlink(floatfile)
    return data

def run_pytorch(args_list):
    """Run PyTorch implementation with given arguments."""
    import sys
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
        floatfile = f.name

    cmd = [sys.executable, '-m', 'nanobrag_torch'] + args_list + ['-floatfile', floatfile]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"PyTorch failed: {result.stderr}")
        return None

    # Read the output
    with open(floatfile, 'rb') as f:
        data = np.fromfile(f, dtype=np.float32)

    os.unlink(floatfile)
    return data

def main():
    # Test AT-PARALLEL-006 case (N=1, oversample=2, uses subpixel path)
    args = [
        '-default_F', '100',
        '-cell', '100', '100', '100', '90', '90', '90',
        '-lambda', '1.0',
        '-N', '1',
        '-distance', '50',
        '-pixel', '0.1',
        '-detpixels', '256',
        '-mosflm',
        '-seed', '1'
    ]

    print("Running AT-PARALLEL-006 case (N=1, dist=50mm, lambda=1.0)")
    print("="*70)

    c_data = run_c_reference(args)
    py_data = run_pytorch(args)

    if c_data is None or py_data is None:
        print("Failed to run one or both implementations")
        return

    # Reshape to 2D
    size = int(np.sqrt(len(c_data)))
    c_img = c_data.reshape(size, size)
    py_img = py_data.reshape(size, size)

    # Find the peak
    c_max_idx = np.unravel_index(np.argmax(c_img), c_img.shape)
    py_max_idx = np.unravel_index(np.argmax(py_img), py_img.shape)

    print(f"C peak at: {c_max_idx}, value: {c_img[c_max_idx]:.6f}")
    print(f"PyTorch peak at: {py_max_idx}, value: {py_img[py_max_idx]:.6f}")
    print()

    # Compare values at various points
    test_points = [
        (128, 128),  # Center
        (64, 64),    # Corner region
        (128, 64),   # Side
        (64, 128),   # Side
        (192, 192),  # Opposite corner
    ]

    print("Pixel-by-pixel comparison:")
    print(f"{'Position':<15} {'C Value':<15} {'Py Value':<15} {'Ratio':<10} {'Diff':<10}")
    print("-"*70)

    for pos in test_points:
        s, f = pos
        c_val = c_img[s, f]
        py_val = py_img[s, f]
        if c_val > 0:
            ratio = py_val / c_val
            diff = py_val - c_val
            print(f"{str(pos):<15} {c_val:<15.6f} {py_val:<15.6f} {ratio:<10.6f} {diff:<10.6f}")

    print()
    print("Overall statistics:")
    print(f"C sum: {c_img.sum():.6f}")
    print(f"PyTorch sum: {py_img.sum():.6f}")
    print(f"Sum ratio: {py_img.sum() / c_img.sum():.9f}")
    print(f"Correlation: {np.corrcoef(c_img.flat, py_img.flat)[0, 1]:.9f}")
    print(f"Max absolute diff: {np.abs(c_img - py_img).max():.6f}")

if __name__ == '__main__':
    main()