#!/usr/bin/env python3
"""
Verify PyTorch Detector beam center calculations against correct C values.

Key Discovery from Phase 4.1:
- C correctly calculates: Fclose = Sclose = 0.05125 m
- The 5.125e-05 was just a logging bug (double conversion)
- C's actual calculation: 0.0512 m (input) + 0.5 * 0.0001 m (pixel) = 0.05125 m

This script checks:
1. What PyTorch currently produces for Fclose/Sclose
2. How it compares to C's correct values
3. Whether correlation issues remain
"""

import os
import sys
import torch
import numpy as np

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path for imports
sys.path.insert(0, '/Users/ollie/Documents/nanoBragg/golden_suite_generator/src')

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig

def check_pytorch_beam_center():
    """Check what PyTorch Detector produces for beam center calculations."""
    
    print("=" * 60)
    print("PyTorch Beam Center Verification")
    print("=" * 60)
    
    # Test parameters matching the simple cubic case
    config = DetectorConfig(
        distance_mm=100.0,  # mm
        spixels=1024,
        fpixels=1024,
        pixel_size_mm=0.1,  # mm
        beam_center_s=51.2,  # mm (center of 1024x1024 detector)
        beam_center_f=51.2,  # mm
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=0.0
    )
    
    print(f"Input Configuration:")
    print(f"  beam_center_s: {config.beam_center_s} mm")
    print(f"  beam_center_f: {config.beam_center_f} mm") 
    print(f"  pixel_size_mm: {config.pixel_size_mm} mm")
    print(f"  distance_mm: {config.distance_mm} mm")
    print()
    
    # Create detector
    detector = Detector(config)
    
    # Check internal calculations
    print(f"PyTorch Internal Calculations:")
    print(f"  beam_center_s (internal): {detector.beam_center_s} m")
    print(f"  beam_center_f (internal): {detector.beam_center_f} m")
    print(f"  pixel_size (internal): {detector.pixel_size} m")
    print()
    
    # Calculate pixel coordinates for center pixel (512, 512)
    # This should match the C calculation
    center_s = 512
    center_f = 512
    
    # Get pixel coordinates using detector's method
    pixel_coords = detector.get_pixel_coords()
    
    # Extract coordinates for center pixel
    slow_coord = pixel_coords[center_s, center_f, 0].item()  # X component
    fast_coord = pixel_coords[center_s, center_f, 1].item()  # Y component 
    normal_coord = pixel_coords[center_s, center_f, 2].item()  # Z component
    
    print(f"PyTorch Pixel Coordinates for pixel ({center_s}, {center_f}):")
    print(f"  X coordinate: {slow_coord:.6f} m")
    print(f"  Y coordinate: {fast_coord:.6f} m") 
    print(f"  Z coordinate: {normal_coord:.6f} m")
    print()
    
    # The C code logs show Fclose and Sclose both equal to 0.05125 m
    # Based on the detector geometry, we need to check which PyTorch coordinate
    # corresponds to the C values. From the basis vectors:
    # fdet_vec = [0, 0, 1] (Z axis)
    # sdet_vec = [0, -1, 0] (negative Y axis)
    # So Fclose should correspond to Z, Sclose to -Y
    
    # For the center pixel (512, 512), we expect:
    # - Fclose (from Ybeam) = 0.05125 m -> should be abs(Y coordinate)
    # - Sclose (from Xbeam) = 0.05125 m -> should be Z coordinate
    
    c_correct_fclose = 0.05125  # m (corresponds to Z coordinate in PyTorch)
    c_correct_sclose = 0.05125  # m (corresponds to abs(Y coordinate) in PyTorch)
    
    print(f"C Reference Values (correct):")
    print(f"  Fclose = {c_correct_fclose:.6f} m (expected in Z coordinate)")
    print(f"  Sclose = {c_correct_sclose:.6f} m (expected in abs(Y coordinate))")
    print()
    
    print(f"Comparison:")
    diff_fclose = abs(normal_coord - c_correct_fclose)  # Z vs Fclose
    diff_sclose = abs(abs(fast_coord) - c_correct_sclose)  # abs(Y) vs Sclose
    print(f"  Z coordinate vs Fclose difference: {diff_fclose:.2e} m")
    print(f"  abs(Y coordinate) vs Sclose difference: {diff_sclose:.2e} m")
    
    # Check if they match within reasonable tolerance
    tolerance = 1e-6  # 1 micrometer
    fclose_matches = diff_fclose < tolerance
    sclose_matches = diff_sclose < tolerance
    
    print(f"  Z coordinate matches Fclose (< {tolerance:.0e} m): {fclose_matches}")
    print(f"  abs(Y coordinate) matches Sclose (< {tolerance:.0e} m): {sclose_matches}")
    
    if fclose_matches and sclose_matches:
        print("\n✅ SUCCESS: PyTorch matches C's correct beam center calculations!")
    else:
        print("\n❌ MISMATCH: PyTorch does not match C's calculations")
        
        # Investigate potential causes
        print(f"\nPotential Issues:")
        
        # Check if it's a unit conversion issue
        if abs(normal_coord * 1000 - c_correct_fclose) < tolerance:
            print(f"  - Unit conversion issue: PyTorch might be in wrong units")
            
        # Check if it's the +0.5 pixel offset
        # The expected value without offset should be close to detector distance
        expected_distance = detector.distance  # Should be 0.1 m
        if abs(slow_coord - expected_distance) < tolerance:
            print(f"  - X coordinate matches detector distance: possible geometry issue")
            
        # Check specific values
        print(f"\nDetailed Analysis:")
        print(f"  Expected Z (Fclose): {c_correct_fclose:.6f} m")
        print(f"  Actual Z: {normal_coord:.6f} m")
        print(f"  Expected abs(Y) (Sclose): {c_correct_sclose:.6f} m")
        print(f"  Actual abs(Y): {abs(fast_coord):.6f} m")
        print(f"  Actual Y: {fast_coord:.6f} m")
        print(f"  Actual X: {slow_coord:.6f} m")
        print(f"  Detector distance: {detector.distance:.6f} m")
    
    return fclose_matches and sclose_matches

