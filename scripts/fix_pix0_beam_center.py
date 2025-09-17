#!/usr/bin/env python3
"""
Fix pix0_vector beam center calculation to match C implementation.

Based on the diagnostic analysis, the C implementation uses beam center values
that are 100x smaller than expected, suggesting a different unit convention.
"""

import os
import sys
import torch
import numpy as np
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig, DetectorPivot, DetectorConvention


def test_beam_center_hypothesis():
    """Test different beam center scaling factors to match C implementation."""
    
    print("Testing Beam Center Scaling Hypothesis")
    print("=" * 60)
    
    # Target C values
    c_pix0_target = np.array([0.11485272, 0.05360999, -0.04656979])
    c_fdet_target = np.array([0.022652, -0.099001, 0.994829])
    
    # Base configuration
    base_config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=20.0,
        detector_pivot=DetectorPivot.SAMPLE,
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        fpixels=1024,
        spixels=1024,
    )
    
    print("Testing different beam center scaling factors:")
    print(f"Target C pix0: {c_pix0_target}")
    print(f"Target C fdet: {c_fdet_target}")
    print()
    
    # Test various scaling factors
    scaling_factors = [1.0, 0.1, 0.01, 0.001, 10.0, 100.0]
    
    best_pix0_diff = float('inf')
    best_factor = None
    
    for factor in scaling_factors:
        # Modify beam center
        test_config = DetectorConfig(
            distance_mm=base_config.distance_mm,
            beam_center_s=base_config.beam_center_s * factor,
            beam_center_f=base_config.beam_center_f * factor,
            detector_rotx_deg=base_config.detector_rotx_deg,
            detector_roty_deg=base_config.detector_roty_deg,
            detector_rotz_deg=base_config.detector_rotz_deg,
            detector_twotheta_deg=base_config.detector_twotheta_deg,
            detector_pivot=base_config.detector_pivot,
            detector_convention=base_config.detector_convention,
            pixel_size_mm=base_config.pixel_size_mm,
            fpixels=base_config.fpixels,
            spixels=base_config.spixels,
        )
        
        detector = Detector(test_config)
        pytorch_pix0 = detector.pix0_vector.numpy()
        pytorch_fdet = detector.fdet_vec.numpy()
        
        # Calculate differences
        pix0_diff = pytorch_pix0 - c_pix0_target
        fdet_diff = pytorch_fdet - c_fdet_target
        
        pix0_max_diff = np.max(np.abs(pix0_diff))
        fdet_max_diff = np.max(np.abs(fdet_diff))
        
        print(f"Factor {factor:6.3f}: pix0_diff={pix0_max_diff:.6f}, fdet_diff={fdet_max_diff:.6f}")
        print(f"             pix0: [{pytorch_pix0[0]:10.6f}, {pytorch_pix0[1]:10.6f}, {pytorch_pix0[2]:10.6f}]")
        
        # Track best pix0 match
        if pix0_max_diff < best_pix0_diff:
            best_pix0_diff = pix0_max_diff
            best_factor = factor
    
    print(f"\nBest scaling factor for pix0: {best_factor} (diff: {best_pix0_diff:.6f})")
    
    # Test the C beam center values directly
    print(f"\nTesting C beam center values directly:")
    
    # From C trace: X:5.125e-05 Y:5.125e-05 (in meters)
    c_beam_x = 5.125e-05  # meters
    c_beam_y = 5.125e-05  # meters
    
    # Convert to mm
    c_beam_x_mm = c_beam_x * 1000.0  # 0.05125 mm
    c_beam_y_mm = c_beam_y * 1000.0  # 0.05125 mm
    
    print(f"C beam center: X={c_beam_x} m = {c_beam_x_mm} mm")
    print(f"C beam center: Y={c_beam_y} m = {c_beam_y_mm} mm")
    
    # Test with these exact values
    c_exact_config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=c_beam_y_mm,  # Note: C maps Y to S (slow)
        beam_center_f=c_beam_x_mm,  # Note: C maps X to F (fast)
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=20.0,
        detector_pivot=DetectorPivot.SAMPLE,
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        fpixels=1024,
        spixels=1024,
    )
    
    detector_exact = Detector(c_exact_config)
    pytorch_exact_pix0 = detector_exact.pix0_vector.numpy()
    
    exact_pix0_diff = pytorch_exact_pix0 - c_pix0_target
    exact_pix0_max_diff = np.max(np.abs(exact_pix0_diff))
    
    print(f"With C exact values: pix0_diff={exact_pix0_max_diff:.6f}")
    print(f"PyTorch pix0: [{pytorch_exact_pix0[0]:10.6f}, {pytorch_exact_pix0[1]:10.6f}, {pytorch_exact_pix0[2]:10.6f}]")
    print(f"C target:     [{c_pix0_target[0]:10.6f}, {c_pix0_target[1]:10.6f}, {c_pix0_target[2]:10.6f}]")
    print(f"Difference:   [{exact_pix0_diff[0]:10.6f}, {exact_pix0_diff[1]:10.6f}, {exact_pix0_diff[2]:10.6f}]")
    
    if exact_pix0_max_diff < 1e-3:
        print("✅ EXACT MATCH FOUND! C uses beam center values directly in meters.")
        return c_beam_x_mm, c_beam_y_mm
    else:
        print("❌ Still no exact match. Other issues remain.")
        return None, None


