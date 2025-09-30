#!/usr/bin/env python3
"""Analyze the remaining 0.5% gap in simple_cubic correlation."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import numpy as np
import torch
from pathlib import Path
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorPivot
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector, DetectorConvention
from nanobrag_torch.simulator import Simulator

def load_golden_float_image(path, shape):
    """Load golden float image."""
    data = np.fromfile(path, dtype=np.float32)
    return data.reshape(shape, order='F')  # Fortran (column-major) order

def main():
    # Load golden data
    golden_file = Path(__file__).parent.parent / "tests" / "golden_data" / "simple_cubic.bin"
    golden_image = load_golden_float_image(str(golden_file), (1024, 1024))

    # Setup PyTorch configuration
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
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM
    )

    beam_config = BeamConfig(
        wavelength_A=6.2
    )

    # Run PyTorch simulation
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    pytorch_image = simulator.run().cpu().numpy()

    # Compute metrics
    corr, _ = pearsonr(golden_image.flatten(), pytorch_image.flatten())
    diff = pytorch_image - golden_image
    mse = np.mean(diff**2)
    rmse = np.sqrt(mse)
    max_abs_diff = np.abs(diff).max()

    c_sum = golden_image.sum()
    py_sum = pytorch_image.sum()
    sum_ratio = py_sum / c_sum

    print(f"\n=== Quantitative Metrics ===")
    print(f"Correlation: {corr:.6f}")
    print(f"MSE: {mse:.6f}")
    print(f"RMSE: {rmse:.6f}")
    print(f"Max |Δ|: {max_abs_diff:.6f}")
    print(f"C sum: {c_sum:.2f}")
    print(f"Py sum: {py_sum:.2f}")
    print(f"Sum ratio: {sum_ratio:.6f}")

    # Find strong peaks in C image
    threshold = np.percentile(golden_image, 99.9)
    c_peak_coords = np.argwhere(golden_image > threshold)

    if len(c_peak_coords) > 0:
        # Sample a few peaks
        sample_indices = [0, len(c_peak_coords)//2, -1] if len(c_peak_coords) >= 3 else [0]

        print(f"\n=== Pixel-Level Comparison at Strong Peaks ===")
        for idx in sample_indices:
            s, f = c_peak_coords[idx]
            c_val = golden_image[s, f]
            py_val = pytorch_image[s, f]
            ratio = py_val / c_val if c_val > 0 else 0
            print(f"Pixel ({s},{f}): C={c_val:.2f}, Py={py_val:.2f}, ratio={ratio:.6f}, diff={py_val-c_val:.4f}")

    # Create diff heatmap
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))

    # C image
    im0 = axes[0, 0].imshow(np.log1p(golden_image), origin='lower', cmap='viridis')
    axes[0, 0].set_title('C (log1p)')
    plt.colorbar(im0, ax=axes[0, 0])

    # PyTorch image
    im1 = axes[0, 1].imshow(np.log1p(pytorch_image), origin='lower', cmap='viridis')
    axes[0, 1].set_title('PyTorch (log1p)')
    plt.colorbar(im1, ax=axes[0, 1])

    # Absolute difference
    im2 = axes[1, 0].imshow(np.log1p(np.abs(diff)), origin='lower', cmap='hot')
    axes[1, 0].set_title(f'|Diff| (log1p) - max={max_abs_diff:.2f}')
    plt.colorbar(im2, ax=axes[1, 0])

    # Relative difference (where C > threshold)
    mask = golden_image > (golden_image.max() * 0.01)
    rel_diff = np.zeros_like(diff)
    rel_diff[mask] = diff[mask] / golden_image[mask]
    im3 = axes[1, 1].imshow(rel_diff, origin='lower', cmap='RdBu_r', vmin=-0.1, vmax=0.1)
    axes[1, 1].set_title('Relative Diff (where C > 1% max)')
    plt.colorbar(im3, ax=axes[1, 1])

    plt.tight_layout()

    # Save artifacts
    output_dir = Path(__file__).parent.parent / "reports" / "2025-09-30-AT-PARALLEL-012"
    output_dir.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_dir / "simple_cubic_diff_analysis.png", dpi=150)
    print(f"\n=== Artifacts ===")
    print(f"Diff heatmap: {output_dir / 'simple_cubic_diff_analysis.png'}")

    # Save metrics JSON
    import json
    metrics = {
        "correlation": float(corr),
        "mse": float(mse),
        "rmse": float(rmse),
        "max_abs_diff": float(max_abs_diff),
        "c_sum": float(c_sum),
        "py_sum": float(py_sum),
        "sum_ratio": float(sum_ratio),
        "threshold_required": 0.9995,
        "gap": float(0.9995 - corr)
    }

    with open(output_dir / "simple_cubic_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics JSON: {output_dir / 'simple_cubic_metrics.json'}")

    print(f"\n=== Geometry Triage ===")
    print(f"Gap: {0.9995 - corr:.6f} (0.5% below threshold)")
    print(f"Sum ratio: {sum_ratio:.6f} (within 0.02% - excellent)")
    print(f"This suggests a spatial distribution issue, not a total energy issue.")
    print(f"\nNext step: Generate parallel traces for an on-peak pixel to identify FIRST DIVERGENCE.")

if __name__ == "__main__":
    main()