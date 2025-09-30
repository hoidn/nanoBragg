#!/usr/bin/env python3
"""
Diagnostic script for AT-PARALLEL-012 simple_cubic correlation gap.

Current status: corr=0.9946, need corr≥0.9995 (0.5% short)
Root cause identified (Attempt #2): Convention mismatch fixed (ADXV→MOSFLM),
but remaining 0.5% gap requires parallel trace analysis.

This script generates:
- Quantitative metrics (correlation, MSE, RMSE, max|Δ|, sum ratio)
- Diff heatmap (log1p scale)
- Peak diagnostics
- Artifacts saved to reports/2025-09-30-AT-PARALLEL-012/simple_cubic/
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import json
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def load_golden_float_image(filepath, shape):
    """Load binary float image from C code."""
    with open(filepath, 'rb') as f:
        data = np.fromfile(f, dtype=np.float32)
    return data.reshape(shape)


def compute_metrics(c_img, py_img):
    """Compute quantitative metrics."""
    c_flat = c_img.flatten()
    py_flat = py_img.flatten()

    # Correlation
    corr, _ = pearsonr(c_flat, py_flat)

    # MSE, RMSE
    mse = np.mean((c_flat - py_flat) ** 2)
    rmse = np.sqrt(mse)

    # Max absolute difference
    max_abs_diff = np.max(np.abs(c_flat - py_flat))

    # Sum ratio
    c_sum = np.sum(c_flat)
    py_sum = np.sum(py_flat)
    sum_ratio = py_sum / c_sum if c_sum > 0 else 0

    return {
        'correlation': float(corr),
        'mse': float(mse),
        'rmse': float(rmse),
        'max_abs_diff': float(max_abs_diff),
        'c_sum': float(c_sum),
        'py_sum': float(py_sum),
        'sum_ratio': float(sum_ratio)
    }


def plot_diff_heatmap(c_img, py_img, output_path):
    """Generate diff heatmap (log1p scale)."""
    diff = np.abs(c_img - py_img)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # C image
    im0 = axes[0].imshow(c_img, origin='lower', cmap='gray', vmin=0, vmax=np.percentile(c_img, 99.5))
    axes[0].set_title('C Reference (Golden Data)')
    axes[0].set_xlabel('Fast (pixels)')
    axes[0].set_ylabel('Slow (pixels)')
    plt.colorbar(im0, ax=axes[0], label='Intensity')

    # PyTorch image
    im1 = axes[1].imshow(py_img, origin='lower', cmap='gray', vmin=0, vmax=np.percentile(py_img, 99.5))
    axes[1].set_title('PyTorch Implementation')
    axes[1].set_xlabel('Fast (pixels)')
    axes[1].set_ylabel('Slow (pixels)')
    plt.colorbar(im1, ax=axes[1], label='Intensity')

    # Difference (log scale)
    im2 = axes[2].imshow(np.log1p(diff), origin='lower', cmap='hot')
    axes[2].set_title(f'log1p(|Δ|) — Max|Δ|={np.max(diff):.2f}')
    axes[2].set_xlabel('Fast (pixels)')
    axes[2].set_ylabel('Slow (pixels)')
    plt.colorbar(im2, ax=axes[2], label='log1p(|Difference|)')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Diff heatmap saved to {output_path}")


def find_on_peak_pixel(image, percentile=99.9):
    """Find a strong on-peak pixel for trace generation."""
    threshold = np.percentile(image, percentile)
    candidates = np.argwhere(image >= threshold)

    if len(candidates) == 0:
        return None

    # Pick the brightest pixel
    intensities = image[candidates[:, 0], candidates[:, 1]]
    brightest_idx = np.argmax(intensities)
    s, f = candidates[brightest_idx]

    return (int(s), int(f), float(image[s, f]))


def main():
    # Setup output directory
    timestamp = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path("reports") / f"{timestamp}-AT-PARALLEL-012" / "simple_cubic"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"AT-PARALLEL-012 simple_cubic Diagnostic")
    print(f"Output directory: {output_dir}")
    print("-" * 60)

    # Load golden data
    golden_file = Path("tests/golden_data/simple_cubic.bin")
    if not golden_file.exists():
        print(f"ERROR: Golden data not found at {golden_file}")
        return 1

    print(f"Loading golden data from {golden_file}")
    c_image = load_golden_float_image(str(golden_file), (1024, 1024))
    print(f"  Shape: {c_image.shape}, Sum: {np.sum(c_image):.2f}")

    # Setup PyTorch configuration (matching test_at_parallel_012.py:139-158)
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )

    detector_config = DetectorConfig(
        spixels=1024,
        fpixels=1024,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,  # Fixed in Attempt #2
        detector_pivot=DetectorPivot.BEAM
    )

    beam_config = BeamConfig(
        wavelength_A=6.2
    )

    # Run PyTorch simulation
    print("\nRunning PyTorch simulation...")
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)
    py_image = simulator.run().cpu().numpy()
    print(f"  Shape: {py_image.shape}, Sum: {np.sum(py_image):.2f}")

    # Compute metrics
    print("\nComputing metrics...")
    metrics = compute_metrics(c_image, py_image)

    print(f"  Correlation: {metrics['correlation']:.6f} (threshold: 0.9995)")
    print(f"  RMSE: {metrics['rmse']:.4f}")
    print(f"  MSE: {metrics['mse']:.4f}")
    print(f"  Max |Δ|: {metrics['max_abs_diff']:.4f}")
    print(f"  C sum: {metrics['c_sum']:.2f}")
    print(f"  PyTorch sum: {metrics['py_sum']:.2f}")
    print(f"  Sum ratio: {metrics['sum_ratio']:.6f}")

    # Save metrics
    metrics_file = output_dir / "metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\nMetrics saved to {metrics_file}")

    # Generate diff heatmap
    heatmap_file = output_dir / "diff_heatmap.png"
    print(f"\nGenerating diff heatmap...")
    plot_diff_heatmap(c_image, py_image, heatmap_file)

    # Find on-peak pixel for trace
    print("\nFinding on-peak pixel for trace generation...")
    c_peak = find_on_peak_pixel(c_image, percentile=99.9)
    py_peak = find_on_peak_pixel(py_image, percentile=99.9)

    if c_peak:
        print(f"  C brightest pixel: ({c_peak[0]}, {c_peak[1]}) = {c_peak[2]:.2f}")
    if py_peak:
        print(f"  PyTorch brightest pixel: ({py_peak[0]}, {py_peak[1]}) = {py_peak[2]:.2f}")

    # Save peak info
    peak_info = {
        'c_peak': {'slow': c_peak[0], 'fast': c_peak[1], 'intensity': c_peak[2]} if c_peak else None,
        'py_peak': {'slow': py_peak[0], 'fast': py_peak[1], 'intensity': py_peak[2]} if py_peak else None
    }

    peak_file = output_dir / "peak_info.json"
    with open(peak_file, 'w') as f:
        json.dump(peak_info, f, indent=2)
    print(f"Peak info saved to {peak_file}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Correlation: {metrics['correlation']:.6f} (need ≥0.9995)")
    print(f"Gap: {(0.9995 - metrics['correlation']) * 100:.2f}%")
    print(f"Sum ratio: {metrics['sum_ratio']:.6f} (nearly perfect)")
    print(f"Max |Δ|: {metrics['max_abs_diff']:.4f}")
    print(f"\nNext action: Generate parallel traces for pixel {c_peak[:2]} to find FIRST DIVERGENCE")
    print(f"\nArtifacts saved to: {output_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())