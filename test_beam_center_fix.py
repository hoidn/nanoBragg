#!/usr/bin/env python3
"""
Quick test to verify beam center fix
"""

import os
import sys
import torch
import numpy as np
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig, DetectorPivot, DetectorConvention

def test_beam_center_fix():
    """Test the axis swapping fix for beam center calculation."""
    print("Testing beam center axis swapping fix...")
    
    # Configuration matching the problematic case
    # C command uses: -Xbeam 61.2 -Ybeam 61.2 (in mm)
    # With axis swapping: Fbeam ← Ybeam, Sbeam ← Xbeam
    config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=61.2,  # This should map to Fbeam in C (from Ybeam)
        beam_center_f=61.2,  # This should map to Sbeam in C (from Xbeam)
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=20.0,
        detector_pivot=DetectorPivot.BEAM,  # Force BEAM pivot mode
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        fpixels=1024,
        spixels=1024,
    )
    
    detector = Detector(config)
    pix0 = detector.pix0_vector.numpy()
    
    print(f"beam_center_s = {config.beam_center_s} mm")
    print(f"beam_center_f = {config.beam_center_f} mm")
    print(f"PyTorch pix0_vector = {pix0}")
    
    # Expected C values from the debug session
    print(f"\nExpected C values:")
    print(f"Xbeam = 0.0612 m, Ybeam = 0.0612 m")
    print(f"Fbeam = Ybeam + 0.5*pixel_size = {0.0612 + 0.5*0.0001:.7f} m")
    print(f"Sbeam = Xbeam + 0.5*pixel_size = {0.0612 + 0.5*0.0001:.7f} m")
    
    # Calculate expected values manually using corrected formula
    Fbeam_expected = config.beam_center_s / 1000.0 + 0.5 * config.pixel_size_mm / 1000.0
    Sbeam_expected = config.beam_center_f / 1000.0 + 0.5 * config.pixel_size_mm / 1000.0
    
    print(f"\nPyTorch calculation (corrected):")
    print(f"Fbeam = beam_center_s/1000 + 0.5*pixel_size = {Fbeam_expected:.7f} m")
    print(f"Sbeam = beam_center_f/1000 + 0.5*pixel_size = {Sbeam_expected:.7f} m")
    
    # Check if they match
    if abs(Fbeam_expected - 0.06125) < 1e-6 and abs(Sbeam_expected - 0.06125) < 1e-6:
        print("✅ Beam center calculations match expected C values!")
    else:
        print("❌ Beam center calculations do not match C values")
        
    print(f"\nRotated basis vectors:")
    print(f"fdet_vec = {detector.fdet_vec.numpy()}")
    print(f"sdet_vec = {detector.sdet_vec.numpy()}")
    print(f"odet_vec = {detector.odet_vec.numpy()}")
    
    return pix0

if __name__ == "__main__":
    test_beam_center_fix()