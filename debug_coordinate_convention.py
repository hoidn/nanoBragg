#!/usr/bin/env python3
"""
Debug script to identify coordinate convention mismatch in detector geometry.
Focus on finding why spots align at center but diverge towards edges.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention

def test_pixel_coordinate_mapping():
    """Test how pixels map to 3D coordinates."""
    print("="*70)
    print("COORDINATE CONVENTION DEBUG")
    print("="*70)
    
    # Test with simple configuration (no rotations)
    config = DetectorConfig(
        distance_mm=100.0,
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=0.0,
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s=51.2,  # mm
        beam_center_f=51.2   # mm
    )
    
    detector = Detector(config)
    
    print("DETECTOR CONFIGURATION:")
    print(f"  Convention: {config.detector_convention}")
    print(f"  Distance: {config.distance_mm} mm = {detector.distance:.6f} m")
    print(f"  Pixel size: {config.pixel_size_mm} mm = {detector.pixel_size:.6f} m") 
    print(f"  Beam center (s,f): ({config.beam_center_s}, {config.beam_center_f}) mm")
    print()
    
    print("BASIS VECTORS (should be orthonormal):")
    print(f"  fdet_vec: {detector.fdet_vec.numpy()}")
    print(f"  sdet_vec: {detector.sdet_vec.numpy()}")  
    print(f"  odet_vec: {detector.odet_vec.numpy()}")
    print()
    
    print("PIX0 VECTOR (position of pixel 0,0):")
    print(f"  pix0_vector: {detector.pix0_vector.numpy()}")
    print()
    
    # Check specific pixels
    positions = detector.get_pixel_coords()
    
    print("CRITICAL PIXEL POSITIONS:")
    test_pixels = [
        (0, 0, "Corner: (0,0)"),
        (512, 512, "Center: (512,512)"),  # Should be close to beam center
        (0, 512, "Edge: (0,512)"),
        (512, 0, "Edge: (512,0)"),
        (1023, 1023, "Corner: (1023,1023)"),
        (100, 200, "Random: (100,200)")
    ]
    
    for s, f, desc in test_pixels:
        pos = positions[s, f].numpy()
        # Calculate distance from origin
        dist = np.linalg.norm(pos)
        print(f"  {desc:20} → {pos} (dist: {dist:.6f}m)")
    
    print()
    
    # Manual calculation check
    print("MANUAL CALCULATION VERIFICATION:")
    s, f = 100, 200
    manual_pos = (detector.pix0_vector + 
                  s * detector.pixel_size * detector.sdet_vec + 
                  f * detector.pixel_size * detector.fdet_vec).numpy()
    actual_pos = positions[s, f].numpy()
    diff = actual_pos - manual_pos
    print(f"  Manual calc (100,200):  {manual_pos}")
    print(f"  Actual pos (100,200):   {actual_pos}")
    print(f"  Difference:             {diff}")
    print(f"  Max diff:               {np.max(np.abs(diff))}")
    
    return positions

def test_mosflm_convention_details():
    """Test MOSFLM convention axis swapping."""
    print("\n" + "="*70)
    print("MOSFLM CONVENTION ANALYSIS")
    print("="*70)
    
    # Test both conventions
    for conv in [DetectorConvention.MOSFLM, DetectorConvention.XDS]:
        print(f"\n--- {conv.name} Convention ---")
        
        config = DetectorConfig(
            distance_mm=100.0,
            detector_convention=conv,
            beam_center_s=51.2,  # mm
            beam_center_f=51.2   # mm
        )
        
        detector = Detector(config)
        
        # Check beam center mapping
        beam_f_m, beam_s_m = detector._apply_mosflm_beam_convention()
        print(f"  Input beam center (s,f): ({config.beam_center_s}, {config.beam_center_f}) mm")
        print(f"  Applied beam center (f,s): ({beam_f_m*1000:.3f}, {beam_s_m*1000:.3f}) mm")
        
        # Check pixel (512, 512) - should be close to beam center
        pos_center = detector.get_pixel_coords()[512, 512].numpy()
        print(f"  Pixel (512,512) position: {pos_center}")
        
        # Calculate expected position for beam center
        # In MOSFLM: beam_center_s → F axis, beam_center_f → S axis
        if conv == DetectorConvention.MOSFLM:
            # With axis swap: s=51.2mm → F, f=51.2mm → S  
            # Pixel (512,512) should be close to (-F, -S, distance)
            expected_f = -(51.2 + 0.5*0.1) / 1000  # -(beam_s + 0.5*pixel_size)
            expected_s = -(51.2 + 0.5*0.1) / 1000  # -(beam_f + 0.5*pixel_size)
        else:
            expected_f = -51.2 / 1000  # -beam_f
            expected_s = -51.2 / 1000  # -beam_s
        
        expected_pos = np.array([0.1, expected_f, expected_s])  # [distance, -F, -S]
        print(f"  Expected beam spot: {expected_pos}")
        diff = pos_center - expected_pos
        print(f"  Difference: {diff}")
        print(f"  Max diff: {np.max(np.abs(diff)):.6f}m")

def test_coordinate_system_orientation():
    """Test the coordinate system orientation."""
    print("\n" + "="*70) 
    print("COORDINATE SYSTEM ORIENTATION")
    print("="*70)
    
    config = DetectorConfig(distance_mm=100.0, detector_convention=DetectorConvention.MOSFLM)
    detector = Detector(config)
    positions = detector.get_pixel_coords()
    
    # Check if coordinate system is right-handed
    print("COORDINATE SYSTEM CHECK:")
    print(f"  X-axis (beam): [1, 0, 0]")
    print(f"  Y-axis (up):   [0, 1, 0]")  
    print(f"  Z-axis (right):[0, 0, 1]")
    print()
    
    # Check movement patterns
    print("PIXEL MOVEMENT ANALYSIS:")
    
    # Moving in S (slow) direction: (0,0) to (100,0)
    pos_00 = positions[0, 0].numpy()
    pos_100_0 = positions[100, 0].numpy() 
    s_movement = pos_100_0 - pos_00
    print(f"  S-direction (0,0)→(100,0): {s_movement}")
    print(f"  Expected: S pixels * sdet_vec = 100 * {detector.sdet_vec.numpy()}")
    expected_s = 100 * detector.pixel_size * detector.sdet_vec.numpy()
    print(f"  Manual calc: {expected_s}")
    print(f"  Match S: {np.allclose(s_movement, expected_s)}")
    
    # Moving in F (fast) direction: (0,0) to (0,100)  
    pos_0_100 = positions[0, 100].numpy()
    f_movement = pos_0_100 - pos_00
    print(f"  F-direction (0,0)→(0,100): {f_movement}")
    print(f"  Expected: F pixels * fdet_vec = 100 * {detector.fdet_vec.numpy()}")
    expected_f = 100 * detector.pixel_size * detector.fdet_vec.numpy()
    print(f"  Manual calc: {expected_f}")
    print(f"  Match F: {np.allclose(f_movement, expected_f)}")

def check_divergence_pattern():
    """Analyze the divergence pattern - center vs edges."""
    print("\n" + "="*70)
    print("DIVERGENCE PATTERN ANALYSIS")
    print("="*70)
    
    config = DetectorConfig(
        distance_mm=100.0, 
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s=51.2,
        beam_center_f=51.2
    )
    detector = Detector(config)
    positions = detector.get_pixel_coords()
    
    center_s, center_f = 512, 512
    
    print("RADIAL DISTANCE CHECK:")
    print("(Looking for systematic bias that increases with distance from center)")
    
    # Test pixels at different distances from center
    test_distances = [0, 100, 200, 400, 512]
    
    for dist in test_distances:
        if dist == 0:
            s, f = center_s, center_f
            desc = "Center"
        else:
            # Test pixel at distance 'dist' in diagonal direction
            s = center_s + int(dist / np.sqrt(2))
            f = center_f + int(dist / np.sqrt(2))
            if s >= 1024 or f >= 1024:
                continue
            desc = f"Dist {dist}"
        
        pos = positions[s, f].numpy()
        
        # Calculate distance from detector center in detector plane
        # Project position onto detector plane (remove X component)
        detector_plane_pos = pos[1:3]  # Y, Z components
        radial_dist = np.linalg.norm(detector_plane_pos)
        
        # Calculate expected position based on pixel indices
        pixel_dist_from_center = np.sqrt((s - center_s)**2 + (f - center_f)**2)
        expected_radial = pixel_dist_from_center * detector.pixel_size
        
        print(f"  {desc:10} ({s:3},{f:3}): pos={pos}, radial={radial_dist:.6f}m, expected={expected_radial:.6f}m")

if __name__ == "__main__":
    positions = test_pixel_coordinate_mapping()
    test_mosflm_convention_details()
    test_coordinate_system_orientation() 
    check_divergence_pattern()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("Check the output above for:")
    print("1. Incorrect meshgrid indexing")
    print("2. Wrong MOSFLM axis mapping")
    print("3. Incorrect pixel origin convention") 
    print("4. Wrong basis vector application order")
    print("5. Systematic radial errors")