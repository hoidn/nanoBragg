#!/usr/bin/env python
"""
nb_compare.py - Dual-Runner Comparison Script for C and PyTorch nanoBragg

Implementation of AT-TOOLS-001 from spec-a.md:963-1012

Purpose: Run the C and PyTorch implementations with identical arguments;
capture runtimes; compute comparison metrics; save preview images and
a reproducible artifact bundle.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def find_c_binary(c_bin_path: Optional[str] = None) -> Path:
    """Find the C nanoBragg binary following the spec's resolution order."""
    # 1. Explicit --c-bin argument
    if c_bin_path:
        path = Path(c_bin_path)
        if path.exists():
            return path.resolve()
        raise FileNotFoundError(f"Specified C binary not found: {c_bin_path}")

    # 2. NB_C_BIN environment variable
    if 'NB_C_BIN' in os.environ:
        path = Path(os.environ['NB_C_BIN'])
        if path.exists():
            return path.resolve()
        raise FileNotFoundError(f"NB_C_BIN binary not found: {os.environ['NB_C_BIN']}")

    # 3. ./golden_suite_generator/nanoBragg if present
    path = Path('./golden_suite_generator/nanoBragg')
    if path.exists():
        return path.resolve()

    # 4. ./nanoBragg
    path = Path('./nanoBragg')
    if path.exists():
        return path.resolve()

    # 5. Error with guidance
    raise FileNotFoundError(
        "C nanoBragg binary not found. Please specify using:\n"
        "  --c-bin PATH\n"
        "  or set NB_C_BIN environment variable\n"
        "  or ensure ./nanoBragg or ./golden_suite_generator/nanoBragg exists"
    )


def find_py_binary(py_bin_path: Optional[str] = None) -> List[str]:
    """Find the PyTorch nanoBragg runner following the spec's resolution order."""
    # 1. Explicit --py-bin argument
    if py_bin_path:
        if py_bin_path.endswith('.py'):
            return ['python', py_bin_path]
        return [py_bin_path]

    # 2. NB_PY_BIN environment variable
    if 'NB_PY_BIN' in os.environ:
        py_bin = os.environ['NB_PY_BIN']
        if py_bin.endswith('.py'):
            return ['python', py_bin]
        return [py_bin]

    # 3. Try nanoBragg on PATH
    try:
        subprocess.run(['nanoBragg', '-h'], capture_output=True, check=False)
        return ['nanoBragg']
    except FileNotFoundError:
        pass

    # 4. Default to python -m nanobrag_torch
    return ['python', '-m', 'nanobrag_torch']


def run_simulation(
    cmd: List[str],
    float_file: str,
    capture_stdout: bool = True
) -> Tuple[float, str, str]:
    """Run a simulation and capture runtime, stdout, stderr."""
    # Ensure -floatfile is set
    if '-floatfile' not in cmd:
        cmd.extend(['-floatfile', float_file])
    else:
        # Replace the existing floatfile
        idx = cmd.index('-floatfile')
        cmd[idx + 1] = float_file

    start_time = time.monotonic()
    result = subprocess.run(
        cmd,
        capture_output=capture_stdout,
        text=True,
        env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
    )
    runtime = time.monotonic() - start_time

    return runtime, result.stdout, result.stderr


