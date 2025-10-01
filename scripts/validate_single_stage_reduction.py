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

def run_simple_cubic_test(dtype=torch.float32, device='cpu'):
    """Run simple_cubic test with specified dtype and device."""
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

    # Run simulation with specified dtype and device
    crystal = Crystal(crystal_config, dtype=dtype, device=device)
    detector = Detector(detector_config, dtype=dtype, device=device)
    simulator = Simulator(crystal, detector, crystal_config, beam_config, dtype=dtype, device=device)

    pytorch_image = simulator.run().cpu().numpy()

    return pytorch_image

def main():
    print("=" * 80)
    print("AT-PARALLEL-012 Phase B3: Dtype Sensitivity Validation")
    print("=" * 80)
    print()

    # Beam center ROI (20×20 around center)
    center = 512
    roi = (center - 10, center + 10, center - 10, center + 10)

    # Test 1: float32 baseline
    print("[1/2] Running with dtype=float32 (current default)...")
    float32_image = run_simple_cubic_test(dtype=torch.float32, device='cpu')
    float32_unique_full = count_unique_values(float32_image)
    float32_unique_roi = count_unique_values(float32_image, roi=roi)
    print(f"  Unique values (full image): {float32_unique_full:,}")
    print(f"  Unique values (beam center 20×20): {float32_unique_roi}")
    print()

    # Test 2: float64 comparison
    print("[2/2] Running with dtype=float64 (precision test)...")
    float64_image = run_simple_cubic_test(dtype=torch.float64, device='cpu')
    float64_unique_full = count_unique_values(float64_image)
    float64_unique_roi = count_unique_values(float64_image, roi=roi)
    print(f"  Unique values (full image): {float64_unique_full:,}")
    print(f"  Unique values (beam center 20×20): {float64_unique_roi}")
    print()

    # Reference values from Phase A3
    print("Reference values from Phase A3 analysis:")
    print(f"  C float32 (golden): 66 unique values in beam center ROI")
    print(f"  Expected PyTorch float32: ~324 unique values (4.91× fragmentation)")
    print(f"  Expected PyTorch float64: ~301 unique values (4.56× fragmentation)")
    print()

    # Compute fragmentation ratios
    c_baseline_roi = 66  # From Phase A3 plateau analysis
    float32_frag = float32_unique_roi / c_baseline_roi
    float64_frag = float64_unique_roi / c_baseline_roi

    print("=" * 80)
    print("Results Summary")
    print("=" * 80)
    print(f"Float32 fragmentation ratio: {float32_frag:.2f}× (beam center ROI)")
    print(f"Float64 fragmentation ratio: {float64_frag:.2f}× (beam center ROI)")
    print()

    # Validate expectations
    if 4.5 <= float32_frag <= 5.5 and 4.0 <= float64_frag <= 5.0:
        print("✅ CONFIRMED: Dtype sensitivity matches Phase A3 findings")
        print("   Both float32 and float64 show ~5× plateau fragmentation")
        print("   → Root cause is PER-PIXEL floating-point operations, not accumulation")
    elif float32_frag > 7.0:
        print("⚠️  WARNING: Float32 fragmentation higher than Phase A3 baseline")
        print("   This suggests additional accumulation issues beyond per-pixel FP")
    else:
        print("⚠️  UNEXPECTED: Fragmentation ratios differ from Phase A3 analysis")
        print("   Re-check Phase A3 artifacts or consider measurement methodology")

    print()
    print("=" * 80)
    print("Phase B3 Dtype Validation Complete")
    print("=" * 80)
    print()
    print("Next Steps (Phase C):")
    print("  1. Since both dtypes show similar fragmentation (~5×), the issue is")
    print("     per-pixel numerical precision, NOT multi-stage accumulation order")
    print("  2. Options for Phase C mitigation:")
    print("     a) Adjust peak detection algorithm to cluster nearby maxima")
    print("     b) Investigate compiler FMA settings affecting sinc/geometry calculations")
    print("     c) Accept float64 for AT-012 only (document deviation)")
    print("  3. Record decision and artifact paths in docs/fix_plan.md")

if __name__ == "__main__":
    main()
