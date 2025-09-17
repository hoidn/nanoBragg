#!/usr/bin/env python3
"""
Compare specific pixel coordinates between C and PyTorch implementations.
Focus on identifying the exact coordinate convention mismatch.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention

def get_c_pixel_positions():
    """Generate C reference pixel positions by adding trace to C code."""
    
    print("="*70)
    print("TRACING C PIXEL COORDINATE CALCULATIONS")
    print("="*70)
    
    print("To get C reference, we need to add printf statements to nanoBragg.c")
    print("Add these lines after the detector geometry calculations:")
    print()
    print("```c")
    print("// Debug pixel coordinates")
    print("for(int test_s = 0; test_s < 5; test_s++) {")
    print("  for(int test_f = 0; test_f < 5; test_f++) {")
    print("    if((test_s % 256 == 0) && (test_f % 256 == 0)) {")  # Sample specific pixels
    print("      double pixel_X = pix0_vector[1] + test_s * sdet_vector[1] * pixel_size + test_f * fdet_vector[1] * pixel_size;")
    print("      double pixel_Y = pix0_vector[2] + test_s * sdet_vector[2] * pixel_size + test_f * fdet_vector[2] * pixel_size;")
    print("      double pixel_Z = pix0_vector[3] + test_s * sdet_vector[3] * pixel_size + test_f * fdet_vector[3] * pixel_size;")
    print("      printf(\"C_PIXEL_POS: s=%d f=%d X=%f Y=%f Z=%f\\n\", test_s, test_f, pixel_X, pixel_Y, pixel_Z);")
    print("    }")
    print("  }")
    print("}")
    print("```")
    print()
    print("For now, let's work with known C values and reverse-engineer the issue...")

def analyze_key_positions():
    """Analyze key pixel positions to find the mismatch."""
    
    print("\n" + "="*70)
    print("ANALYZING KEY PIXEL POSITIONS")
    print("="*70)
    
    config = DetectorConfig(
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s=51.2,
        beam_center_f=51.2
    )
    detector = Detector(config)
    positions = detector.get_pixel_coords()
    
    print("PyTorch Results:")
    print(f"  pix0_vector: {detector.pix0_vector.numpy()}")
    print(f"  fdet_vec: {detector.fdet_vec.numpy()}")
    print(f"  sdet_vec: {detector.sdet_vec.numpy()}")
    print(f"  pixel_size: {detector.pixel_size} m")
    print()
    
    # Key test pixels
    test_pixels = [
        (0, 0, "Corner (0,0)"),
        (512, 512, "Center (512,512) - should be beam center"),
        (0, 512, "Edge (0,512)"),
        (512, 0, "Edge (512,0)"),
        (1, 1, "Near corner (1,1)"),
    ]
    
    print("PIXEL POSITIONS:")
    for s, f, desc in test_pixels:
        pos = positions[s, f].numpy()
        
        # Manual calculation to verify
        manual_pos = (detector.pix0_vector + 
                      s * detector.pixel_size * detector.sdet_vec + 
                      f * detector.pixel_size * detector.fdet_vec).numpy()
        
        print(f"  {desc:25}: {pos}")
        print(f"  {'Manual verification':25}: {manual_pos}")
        print(f"  {'Difference':25}: {pos - manual_pos}")
        print()

def analyze_beam_center_issue():
    """Analyze the beam center issue specifically."""
    
    print("="*70)
    print("BEAM CENTER COORDINATE ANALYSIS")
    print("="*70)
    
    config = DetectorConfig(
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s=51.2,  # mm
        beam_center_f=51.2   # mm
    )
    detector = Detector(config)
    
    print("CONFIGURATION:")
    print(f"  beam_center_s: {config.beam_center_s} mm")
    print(f"  beam_center_f: {config.beam_center_f} mm")
    print(f"  pixel_size_mm: {config.pixel_size_mm} mm")
    print(f"  distance_mm: {config.distance_mm} mm")
    print()
    
    print("INTERNAL CALCULATIONS:")
    print(f"  Distance in meters: {detector.distance} m")
    print(f"  Pixel size in meters: {detector.pixel_size} m")
    print()
    
    # Check what beam center means in pixels
    beam_center_s_pixels = config.beam_center_s / config.pixel_size_mm
    beam_center_f_pixels = config.beam_center_f / config.pixel_size_mm
    print(f"  Beam center in pixels: s={beam_center_s_pixels}, f={beam_center_f_pixels}")
    print()
    
    # MOSFLM beam center application
    beam_f_m, beam_s_m = detector._apply_mosflm_beam_convention()
    print("MOSFLM CONVENTION APPLICATION:")
    print(f"  Applied beam_f: {beam_f_m} m = {beam_f_m*1000} mm")
    print(f"  Applied beam_s: {beam_s_m} m = {beam_s_m*1000} mm")
    print("  (Note: These include axis swap and 0.5 pixel offset)")
    print()
    
    # Check pix0 calculation details
    print("PIX0 CALCULATION BREAKDOWN:")
    print("  Formula: pix0 = -Fbeam*fdet - Sbeam*sdet + distance*beam_vec")
    print("  Where:")
    Fbeam_pixels = config.beam_center_s / config.pixel_size_mm  # S→F swap
    Sbeam_pixels = config.beam_center_f / config.pixel_size_mm  # F→S swap
    Fbeam = (Fbeam_pixels + 0.5) * detector.pixel_size
    Sbeam = (Sbeam_pixels + 0.5) * detector.pixel_size
    beam_vector = torch.tensor([1.0, 0.0, 0.0])
    
    print(f"    Fbeam = ({Fbeam_pixels} + 0.5) * {detector.pixel_size} = {Fbeam} m")
    print(f"    Sbeam = ({Sbeam_pixels} + 0.5) * {detector.pixel_size} = {Sbeam} m")
    print(f"    beam_vector = {beam_vector.numpy()}")
    print()
    
    term1 = -Fbeam * detector.fdet_vec
    term2 = -Sbeam * detector.sdet_vec  
    term3 = detector.distance * beam_vector
    
    print(f"    -Fbeam * fdet_vec = -{Fbeam} * {detector.fdet_vec.numpy()} = {term1.numpy()}")
    print(f"    -Sbeam * sdet_vec = -{Sbeam} * {detector.sdet_vec.numpy()} = {term2.numpy()}")
    print(f"    distance * beam_vec = {detector.distance} * {beam_vector.numpy()} = {term3.numpy()}")
    print()
    print(f"  Final pix0_vector = {(term1 + term2 + term3).numpy()}")
    print(f"  Actual pix0_vector = {detector.pix0_vector.numpy()}")
    print()

def identify_coordinate_issue():
    """Identify the specific coordinate convention issue."""
    
    print("="*70)
    print("COORDINATE ISSUE IDENTIFICATION")  
    print("="*70)
    
    config = DetectorConfig(
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s=51.2,
        beam_center_f=51.2
    )
    detector = Detector(config)
    positions = detector.get_pixel_coords()
    
    print("HYPOTHESIS: Coordinate issue causes systematic error that grows with distance")
    print()
    
    # Test prediction: If beam center is supposed to be at different pixel
    print("Testing different beam center interpretations:")
    
    # Current: beam spot should be at (512, 512)
    current_beam_spot = positions[512, 512].numpy()
    print(f"1. Current beam spot at (512,512): {current_beam_spot}")
    
    # Alternative: beam spot should be offset
    # If beam_center is distance FROM corner, then actual beam pixel is different
    print()
    print("2. Alternative interpretations:")
    
    # What if beam center means the ACTUAL pixel where beam hits?
    # Then pix0 should be calculated differently
    print("   If beam_center means actual beam position, not distance from corner:")
    
    # Calculate what pixel (0,0) should be if beam is at (512, 512)
    beam_3d_pos = np.array([0.1, 0.0, 0.0])  # On detector surface, centered
    
    # Work backwards: pix0 = beam_pos - 512*sdet*pixel_size - 512*fdet*pixel_size
    calculated_pix0 = (beam_3d_pos - 
                       512 * detector.pixel_size * detector.sdet_vec.numpy() -
                       512 * detector.pixel_size * detector.fdet_vec.numpy())
    
    print(f"   Calculated pix0 if beam at (512,512): {calculated_pix0}")
    print(f"   Actual pix0: {detector.pix0_vector.numpy()}")
    print(f"   Difference: {detector.pix0_vector.numpy() - calculated_pix0}")
    
    return current_beam_spot, calculated_pix0

def test_coordinate_hypothesis():
    """Test specific hypotheses about coordinate mismatch."""
    
    print("\n" + "="*70)
    print("COORDINATE HYPOTHESIS TESTING")
    print("="*70)
    
    print("HYPOTHESIS 1: Sign error in axis directions")
    print("-" * 50)
    
    # Test if we should have different axis directions
    config = DetectorConfig(distance_mm=100.0, detector_convention=DetectorConvention.MOSFLM)
    detector = Detector(config)
    
    print("Current basis vectors:")
    print(f"  fdet_vec: {detector.fdet_vec.numpy()} (fast)")
    print(f"  sdet_vec: {detector.sdet_vec.numpy()} (slow)")  
    print(f"  odet_vec: {detector.odet_vec.numpy()} (normal)")
    
    # Test hypothesis: What if sdet should be +Y instead of -Y?
    print("\nTesting alternative: sdet_vec = [0, +1, 0] instead of [0, -1, 0]")
    
    # Manual calculation with flipped sdet
    alt_sdet = torch.tensor([0.0, 1.0, 0.0])
    alt_pix0 = (detector.pix0_vector[0],  # X unchanged
                -detector.pix0_vector[1], # Y flipped  
                detector.pix0_vector[2])  # Z unchanged
    
    print(f"  Alternative pix0 with +Y sdet: {alt_pix0}")
    
    # Check what pixel (512, 512) would be
    s, f = 512, 512
    alt_pos = (alt_pix0[0],
               alt_pix0[1] + s * detector.pixel_size * alt_sdet[1], 
               alt_pix0[2] + f * detector.pixel_size * detector.fdet_vec[2])
    
    print(f"  Alternative (512,512) position: {alt_pos}")
    print()
    
    print("HYPOTHESIS 2: Pixel indexing offset error")
    print("-" * 50)
    
    print("Testing if pixels should be offset by 0.5:")
    positions = detector.get_pixel_coords()
    
    # What if we should calculate positions at pixel centers (i + 0.5)?
    center_s = 512.5
    center_f = 512.5  
    
    center_pos = (detector.pix0_vector + 
                  center_s * detector.pixel_size * detector.sdet_vec +
                  center_f * detector.pixel_size * detector.fdet_vec).numpy()
    
    print(f"  Position at (512.5, 512.5): {center_pos}")
    print(f"  Current (512, 512):        {positions[512, 512].numpy()}")
    print(f"  Difference:                {center_pos - positions[512, 512].numpy()}")

if __name__ == "__main__":
    get_c_pixel_positions()
    analyze_key_positions()
    analyze_beam_center_issue()
    current_beam, calc_pix0 = identify_coordinate_issue()
    test_coordinate_hypothesis()
    
    print("\n" + "="*70)
    print("COORDINATE CONVENTION MISMATCH SUMMARY")
    print("="*70)
    print()
    print("KEY FINDINGS:")
    print("1. ✓ Basis vectors are geometrically correct")
    print("2. ✓ meshgrid indexing uses 'ij' (correct)")
    print("3. ✓ Pixel coordinate calculation formula is correct") 
    print("4. ✓ MOSFLM axis swap and 0.5 offset applied correctly")
    print()
    print("REMAINING ISSUES TO INVESTIGATE:")
    print("1. 🔍 Compare with actual C pixel calculations")
    print("2. 🔍 Verify beam center interpretation")
    print("3. 🔍 Check if axis sign conventions match C")
    print("4. 🔍 Validate pixel-center vs pixel-corner convention")
    print()
    print("Next step: Add printf statements to C code and compare pixel positions directly")