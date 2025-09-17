#!/usr/bin/env python3
"""
Minimal test case for pix0_vector calculation in isolation.

This script tests just the mathematical operations to verify each step
and identify where discrepancies might occur.
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

from nanobrag_torch.utils.units import degrees_to_radians
from nanobrag_torch.utils.geometry import angles_to_rotation_matrix, rotate_axis

def test_basic_vectors():
    """Test basic vector operations."""
    print("=" * 60)
    print("BASIC VECTOR OPERATIONS TEST")
    print("=" * 60)
    
    # Test vectors
    v1 = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    v2 = torch.tensor([0.0, 1.0, 0.0], dtype=torch.float64)
    v3 = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    
    print(f"Unit vectors:")
    print(f"  v1 = {v1}")
    print(f"  v2 = {v2}")
    print(f"  v3 = {v3}")
    
    # Test scalar multiplication
    scalar = 2.5
    result = scalar * v1
    print(f"Scalar multiplication: {scalar} * {v1} = {result}")
    
    # Test vector addition
    combined = v1 + v2 + v3
    print(f"Vector addition: v1 + v2 + v3 = {combined}")
    
    return True

def test_rotation_matrices():
    """Test rotation matrix construction for specific angles."""
    print("\n" + "=" * 60)
    print("ROTATION MATRIX TEST")
    print("=" * 60)
    
    # Test angles from our problem case
    rotx_deg = 5.0
    roty_deg = 3.0
    rotz_deg = 2.0
    
    rotx_rad = torch.tensor(degrees_to_radians(rotx_deg), dtype=torch.float64)
    roty_rad = torch.tensor(degrees_to_radians(roty_deg), dtype=torch.float64)
    rotz_rad = torch.tensor(degrees_to_radians(rotz_deg), dtype=torch.float64)
    
    print(f"Input angles: rotx={rotx_deg}°, roty={roty_deg}°, rotz={rotz_deg}°")
    print(f"In radians: rotx={rotx_rad}, roty={roty_rad}, rotz={rotz_rad}")
    
    # Test individual rotation matrices
    print(f"\nIndividual rotation matrices:")
    
    # X rotation matrix
    cos_x = torch.cos(rotx_rad)
    sin_x = torch.sin(rotx_rad)
    Rx = torch.tensor([
        [1.0, 0.0, 0.0],
        [0.0, cos_x, -sin_x],
        [0.0, sin_x, cos_x]
    ], dtype=torch.float64)
    print(f"Rx (around X-axis):\n{Rx}")
    
    # Y rotation matrix
    cos_y = torch.cos(roty_rad)
    sin_y = torch.sin(roty_rad)
    Ry = torch.tensor([
        [cos_y, 0.0, sin_y],
        [0.0, 1.0, 0.0],
        [-sin_y, 0.0, cos_y]
    ], dtype=torch.float64)
    print(f"Ry (around Y-axis):\n{Ry}")
    
    # Z rotation matrix
    cos_z = torch.cos(rotz_rad)
    sin_z = torch.sin(rotz_rad)
    Rz = torch.tensor([
        [cos_z, -sin_z, 0.0],
        [sin_z, cos_z, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=torch.float64)
    print(f"Rz (around Z-axis):\n{Rz}")
    
    # Combined rotation: R = Rz @ Ry @ Rx (XYZ order)
    R_manual = torch.matmul(torch.matmul(Rz, Ry), Rx)
    print(f"Combined R = Rz @ Ry @ Rx:\n{R_manual}")
    
    # Test against our utility function
    R_utility = angles_to_rotation_matrix(rotx_rad, roty_rad, rotz_rad)
    print(f"Utility function result:\n{R_utility}")
    
    # Check if they match
    match = torch.allclose(R_manual, R_utility, atol=1e-15)
    print(f"Manual vs utility match: {match}")
    
    if not match:
        print(f"Difference:\n{R_manual - R_utility}")
    
    return R_utility

def test_rodrigues_rotation():
    """Test Rodrigues rotation formula implementation."""
    print("\n" + "=" * 60)
    print("RODRIGUES ROTATION TEST")
    print("=" * 60)
    
    # Test vector
    v = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    
    # Test axes
    axis_z_pos = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    axis_z_neg = torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64)
    
    # Test angle
    angle_deg = 20.0
    angle_rad = torch.tensor(degrees_to_radians(angle_deg), dtype=torch.float64)
    
    print(f"Test vector: {v}")
    print(f"Rotation angle: {angle_deg}° = {angle_rad} rad")
    print(f"Test axes:")
    print(f"  +Z axis: {axis_z_pos}")
    print(f"  -Z axis: {axis_z_neg}")
    
    # Apply rotation with both axes
    v_rot_pos = rotate_axis(v, axis_z_pos, angle_rad)
    v_rot_neg = rotate_axis(v, axis_z_neg, angle_rad)
    
    print(f"Rotation results:")
    print(f"  v rotated around +Z: {v_rot_pos}")
    print(f"  v rotated around -Z: {v_rot_neg}")
    
    # Expected results for rotation around Z-axis
    cos_angle = torch.cos(angle_rad)
    sin_angle = torch.sin(angle_rad)
    
    # For +Z axis rotation: [cos(θ), sin(θ), 0]
    expected_pos = torch.tensor([cos_angle, sin_angle, 0.0], dtype=torch.float64)
    # For -Z axis rotation: [cos(θ), -sin(θ), 0]
    expected_neg = torch.tensor([cos_angle, -sin_angle, 0.0], dtype=torch.float64)
    
    print(f"Expected results:")
    print(f"  +Z expected: {expected_pos}")
    print(f"  -Z expected: {expected_neg}")
    
    print(f"Matches:")
    print(f"  +Z match: {torch.allclose(v_rot_pos, expected_pos, atol=1e-15)}")
    print(f"  -Z match: {torch.allclose(v_rot_neg, expected_neg, atol=1e-15)}")
    
    return v_rot_pos, v_rot_neg

def test_pix0_calculation_isolated():
    """Test the isolated pix0 calculation with known values."""
    print("\n" + "=" * 60)
    print("ISOLATED PIX0 CALCULATION TEST")
    print("=" * 60)
    
    # Known values from our configuration
    beam_center_f_pixels = 51.2 / 0.1  # 512.0 pixels
    beam_center_s_pixels = 51.2 / 0.1  # 512.0 pixels
    pixel_size_m = 0.1 / 1000.0        # 0.0001 m
    distance_m = 100.0 / 1000.0         # 0.1 m
    
    print(f"Input values:")
    print(f"  Beam center: ({beam_center_f_pixels}, {beam_center_s_pixels}) pixels")
    print(f"  Pixel size: {pixel_size_m} m")
    print(f"  Distance: {distance_m} m")
    
    # MOSFLM initial basis vectors
    fdet_initial = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    sdet_initial = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
    odet_initial = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    
    print(f"MOSFLM basis vectors:")
    print(f"  fdet = {fdet_initial}")
    print(f"  sdet = {sdet_initial}")
    print(f"  odet = {odet_initial}")
    
    # Calculate distances (with 0.5 pixel offset)
    Fclose = (beam_center_f_pixels + 0.5) * pixel_size_m
    Sclose = (beam_center_s_pixels + 0.5) * pixel_size_m
    
    print(f"Beam distances:")
    print(f"  Fclose = ({beam_center_f_pixels} + 0.5) * {pixel_size_m} = {Fclose}")
    print(f"  Sclose = ({beam_center_s_pixels} + 0.5) * {pixel_size_m} = {Sclose}")
    
    # Calculate unrotated pix0
    term1 = -Fclose * fdet_initial
    term2 = -Sclose * sdet_initial
    term3 = distance_m * odet_initial
    
    print(f"Pix0 components:")
    print(f"  Term 1: -Fclose * fdet = -{Fclose} * {fdet_initial} = {term1}")
    print(f"  Term 2: -Sclose * sdet = -{Sclose} * {sdet_initial} = {term2}")
    print(f"  Term 3: distance * odet = {distance_m} * {odet_initial} = {term3}")
    
    pix0_unrotated = term1 + term2 + term3
    print(f"  Unrotated pix0 = {pix0_unrotated}")
    
    # Apply rotations
    rotx_rad = torch.tensor(degrees_to_radians(5.0), dtype=torch.float64)
    roty_rad = torch.tensor(degrees_to_radians(3.0), dtype=torch.float64)
    rotz_rad = torch.tensor(degrees_to_radians(2.0), dtype=torch.float64)
    
    R = angles_to_rotation_matrix(rotx_rad, roty_rad, rotz_rad)
    pix0_after_xyz = torch.matmul(R, pix0_unrotated)
    
    print(f"After XYZ rotations: {pix0_after_xyz}")
    
    # Apply two-theta rotation
    twotheta_rad = torch.tensor(degrees_to_radians(20.0), dtype=torch.float64)
    
    # Test with both axis directions
    axis_pos_z = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    axis_neg_z = torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64)
    
    pix0_final_pos = rotate_axis(pix0_after_xyz, axis_pos_z, twotheta_rad)
    pix0_final_neg = rotate_axis(pix0_after_xyz, axis_neg_z, twotheta_rad)
    
    print(f"Final results:")
    print(f"  With +Z axis: {pix0_final_pos}")
    print(f"  With -Z axis: {pix0_final_neg}")
    
    # Expected from our previous debugging (manual calculation)
    expected_manual = torch.tensor([0.0965, -0.0255, -0.0099], dtype=torch.float64)
    print(f"Expected (manual): {expected_manual}")
    
    print(f"Matches:")
    print(f"  +Z matches manual: {torch.allclose(pix0_final_pos, expected_manual, atol=1e-3)}")
    print(f"  -Z matches manual: {torch.allclose(pix0_final_neg, expected_manual, atol=1e-3)}")
    
    return pix0_final_pos, pix0_final_neg

def test_precision_issues():
    """Test for potential precision issues in calculations."""
    print("\n" + "=" * 60)
    print("PRECISION ISSUES TEST")
    print("=" * 60)
    
    # Test with different precisions
    angles_deg = [5.0, 3.0, 2.0, 20.0]
    
    print("Testing angle precision (degrees to radians):")
    for angle_deg in angles_deg:
        angle_rad_float32 = torch.tensor(degrees_to_radians(angle_deg), dtype=torch.float32)
        angle_rad_float64 = torch.tensor(degrees_to_radians(angle_deg), dtype=torch.float64)
        
        print(f"  {angle_deg}°:")
        print(f"    float32: {angle_rad_float32}")
        print(f"    float64: {angle_rad_float64}")
        print(f"    difference: {abs(angle_rad_float64 - angle_rad_float32.double())}")
    
    # Test matrix multiplication precision
    print("\nTesting matrix multiplication precision:")
    
    R_f32 = angles_to_rotation_matrix(
        torch.tensor(degrees_to_radians(5.0), dtype=torch.float32),
        torch.tensor(degrees_to_radians(3.0), dtype=torch.float32),
        torch.tensor(degrees_to_radians(2.0), dtype=torch.float32)
    )
    
    R_f64 = angles_to_rotation_matrix(
        torch.tensor(degrees_to_radians(5.0), dtype=torch.float64),
        torch.tensor(degrees_to_radians(3.0), dtype=torch.float64),
        torch.tensor(degrees_to_radians(2.0), dtype=torch.float64)
    )
    
    print(f"Float32 rotation matrix:\n{R_f32}")
    print(f"Float64 rotation matrix:\n{R_f64}")
    print(f"Matrix difference:\n{R_f64 - R_f32.double()}")
    
    return True

def main():
    """Run all minimal tests."""
    print("Minimal Pix0 Calculation Tests")
    print("Testing individual components to isolate issues")
    
    # Run tests
    test_basic_vectors()
    R = test_rotation_matrices()
    test_rodrigues_rotation()
    test_pix0_calculation_isolated()
    test_precision_issues()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("All tests completed. Check for any discrepancies above.")
    print("This helps isolate whether issues are in:")
    print("1. Basic vector operations")
    print("2. Rotation matrix construction")
    print("3. Rodrigues formula implementation")
    print("4. Overall calculation pipeline")
    print("5. Precision/dtype issues")

if __name__ == "__main__":
    main()