#!/usr/bin/env python3
"""
Enhanced tracing to debug pix0_vector calculation.

This script adds detailed logging to identify exactly where the pix0_vector calculation diverges.
"""

import os
import sys
import torch
import numpy as np

# Set environment for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector

def debug_pix0_calculation():
    """Deep debug of pix0_vector calculation."""
    
    print("=== PIX0_VECTOR CALCULATION DEBUGGING ===")
    
    # Create configuration for tilted detector case (matching C trace)
    config = DetectorConfig(
        # Detector parameters (tilted case)
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=61.2,
        beam_center_f=61.2,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0, 
        detector_rotz_deg=2.0,
        detector_twotheta_deg=15.0,  # From C trace: -twotheta 15
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
    )
    
    # Expected C values from trace (cubic_tilted_detector)
    c_pix0_vector = torch.tensor([0.112087366299472, 0.0653100408232811, -0.0556023303792543])
    
    # Debug the detector configuration
    print("\nStep 1: Configuration verification")
    print(f"  detector_distance_mm: {config.distance_mm}")
    print(f"  detector_pixel_size_mm: {config.pixel_size_mm}")
    print(f"  detector_beam_center_s_mm: {config.beam_center_s}")
    print(f"  detector_beam_center_f_mm: {config.beam_center_f}")
    print(f"  detector_rotx_deg: {config.detector_rotx_deg}")
    print(f"  detector_roty_deg: {config.detector_roty_deg}")
    print(f"  detector_rotz_deg: {config.detector_rotz_deg}")
    print(f"  detector_twotheta_deg: {config.detector_twotheta_deg}")
    
    # Create detector and get initial values
    detector = Detector(config)
    
    print("\nStep 2: Internal detector values")
    print(f"  distance (meters): {detector.distance}")
    print(f"  pixel_size (meters): {detector.pixel_size}")
    print(f"  beam_center_s (pixels): {detector.beam_center_s}")
    print(f"  beam_center_f (pixels): {detector.beam_center_f}")
    
    # Debug basis vectors
    print("\nStep 3: Basis vectors")
    print(f"  fdet_vec: {detector.fdet_vec}")
    print(f"  sdet_vec: {detector.sdet_vec}")
    print(f"  odet_vec: {detector.odet_vec}")
    
    # Expected C basis vectors after rotations (from cubic_tilted_detector trace)
    c_fdet_final = torch.tensor([0.0311947630447082, -0.096650175316428, 0.994829447880333])
    c_sdet_final = torch.tensor([-0.228539518954453, -0.969636205471835, -0.0870362988312832])  
    c_odet_final = torch.tensor([0.973034724475264, -0.224642766741965, -0.0523359562429438])
    
    print("\nStep 4: Basis vector comparison")
    print(f"  C fdet_vec: {c_fdet_final}")
    print(f"  PyTorch fdet_vec: {detector.fdet_vec}")
    print(f"  Difference: {torch.abs(detector.fdet_vec - c_fdet_final)}")
    print(f"  Max diff: {torch.max(torch.abs(detector.fdet_vec - c_fdet_final))}")
    
    print(f"\n  C sdet_vec: {c_sdet_final}")
    print(f"  PyTorch sdet_vec: {detector.sdet_vec}")
    print(f"  Difference: {torch.abs(detector.sdet_vec - c_sdet_final)}")
    print(f"  Max diff: {torch.max(torch.abs(detector.sdet_vec - c_sdet_final))}")
    
    print(f"\n  C odet_vec: {c_odet_final}")
    print(f"  PyTorch odet_vec: {detector.odet_vec}")
    print(f"  Difference: {torch.abs(detector.odet_vec - c_odet_final)}")
    print(f"  Max diff: {torch.max(torch.abs(detector.odet_vec - c_odet_final))}")
    
    # Calculate pix0_vector step by step (BEAM pivot mode)
    print("\nStep 5: Manual pix0_vector calculation (BEAM pivot)")
    
    # From C trace values:
    c_fbeam = 0.06125  # meters
    c_sbeam = 0.06125  # meters
    c_distance = 0.1   # meters
    c_beam_vector = torch.tensor([1.0, 0.0, 0.0])
    
    print(f"  C values:")
    print(f"    Fbeam: {c_fbeam}")
    print(f"    Sbeam: {c_sbeam}")
    print(f"    distance: {c_distance}")
    print(f"    beam_vector: {c_beam_vector}")
    
    # Manual calculation using C formula: pix0_vector = -Fbeam*fdet_vector - Sbeam*sdet_vector + distance*beam_vector
    manual_pix0 = (
        -c_fbeam * detector.fdet_vec
        - c_sbeam * detector.sdet_vec
        + c_distance * c_beam_vector
    )
    
    print(f"\n  Manual calculation:")
    print(f"    -Fbeam*fdet_vec = {-c_fbeam * detector.fdet_vec}")
    print(f"    -Sbeam*sdet_vec = {-c_sbeam * detector.sdet_vec}")  
    print(f"    +distance*beam_vec = {c_distance * c_beam_vector}")
    print(f"    Sum = {manual_pix0}")
    
    # Compare with detector's calculation
    print(f"\nStep 6: Compare with detector pix0_vector")
    print(f"  Detector pix0_vector: {detector.pix0_vector}")
    print(f"  Manual calculation: {manual_pix0}")
    print(f"  Expected C value: {c_pix0_vector}")
    
    # Differences
    diff_detector_manual = torch.abs(detector.pix0_vector - manual_pix0)
    diff_detector_c = torch.abs(detector.pix0_vector - c_pix0_vector)
    diff_manual_c = torch.abs(manual_pix0 - c_pix0_vector)
    
    print(f"\nStep 7: Differences")
    print(f"  Detector vs Manual: {diff_detector_manual} (max: {torch.max(diff_detector_manual)})")
    print(f"  Detector vs C: {diff_detector_c} (max: {torch.max(diff_detector_c)})")
    print(f"  Manual vs C: {diff_manual_c} (max: {torch.max(diff_manual_c)})")
    
    # Check beam center calculation in detector
    print(f"\nStep 8: Detector beam center calculation debug")
    print(f"  config.beam_center_s_mm: {config.beam_center_s}")
    print(f"  config.beam_center_f_mm: {config.beam_center_f}")
    print(f"  config.pixel_size_mm: {config.pixel_size_mm}")
    
    # Calculate what Fbeam/Sbeam should be in detector
    beam_s_mm = config.beam_center_s  # 61.2
    beam_f_mm = config.beam_center_f  # 61.2
    pixel_size_mm = config.pixel_size_mm  # 0.1
    
    # MOSFLM convention: Add 0.5 pixel offset, but check axis mapping
    # From C trace: Fbeam comes from Ybeam (beam_center_s), Sbeam from Xbeam (beam_center_f)
    beam_s_pixels = beam_s_mm / pixel_size_mm  # 612 pixels
    beam_f_pixels = beam_f_mm / pixel_size_mm  # 612 pixels
    
    # MOSFLM axis mapping + 0.5 pixel offset
    # Fbeam = beam_center_s + 0.5 (axis swap: S→F)
    # Sbeam = beam_center_f + 0.5 (axis swap: F→S)
    detector_fbeam = (beam_s_pixels + 0.5) * (pixel_size_mm / 1000.0)  # to meters: 612.5 * 0.0001 = 0.06125
    detector_sbeam = (beam_f_pixels + 0.5) * (pixel_size_mm / 1000.0)  # to meters: 612.5 * 0.0001 = 0.06125
    
    print(f"\nStep 9: Expected beam center calculation")
    print(f"  beam_s_pixels: {beam_s_pixels}")
    print(f"  beam_f_pixels: {beam_f_pixels}")
    print(f"  Expected Fbeam (S→F): {detector_fbeam} meters")
    print(f"  Expected Sbeam (F→S): {detector_sbeam} meters")
    print(f"  C trace Fbeam: {c_fbeam}")
    print(f"  C trace Sbeam: {c_sbeam}")
    print(f"  Matches: Fbeam={abs(detector_fbeam - c_fbeam) < 1e-10}, Sbeam={abs(detector_sbeam - c_sbeam) < 1e-10}")
    
    # Error summary
    print(f"\n=== ERROR SUMMARY ===")
    max_basis_error = max(
        torch.max(torch.abs(detector.fdet_vec - c_fdet_final)),
        torch.max(torch.abs(detector.sdet_vec - c_sdet_final)), 
        torch.max(torch.abs(detector.odet_vec - c_odet_final))
    )
    max_pix0_error = torch.max(diff_detector_c)
    
    print(f"  Max basis vector error: {max_basis_error}")
    print(f"  Max pix0_vector error: {max_pix0_error}")
    print(f"  Basis vectors match C: {max_basis_error < 1e-9}")
    print(f"  pix0_vector matches C: {max_pix0_error < 1e-9}")
    
    # If basis vectors match but pix0 doesn't, the issue is in the beam center calculation
    if max_basis_error < 1e-9 and max_pix0_error > 1e-9:
        print(f"\n  🔍 ROOT CAUSE: Basis vectors are correct, but pix0_vector calculation has error.")
        print(f"     This suggests the issue is in beam center (Fbeam/Sbeam) calculation")
        print(f"     or the formula application in _calculate_pix0_vector().")
    
    # Check the pivot mode
    print(f"\nStep 10: Pivot mode check")
    print(f"  detector_pivot: {config.detector_pivot}")
    print(f"  Using BEAM pivot (expected): {config.detector_pivot.name == 'BEAM'}")

if __name__ == "__main__":
    debug_pix0_calculation()