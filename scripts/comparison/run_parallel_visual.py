#!/usr/bin/env python3
"""
Script to run AT-PARALLEL tests with C reference and generate visual comparisons.

This script runs selected AT-PARALLEL tests that produce diffraction patterns,
executes both C and PyTorch implementations, and generates PNG visualizations
for comparison.
"""

import os
import sys
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import tempfile
import json
from typing import Dict, Any, Optional, Tuple

# Ensure environment is set
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
# Respect externally provided NB_C_BIN; do not override here. Fallbacks handled in main().

# Output directory
OUTPUT_DIR = Path("parallel_test_visuals")
OUTPUT_DIR.mkdir(exist_ok=True)


def run_command(cmd: str, cwd: str = ".", timeout: int = 60) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"


def load_float_image(filepath: Path) -> Optional[np.ndarray]:
    """Load a float32 binary image file."""
    if not filepath.exists():
        return None

    data = np.fromfile(filepath, dtype=np.float32)
    # Try to determine image dimensions
    size = int(np.sqrt(len(data)))
    if size * size == len(data):
        return data.reshape(size, size)
    return None


def generate_comparison_plot(c_image: np.ndarray,
                            py_image: np.ndarray,
                            test_name: str,
                            output_path: Path,
                            command: str = None) -> Dict[str, Any]:
    """Generate a comparison plot and compute metrics."""

    fig, axes = plt.subplots(2, 3, figsize=(15, 11))

    # Determine common color scale
    vmin = min(c_image.min(), py_image.min())
    vmax = max(c_image.max(), py_image.max())

    # Plot C reference
    im1 = axes[0, 0].imshow(c_image, cmap='viridis', origin='lower', vmin=vmin, vmax=vmax)
    axes[0, 0].set_title('C Reference')
    axes[0, 0].axis('off')
    plt.colorbar(im1, ax=axes[0, 0], fraction=0.046)

    # Plot PyTorch
    im2 = axes[0, 1].imshow(py_image, cmap='viridis', origin='lower', vmin=vmin, vmax=vmax)
    axes[0, 1].set_title('PyTorch')
    axes[0, 1].axis('off')
    plt.colorbar(im2, ax=axes[0, 1], fraction=0.046)

    # Plot difference
    diff = py_image - c_image
    im3 = axes[0, 2].imshow(diff, cmap='RdBu_r', origin='lower', vmin=-np.abs(diff).max(), vmax=np.abs(diff).max())
    axes[0, 2].set_title('Difference (PyTorch - C)')
    axes[0, 2].axis('off')
    plt.colorbar(im3, ax=axes[0, 2], fraction=0.046)

    # Log scale plots
    c_log = np.log10(np.maximum(c_image, 1e-10))
    py_log = np.log10(np.maximum(py_image, 1e-10))
    log_vmin = min(c_log.min(), py_log.min())
    log_vmax = max(c_log.max(), py_log.max())

    im4 = axes[1, 0].imshow(c_log, cmap='viridis', origin='lower', vmin=log_vmin, vmax=log_vmax)
    axes[1, 0].set_title('C Reference (log scale)')
    axes[1, 0].axis('off')
    plt.colorbar(im4, ax=axes[1, 0], fraction=0.046)

    im5 = axes[1, 1].imshow(py_log, cmap='viridis', origin='lower', vmin=log_vmin, vmax=log_vmax)
    axes[1, 1].set_title('PyTorch (log scale)')
    axes[1, 1].axis('off')
    plt.colorbar(im5, ax=axes[1, 1], fraction=0.046)

    # Histogram of intensities
    axes[1, 2].hist(c_image.flatten(), bins=50, alpha=0.5, label='C', color='blue')
    axes[1, 2].hist(py_image.flatten(), bins=50, alpha=0.5, label='PyTorch', color='red')
    axes[1, 2].set_xlabel('Intensity')
    axes[1, 2].set_ylabel('Count')
    axes[1, 2].set_title('Intensity Distribution')
    axes[1, 2].legend()
    axes[1, 2].set_yscale('log')

    # Create title with command if provided
    if command:
        # Wrap long commands
        import textwrap
        wrapped_cmd = '\n'.join(textwrap.wrap(command, width=100))
        title = f'{test_name}\nCommand: {wrapped_cmd}'
        fig.suptitle(title, fontsize=10, y=0.98)
    else:
        fig.suptitle(f'{test_name} Comparison', fontsize=14, y=0.98)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    # Compute metrics
    correlation = np.corrcoef(c_image.flatten(), py_image.flatten())[0, 1]
    rmse = np.sqrt(np.mean((c_image - py_image)**2))
    max_diff = np.abs(diff).max()
    relative_rmse = rmse / np.mean(c_image)

    metrics = {
        'correlation': float(correlation),
        'rmse': float(rmse),
        'max_diff': float(max_diff),
        'relative_rmse': float(relative_rmse),
        'c_max': float(c_image.max()),
        'py_max': float(py_image.max()),
        'c_mean': float(c_image.mean()),
        'py_mean': float(py_image.mean())
    }

    return metrics


