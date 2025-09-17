#!/usr/bin/env python3
"""
Test coordinate convention with the SAME rotated configuration as the C trace.
This should identify the exact coordinate convention mismatch.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention

def test_rotated_configuration():
    """Test with the same rotations as the C trace."""
    
    print("="*70)
    print("TESTING ROTATED CONFIGURATION FROM C TRACE")
    print("="*70)
    
    # Convert radians to degrees for configuration
    rotx_rad = 0.0872664625997165  # ≈ 5°
    roty_rad = 0.0523598775598299  # ≈ 3°
    rotz_rad = 0.0349065850398866  # ≈ 2°
    
    rotx_deg = np.degrees(rotx_rad)
    roty_deg = np.degrees(roty_rad)
    rotz_deg = np.degrees(rotz_rad)
    
    print(f"C TRACE ROTATION ANGLES:")
    print(f"  rotx: {rotx_rad:.6f} rad = {rotx_deg:.3f}°")
    print(f"  roty: {roty_rad:.6f} rad = {roty_deg:.3f}°")
    print(f"  rotz: {rotz_rad:.6f} rad = {rotz_deg:.3f}°")
    print(f"  twotheta: 0°")
    print()
    
    # Configure with same parameters
    config = DetectorConfig(
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s=51.2,  # mm
        beam_center_f=51.2,  # mm
        detector_rotx_deg=rotx_deg,
        detector_roty_deg=roty_deg,
        detector_rotz_deg=rotz_deg,
        detector_twotheta_deg=0.0
    )
    
    detector = Detector(config)
    
    print("PYTORCH RESULTS:")
    print(f"  fdet_vec: {detector.fdet_vec.numpy()}")
    print(f"  sdet_vec: {detector.sdet_vec.numpy()}")
    print(f"  odet_vec: {detector.odet_vec.numpy()}")
    print(f"  pix0_vector: {detector.pix0_vector.numpy()}")
    print()
    
    print("C TRACE RESULTS (for comparison):")
    c_fdet = np.array([0.0551467333542405, -0.0852831016700733, 0.994829447880333])
    c_sdet = np.array([0.0302080931112661, -0.99574703303416, -0.0870362988312832])
    c_odet = np.array([0.998021196624068, 0.0348516681551873, -0.0523359562429438])
    c_pix0 = np.array([0.0956255651436428, 0.055402794403592, -0.0465243988887638])
    
    print(f"  fdet_vec: {c_fdet}")
    print(f"  sdet_vec: {c_sdet}")
    print(f"  odet_vec: {c_odet}")
    print(f"  pix0_vector: {c_pix0}")
    print()
    
    print("DIFFERENCES:")
    fdet_diff = detector.fdet_vec.numpy() - c_fdet
    sdet_diff = detector.sdet_vec.numpy() - c_sdet
    odet_diff = detector.odet_vec.numpy() - c_odet
    pix0_diff = detector.pix0_vector.numpy() - c_pix0
    
    print(f"  fdet difference: {fdet_diff} (max: {np.max(np.abs(fdet_diff)):.6f})")
    print(f"  sdet difference: {sdet_diff} (max: {np.max(np.abs(sdet_diff)):.6f})")
    print(f"  odet difference: {odet_diff} (max: {np.max(np.abs(odet_diff)):.6f})")
    print(f"  pix0 difference: {pix0_diff} (max: {np.max(np.abs(pix0_diff)):.6f})")
    print()
    
    return detector, c_pix0

def compare_pixel_positions(detector, c_pix0):
    """Compare pixel positions between PyTorch and inferred C positions."""
    
    print("="*70)
    print("PIXEL POSITION COMPARISON")
    print("="*70)
    
    # Get PyTorch pixel positions
    positions = detector.get_pixel_coords()
    
    # Infer C pixel positions using C basis vectors
    c_fdet = np.array([0.0551467333542405, -0.0852831016700733, 0.994829447880333])
    c_sdet = np.array([0.0302080931112661, -0.99574703303416, -0.0870362988312832])
    c_pixel_size = 0.0001  # meters
    
    test_pixels = [
        (0, 0, "Corner (0,0)"),
        (512, 512, "Center (512,512)"),
        (100, 200, "Random (100,200)"),
        (0, 512, "Edge (0,512)"),
        (512, 0, "Edge (512,0)")
    ]
    
    print("PIXEL COORDINATE COMPARISON:")
    for s, f, desc in test_pixels:
        # PyTorch calculation
        py_pos = positions[s, f].numpy()
        
        # Inferred C calculation using C basis vectors
        c_pos = c_pix0 + s * c_pixel_size * c_sdet + f * c_pixel_size * c_fdet
        
        # Difference
        diff = py_pos - c_pos
        max_diff = np.max(np.abs(diff))
        
        print(f"  {desc:15}")
        print(f"    PyTorch: {py_pos}")
        print(f"    C (est):  {c_pos}")
        print(f"    Diff:     {diff} (max: {max_diff:.6f})")
        print()

def analyze_coordinate_system_differences():
    """Analyze the fundamental coordinate system differences."""
    
    print("="*70)
    print("COORDINATE SYSTEM ANALYSIS")
    print("="*70)
    
    # From C trace - analyze the rotation matrix
    print("C TRACE ROTATION MATRIX ANALYSIS:")
    
    # From C trace line 16
    R_total_c = np.array([
        [0.998021196624068, -0.0302080931112661, 0.0551467333542405],
        [0.0348516681551873, 0.99574703303416, -0.0852831016700733], 
        [-0.0523359562429438, 0.0870362988312832, 0.994829447880333]
    ])
    
    print("C rotation matrix:")
    print(R_total_c)
    print()
    
    # Calculate our rotation matrix
    from src.nanobrag_torch.utils.geometry import angles_to_rotation_matrix
    from src.nanobrag_torch.utils.units import degrees_to_radians
    
    rotx_rad = 0.0872664625997165
    roty_rad = 0.0523598775598299
    rotz_rad = 0.0349065850398866
    
    rotx = torch.tensor(rotx_rad)
    roty = torch.tensor(roty_rad)
    rotz = torch.tensor(rotz_rad)
    
    R_pytorch = angles_to_rotation_matrix(rotx, roty, rotz).numpy()
    
    print("PyTorch rotation matrix:")
    print(R_pytorch)
    print()
    
    print("Matrix difference:")
    R_diff = R_pytorch - R_total_c
    print(R_diff)
    print(f"Max difference: {np.max(np.abs(R_diff)):.10f}")
    print()
    
    # Test if the matrices are the same within tolerance
    matrices_match = np.allclose(R_pytorch, R_total_c, atol=1e-10)
    print(f"Matrices match (1e-10 tolerance): {matrices_match}")
    
    if not matrices_match:
        print("🚨 ROTATION MATRIX MISMATCH DETECTED!")
        print("This is likely the root cause of the coordinate convention issue.")
    else:
        print("✓ Rotation matrices match - issue is elsewhere")

def test_simple_case_for_validation():
    """Test a simple case to ensure our basic implementation is correct."""
    
    print("\n" + "="*70)
    print("SIMPLE CASE VALIDATION")
    print("="*70)
    
    # Test with no rotations to validate basic implementation
    config_simple = DetectorConfig(
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=0.0
    )
    
    detector_simple = Detector(config_simple)
    
    print("SIMPLE CASE (no rotations):")
    print(f"  fdet_vec: {detector_simple.fdet_vec.numpy()}")
    print(f"  sdet_vec: {detector_simple.sdet_vec.numpy()}")
    print(f"  odet_vec: {detector_simple.odet_vec.numpy()}")
    print(f"  pix0_vector: {detector_simple.pix0_vector.numpy()}")
    
    print("\nExpected for unrotated MOSFLM:")
    print("  fdet_vec: [0, 0, 1] (Z-axis)")
    print("  sdet_vec: [0, -1, 0] (-Y-axis)")
    print("  odet_vec: [1, 0, 0] (X-axis)")
    print("  pix0_vector: [0.1, 0.05125, -0.05125] (calculated)")
    
    # Check pixel (512, 512) in simple case
    positions_simple = detector_simple.get_pixel_coords()
    center_pos_simple = positions_simple[512, 512].numpy()
    print(f"\nPixel (512,512) position: {center_pos_simple}")
    print("This should be close to the beam center on the detector surface")

if __name__ == "__main__":
    detector, c_pix0 = test_rotated_configuration()
    compare_pixel_positions(detector, c_pix0)
    analyze_coordinate_system_differences()
    test_simple_case_for_validation()
    
    print("\n" + "="*70)
    print("COORDINATE CONVENTION DIAGNOSIS")
    print("="*70)
    print("If rotation matrices match but pixel positions differ,")
    print("the issue is in pix0_vector calculation or axis interpretation.")
    print("If rotation matrices differ, the issue is in rotation implementation.")