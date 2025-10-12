#!/usr/bin/env python3
"""
C15 Mixed Units Zero Intensity — H1 dmin Probe

Test whether dmin=2.0Å filtering is excluding all reflections.
This is the first hypothesis test per phase_m3/20251012T014618Z/remaining_clusters/summary.md
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention

def test_with_dmin(dmin_value):
    """Run simulator with specified dmin and return max intensity."""
    crystal_config = CrystalConfig(
        cell_a=75.5, cell_b=82.3, cell_c=91.7,
        cell_alpha=87.5, cell_beta=92.3, cell_gamma=95.8,
        default_F=100.0,
        N_cells=(3, 3, 3),
        phi_start_deg=0.0,
        osc_range_deg=1.0,
        phi_steps=1,
    )

    detector_config = DetectorConfig(
        distance_mm=150.5,
        pixel_size_mm=0.172,
        spixels=128,
        fpixels=128,
        detector_convention=DetectorConvention.XDS,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=10.0,
    )

    beam_config = BeamConfig(
        wavelength_A=1.54,  # Cu K-alpha
        fluence=1e23,
        polarization_factor=0.95,
        dmin=dmin_value,
    )

    det = Detector(detector_config)
    crystal = Crystal(crystal_config)
    sim = Simulator(detector=det, crystal=crystal, beam_config=beam_config, crystal_config=crystal_config)

    intensity = sim.run(oversample=1)

    return intensity.max().item(), intensity.sum().item(), (intensity > 0).sum().item()

if __name__ == "__main__":
    print("=" * 80)
    print("C15 dmin Probe — Hypothesis H1 Test")
    print("=" * 80)
    print()

    print("Configuration:")
    print("  Crystal: triclinic (75.5×82.3×91.7 Å, angles 87.5°×92.3°×95.8°)")
    print("  N_cells: (3,3,3)")
    print("  Detector: XDS, 128×128 pixels, 150.5mm distance, 0.172mm pixel")
    print("  Rotations: rotx=5°, roty=3°, rotz=2°, twotheta=10°")
    print("  Beam: λ=1.54Å, fluence=1e23, polarization=0.95")
    print()

    # Test 1: With dmin=2.0 (original failing case)
    print("Test 1: dmin=2.0Å (original configuration)")
    print("-" * 80)
    try:
        max_1, sum_1, nonzero_1 = test_with_dmin(2.0)
        print(f"  Max intensity: {max_1:.6e}")
        print(f"  Sum intensity: {sum_1:.6e}")
        print(f"  Non-zero pixels: {nonzero_1} / 16384")
        result_1 = "FAIL (zero)" if max_1 == 0 else "PASS (non-zero)"
        print(f"  Result: {result_1}")
    except Exception as e:
        print(f"  ERROR: {e}")
        result_1 = "ERROR"
    print()

    # Test 2: With dmin=None (disable filtering)
    print("Test 2: dmin=None (filtering disabled)")
    print("-" * 80)
    try:
        max_2, sum_2, nonzero_2 = test_with_dmin(None)
        print(f"  Max intensity: {max_2:.6e}")
        print(f"  Sum intensity: {sum_2:.6e}")
        print(f"  Non-zero pixels: {nonzero_2} / 16384")
        result_2 = "FAIL (zero)" if max_2 == 0 else "PASS (non-zero)"
        print(f"  Result: {result_2}")
    except Exception as e:
        print(f"  ERROR: {e}")
        result_2 = "ERROR"
    print()

    # Test 3: With dmin=10.0 (very loose filtering)
    print("Test 3: dmin=10.0Å (very loose filtering)")
    print("-" * 80)
    try:
        max_3, sum_3, nonzero_3 = test_with_dmin(10.0)
        print(f"  Max intensity: {max_3:.6e}")
        print(f"  Sum intensity: {sum_3:.6e}")
        print(f"  Non-zero pixels: {nonzero_3} / 16384")
        result_3 = "FAIL (zero)" if max_3 == 0 else "PASS (non-zero)"
        print(f"  Result: {result_3}")
    except Exception as e:
        print(f"  ERROR: {e}")
        result_3 = "ERROR"
    print()

    print("=" * 80)
    print("H1 Hypothesis Test Results")
    print("=" * 80)
    print()

    if result_1 == "FAIL (zero)" and result_2 == "PASS (non-zero)":
        print("✅ H1 CONFIRMED: dmin=2.0Å filtering is too aggressive")
        print("   → All reflections are being culled by dmin cutoff")
        print("   → Root cause identified: dmin threshold needs adjustment or removal")
        print()
        print("Next Actions:")
        print("  1. Investigate why dmin=2.0Å excludes all reflections")
        print("  2. Check scattering vector magnitudes and stol values")
        print("  3. Adjust dmin value or remove from test configuration")
    elif result_1 == "FAIL (zero)" and result_2 == "FAIL (zero)":
        print("❌ H1 REJECTED: dmin filtering is NOT the root cause")
        print("   → Zero intensity persists even with filtering disabled")
        print("   → Must investigate H2-H6 or perform parallel trace debugging")
        print()
        print("Next Actions:")
        print("  1. Execute H2: Test with cubic cell + no rotations")
        print("  2. Execute H3: Test with MOSFLM convention")
        print("  3. Parallel trace comparison per debugging.md SOP")
    else:
        print(f"⚠️  INCONCLUSIVE: Test 1={result_1}, Test 2={result_2}, Test 3={result_3}")
        print("   → Unexpected result pattern")
        print()
        print("Next Actions:")
        print("  1. Review error messages if any tests errored")
        print("  2. Check simulator initialization and configuration")
        print("  3. Verify test environment (Python/PyTorch versions)")

    print()