def analyze_c_beam_calculation():
    """Analyze how C calculates beam center from the trace."""
    
    print(f"\nAnalyzing C Beam Center Calculation")
    print("=" * 60)
    
    # From C trace analysis:
    # TRACE_C:beam_center_m=X:5.125e-05 Y:5.125e-05 pixel_mm:0.1
    # TRACE_C:Fbeam_m=0.0513
    # TRACE_C:Sbeam_m=0.0513
    
    c_beam_x_m = 5.125e-05  # meters
    c_beam_y_m = 5.125e-05  # meters
    c_fbeam_m = 0.0513      # meters 
    c_sbeam_m = 0.0513      # meters
    pixel_size_mm = 0.1     # mm
    
    print(f"C trace values:")
    print(f"  beam_center X: {c_beam_x_m} m")
    print(f"  beam_center Y: {c_beam_y_m} m")
    print(f"  Fbeam_m: {c_fbeam_m} m")
    print(f"  Sbeam_m: {c_sbeam_m} m")
    print(f"  pixel_size: {pixel_size_mm} mm")
    
    # Calculate expected relationships
    print(f"\nExpected relationships:")
    
    # If beam center is in pixels
    if abs(c_beam_x_m - 51.2) < 1e-6:
        print(f"  C beam center appears to be in pixels (51.2)")
    elif abs(c_beam_x_m - 0.05125) < 1e-6:
        print(f"  C beam center appears to be in mm ({c_beam_x_m * 1000} mm)")
    else:
        print(f"  C beam center unit unclear")
    
    # Check if Fbeam/Sbeam are calculated from beam center
    expected_fbeam_1 = (51.2 + 0.5) * 0.1 / 1000.0  # (pixels + 0.5) * pixel_size_mm / 1000
    expected_fbeam_2 = c_beam_x_m * 1000 + 0.5 * 0.1  # beam_center_mm * 1000 + 0.5 * pixel_size_mm
    
    print(f"  Expected Fbeam (method 1): {expected_fbeam_1} m")
    print(f"  Expected Fbeam (method 2): {expected_fbeam_2} m") 
    print(f"  Actual C Fbeam: {c_fbeam_m} m")
    
    # Check which method matches
    diff_1 = abs(c_fbeam_m - expected_fbeam_1)
    diff_2 = abs(c_fbeam_m - expected_fbeam_2)
    
    print(f"  Method 1 difference: {diff_1:.2e}")
    print(f"  Method 2 difference: {diff_2:.2e}")
    
    if diff_1 < 1e-6:
        print(f"  ✅ C uses method 1: (pixels + 0.5) * pixel_size_mm / 1000")
    elif diff_2 < 1e-6:
        print(f"  ✅ C uses method 2: beam_center_mm * 1000 + 0.5 * pixel_size_mm")
    else:
        print(f"  ❌ Neither method matches C calculation")
    
    # Test hypothesis: maybe beam_center is in pixels and C calculation is correct
    input_beam_center_pixels = 51.2
    c_calculated_beam_center_mm = input_beam_center_pixels * pixel_size_mm  # 5.12 mm
    c_calculated_beam_center_m = c_calculated_beam_center_mm / 1000.0      # 0.00512 m
    
    print(f"\nHypothesis test:")
    print(f"  Input beam center: {input_beam_center_pixels} pixels")
    print(f"  C calc beam center: {c_calculated_beam_center_m} m")
    print(f"  Actual C beam center: {c_beam_x_m} m")
    print(f"  Difference: {abs(c_calculated_beam_center_m - c_beam_x_m):.2e}")
    
    # The values don't match, so investigate the MOSFLM mapping
    print(f"\nMOSFLM Convention Analysis:")
    
    # From C trace: "convention_mapping=Fbeam←Ybeam_mm(+0.5px),Sbeam←Xbeam_mm(+0.5px)"
    # This suggests:
    # - Fbeam comes from Ybeam_mm (with +0.5 pixel offset)
    # - Sbeam comes from Xbeam_mm (with +0.5 pixel offset)
    
    print(f"  C convention mapping: Fbeam←Ybeam_mm(+0.5px), Sbeam←Xbeam_mm(+0.5px)")
    print(f"  This means beam center input might be interpreted differently")


def main():
    """Main analysis and fix function."""
    print("Phase 4.1: pix0_vector Beam Center Fix")
    print("=" * 80)
    
    # Test beam center scaling
    best_f, best_s = test_beam_center_hypothesis()
    
    # Analyze C calculation
    analyze_c_beam_calculation()
    
    print(f"\n{'='*80}")
    print("CONCLUSIONS")
    print(f"{'='*80}")
    
    if best_f is not None:
        print(f"✅ Found beam center values that match C implementation:")
        print(f"   beam_center_f: {best_f} mm")
        print(f"   beam_center_s: {best_s} mm")
        print(f"   Scale factor: {best_f / 51.2:.6f}")
    else:
        print(f"❌ No simple scaling factor resolves the discrepancy")
        print(f"   The issue may be more complex (coordinate mapping, pivot logic, etc.)")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Update PyTorch Detector class with correct beam center calculation")
    print(f"   2. Investigate MOSFLM coordinate mapping conventions")  
    print(f"   3. Test updated implementation against C reference")
    print(f"   4. Verify correlation improvement")


if __name__ == "__main__":
    main()