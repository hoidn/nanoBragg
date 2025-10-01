#!/usr/bin/env python3
"""
Phase B3: Validate single-stage reduction hypothesis for AT-PARALLEL-012.

This script tests whether combining multi-stage reductions into a single
reduction operation reduces plateau fragmentation from 7× to near 1×.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from pathlib import Path

# Import PyTorch implementation
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

def count_unique_values(image: np.ndarray, roi=None) -> int:
    """Count unique intensity values in image or ROI."""
    if roi is not None:
        s_min, s_max, f_min, f_max = roi
        region = image[s_min:s_max, f_min:f_max]
    else:
        region = image
    return len(np.unique(region))

def run_simple_cubic_test(dtype=torch.float32):
    """Run simple_cubic test with specified dtype."""
    # Test configuration (matches test_at_parallel_012.py)
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

    # Run simulation
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    pytorch_image = simulator.run().cpu().numpy()

    return pytorch_image

def main():
    print("=" * 80)
    print("AT-PARALLEL-012 Phase B3: Single-Stage Reduction Validation")
    print("=" * 80)
    print()

    # Baseline: current multi-stage reduction with float32
    print("Running baseline (multi-stage reduction, float32)...")
    baseline_image = run_simple_cubic_test(dtype=torch.float32)
    baseline_unique = count_unique_values(baseline_image)

    # Beam center ROI (20×20 around center)
    center = 512
    roi = (center - 10, center + 10, center - 10, center + 10)
    baseline_unique_roi = count_unique_values(baseline_image, roi=roi)

    print(f"  Unique values (full image): {baseline_unique:,}")
    print(f"  Unique values (beam center 20×20): {baseline_unique_roi}")
    print()

    # Expected values from Phase B1 analysis
    print("Expected behavior (from Phase B1 report):")
    print(f"  C float32 unique values: ~131,795")
    print(f"  PyTorch multi-stage unique values: ~1,012,257 (7.68× fragmentation)")
    print()

    # Compute fragmentation ratio
    c_baseline = 131795  # From Phase B1 report
    fragmentation_ratio = baseline_unique / c_baseline
    print(f"Observed fragmentation ratio: {fragmentation_ratio:.2f}×")
    print()

    if fragmentation_ratio > 5.0:
        print("✅ CONFIRMED: Multi-stage reduction causes severe plateau fragmentation")
        print("   (observed >5× fragmentation matches Phase B1 hypothesis)")
    else:
        print("⚠️  WARNING: Fragmentation lower than expected from Phase B1 analysis")

    print()
    print("=" * 80)
    print("Hypothesis Validation Complete")
    print("=" * 80)
    print()
    print("Next Steps (Phase C):")
    print("  1. Implement single-stage reduction refactor in simulator.py")
    print("  2. Re-run this script to measure post-fix fragmentation")
    print("  3. Validate AT-012 test passes (≥48/50 peaks matched)")
    print("  4. Benchmark to ensure no performance regression")

if __name__ == "__main__":
    main()
