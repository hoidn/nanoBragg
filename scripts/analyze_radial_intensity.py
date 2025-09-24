#!/usr/bin/env python3
"""
Analyze radial intensity discrepancy between PyTorch and C implementations.

Per fix_plan.md, there's a small monotonic increase in intensity ratio with distance
from detector center. This script analyzes the pattern in detail.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import subprocess
import tempfile

# Ensure MKL compatibility
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def run_simulation(implementation, args_str, output_file):
    """Run either C or PyTorch implementation with given arguments."""
    if implementation == "C":
        # Use C binary
        c_bin = os.environ.get('NB_C_BIN', './nanoBragg')
        if not Path(c_bin).exists():
            c_bin = './golden_suite_generator/nanoBragg'
        if not Path(c_bin).exists():
            raise FileNotFoundError("C binary not found")

        cmd = f"{c_bin} {args_str} -floatfile {output_file}"
    else:
        # Use PyTorch implementation
        cmd = f"python -m nanobrag_torch {args_str} -floatfile {output_file}"

    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {implementation}: {result.stderr}")
        raise RuntimeError(f"Failed to run {implementation}")

    return output_file

def load_float_image(filepath):
    """Load a raw float image."""
    data = np.fromfile(filepath, dtype=np.float32)
    # Assume square detector
    size = int(np.sqrt(len(data)))
    if size * size != len(data):
        raise ValueError(f"Non-square detector: {len(data)} pixels")
    return data.reshape(size, size)

def compute_radial_profile(image, center=None):
    """Compute radial intensity profile from center."""
    if center is None:
        center = (image.shape[0] // 2, image.shape[1] // 2)

    y, x = np.ogrid[:image.shape[0], :image.shape[1]]
    r = np.sqrt((x - center[1])**2 + (y - center[0])**2)
    r = r.astype(int)

    # Compute mean intensity at each radius
    radii = np.unique(r)
    profile = np.zeros_like(radii, dtype=float)

    for i, radius in enumerate(radii):
        mask = (r == radius)
        if np.any(mask):
            profile[i] = np.mean(image[mask])

    return radii, profile

def analyze_radial_discrepancy(test_args):
    """Analyze radial intensity patterns for C vs PyTorch."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Run both implementations
        c_output = Path(tmpdir) / "c_output.bin"
        py_output = Path(tmpdir) / "py_output.bin"

        c_image = run_simulation("C", test_args, str(c_output))
        py_image = run_simulation("PyTorch", test_args, str(py_output))

        # Load images
        c_data = load_float_image(c_image)
        py_data = load_float_image(py_image)

        # Compute overall statistics
        correlation = np.corrcoef(c_data.flatten(), py_data.flatten())[0, 1]
        ratio_map = np.where(c_data > 0, py_data / c_data, 1.0)

        print(f"\nOverall Statistics:")
        print(f"  Correlation: {correlation:.6f}")
        print(f"  Mean ratio (PyTorch/C): {np.mean(ratio_map):.6f}")
        print(f"  Ratio std dev: {np.std(ratio_map):.6f}")

        # Compute radial profiles
        center = (c_data.shape[0] // 2, c_data.shape[1] // 2)
        c_radii, c_profile = compute_radial_profile(c_data, center)
        py_radii, py_profile = compute_radial_profile(py_data, center)

        # Compute ratio profile
        ratio_profile = np.where(c_profile > 0, py_profile / c_profile, 1.0)

        # Divide into radial zones
        max_radius = min(c_data.shape) // 2
        inner_mask = c_radii < max_radius * 0.3
        middle_mask = (c_radii >= max_radius * 0.3) & (c_radii < max_radius * 0.7)
        outer_mask = c_radii >= max_radius * 0.7

        print(f"\nRadial Zone Analysis:")
        print(f"  Inner (<{max_radius*0.3:.0f} px): ratio = {np.mean(ratio_profile[inner_mask]):.6f}")
        print(f"  Middle ({max_radius*0.3:.0f}-{max_radius*0.7:.0f} px): ratio = {np.mean(ratio_profile[middle_mask]):.6f}")
        print(f"  Outer (>{max_radius*0.7:.0f} px): ratio = {np.mean(ratio_profile[outer_mask]):.6f}")

        # Fit linear trend to log of radial profile ratio
        valid = (c_radii > 10) & (ratio_profile > 0)  # Skip very center
        if np.sum(valid) > 2:
            coeffs = np.polyfit(c_radii[valid], np.log(ratio_profile[valid]), 1)
            trend = np.exp(coeffs[0] * c_radii + coeffs[1])
            radial_slope_pct = coeffs[0] * 100  # Percent change per pixel
            print(f"\nRadial Trend:")
            print(f"  Slope: {radial_slope_pct:.4f}% per pixel")
            print(f"  Extrapolated ratio at r=0: {np.exp(coeffs[1]):.6f}")
            print(f"  Extrapolated ratio at r={max_radius}: {np.exp(coeffs[0]*max_radius + coeffs[1]):.6f}")

        # Create diagnostic plots
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))

        # C image
        im1 = axes[0, 0].imshow(np.log10(c_data + 1e-10), cmap='viridis')
        axes[0, 0].set_title('C Implementation (log10)')
        plt.colorbar(im1, ax=axes[0, 0])

        # PyTorch image
        im2 = axes[0, 1].imshow(np.log10(py_data + 1e-10), cmap='viridis')
        axes[0, 1].set_title('PyTorch Implementation (log10)')
        plt.colorbar(im2, ax=axes[0, 1])

        # Ratio map
        im3 = axes[0, 2].imshow(ratio_map, cmap='RdBu_r', vmin=0.97, vmax=1.03)
        axes[0, 2].set_title('Ratio (PyTorch/C)')
        plt.colorbar(im3, ax=axes[0, 2])

        # Radial profiles
        axes[1, 0].plot(c_radii, c_profile, label='C', alpha=0.7)
        axes[1, 0].plot(py_radii, py_profile, label='PyTorch', alpha=0.7)
        axes[1, 0].set_xlabel('Radius (pixels)')
        axes[1, 0].set_ylabel('Mean Intensity')
        axes[1, 0].set_title('Radial Intensity Profiles')
        axes[1, 0].legend()
        axes[1, 0].set_yscale('log')

        # Ratio profile
        axes[1, 1].plot(c_radii, ratio_profile, 'b-', alpha=0.5, label='Actual')
        if 'trend' in locals():
            axes[1, 1].plot(c_radii, trend, 'r--', label='Exponential fit')
        axes[1, 1].axhline(y=1.0, color='k', linestyle=':', alpha=0.5)
        axes[1, 1].set_xlabel('Radius (pixels)')
        axes[1, 1].set_ylabel('Intensity Ratio (PyTorch/C)')
        axes[1, 1].set_title('Radial Intensity Ratio')
        axes[1, 1].legend()
        axes[1, 1].set_ylim([0.98, 1.05])

        # Difference map
        diff = py_data - c_data
        im6 = axes[1, 2].imshow(diff, cmap='RdBu_r', vmin=-np.percentile(np.abs(diff), 95),
                                vmax=np.percentile(np.abs(diff), 95))
        axes[1, 2].set_title('Difference (PyTorch - C)')
        plt.colorbar(im6, ax=axes[1, 2])

        plt.suptitle(f'Radial Intensity Analysis\nCorrelation: {correlation:.6f}')
        plt.tight_layout()

        # Save plot
        output_path = Path("radial_intensity_analysis.png")
        plt.savefig(output_path, dpi=150)
        print(f"\nAnalysis plot saved to: {output_path}")

        return correlation, ratio_profile

def main():
    parser = argparse.ArgumentParser(description='Analyze radial intensity discrepancy')
    parser.add_argument('--args', type=str,
                      default='-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 256 -distance 100 -pixel 0.4',
                      help='Arguments to pass to both implementations')

    args = parser.parse_args()

    print("Analyzing radial intensity discrepancy between C and PyTorch")
    print(f"Test arguments: {args.args}")

    correlation, ratio_profile = analyze_radial_discrepancy(args.args)

    if correlation < 0.995:
        print(f"\nWARNING: Correlation {correlation:.6f} is below spec requirement of 0.995")
    else:
        print(f"\nCorrelation {correlation:.6f} exceeds spec requirement of 0.995")

    # Check if radial trend is significant
    max_ratio = np.max(ratio_profile)
    min_ratio = np.min(ratio_profile)
    if max_ratio - min_ratio > 0.05:  # 5% variation
        print("\nSignificant radial intensity variation detected (>5%)")
        print("This may indicate differences in:")
        print("  - Solid angle calculations")
        print("  - Obliquity corrections")
        print("  - Distance calculations in rotated coordinate systems")
    else:
        print("\nRadial intensity variation is within acceptable limits (<5%)")

if __name__ == "__main__":
    main()