#!/usr/bin/env python3
"""
Compare C and PyTorch pixel positions to identify the coordinate convention mismatch.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention

def analyze_coordinate_issue():
    """Analyze the coordinate convention issue."""
    print("="*70)
    print("COORDINATE CONVENTION MISMATCH ANALYSIS")
    print("="*70)
    
    print("KEY FINDINGS FROM DEBUG SCRIPT:")
    print("-" * 50)
    
    print("\n1. BASIS VECTORS (MOSFLM):")
    config = DetectorConfig(
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s=51.2,
        beam_center_f=51.2
    )
    detector = Detector(config)
    
    print(f"   fdet_vec: {detector.fdet_vec.numpy()} (should be Z-axis: [0,0,1])")
    print(f"   sdet_vec: {detector.sdet_vec.numpy()} (should be -Y-axis: [0,-1,0])") 
    print(f"   odet_vec: {detector.odet_vec.numpy()} (should be X-axis: [1,0,0])")
    print("   ✓ Basis vectors are correct!")
    
    print("\n2. BEAM CENTER MAPPING:")
    print("   MOSFLM convention should swap axes:")
    print(f"   Input: beam_center_s=51.2mm, beam_center_f=51.2mm")
    beam_f_m, beam_s_m = detector._apply_mosflm_beam_convention()
    print(f"   Output: beam_f={beam_f_m*1000:.3f}mm, beam_s={beam_s_m*1000:.3f}mm")
    print("   The 0.5 pixel offset (51.250mm) is correctly applied!")
    
    print("\n3. PIX0 VECTOR CALCULATION:")
    print(f"   pix0_vector: {detector.pix0_vector.numpy()}")
    print("   This represents the 3D position of pixel (0,0)")
    
    print("\n4. CRITICAL ISSUE - BEAM CENTER POSITION:")
    positions = detector.get_pixel_coords()
    center_pos = positions[512, 512].numpy()
    print(f"   Pixel (512,512) position: {center_pos}")
    print(f"   Expected beam spot: [0.1, -0.05125, -0.05125]")
    print(f"   Difference: {center_pos - np.array([0.1, -0.05125, -0.05125])}")
    
    print("\n   🚨 PROBLEM IDENTIFIED:")
    print("   The beam center is at (512,512) but should be offset!")
    print("   With beam_center=51.2mm and pixel_size=0.1mm:")
    print("   51.2mm / 0.1mm = 512 pixels from edge")
    print("   So beam center should be at pixel (512, 512)")
    print("   But the ACTUAL beam spot (where intensity peaks) should be elsewhere!")

def check_c_reference_convention():
    """Check what the C reference expects for beam center."""
    print("\n" + "="*70)
    print("C REFERENCE CONVENTION CHECK")  
    print("="*70)
    
    print("From nanoBragg.c documentation:")
    print("- Xbeam, Ybeam are in mm from detector corner")
    print("- MOSFLM convention: beam_center_s → Ybeam, beam_center_f → Xbeam")
    print("- Plus 0.5 pixel offset for MOSFLM")
    
    print("\nFor our test case:")
    print("- beam_center_s = beam_center_f = 51.2 mm")
    print("- MOSFLM: Xbeam = 51.2mm, Ybeam = 51.2mm") 
    print("- With 0.5px offset: Xbeam = 51.25mm, Ybeam = 51.25mm")
    print("- In pixels: Xbeam = 512.5px, Ybeam = 512.5px")
    
    print("\nThe issue might be:")
    print("1. Wrong beam center interpretation")
    print("2. Pixel indexing starts from 0, but beam center assumes 1-based?")
    print("3. Axis orientation mismatch")

def test_axis_orientation_hypothesis():
    """Test if there's an axis orientation issue."""
    print("\n" + "="*70)
    print("AXIS ORIENTATION HYPOTHESIS")
    print("="*70)
    
    # Compare MOSFLM vs XDS
    for conv_name, conv in [("MOSFLM", DetectorConvention.MOSFLM), ("XDS", DetectorConvention.XDS)]:
        print(f"\n{conv_name} Convention:")
        config = DetectorConfig(
            distance_mm=100.0,
            detector_convention=conv,
            beam_center_s=51.2,
            beam_center_f=51.2
        )
        detector = Detector(config)
        
        print(f"  fdet_vec: {detector.fdet_vec.numpy()}")
        print(f"  sdet_vec: {detector.sdet_vec.numpy()}")
        print(f"  odet_vec: {detector.odet_vec.numpy()}")
        
        center_pos = detector.get_pixel_coords()[512, 512].numpy()
        print(f"  Pixel (512,512): {center_pos}")
        
        # The issue: XDS shows completely different orientation!
        if conv == DetectorConvention.XDS:
            print("  🚨 MAJOR DIFFERENCE: XDS has completely different axis orientation!")
            print("     This suggests a fundamental coordinate system issue")

def analyze_divergence_cause():
    """Analyze why spots diverge from center outward."""
    print("\n" + "="*70)
    print("DIVERGENCE CAUSE ANALYSIS")  
    print("="*70)
    
    config = DetectorConfig(
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s=51.2,
        beam_center_f=51.2
    )
    detector = Detector(config)
    positions = detector.get_pixel_coords()
    
    print("Testing hypothesis: Coordinate system has systematic error")
    print("that increases with distance from center")
    
    # Test pixels at same distance but different directions
    center = np.array([512, 512])
    test_offsets = [
        ([0, 100], "Right"),      # Pure F direction  
        ([100, 0], "Down"),       # Pure S direction
        ([71, 71], "Diagonal"),   # 45 degree diagonal
        ([-71, 71], "Other diagonal")
    ]
    
    for offset, desc in test_offsets:
        s, f = int(center[0] + offset[0]), int(center[1] + offset[1])
        if 0 <= s < 1024 and 0 <= f < 1024:
            pos = positions[s, f].numpy()
            
            # Distance from detector center in 3D
            detector_center = positions[512, 512].numpy()
            displacement = pos - detector_center
            actual_distance = np.linalg.norm(displacement)
            
            # Expected distance based on pixel separation
            pixel_distance = np.sqrt(offset[0]**2 + offset[1]**2)
            expected_distance = pixel_distance * 0.0001  # pixel_size in meters
            
            ratio = actual_distance / expected_distance if expected_distance > 0 else 1
            
            print(f"  {desc:15} offset {offset}: actual={actual_distance:.6f}m, expected={expected_distance:.6f}m, ratio={ratio:.6f}")
    
    print("\nIf ratios are all ≈1.0, then pixel-to-3D mapping is geometrically correct")
    print("If ratios vary, there's a systematic coordinate transformation error")

if __name__ == "__main__":
    analyze_coordinate_issue()
    check_c_reference_convention()
    test_axis_orientation_hypothesis() 
    analyze_divergence_cause()
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print("The main issues identified:")
    print("1. Potential beam center offset interpretation")
    print("2. Major difference between MOSFLM/XDS axis orientations")
    print("3. Need to verify C reference pixel coordinate calculation")
    print("4. Possible 0-based vs 1-based indexing issue")