# Define test configurations
TEST_CONFIGS = {
    'AT-PARALLEL-001': {
        'name': 'Beam Center Scaling',
        'sizes': [64, 128, 256, 512],
        'base_args': '-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 3 -distance 100'
    },
    'AT-PARALLEL-002': {
        'name': 'Pixel Size Independence',
        'pixel_sizes': [0.05, 0.1, 0.2, 0.4],
        'base_args': '-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 256 -distance 100'
    },
    'AT-PARALLEL-004': {
        'name': 'MOSFLM 0.5 Pixel Offset',
        'conventions': ['mosflm', 'xds'],
        'base_args': '-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100'
    },
    'AT-PARALLEL-006': {
        'name': 'Single Reflection Position',
        'distances': [50, 100, 200],
        'base_args': '-default_F 100 -cell 100 100 100 90 90 90 -N 5 -detpixels 256'
    },
    'AT-PARALLEL-007': {
        'name': 'Peak Position with Rotations',
        'rotations': [(0, 0, 0), (5, 3, 2), (10, 5, 3)],
        'base_args': '-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -N 5 -detpixels 256 -distance 100 -mosflm'
    },
    'AT-PARALLEL-012': {
        'name': 'Reference Pattern - Simple Cubic',
        'configs': [
            {
                'name': 'simple_cubic',
                'args': '-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 1024 -distance 100'
            },
            {
                'name': 'triclinic',
                'args': '-default_F 100 -cell 70 80 90 75 85 95 -lambda 1.0 -N 5 -detpixels 512 -distance 100 -misset 10 5 3'
            }
        ]
    },
    'AT-PARALLEL-026': {
        'name': 'Triclinic Absolute Position',
        'configs': [
            {
                'name': 'triclinic',
                'args': '-default_F 100 -cell 70 80 90 85 95 105 -lambda 1.5 -N 1 -detpixels 256 -distance 150 -misset 5 3 2'
            },
            {
                'name': 'cubic_compare',
                'args': '-default_F 100 -cell 80 80 80 90 90 90 -lambda 1.5 -N 1 -detpixels 256 -distance 150 -misset 5 3 2'
            }
        ]
    }
}


