#!/usr/bin/env python3
"""
Detailed step-by-step trace of detector geometry calculations to match C code output.
"""

import os
import sys
from pathlib import Path
import torch
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import (
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.utils.geometry import rotate_axis

def trace_detector_geometry():
    """Trace detector geometry calculation step by step."""
    print("DETAILED DETECTOR GEOMETRY TRACE")
    print("=" * 50)
    
    # Configuration matching our failing test case
    config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_rotx_deg=0.0,  # Start with twotheta only
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=15.0,
        detector_pivot=DetectorPivot.BEAM,
        detector_convention=DetectorConvention.MOSFLM,
    )
    
    print(f"Configuration:")
    print(f"  Distance: {config.distance_mm} mm")
    print(f"  Beam center: ({config.beam_center_s}, {config.beam_center_f}) mm")
    print(f"  Rotations: rotx={config.detector_rotx_deg}°, roty={config.detector_roty_deg}°, rotz={config.detector_rotz_deg}°")
    print(f"  Two-theta: {config.detector_twotheta_deg}°")
    print(f"  Pivot: {config.detector_pivot}")
    
    # Manual calculation step by step to match C code
    print(f"\n=== MANUAL STEP-BY-STEP CALCULATION ===")
    
    # Constants
    pixel_size = config.pixel_size_mm / 1000.0  # Convert mm to meters
    distance = config.distance_mm / 1000.0      # Convert mm to meters
    beam_center_s_m = config.beam_center_s / 1000.0  # Convert mm to meters
    beam_center_f_m = config.beam_center_f / 1000.0  # Convert mm to meters
    
    print(f"Pixel size: {pixel_size} m")
    print(f"Distance: {distance} m")
    print(f"Beam center: ({beam_center_s_m}, {beam_center_f_m}) m")
    
    # C code initial vectors (from nanoBragg.c)
    # double fdet_vector[4]  = {0,0,0,1};    -> [0, 0, 1]
    # double sdet_vector[4]  = {0,0,-1,0};   -> [0, -1, 0]  
    # double odet_vector[4]  = {0,1,0,0};    -> [1, 0, 0]
    print(f"\n--- Initial basis vectors (C code defaults) ---")
    fdet_initial = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    sdet_initial = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
    odet_initial = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    
    print(f"fdet_vector (fast axis): {fdet_initial.numpy()}")
    print(f"sdet_vector (slow axis): {sdet_initial.numpy()}")
    print(f"odet_vector (normal):    {odet_initial.numpy()}")
    
    # Pix0 calculation (C code logic)
    # pix0_vector[1] = -Sbeam*sdet_vector[1] - Fbeam*fdet_vector[1] + distance*odet_vector[1];
    # pix0_vector[2] = -Sbeam*sdet_vector[2] - Fbeam*fdet_vector[2] + distance*odet_vector[2];
    # pix0_vector[3] = -Sbeam*sdet_vector[3] - Fbeam*fdet_vector[3] + distance*odet_vector[3];
    print(f"\n--- Pix0 calculation ---")
    pix0_initial = (-beam_center_s_m * sdet_initial - 
                   beam_center_f_m * fdet_initial + 
                   distance * odet_initial)
    print(f"pix0_vector (initial): {pix0_initial.numpy()}")
    
    # Convert rotation angles to radians
    detector_rotx = config.detector_rotx_deg * np.pi / 180.0
    detector_roty = config.detector_roty_deg * np.pi / 180.0  
    detector_rotz = config.detector_rotz_deg * np.pi / 180.0
    detector_twotheta = config.detector_twotheta_deg * np.pi / 180.0
    
    print(f"\n--- Rotation angles (radians) ---")
    print(f"detector_rotx: {detector_rotx}")
    print(f"detector_roty: {detector_roty}")
    print(f"detector_rotz: {detector_rotz}")
    print(f"detector_twotheta: {detector_twotheta}")
    
    # Apply XYZ rotations (C code calls rotate function)
    print(f"\n--- Applying XYZ rotations ---")
    # For now, rotx=roty=rotz=0, so vectors unchanged
    fdet_after_xyz = fdet_initial.clone()
    sdet_after_xyz = sdet_initial.clone() 
    odet_after_xyz = odet_initial.clone()
    pix0_after_xyz = pix0_initial.clone()
    
    print(f"fdet after XYZ: {fdet_after_xyz.numpy()}")
    print(f"sdet after XYZ: {sdet_after_xyz.numpy()}")
    print(f"odet after XYZ: {odet_after_xyz.numpy()}")
    print(f"pix0 after XYZ: {pix0_after_xyz.numpy()}")
    
    # Apply twotheta rotation
    print(f"\n--- Applying twotheta rotation ---")
    twotheta_axis = torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64)  # Our current default
    print(f"twotheta_axis: {twotheta_axis.numpy()}")
    
    fdet_final = rotate_axis(fdet_after_xyz, twotheta_axis, torch.tensor(detector_twotheta))
    sdet_final = rotate_axis(sdet_after_xyz, twotheta_axis, torch.tensor(detector_twotheta))
    odet_final = rotate_axis(odet_after_xyz, twotheta_axis, torch.tensor(detector_twotheta))
    pix0_final = rotate_axis(pix0_after_xyz, twotheta_axis, torch.tensor(detector_twotheta))
    
    print(f"fdet final (fast axis): {fdet_final.numpy()}")
    print(f"sdet final (slow axis): {sdet_final.numpy()}")
    print(f"odet final (normal):    {odet_final.numpy()}")
    print(f"pix0 final:             {pix0_final.numpy()}")
    
    # Now compare with what our Detector class produces
    print(f"\n=== COMPARISON WITH DETECTOR CLASS ===")
    detector = Detector(config)
    
    # Get the basis vectors
    fdet_class, sdet_class, odet_class = detector._calculate_basis_vectors()
    pix0_class = detector.pix0_vector
    
    print(f"Detector class results:")
    print(f"fdet (fast axis): {fdet_class.numpy()}")
    print(f"sdet (slow axis): {sdet_class.numpy()}")
    print(f"odet (normal):    {odet_class.numpy()}")
    print(f"pix0:             {pix0_class.numpy()}")
    
    print(f"\n=== DIFFERENCES ===")
    fdet_diff = torch.abs(fdet_final - fdet_class)
    sdet_diff = torch.abs(sdet_final - sdet_class)
    odet_diff = torch.abs(odet_final - odet_class)
    pix0_diff = torch.abs(pix0_final - pix0_class)
    
    print(f"fdet difference: {fdet_diff.numpy()} (max: {torch.max(fdet_diff).item():.2e})")
    print(f"sdet difference: {sdet_diff.numpy()} (max: {torch.max(sdet_diff).item():.2e})")
    print(f"odet difference: {odet_diff.numpy()} (max: {torch.max(odet_diff).item():.2e})")
    print(f"pix0 difference: {pix0_diff.numpy()} (max: {torch.max(pix0_diff).item():.2e})")
    
    # Check if they match
    max_diff = max(torch.max(fdet_diff).item(), torch.max(sdet_diff).item(), 
                   torch.max(odet_diff).item(), torch.max(pix0_diff).item())
    
    if max_diff < 1e-12:
        print(f"\n✅ MATCH: Manual calculation matches Detector class (max diff: {max_diff:.2e})")
    else:
        print(f"\n❌ MISMATCH: Manual calculation differs from Detector class (max diff: {max_diff:.2e})")
        print(f"Need to investigate Detector class implementation!")

if __name__ == "__main__":
    trace_detector_geometry()