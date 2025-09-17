#!/usr/bin/env python3
"""
Manual pix0_vector verification script for Phase 4.1.

This script calculates pix0 step by step manually using known correct formulas
and compares with both C and Python results to identify the source of discrepancy.
"""

import os
import sys
import torch
import numpy as np
import math
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig, DetectorPivot, DetectorConvention


def manual_pix0_calculation():
    """
    Calculate pix0_vector manually using the exact mathematical formulas.
    
    This implements the SAMPLE pivot mode calculation from first principles
    to serve as a reference implementation.
    """
    print("=" * 80)
    print("MANUAL PIX0_VECTOR VERIFICATION")
    print("=" * 80)
    
    # Configuration (exact same as problematic case)
    distance_mm = 100.0
    beam_center_s = 51.2  # mm
    beam_center_f = 51.2  # mm
    pixel_size_mm = 0.1
    
    rotx_deg = 5.0
    roty_deg = 3.0  
    rotz_deg = 2.0
    twotheta_deg = 20.0
    
    print("CONFIGURATION:")
    print(f"  distance_mm = {distance_mm}")
    print(f"  beam_center_s = {beam_center_s} mm")
    print(f"  beam_center_f = {beam_center_f} mm") 
    print(f"  pixel_size_mm = {pixel_size_mm}")
    print(f"  rotx = {rotx_deg}°, roty = {roty_deg}°, rotz = {rotz_deg}°")
    print(f"  twotheta = {twotheta_deg}°")
    print(f"  convention = MOSFLM")
    print(f"  pivot = SAMPLE")
    
    # Convert to radians
    rotx_rad = math.radians(rotx_deg)
    roty_rad = math.radians(roty_deg)
    rotz_rad = math.radians(rotz_deg)
    twotheta_rad = math.radians(twotheta_deg)
    
    print(f"\nANGLES IN RADIANS:")
    print(f"  rotx = {rotx_rad:.15f}")
    print(f"  roty = {roty_rad:.15f}")
    print(f"  rotz = {rotz_rad:.15f}")
    print(f"  twotheta = {twotheta_rad:.15f}")
    
    # Step 1: Initial basis vectors (MOSFLM convention)
    print(f"\nSTEP 1: INITIAL BASIS VECTORS (MOSFLM):")
    fdet_init = np.array([0.0, 0.0, 1.0])
    sdet_init = np.array([0.0, -1.0, 0.0])  
    odet_init = np.array([1.0, 0.0, 0.0])
    
    print(f"  fdet_initial = {fdet_init}")
    print(f"  sdet_initial = {sdet_init}")
    print(f"  odet_initial = {odet_init}")
    
    # Step 2: Calculate unrotated pix0 (SAMPLE pivot mode)
    print(f"\nSTEP 2: UNROTATED PIX0 CALCULATION (SAMPLE PIVOT):")
    
    # MOSFLM beam center convention: add 0.5 for pixel center
    Fclose = (beam_center_f + 0.5) * pixel_size_mm / 1000.0  # Convert mm to m
    Sclose = (beam_center_s + 0.5) * pixel_size_mm / 1000.0  # Convert mm to m
    distance_m = distance_mm / 1000.0  # Convert mm to m
    
    print(f"  beam_center_f + 0.5 = {beam_center_f + 0.5}")
    print(f"  beam_center_s + 0.5 = {beam_center_s + 0.5}")
    print(f"  Fclose = {Fclose:.15f} m")
    print(f"  Sclose = {Sclose:.15f} m")
    print(f"  distance = {distance_m:.15f} m")
    
    # Calculate components
    fdet_component = -Fclose * fdet_init
    sdet_component = -Sclose * sdet_init
    odet_component = distance_m * odet_init
    
    print(f"  fdet_component = {fdet_component}")
    print(f"  sdet_component = {sdet_component}")
    print(f"  odet_component = {odet_component}")
    
    # Sum components for unrotated pix0
    pix0_unrotated = fdet_component + sdet_component + odet_component
    print(f"  pix0_unrotated = {pix0_unrotated}")
    
    # Step 3: Create rotation matrices
    print(f"\nSTEP 3: ROTATION MATRICES:")
    
    # X rotation matrix
    cos_x = math.cos(rotx_rad)
    sin_x = math.sin(rotx_rad)
    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, cos_x, -sin_x],
        [0.0, sin_x, cos_x]
    ])
    print(f"  Rx (rotx={rotx_deg}°):")
    for i in range(3):
        print(f"    [{Rx[i,0]:12.8f}, {Rx[i,1]:12.8f}, {Rx[i,2]:12.8f}]")
    
    # Y rotation matrix
    cos_y = math.cos(roty_rad)
    sin_y = math.sin(roty_rad)
    Ry = np.array([
        [cos_y, 0.0, sin_y],
        [0.0, 1.0, 0.0],
        [-sin_y, 0.0, cos_y]
    ])
    print(f"  Ry (roty={roty_deg}°):")
    for i in range(3):
        print(f"    [{Ry[i,0]:12.8f}, {Ry[i,1]:12.8f}, {Ry[i,2]:12.8f}]")
    
    # Z rotation matrix  
    cos_z = math.cos(rotz_rad)
    sin_z = math.sin(rotz_rad)
    Rz = np.array([
        [cos_z, -sin_z, 0.0],
        [sin_z, cos_z, 0.0],
        [0.0, 0.0, 1.0]
    ])
    print(f"  Rz (rotz={rotz_deg}°):")
    for i in range(3):
        print(f"    [{Rz[i,0]:12.8f}, {Rz[i,1]:12.8f}, {Rz[i,2]:12.8f}]")
    
    # Two-theta rotation matrix (around Y-axis for MOSFLM)
    cos_tt = math.cos(twotheta_rad)
    sin_tt = math.sin(twotheta_rad)
    R_twotheta = np.array([
        [cos_tt, 0.0, sin_tt],
        [0.0, 1.0, 0.0],
        [-sin_tt, 0.0, cos_tt]
    ])
    print(f"  R_twotheta (twotheta={twotheta_deg}° around Y-axis):")
    for i in range(3):
        print(f"    [{R_twotheta[i,0]:12.8f}, {R_twotheta[i,1]:12.8f}, {R_twotheta[i,2]:12.8f}]")
    
    # Step 4: Combined rotation matrix
    print(f"\nSTEP 4: COMBINED ROTATION MATRIX:")
    print(f"  Order: R_twotheta @ Rz @ Ry @ Rx")
    
    # Apply rotations in order: rotx -> roty -> rotz -> twotheta
    R1 = Rx
    R2 = Ry @ R1
    R3 = Rz @ R2  
    R_combined = R_twotheta @ R3
    
    print(f"  R_combined:")
    for i in range(3):
        print(f"    [{R_combined[i,0]:12.8f}, {R_combined[i,1]:12.8f}, {R_combined[i,2]:12.8f}]")
    
    # Verify orthonormality
    det_R = np.linalg.det(R_combined)
    print(f"  Determinant = {det_R:.12f} (should be 1.0)")
    
    # Step 5: Apply rotation to pix0
    print(f"\nSTEP 5: APPLY ROTATION TO PIX0:")
    pix0_rotated = R_combined @ pix0_unrotated
    print(f"  pix0_rotated = {pix0_rotated}")
    
    # Also calculate rotated basis vectors for verification
    fdet_rotated = R_combined @ fdet_init
    sdet_rotated = R_combined @ sdet_init  
    odet_rotated = R_combined @ odet_init
    
    print(f"\nROTATED BASIS VECTORS:")
    print(f"  fdet_rotated = {fdet_rotated}")
    print(f"  sdet_rotated = {sdet_rotated}")
    print(f"  odet_rotated = {odet_rotated}")
    
    # Verify orthonormality of basis vectors
    print(f"\nORTHONORMALITY CHECK:")
    fdet_norm = np.linalg.norm(fdet_rotated)
    sdet_norm = np.linalg.norm(sdet_rotated)
    odet_norm = np.linalg.norm(odet_rotated)
    
    print(f"  ||fdet|| = {fdet_norm:.12f} (should be 1.0)")
    print(f"  ||sdet|| = {sdet_norm:.12f} (should be 1.0)")
    print(f"  ||odet|| = {odet_norm:.12f} (should be 1.0)")
    
    fdet_dot_sdet = np.dot(fdet_rotated, sdet_rotated)
    fdet_dot_odet = np.dot(fdet_rotated, odet_rotated)
    sdet_dot_odet = np.dot(sdet_rotated, odet_rotated)
    
    print(f"  fdet·sdet = {fdet_dot_sdet:.12e} (should be 0.0)")
    print(f"  fdet·odet = {fdet_dot_odet:.12e} (should be 0.0)")
    print(f"  sdet·odet = {sdet_dot_odet:.12e} (should be 0.0)")
    
    return pix0_rotated, fdet_rotated, sdet_rotated, odet_rotated