def load_float_image(filepath: str) -> np.ndarray:
    """Load a float image from binary file."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Float image not found: {filepath}")

    # Try to infer dimensions from file size
    filesize = Path(filepath).stat().st_size
    n_pixels = filesize // 4  # float32

    # Common detector sizes to try
    common_sizes = [
        (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024),
        (2048, 2048), (4096, 4096)
    ]

    data = np.fromfile(filepath, dtype=np.float32)

    # Try to find matching size
    for h, w in common_sizes:
        if h * w == n_pixels:
            return data.reshape(h, w)

    # If no match, try square
    sqrt = int(np.sqrt(n_pixels))
    if sqrt * sqrt == n_pixels:
        return data.reshape(sqrt, sqrt)

    # Fall back to 1D
    print(f"Warning: Could not determine image dimensions for {n_pixels} pixels")
    return data


def resample_image(img: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
    """Resample image to target shape using nearest neighbor."""
    from scipy.ndimage import zoom

    zoom_factors = (target_shape[0] / img.shape[0], target_shape[1] / img.shape[1])
    return zoom(img, zoom_factors, order=0)  # order=0 for nearest neighbor


def compute_metrics(
    c_img: np.ndarray,
    py_img: np.ndarray,
    roi: Optional[Tuple[int, int, int, int]] = None
) -> Dict:
    """Compute comparison metrics between C and PyTorch images."""
    # Apply ROI if specified
    if roi:
        xmin, xmax, ymin, ymax = roi
        c_img = c_img[ymin:ymax+1, xmin:xmax+1]
        py_img = py_img[ymin:ymax+1, xmin:xmax+1]

    # Flatten for correlation
    c_flat = c_img.flatten()
    py_flat = py_img.flatten()

    # Compute metrics
    metrics = {}

    # Pearson correlation
    if np.std(c_flat) > 0 and np.std(py_flat) > 0:
        metrics['correlation'] = np.corrcoef(c_flat, py_flat)[0, 1]
    else:
        metrics['correlation'] = np.nan

    # MSE and RMSE
    mse = np.mean((c_flat - py_flat) ** 2)
    metrics['mse'] = float(mse)
    metrics['rmse'] = float(np.sqrt(mse))

    # Max absolute difference
    metrics['max_abs_diff'] = float(np.max(np.abs(c_flat - py_flat)))

    # Sums and ratio
    c_sum = np.sum(c_flat)
    py_sum = np.sum(py_flat)
    metrics['c_sum'] = float(c_sum)
    metrics['py_sum'] = float(py_sum)
    metrics['sum_ratio'] = float(py_sum / c_sum) if c_sum != 0 else np.inf

    # Peak finding (top N peaks)
    n_peaks = 10
    c_peaks = find_peaks(c_img, n_peaks)
    py_peaks = find_peaks(py_img, n_peaks)

    # Match peaks and compute alignment
    if c_peaks and py_peaks:
        peak_distances = []
        for c_peak in c_peaks:
            distances = [np.linalg.norm(np.array(c_peak) - np.array(p))
                        for p in py_peaks]
            peak_distances.append(min(distances))
        metrics['mean_peak_distance'] = float(np.mean(peak_distances))
        metrics['max_peak_distance'] = float(np.max(peak_distances))
    else:
        metrics['mean_peak_distance'] = np.nan
        metrics['max_peak_distance'] = np.nan

    return metrics


def find_peaks(img: np.ndarray, n_peaks: int) -> List[Tuple[int, int]]:
    """Find top N peaks in image."""
    from scipy.ndimage import maximum_filter

    # Find local maxima
    local_max = (maximum_filter(img, size=3) == img)

    # Get peak values and positions
    peak_mask = local_max & (img > np.percentile(img, 95))
    peak_coords = np.argwhere(peak_mask)
    peak_values = img[peak_mask]

    # Sort by value and take top N
    if len(peak_values) > 0:
        sorted_idx = np.argsort(peak_values)[::-1][:n_peaks]
        return [(int(coord[0]), int(coord[1]))
                for coord in peak_coords[sorted_idx]]
    return []


def save_png_previews(
    c_img: np.ndarray,
    py_img: np.ndarray,
    diff_img: np.ndarray,
    outdir: Path,
    png_scale: int = 99
) -> None:
    """Save PNG preview images."""
    try:
        from PIL import Image
    except ImportError:
        print("Warning: PIL not available, skipping PNG previews")
        return

    # Scale to percentile
    def scale_to_uint8(img, percentile):
        vmax = np.percentile(img[img > 0], percentile) if np.any(img > 0) else 1.0
        scaled = np.clip(img / vmax * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(scaled)

    # Save images
    scale_to_uint8(c_img, png_scale).save(outdir / 'c_output.png')
    scale_to_uint8(py_img, png_scale).save(outdir / 'py_output.png')

    # For diff, use symmetric scaling
    vmax = np.percentile(np.abs(diff_img), png_scale)
    diff_scaled = np.clip((diff_img + vmax) / (2 * vmax) * 255, 0, 255).astype(np.uint8)
    Image.fromarray(diff_scaled).save(outdir / 'diff.png')


def main():
    parser = argparse.ArgumentParser(
        description='Compare C and PyTorch nanoBragg implementations',
        usage='nb-compare [options] -- ARGS...'
    )

    parser.add_argument('--outdir', type=str, default='comparison_artifacts',
                       help='Output directory for artifacts')
    parser.add_argument('--roi', type=int, nargs=4, metavar=('xmin', 'xmax', 'ymin', 'ymax'),
                       help='ROI for metric computation')
    parser.add_argument('--threshold', type=float, default=0.95,
                       help='Correlation threshold for pass/fail')
    parser.add_argument('--resample', action='store_true',
                       help='Resample images if shapes differ')
    parser.add_argument('--png-scale', type=int, default=99, metavar='PCTL',
                       help='Percentile for PNG scaling (default: 99)')
    parser.add_argument('--save-diff', action='store_true',
                       help='Save difference image')
    parser.add_argument('--c-bin', type=str, help='Path to C nanoBragg binary')
    parser.add_argument('--py-bin', type=str, help='Path to PyTorch runner')
    parser.add_argument('args', nargs='*', help='Arguments to pass to both runners')

    # Handle the -- separator
    if '--' in sys.argv:
        idx = sys.argv.index('--')
        args = parser.parse_args(sys.argv[1:idx])
        args.args = sys.argv[idx+1:]
    else:
        args = parser.parse_args()

    # Create output directory
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Find binaries
    try:
        c_bin = find_c_binary(args.c_bin)
        py_cmd = find_py_binary(args.py_bin)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 3

    print(f"C binary: {c_bin}")
    print(f"PyTorch command: {' '.join(py_cmd)}")

    # Prepare commands with temp float files
    with tempfile.NamedTemporaryFile(suffix='_c.bin', delete=False) as c_float_file:
        c_float_path = c_float_file.name
    with tempfile.NamedTemporaryFile(suffix='_py.bin', delete=False) as py_float_file:
        py_float_path = py_float_file.name

    try:
        # Run C implementation
        print("\nRunning C implementation...")
        c_cmd = [str(c_bin)] + args.args
        c_runtime, c_stdout, c_stderr = run_simulation(c_cmd, c_float_path)
        print(f"C runtime: {c_runtime:.3f} s")

        # Save C outputs
        with open(outdir / 'c_stdout.txt', 'w') as f:
            f.write(c_stdout)
        with open(outdir / 'c_stderr.txt', 'w') as f:
            f.write(c_stderr)

        # Run PyTorch implementation
        print("Running PyTorch implementation...")
        py_cmd_full = py_cmd + args.args
        py_runtime, py_stdout, py_stderr = run_simulation(py_cmd_full, py_float_path)
        print(f"Py runtime: {py_runtime:.3f} s")

        # Save PyTorch outputs
        with open(outdir / 'py_stdout.txt', 'w') as f:
            f.write(py_stdout)
        with open(outdir / 'py_stderr.txt', 'w') as f:
            f.write(py_stderr)

        # Load float images
        print("\nLoading float images...")
        c_img = load_float_image(c_float_path)
        py_img = load_float_image(py_float_path)

        print(f"C image shape: {c_img.shape}")
        print(f"PyTorch image shape: {py_img.shape}")

        # Handle shape mismatch
        if c_img.shape != py_img.shape:
            if args.resample:
                print(f"Resampling PyTorch image from {py_img.shape} to {c_img.shape}")
                py_img = resample_image(py_img, c_img.shape)
                resample_note = f"PyTorch image resampled from {py_img.shape} to {c_img.shape}"
            else:
                print(f"Error: Image shapes differ and --resample not specified", file=sys.stderr)
                return 4
        else:
            resample_note = None

        # Compute metrics
        print("\nComputing metrics...")
        metrics = compute_metrics(c_img, py_img, args.roi)

        # Add runtime info
        metrics['c_runtime_s'] = c_runtime
        metrics['py_runtime_s'] = py_runtime
        metrics['speedup'] = c_runtime / py_runtime if py_runtime > 0 else np.inf

        if resample_note:
            metrics['resample_note'] = resample_note

        # Print summary
        print("\n" + "="*50)
        print("COMPARISON SUMMARY")
        print("="*50)
        print(f"Correlation: {metrics['correlation']:.6f}")
        print(f"RMSE: {metrics['rmse']:.6f}")
        print(f"Max absolute difference: {metrics['max_abs_diff']:.6f}")
        print(f"C sum: {metrics['c_sum']:.2f}")
        print(f"Py sum: {metrics['py_sum']:.2f}")
        print(f"Sum ratio (Py/C): {metrics['sum_ratio']:.6f}")
        if not np.isnan(metrics.get('mean_peak_distance', np.nan)):
            print(f"Mean peak distance: {metrics['mean_peak_distance']:.2f} pixels")
            print(f"Max peak distance: {metrics['max_peak_distance']:.2f} pixels")
        print(f"Runtime speedup (C/Py): {metrics['speedup']:.2f}x")

        # Save JSON summary
        with open(outdir / 'summary.json', 'w') as f:
            json.dump(metrics, f, indent=2)

        # Save PNG previews
        print(f"\nSaving PNG previews to {outdir}/")
        diff_img = py_img - c_img
        save_png_previews(c_img, py_img, diff_img, outdir, args.png_scale)

        # Save difference image if requested
        if args.save_diff:
            diff_path = outdir / 'diff.bin'
            diff_img.astype(np.float32).tofile(diff_path)
            print(f"Saved difference image to {diff_path}")

        # Pass/fail based on correlation threshold
        if metrics['correlation'] >= args.threshold:
            print(f"\n✓ PASS: Correlation {metrics['correlation']:.6f} >= {args.threshold}")
            return 0
        else:
            print(f"\n✗ FAIL: Correlation {metrics['correlation']:.6f} < {args.threshold}")
            return 1

    finally:
        # Clean up temp files
        Path(c_float_path).unlink(missing_ok=True)
        Path(py_float_path).unlink(missing_ok=True)


if __name__ == '__main__':
    sys.exit(main())