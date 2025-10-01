#!/usr/bin/env python3
"""
Phase A3: Quantify plateau fragmentation for AT-PARALLEL-012 regression.

Compares unique value counts in beam-center ROI across:
- C float32 golden reference
- PyTorch float32 (native default)
- PyTorch float64 (workaround)

Output: histogram PNGs + CSV summary under reports/2025-10-AT012-regression/
"""

import os
import struct
import numpy as np
import torch
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Tuple

# Ensure correct environment
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import (
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
    CrystalConfig,
    BeamConfig,
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator


def load_golden_float_image(filename: str, shape: Tuple[int, int]) -> np.ndarray:
    """Load C golden data as float32."""
    with open(filename, 'rb') as f:
        data = f.read()
        n_floats = len(data) // 4
        assert n_floats == shape[0] * shape[1], f"Expected {shape[0]*shape[1]} floats, got {n_floats}"
        floats = struct.unpack(f'{n_floats}f', data)
        return np.array(floats, dtype=np.float32).reshape(shape)


def run_pytorch_simulation(dtype: torch.dtype) -> np.ndarray:
    """Run simple_cubic simulation with specified dtype."""
    # Match golden data: -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -default_F 100 -distance 100 -detpixels 1024
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

    beam_config = BeamConfig(wavelength_A=6.2)

    crystal = Crystal(crystal_config, dtype=dtype)
    detector = Detector(detector_config, dtype=dtype)
    simulator = Simulator(crystal, detector, crystal_config, beam_config, dtype=dtype)

    return simulator.run().cpu().numpy()


def analyze_plateau_fragmentation():
    """Quantify plateau fragmentation in beam-center ROI."""
    print("=" * 80)
    print("AT-PARALLEL-012 Phase A3: Plateau Fragmentation Analysis")
    print("=" * 80)
    print()

    # Load golden reference (C float32)
    golden_file = Path(__file__).parent.parent / "tests" / "golden_data" / "simple_cubic.bin"
    print(f"Loading golden reference: {golden_file}")
    golden_image = load_golden_float_image(str(golden_file), (1024, 1024))

    # Run PyTorch simulations
    print("Running PyTorch float32 simulation...")
    pytorch_f32 = run_pytorch_simulation(torch.float32)

    print("Running PyTorch float64 simulation...")
    pytorch_f64 = run_pytorch_simulation(torch.float64)

    # Define beam-center ROI (20x20 around center)
    center_s, center_f = 512, 512
    roi_size = 20
    roi_slice = (
        slice(center_s - roi_size//2, center_s + roi_size//2),
        slice(center_f - roi_size//2, center_f + roi_size//2)
    )

    # Extract ROI data
    golden_roi = golden_image[roi_slice]
    pytorch_f32_roi = pytorch_f32[roi_slice]
    pytorch_f64_roi = pytorch_f64[roi_slice]

    # Count unique values (plateau metric)
    unique_golden = np.unique(golden_roi).size
    unique_f32 = np.unique(pytorch_f32_roi).size
    unique_f64 = np.unique(pytorch_f64_roi).size

    # Compute fragmentation ratios
    frag_ratio_f32 = unique_f32 / unique_golden
    frag_ratio_f64 = unique_f64 / unique_golden

    print()
    print("=" * 80)
    print("RESULTS: Unique Value Counts (20x20 beam-center ROI)")
    print("=" * 80)
    print(f"C golden (float32):      {unique_golden:5d} unique values")
    print(f"PyTorch float32:         {unique_f32:5d} unique values  (× {frag_ratio_f32:.2f})")
    print(f"PyTorch float64:         {unique_f64:5d} unique values  (× {frag_ratio_f64:.2f})")
    print()
    print(f"Fragmentation: PyTorch float32 has {frag_ratio_f32:.2f}× more unique values than C")
    print(f"Fragmentation: PyTorch float64 has {frag_ratio_f64:.2f}× more unique values than C")
    print()

    # Create output directory
    output_dir = Path(__file__).parent.parent / "reports" / "2025-10-AT012-regression"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save CSV summary
    csv_path = output_dir / "phase_a3_plateau_fragmentation.csv"
    with open(csv_path, 'w') as f:
        f.write("implementation,dtype,unique_values,fragmentation_ratio\n")
        f.write(f"C_golden,float32,{unique_golden},1.00\n")
        f.write(f"PyTorch,float32,{unique_f32},{frag_ratio_f32:.3f}\n")
        f.write(f"PyTorch,float64,{unique_f64},{frag_ratio_f64:.3f}\n")
    print(f"✓ Saved CSV summary: {csv_path}")

    # Create histogram comparison
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    bins = 50
    axes[0].hist(golden_roi.flatten(), bins=bins, alpha=0.7, color='blue', edgecolor='black')
    axes[0].set_title(f'C Golden (float32)\n{unique_golden} unique values')
    axes[0].set_xlabel('Intensity')
    axes[0].set_ylabel('Frequency')
    axes[0].grid(True, alpha=0.3)

    axes[1].hist(pytorch_f32_roi.flatten(), bins=bins, alpha=0.7, color='red', edgecolor='black')
    axes[1].set_title(f'PyTorch float32\n{unique_f32} unique values (×{frag_ratio_f32:.2f})')
    axes[1].set_xlabel('Intensity')
    axes[1].set_ylabel('Frequency')
    axes[1].grid(True, alpha=0.3)

    axes[2].hist(pytorch_f64_roi.flatten(), bins=bins, alpha=0.7, color='green', edgecolor='black')
    axes[2].set_title(f'PyTorch float64\n{unique_f64} unique values (×{frag_ratio_f64:.2f})')
    axes[2].set_xlabel('Intensity')
    axes[2].set_ylabel('Frequency')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    hist_path = output_dir / "phase_a3_plateau_histogram.png"
    plt.savefig(hist_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved histogram: {hist_path}")

    # Create value distribution plot (first 100 unique values sorted)
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    sorted_golden = np.sort(np.unique(golden_roi))[:100]
    sorted_f32 = np.sort(np.unique(pytorch_f32_roi))[:100]
    sorted_f64 = np.sort(np.unique(pytorch_f64_roi))[:100]

    axes[0].plot(sorted_golden, 'o-', markersize=3, label='C golden')
    axes[0].set_title('C Golden: Top 100 Unique Values')
    axes[0].set_xlabel('Rank')
    axes[0].set_ylabel('Intensity')
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(sorted_f32, 'o-', markersize=3, color='red', label='PyTorch float32')
    axes[1].set_title('PyTorch float32: Top 100 Unique Values')
    axes[1].set_xlabel('Rank')
    axes[1].set_ylabel('Intensity')
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(sorted_f64, 'o-', markersize=3, color='green', label='PyTorch float64')
    axes[2].set_title('PyTorch float64: Top 100 Unique Values')
    axes[2].set_xlabel('Rank')
    axes[2].set_ylabel('Intensity')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    dist_path = output_dir / "phase_a3_value_distribution.png"
    plt.savefig(dist_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved value distribution: {dist_path}")

    # Save summary report
    report_path = output_dir / "phase_a3_summary.md"
    with open(report_path, 'w') as f:
        f.write("# AT-PARALLEL-012 Phase A3: Plateau Fragmentation Analysis\n\n")
        f.write("**Date:** 2025-09-30\n")
        f.write("**Test Case:** simple_cubic (1024×1024, λ=6.2Å, cubic cell)\n")
        f.write("**ROI:** 20×20 pixels at beam center (512, 512)\n\n")
        f.write("## Findings\n\n")
        f.write("| Implementation | Dtype | Unique Values | Fragmentation Ratio |\n")
        f.write("|----------------|-------|---------------|---------------------|\n")
        f.write(f"| C golden | float32 | {unique_golden} | 1.00 (baseline) |\n")
        f.write(f"| PyTorch | float32 | {unique_f32} | **{frag_ratio_f32:.2f}×** |\n")
        f.write(f"| PyTorch | float64 | {unique_f64} | {frag_ratio_f64:.2f}× |\n\n")
        f.write("## Analysis\n\n")
        f.write(f"PyTorch float32 produces **{frag_ratio_f32:.2f}× more unique intensity values** than C float32 ")
        f.write("in the beam-center plateau region. This fragmentation breaks scipy.ndimage.maximum_filter's ")
        f.write("plateau tie-breaking, causing peak detection to miss ~7 peaks (43/50 vs spec requirement of ≥48/50).\n\n")
        f.write("## Artifacts\n\n")
        f.write(f"- CSV data: `{csv_path.name}`\n")
        f.write(f"- Histogram: `{hist_path.name}`\n")
        f.write(f"- Value distribution: `{dist_path.name}`\n\n")
        f.write("## Next Actions\n\n")
        f.write("Per plan Phase B3: Evaluate mitigation strategies (single-stage reduction, compensated summation, ")
        f.write("peak clustering) to reduce fragmentation ratio to <2×.\n")
    print(f"✓ Saved summary report: {report_path}")

    print()
    print("=" * 80)
    print(f"Phase A3 Complete: Artifacts saved to {output_dir}")
    print("=" * 80)

    return {
        'unique_golden': unique_golden,
        'unique_f32': unique_f32,
        'unique_f64': unique_f64,
        'frag_ratio_f32': frag_ratio_f32,
        'frag_ratio_f64': frag_ratio_f64
    }


if __name__ == '__main__':
    results = analyze_plateau_fragmentation()
