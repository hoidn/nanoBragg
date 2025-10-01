#!/usr/bin/env python
"""
Compare C and PyTorch intensity scaling across pixel sizes.

Directly compare output intensities to identify scaling discrepancy.
"""

import os
import sys
sys.path.insert(0, '/home/ollie/Documents/nanoBragg')

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import subprocess
import numpy as np
import torch
from pathlib import Path

from src.nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention
)
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator


def run_c_simulation(pixel_size_mm):
    """Run C binary and return image."""
    cmd = [
        './golden_suite_generator/nanoBragg',
        '-detpixels', '256',
        '-pixel', str(pixel_size_mm),
        '-distance', '100',
        '-Xbeam', '25.6',
        '-Ybeam', '25.6',
        '-cell', '100', '100', '100', '90', '90', '90',
        '-lambda', '6.2',
        '-default_F', '100',
        '-N', '5',
        '-floatfile', f'/tmp/c_test_{pixel_size_mm}mm.bin'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"C binary failed: {result.stderr}")
        return None

    # Read binary file
    img_data = np.fromfile(f'/tmp/c_test_{pixel_size_mm}mm.bin', dtype=np.float32)
    img = img_data.reshape(256, 256)
    return img


def run_pytorch_simulation(pixel_size_mm):
    """Run PyTorch simulation and return image."""
    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        distance_mm=100.0,
        pixel_size_mm=pixel_size_mm,
        spixels=256,
        fpixels=256,
        beam_center_s=25.6,
        beam_center_f=25.6,
    )

    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )

    beam_config = BeamConfig(
        wavelength_A=6.2
        # Use default fluence from BeamConfig (~1.26e29 photons/m^2)
    )

    detector = Detector(detector_config)
    crystal = Crystal(crystal_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    image = simulator.run()
    return image.numpy()


def analyze_pixel_size(pixel_size_mm):
    """Compare C and PyTorch for a specific pixel size."""
    print(f"\n{'='*60}")
    print(f"Pixel size: {pixel_size_mm} mm")
    print(f"{'='*60}")

    # Run simulations
    print("Running C simulation...")
    c_img = run_c_simulation(pixel_size_mm)

    print("Running PyTorch simulation...")
    py_img = run_pytorch_simulation(pixel_size_mm)

    if c_img is None:
        print("C simulation failed!")
        return

    # Compare statistics
    print(f"\nImage statistics:")
    print(f"  C:       min={c_img.min():.6e}, max={c_img.max():.6e}, mean={c_img.mean():.6e}, sum={c_img.sum():.6e}")
    print(f"  PyTorch: min={py_img.min():.6e}, max={py_img.max():.6e}, mean={py_img.mean():.6e}, sum={py_img.sum():.6e}")

    # Ratios
    mean_ratio = py_img.mean() / c_img.mean() if c_img.mean() > 0 else 0
    sum_ratio = py_img.sum() / c_img.sum() if c_img.sum() > 0 else 0
    max_ratio = py_img.max() / c_img.max() if c_img.max() > 0 else 0

    print(f"\nRatios (PyTorch/C):")
    print(f"  Mean ratio: {mean_ratio:.6f} ({(mean_ratio-1)*100:.2f}% difference)")
    print(f"  Sum ratio:  {sum_ratio:.6f} ({(sum_ratio-1)*100:.2f}% difference)")
    print(f"  Max ratio:  {max_ratio:.6f} ({(max_ratio-1)*100:.2f}% difference)")

    # Correlation
    c_flat = c_img.flatten()
    py_flat = py_img.flatten()

    # Normalize for correlation
    c_norm = (c_flat - c_flat.mean()) / (c_flat.std() + 1e-10)
    py_norm = (py_flat - py_flat.mean()) / (py_flat.std() + 1e-10)
    correlation = (c_norm * py_norm).mean()

    print(f"  Correlation: {correlation:.10f}")

    # Key insight: check if the discrepancy scales with pixel area
    pixel_area = pixel_size_mm ** 2
    print(f"\nPixel area: {pixel_area:.6f} mm^2")
    print(f"If error scales with pixel area: expected ratio = {1 + 0.07 * pixel_area / 0.16:.6f}")

    return {
        'pixel_size': pixel_size_mm,
        'mean_ratio': mean_ratio,
        'sum_ratio': sum_ratio,
        'max_ratio': max_ratio,
        'correlation': correlation,
        'pixel_area': pixel_area
    }


if __name__ == "__main__":
    pixel_sizes = [0.05, 0.1, 0.2, 0.4]

    results = []
    for px in pixel_sizes:
        result = analyze_pixel_size(px)
        if result:
            results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY: Intensity Ratio vs Pixel Size")
    print(f"{'='*60}")
    print(f"{'Pixel (mm)':<15} {'Area (mm²)':<15} {'Mean Ratio':<15} {'Corr':<10}")
    print("-" * 60)
    for r in results:
        print(f"{r['pixel_size']:<15.2f} {r['pixel_area']:<15.6f} {r['mean_ratio']:<15.6f} {r['correlation']:<10.8f}")

    # Check if ratio scales linearly with pixel area
    print("\nHypothesis: If ratio scales linearly with pixel_area...")
    ref_ratio = results[0]['mean_ratio']
    ref_area = results[0]['pixel_area']

    for r in results:
        # Predict ratio based on linear scaling
        predicted = 1 + (ref_ratio - 1) * (r['pixel_area'] / ref_area)
        actual = r['mean_ratio']
        error = abs(actual - predicted)
        print(f"  {r['pixel_size']:.2f}mm: predicted={predicted:.6f}, actual={actual:.6f}, error={error:.6f}")