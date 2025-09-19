#!/usr/bin/env python3
"""
Detailed analysis of PyTorch beam center calculation issues.
"""

import os
import sys
import torch

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path for imports
sys.path.insert(0, '/Users/ollie/Documents/nanoBragg/src')

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig

def analyze_beam_center_issue():
    """Analyze the beam center calculation step by step."""
    
    print("=" * 60)
    print("PyTorch Beam Center Detailed Analysis")
    print("=" * 60)
    
    config = DetectorConfig(
        distance_mm=100.0,  # mm
        spixels=1024,
        fpixels=1024,
        pixel_size_mm=0.1,  # mm
        beam_center_s=51.2,  # mm
        beam_center_f=51.2,  # mm
    )
    
    detector = Detector(config)
    
    print("Step 1: Configuration input")
    print(f"  beam_center_s: {config.beam_center_s} mm")
    print(f"  beam_center_f: {config.beam_center_f} mm")
    print(f"  pixel_size_mm: {config.pixel_size_mm} mm")
    print()
    
    print("Step 2: Detector internal values")
    print(f"  detector.beam_center_s: {detector.beam_center_s} (should be in pixels)")
    print(f"  detector.beam_center_f: {detector.beam_center_f} (should be in pixels)")
    print(f"  detector.pixel_size: {detector.pixel_size} m")
    print()
    
    # Expected values
    expected_beam_center_pixels = 51.2 / 0.1  # = 512 pixels
    print("Step 3: Expected values")
    print(f"  Expected beam center in pixels: {expected_beam_center_pixels}")
    print()
    
    print("Step 4: pix0_vector calculation")
    print(f"  detector.pix0_vector: {detector.pix0_vector}")
    
    # Manual calculation of what Fclose/Sclose should be
    # From C code: Fbeam = Ybeam/1000 + 0.5*pixel_size
    # where Ybeam = 51.2mm = 0.0512 m, pixel_size = 0.0001 m
    expected_fbeam = 0.0512 + 0.5 * 0.0001  # = 0.05125 m
    expected_sbeam = 0.0512 + 0.5 * 0.0001  # = 0.05125 m
    
    print()
    print("Step 5: Expected C calculation")
    print(f"  Expected Fbeam (C): {expected_fbeam:.6f} m")
    print(f"  Expected Sbeam (C): {expected_sbeam:.6f} m")
    
    # PyTorch calculation (from detector code)
    # Fbeam = (self.beam_center_s + 0.5) * self.pixel_size
    pytorch_fbeam = (detector.beam_center_s + 0.5) * detector.pixel_size
    pytorch_sbeam = (detector.beam_center_f + 0.5) * detector.pixel_size
    
    print()
    print("Step 6: PyTorch calculation")
    print(f"  PyTorch Fbeam: ({detector.beam_center_s} + 0.5) * {detector.pixel_size} = {pytorch_fbeam}")
    print(f"  PyTorch Sbeam: ({detector.beam_center_f} + 0.5) * {detector.pixel_size} = {pytorch_sbeam}")
    
    print()
    print("Step 7: Issue identification")
    if abs(detector.beam_center_s - expected_beam_center_pixels) < 0.001:
        print("  ✅ beam_center_s is correctly converted to pixels")
    else:
        print(f"  ❌ beam_center_s conversion issue: {detector.beam_center_s} != {expected_beam_center_pixels}")
        
    # Check if the problem is in the pix0_vector computation vs pixel coordinate computation
    print()
    print("Step 8: Pixel coordinate calculation")
    pixel_coords = detector.get_pixel_coords()
    center_pixel = pixel_coords[512, 512]
    print(f"  Pixel (512,512) coordinates: {center_pixel}")
    
    # The center pixel should be at beam center position
    # Let's see what the calculation should be
    # pixel_coords = pix0_vector + s_index * pixel_size * sdet_vec + f_index * pixel_size * fdet_vec
    s_index = 512
    f_index = 512
    
    expected_center = (detector.pix0_vector + 
                      s_index * detector.pixel_size * detector.sdet_vec +
                      f_index * detector.pixel_size * detector.fdet_vec)
    
    print(f"  Expected center calculation:")
    print(f"    pix0_vector: {detector.pix0_vector}")
    print(f"    + {s_index} * {detector.pixel_size} * sdet_vec: {s_index * detector.pixel_size * detector.sdet_vec}")
    print(f"    + {f_index} * {detector.pixel_size} * fdet_vec: {f_index * detector.pixel_size * detector.fdet_vec}")
    print(f"    = {expected_center}")
    
    print()
    print("Step 9: Diagnosis")
    # The issue might be that pix0_vector represents pixel (0,0), 
    # but we want the coordinates relative to beam center
    beam_center_coords = expected_center
    distance_from_detector = torch.norm(beam_center_coords).item()
    print(f"  Distance from origin to beam center: {distance_from_detector:.6f} m")
    print(f"  Expected beam center distance: {(0.1**2 + 0.05125**2 + 0.05125**2)**0.5:.6f} m")

if __name__ == "__main__":
    analyze_beam_center_issue()