def compare_with_implementations():
    """Compare manual calculation with PyTorch Detector class."""
    print(f"\n{'='*80}")
    print("COMPARISON WITH IMPLEMENTATIONS")
    print(f"{'='*80}")
    
    # Manual calculation
    manual_pix0, manual_fdet, manual_sdet, manual_odet = manual_pix0_calculation()
    
    # PyTorch Detector class
    print(f"\nPYTORCH DETECTOR CLASS:")
    config = DetectorConfig(
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
    
    detector = Detector(config)
    pytorch_pix0 = detector.pix0_vector.numpy()
    pytorch_fdet = detector.fdet_vec.numpy()
    pytorch_sdet = detector.sdet_vec.numpy()
    pytorch_odet = detector.odet_vec.numpy()
    
    print(f"  pix0_vector = {pytorch_pix0}")
    print(f"  fdet_vec = {pytorch_fdet}")
    print(f"  sdet_vec = {pytorch_sdet}")
    print(f"  odet_vec = {pytorch_odet}")
    
    # Compare results
    print(f"\nCOMPARISON ANALYSIS:")
    
    pix0_diff = pytorch_pix0 - manual_pix0
    fdet_diff = pytorch_fdet - manual_fdet
    sdet_diff = pytorch_sdet - manual_sdet
    odet_diff = pytorch_odet - manual_odet
    
    pix0_max_diff = np.max(np.abs(pix0_diff))
    fdet_max_diff = np.max(np.abs(fdet_diff))
    sdet_max_diff = np.max(np.abs(sdet_diff))
    odet_max_diff = np.max(np.abs(odet_diff))
    
    tolerance = 1e-12
    
    print(f"  pix0 difference: {pix0_diff} (max: {pix0_max_diff:.2e})")
    print(f"  fdet difference: {fdet_diff} (max: {fdet_max_diff:.2e})")
    print(f"  sdet difference: {sdet_diff} (max: {sdet_max_diff:.2e})")
    print(f"  odet difference: {odet_diff} (max: {odet_max_diff:.2e})")
    
    all_equal = (pix0_max_diff < tolerance and fdet_max_diff < tolerance and 
                 sdet_max_diff < tolerance and odet_max_diff < tolerance)
    
    if all_equal:
        print(f"✅ Manual and PyTorch calculations MATCH (within {tolerance})")
    else:
        print(f"❌ Manual and PyTorch calculations DIFFER")
        
        if pix0_max_diff >= tolerance:
            print(f"   • pix0_vector differs by {pix0_max_diff:.2e}")
        if fdet_max_diff >= tolerance:
            print(f"   • fdet_vec differs by {fdet_max_diff:.2e}")
        if sdet_max_diff >= tolerance:
            print(f"   • sdet_vec differs by {sdet_max_diff:.2e}")
        if odet_max_diff >= tolerance:
            print(f"   • odet_vec differs by {odet_max_diff:.2e}")
    
    # Known C values from problem statement
    print(f"\nCOMPARISON WITH KNOWN C VALUES:")
    c_pix0_expected = np.array([0.09523, 0.05882, -0.05170])  # From problem statement
    
    c_manual_diff = manual_pix0 - c_pix0_expected
    c_pytorch_diff = pytorch_pix0 - c_pix0_expected
    
    c_manual_max_diff = np.max(np.abs(c_manual_diff))
    c_pytorch_max_diff = np.max(np.abs(c_pytorch_diff))
    
    print(f"  Expected C pix0: {c_pix0_expected}")
    print(f"  Manual pix0:     {manual_pix0}")
    print(f"  PyTorch pix0:    {pytorch_pix0}")
    print(f"  Manual - C:      {c_manual_diff} (max: {c_manual_max_diff:.2e})")
    print(f"  PyTorch - C:     {c_pytorch_diff} (max: {c_pytorch_max_diff:.2e})")
    
    if c_manual_max_diff < 1e-3:
        print(f"✅ Manual calculation MATCHES expected C values (within 1e-3)")
    else:
        print(f"❌ Manual calculation DIFFERS from expected C values")
    
    if c_pytorch_max_diff < 1e-3:
        print(f"✅ PyTorch calculation MATCHES expected C values (within 1e-3)")
    else:
        print(f"❌ PyTorch calculation DIFFERS from expected C values")
    
    return {
        'manual': {'pix0': manual_pix0, 'fdet': manual_fdet, 'sdet': manual_sdet, 'odet': manual_odet},
        'pytorch': {'pix0': pytorch_pix0, 'fdet': pytorch_fdet, 'sdet': pytorch_sdet, 'odet': pytorch_odet},
        'c_expected': {'pix0': c_pix0_expected},
        'differences': {
            'manual_pytorch_max': max(pix0_max_diff, fdet_max_diff, sdet_max_diff, odet_max_diff),
            'manual_c_max': c_manual_max_diff,
            'pytorch_c_max': c_pytorch_max_diff
        }
    }


def investigate_rotation_order():
    """Investigate different rotation orders to see if that's the issue."""
    print(f"\n{'='*80}")
    print("ROTATION ORDER INVESTIGATION")
    print(f"{'='*80}")
    
    # Test different rotation orders
    rotx_rad = math.radians(5.0)
    roty_rad = math.radians(3.0)
    rotz_rad = math.radians(2.0)
    twotheta_rad = math.radians(20.0)
    
    # Individual matrices
    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, math.cos(rotx_rad), -math.sin(rotx_rad)],
        [0.0, math.sin(rotx_rad), math.cos(rotx_rad)]
    ])
    
    Ry = np.array([
        [math.cos(roty_rad), 0.0, math.sin(roty_rad)],
        [0.0, 1.0, 0.0],
        [-math.sin(roty_rad), 0.0, math.cos(roty_rad)]
    ])
    
    Rz = np.array([
        [math.cos(rotz_rad), -math.sin(rotz_rad), 0.0],
        [math.sin(rotz_rad), math.cos(rotz_rad), 0.0],
        [0.0, 0.0, 1.0]
    ])
    
    R_twotheta = np.array([
        [math.cos(twotheta_rad), 0.0, math.sin(twotheta_rad)],
        [0.0, 1.0, 0.0],
        [-math.sin(twotheta_rad), 0.0, math.cos(twotheta_rad)]
    ])
    
    # Test different orders
    orders = [
        ("Rx·Ry·Rz·Rtt", R_twotheta @ Rz @ Ry @ Rx),
        ("Rtt·Rz·Ry·Rx", R_twotheta @ Rz @ Ry @ Rx),  # Same as above
        ("Rz·Ry·Rx·Rtt", Rz @ Ry @ Rx @ R_twotheta),
        ("Rx·Ry·Rz", Rz @ Ry @ Rx),  # No twotheta
        ("XYZ intrinsic", Rz @ Ry @ Rx),
        ("ZYX extrinsic", Rx @ Ry @ Rz),
    ]
    
    pix0_unrotated = np.array([0.00512, 0.00512, 0.1])  # From manual calculation
    
    for name, R in orders:
        pix0_rotated = R @ pix0_unrotated
        print(f"  {name:<15}: pix0 = [{pix0_rotated[0]:8.5f}, {pix0_rotated[1]:8.5f}, {pix0_rotated[2]:8.5f}]")
    
    print(f"  Expected C     : pix0 = [0.09523, 0.05882, -0.05170]")


def main():
    """Main verification function."""
    results = compare_with_implementations()
    investigate_rotation_order()
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    if results['differences']['manual_pytorch_max'] < 1e-12:
        print("✅ Manual and PyTorch implementations are mathematically identical")
    else:
        print("❌ Manual and PyTorch implementations differ")
    
    if results['differences']['manual_c_max'] < 1e-3:
        print("✅ Manual implementation matches expected C values")
    else:
        print("❌ Manual implementation differs from expected C values")
        print("   This suggests the issue is in the mathematical formulation")
    
    if results['differences']['pytorch_c_max'] < 1e-3:
        print("✅ PyTorch implementation matches expected C values")
    else:
        print("❌ PyTorch implementation differs from expected C values")
        print("   This confirms the correlation issue")
    
    print(f"\n🔍 RECOMMENDED NEXT STEPS:")
    print(f"   1. Run enhanced C trace to get actual C intermediate values")
    print(f"   2. Compare C trace with manual calculation step by step")
    print(f"   3. Focus on rotation matrix order and twotheta axis direction")
    print(f"   4. Check if C uses different pivot mode logic")


if __name__ == "__main__":
    main()