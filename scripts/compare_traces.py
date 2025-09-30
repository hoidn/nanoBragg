#!/usr/bin/env python3
"""
Compare C and PyTorch outputs for AT-PARALLEL-012 simple_cubic

Runs both implementations and compares pixel-by-pixel to identify patterns.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import subprocess
import tempfile
from pathlib import Path
import numpy as np
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def run_c_simulation():
    """Run C simulation matching simple_cubic golden data generation."""
    c_bin = Path("./golden_suite_generator/nanoBragg")
    if not c_bin.exists():
        c_bin = Path("./nanoBragg")

    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
        c_output = f.name

    cmd = [
        str(c_bin),
        '-cell', '100', '100', '100', '90', '90', '90',
        '-lambda', '6.2',
        '-N', '5',
        '-default_F', '100',
        '-distance', '100',
        '-detpixels', '1024',
        '-pixel', '0.1',
        '-mosflm',
        '-floatfile', c_output
    ]

    print("Running C simulation...")
    print(" ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        print(f"C simulation failed: {result.stderr}")
        return None

    # Load output
    data = np.fromfile(c_output, dtype=np.float32)
    os.unlink(c_output)

    return data.reshape((1024, 1024))


def run_pytorch_simulation():
    """Run PyTorch simulation with same parameters."""
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

    print("Running PyTorch simulation...")
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    return simulator.run().cpu().numpy()


def analyze_spatial_pattern(c_img, py_img):
    """Analyze spatial pattern of differences."""
    ratio = np.zeros_like(c_img)
    mask = c_img > 0.1  # Only analyze non-background pixels

    ratio[mask] = py_img[mask] / c_img[mask]

    # Calculate distance from center
    cy, cx = 511.5, 511.5  # MOSFLM beam center (512.5 pixels - 1 for 0-indexing)
    y, x = np.ogrid[:1024, :1024]
    distance = np.sqrt((x - cx)**2 + (y - cy)**2)

    # Sample pixels at various distances
    print("\n" + "=" * 80)
    print("SPATIAL PATTERN ANALYSIS")
    print("=" * 80)
    print(f"{'Distance (px)':>15} {'C Value':>15} {'Py Value':>15} {'Ratio':>15} {'% Diff':>15}")
    print("-" * 80)

    # Sample at different radii
    for target_dist in [0, 50, 100, 150, 200, 300, 400, 500]:
        dist_mask = (distance >= target_dist - 5) & (distance <= target_dist + 5) & mask
        if np.any(dist_mask):
            c_vals = c_img[dist_mask]
            py_vals = py_img[dist_mask]
            ratios = py_vals / c_vals

            print(f"{target_dist:15.0f} {np.mean(c_vals):15.4f} {np.mean(py_vals):15.4f} " +
                  f"{np.mean(ratios):15.6f} {(np.mean(ratios) - 1) * 100:15.2f}%")

    # Overall statistics
    print("\n" + "=" * 80)
    print("OVERALL STATISTICS")
    print("=" * 80)
    corr, _ = pearsonr(c_img.flatten(), py_img.flatten())
    print(f"Correlation: {corr:.6f}")
    print(f"Mean ratio: {np.mean(ratio[mask]):.6f}")
    print(f"Std ratio: {np.std(ratio[mask]):.6f}")
    print(f"C sum: {np.sum(c_img):.2f}")
    print(f"Py sum: {np.sum(py_img):.2f}")
    print(f"Sum ratio: {np.sum(py_img) / np.sum(c_img):.6f}")


def main():
    print("=" * 80)
    print("C vs PyTorch COMPARISON: AT-PARALLEL-012 simple_cubic")
    print("=" * 80)

    # Run both simulations
    c_img = run_c_simulation()
    if c_img is None:
        return 1

    py_img = run_pytorch_simulation()

    # Analyze
    analyze_spatial_pattern(c_img, py_img)

    return 0


if __name__ == "__main__":
    sys.exit(main())