def main():
    """Run visual comparisons for selected AT-PARALLEL tests."""

    print("=" * 60)
    print("AT-PARALLEL Visual Comparison Generator")
    print("=" * 60)

    # Resolve C binary path with fallbacks
    c_bin = os.environ.get('NB_C_BIN')
    if not c_bin:
        # Prefer golden_suite_generator if present, else root-level nanoBragg
        golden = Path('./golden_suite_generator/nanoBragg')
        root = Path('./nanoBragg')
        if golden.exists():
            c_bin = str(golden)
        elif root.exists():
            c_bin = str(root)
        else:
            c_bin = './golden_suite_generator/nanoBragg'  # default for message

    if not Path(c_bin).exists():
        print(f"ERROR: C binary not found at {c_bin}")
        print("Set NB_C_BIN to a valid path (e.g., ./nanoBragg) and re-run.")
        return
    else:
        print(f"Using NB_C_BIN={c_bin}")

    summary = {}

    for test_id, test_config in TEST_CONFIGS.items():
        print(f"\nProcessing {test_id}: {test_config['name']}")
        print("-" * 40)

        test_dir = OUTPUT_DIR / test_id
        test_dir.mkdir(exist_ok=True)

        test_results = []

        if 'sizes' in test_config:
            # Test with different detector sizes
            for size in test_config['sizes']:
                print(f"  Testing size {size}x{size}...")

                with tempfile.TemporaryDirectory() as tmpdir:
                    c_output = Path(tmpdir) / "c_output.bin"
                    py_output = Path(tmpdir) / "py_output.bin"

                    # Run C version
                    base_cmd = f"{test_config['base_args']} -detpixels {size}"
                    c_cmd = f"{c_bin} {base_cmd} -floatfile {c_output}"
                    ret, _, _ = run_command(c_cmd)

                    # Run PyTorch version
                    py_cmd = f"{sys.executable} -m nanobrag_torch {base_cmd} -floatfile {py_output}"
                    ret, _, _ = run_command(py_cmd)

                    # Load and compare
                    c_img = load_float_image(c_output)
                    py_img = load_float_image(py_output)

                    if c_img is not None and py_img is not None:
                        output_path = test_dir / f"comparison_{size}x{size}.png"
                        metrics = generate_comparison_plot(c_img, py_img, f"{test_id} ({size}x{size})", output_path, base_cmd)

                        test_results.append({
                            'config': f'{size}x{size}',
                            'metrics': metrics
                        })

                        print(f"    Correlation: {metrics['correlation']:.4f}")

        elif 'pixel_sizes' in test_config:
            # Test with different pixel sizes
            for pixel_size in test_config['pixel_sizes']:
                print(f"  Testing pixel size {pixel_size}mm...")

                with tempfile.TemporaryDirectory() as tmpdir:
                    c_output = Path(tmpdir) / "c_output.bin"
                    py_output = Path(tmpdir) / "py_output.bin"

                    # Run C version
                    base_cmd = f"{test_config['base_args']} -pixel {pixel_size}"
                    c_cmd = f"{c_bin} {base_cmd} -floatfile {c_output}"
                    ret, _, _ = run_command(c_cmd)

                    # Run PyTorch version
                    py_cmd = f"{sys.executable} -m nanobrag_torch {base_cmd} -floatfile {py_output}"
                    ret, _, _ = run_command(py_cmd)

                    # Load and compare
                    c_img = load_float_image(c_output)
                    py_img = load_float_image(py_output)

                    if c_img is not None and py_img is not None:
                        output_path = test_dir / f"comparison_pixel_{pixel_size}mm.png"
                        metrics = generate_comparison_plot(c_img, py_img, f"{test_id} (pixel {pixel_size}mm)", output_path, base_cmd)

                        test_results.append({
                            'config': f'pixel_{pixel_size}mm',
                            'metrics': metrics
                        })

                        print(f"    Correlation: {metrics['correlation']:.4f}")

        elif 'conventions' in test_config:
            # Test with different conventions
            for convention in test_config['conventions']:
                print(f"  Testing convention {convention}...")

                with tempfile.TemporaryDirectory() as tmpdir:
                    c_output = Path(tmpdir) / "c_output.bin"
                    py_output = Path(tmpdir) / "py_output.bin"

                    # Run C version
                    base_cmd = f"{test_config['base_args']} -{convention}"
                    c_cmd = f"{c_bin} {base_cmd} -floatfile {c_output}"
                    ret, _, _ = run_command(c_cmd)

                    # Run PyTorch version
                    py_cmd = f"{sys.executable} -m nanobrag_torch {base_cmd} -floatfile {py_output}"
                    ret, _, _ = run_command(py_cmd)

                    # Load and compare
                    c_img = load_float_image(c_output)
                    py_img = load_float_image(py_output)

                    if c_img is not None and py_img is not None:
                        output_path = test_dir / f"comparison_{convention}.png"
                        metrics = generate_comparison_plot(c_img, py_img, f"{test_id} ({convention})", output_path, base_cmd)

                        test_results.append({
                            'config': convention,
                            'metrics': metrics
                        })

                        print(f"    Correlation: {metrics['correlation']:.4f}")

        elif 'distances' in test_config:
            # Test with different distances
            for distance in test_config['distances']:
                print(f"  Testing distance {distance}mm...")

                with tempfile.TemporaryDirectory() as tmpdir:
                    c_output = Path(tmpdir) / "c_output.bin"
                    py_output = Path(tmpdir) / "py_output.bin"

                    # Run C version
                    base_cmd = f"{test_config['base_args']} -distance {distance} -lambda 1.0"
                    c_cmd = f"{c_bin} {base_cmd} -floatfile {c_output}"
                    ret, _, _ = run_command(c_cmd)

                    # Run PyTorch version
                    py_cmd = f"{sys.executable} -m nanobrag_torch {base_cmd} -floatfile {py_output}"
                    ret, _, _ = run_command(py_cmd)

                    # Load and compare
                    c_img = load_float_image(c_output)
                    py_img = load_float_image(py_output)

                    if c_img is not None and py_img is not None:
                        output_path = test_dir / f"comparison_distance_{distance}mm.png"
                        metrics = generate_comparison_plot(c_img, py_img, f"{test_id} ({distance}mm)", output_path, base_cmd)

                        test_results.append({
                            'config': f'distance_{distance}mm',
                            'metrics': metrics
                        })

                        print(f"    Correlation: {metrics['correlation']:.4f}")

        elif 'rotations' in test_config:
            # Test with different rotations
            for rotx, roty, rotz in test_config['rotations']:
                print(f"  Testing rotations ({rotx}, {roty}, {rotz})...")

                with tempfile.TemporaryDirectory() as tmpdir:
                    c_output = Path(tmpdir) / "c_output.bin"
                    py_output = Path(tmpdir) / "py_output.bin"

                    # Run C version
                    base_cmd = f"{test_config['base_args']} -detector_rotx {rotx} -detector_roty {roty} -detector_rotz {rotz}"
                    c_cmd = f"{c_bin} {base_cmd} -floatfile {c_output}"
                    ret, _, _ = run_command(c_cmd)

                    # Run PyTorch version
                    py_cmd = f"{sys.executable} -m nanobrag_torch {base_cmd} -floatfile {py_output}"
                    ret, _, _ = run_command(py_cmd)

                    # Load and compare
                    c_img = load_float_image(c_output)
                    py_img = load_float_image(py_output)

                    if c_img is not None and py_img is not None:
                        output_path = test_dir / f"comparison_rot_{rotx}_{roty}_{rotz}.png"
                        metrics = generate_comparison_plot(c_img, py_img, f"{test_id} (rot {rotx},{roty},{rotz})", output_path, base_cmd)

                        test_results.append({
                            'config': f'rot_{rotx}_{roty}_{rotz}',
                            'metrics': metrics
                        })

                        print(f"    Correlation: {metrics['correlation']:.4f}")

        elif 'configs' in test_config:
            # Test with specific configurations
            for config in test_config['configs']:
                print(f"  Testing {config['name']}...")

                with tempfile.TemporaryDirectory() as tmpdir:
                    c_output = Path(tmpdir) / "c_output.bin"
                    py_output = Path(tmpdir) / "py_output.bin"

                    # Run C version
                    base_cmd = config['args']
                    c_cmd = f"{c_bin} {base_cmd} -floatfile {c_output}"
                    ret, _, _ = run_command(c_cmd)

                    # Run PyTorch version
                    py_cmd = f"python3 -m nanobrag_torch {base_cmd} -floatfile {py_output}"
                    ret, _, _ = run_command(py_cmd)

                    # Load and compare
                    c_img = load_float_image(c_output)
                    py_img = load_float_image(py_output)

                    if c_img is not None and py_img is not None:
                        output_path = test_dir / f"comparison_{config['name']}.png"
                        metrics = generate_comparison_plot(c_img, py_img, f"{test_id} ({config['name']})", output_path, base_cmd)

                        test_results.append({
                            'config': config['name'],
                            'metrics': metrics
                        })

                        print(f"    Correlation: {metrics['correlation']:.4f}")

        # Save test summary
        if test_results:
            summary[test_id] = {
                'name': test_config['name'],
                'results': test_results
            }

            with open(test_dir / 'metrics.json', 'w') as f:
                json.dump(test_results, f, indent=2)

    # Generate overall summary
    print("\n" + "=" * 60)
    print("Summary of Results")
    print("=" * 60)

    for test_id, test_data in summary.items():
        print(f"\n{test_id}: {test_data['name']}")

        correlations = [r['metrics']['correlation'] for r in test_data['results']]
        if correlations:
            print(f"  Average correlation: {np.mean(correlations):.4f}")
            print(f"  Min correlation: {np.min(correlations):.4f}")
            print(f"  Max correlation: {np.max(correlations):.4f}")

    # Save overall summary
    with open(OUTPUT_DIR / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to: {OUTPUT_DIR}")
    print(f"Total visualizations generated: {sum(len(t['results']) for t in summary.values())}")


if __name__ == "__main__":
    main()
