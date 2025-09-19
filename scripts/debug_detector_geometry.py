#!/usr/bin/env python3
"""
Isolated detector geometry debugging script for fast feedback loop.

This script focuses solely on the Detector class pixel coordinate calculation
to debug the geometry issues identified in the parallel trace analysis.

Target: Pixel (372, 289) should have position: [0.1, -0.011525, 0.003225] meters
"""

import os
import torch
import numpy as np
from pathlib import Path

# Set environment variable for PyTorch/MKL compatibility
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.config import DetectorConfig
from nanobrag_torch.models.detector import Detector

def debug_detector_geometry():
    """Debug detector geometry calculation for triclinic case."""
    
    print("=" * 80)
    print("DETECTOR GEOMETRY DEBUG SESSION")
    print("=" * 80)
    
    # Use exact triclinic detector configuration
    # C-code trace shows "pivoting detector around direct beam spot" = BEAM pivot
    from nanobrag_torch.config import DetectorPivot
    detector_config = DetectorConfig(
        distance_mm=100.0,          # From params.json
        pixel_size_mm=0.1,          # From params.json  
        spixels=512,                # From params.json (detpixels)
        fpixels=512,                # From params.json (detpixels) 
        beam_center_s=25.6,         # Center of 512x512 detector: 256 pixels * 0.1mm = 25.6mm
        beam_center_f=25.6,         # Center of 512x512 detector: 256 pixels * 0.1mm = 25.6mm
        detector_pivot=DetectorPivot.BEAM  # Match C-code: "pivoting detector around direct beam spot"
    )
    
    print(f"Detector Configuration:")
    print(f"  distance_mm: {detector_config.distance_mm}")
    print(f"  pixel_size_mm: {detector_config.pixel_size_mm}")
    print(f"  image_shape: ({detector_config.spixels}, {detector_config.fpixels})")
    print(f"  beam_center: ({detector_config.beam_center_s}, {detector_config.beam_center_f}) mm")
    
    # Create detector
    detector = Detector(detector_config)
    
    print(f"\nDetector Basis Vectors:")
    print(f"  fdet_vec: {detector.fdet_vec}")
    print(f"  sdet_vec: {detector.sdet_vec}") 
    print(f"  odet_vec: {detector.odet_vec}")
    
    print(f"\nBeam Center Calculations:")
    print(f"  beam_center_s: {detector.beam_center_s} pixels")
    print(f"  beam_center_f: {detector.beam_center_f} pixels")
    
    # Get the pix0_vector (already calculated in __init__)
    print(f"\nPix0 Vector (reference point):")
    print(f"  pix0_vector: {detector.pix0_vector.detach().numpy()}")
    
    # Target pixel coordinates - this is the smoking gun test
    target_s = 372  # slow coordinate
    target_f = 289  # fast coordinate
    
    print(f"\nTarget Pixel Analysis:")
    print(f"  Target pixel (s,f): ({target_s}, {target_f})")
    
    # Get pixel coordinates for our target pixel
    pixel_coords = detector.get_pixel_coords()
    target_coord = pixel_coords[target_s, target_f]  # Shape: (3,)
    
    print(f"  Calculated position: {target_coord.detach().numpy()}")
    
    # Expected from C-trace (ground truth)
    expected_coord = torch.tensor([0.1, -0.011525, 0.003225])
    print(f"  Expected position:   {expected_coord.detach().numpy()}")
    
    # Calculate error
    error = torch.abs(target_coord - expected_coord)
    print(f"  Absolute error:      {error.detach().numpy()}")
    print(f"  Max error:           {torch.max(error).item():.6f}")
    
    # Check if within tolerance
    tolerance = 5e-5  # 50 micrometer tolerance (accounting for floating point differences)
    within_tolerance = torch.all(error < tolerance)
    print(f"  Within tolerance ({tolerance:.0e}): {within_tolerance}")
    
    print("\n" + "=" * 80)
    if within_tolerance:
        print("✅ SUCCESS: Detector geometry matches C-code!")
    else:
        print("❌ FAILURE: Detector geometry does NOT match C-code!")
        print("    This confirms the detector geometry calculation is broken.")
    print("=" * 80)
    
    return within_tolerance, error

if __name__ == "__main__":
    success, error = debug_detector_geometry()
    if not success:
        print(f"\nNext step: Debug _calculate_pix0_vector() and get_pixel_coords()")
        print(f"Maximum error: {torch.max(error).item():.6f} meters")