def check_detector_basis_vectors():
    """Check detector basis vectors for additional insights."""
    
    print(f"\n" + "=" * 60)
    print("Detector Basis Vector Check")
    print("=" * 60)
    
    config = DetectorConfig(
        distance_mm=100.0,  # mm
        spixels=1024,
        fpixels=1024, 
        pixel_size_mm=0.1,  # mm
        beam_center_s=51.2,  # mm
        beam_center_f=51.2,  # mm
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=0.0
    )
    
    detector = Detector(config)
    
    print(f"Detector basis vectors:")
    print(f"  fdet_vec: {detector.fdet_vec}")
    print(f"  sdet_vec: {detector.sdet_vec}")
    print(f"  odet_vec: {detector.odet_vec}")
    print()
    
    # Check orthonormality
    fdet_norm = torch.norm(detector.fdet_vec).item()
    sdet_norm = torch.norm(detector.sdet_vec).item() 
    odet_norm = torch.norm(detector.odet_vec).item()
    
    print(f"Basis vector norms:")
    print(f"  |fdet_vec|: {fdet_norm:.6f}")
    print(f"  |sdet_vec|: {sdet_norm:.6f}")
    print(f"  |odet_vec|: {odet_norm:.6f}")
    
    # Check orthogonality
    fs_dot = torch.dot(detector.fdet_vec, detector.sdet_vec).item()
    fo_dot = torch.dot(detector.fdet_vec, detector.odet_vec).item()
    so_dot = torch.dot(detector.sdet_vec, detector.odet_vec).item()
    
    print(f"Orthogonality check (should be ~0):")
    print(f"  fdet_vec · sdet_vec: {fs_dot:.2e}")
    print(f"  fdet_vec · odet_vec: {fo_dot:.2e}")
    print(f"  sdet_vec · odet_vec: {so_dot:.2e}")
    
    # Also check pix0_vector
    print(f"\nPixel (0,0) vector (pix0_vector):")
    print(f"  pix0_vector: {detector.pix0_vector}")

if __name__ == "__main__":
    matches = check_pytorch_beam_center()
    check_detector_basis_vectors()
    
    print(f"\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if matches:
        print("✅ PyTorch beam center calculations match C reference")
        print("   Ready to run correlation check")
    else:
        print("❌ PyTorch beam center calculations need fixing")
        print("   Fix required before correlation check")