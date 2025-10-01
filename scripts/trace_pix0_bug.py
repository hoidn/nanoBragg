#!/usr/bin/env python3
"""Trace the pix0_vector bug by adding debug to detector initialization."""

import os
import sys
import torch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Monkey patch the detector's _calculate_pix0_vector to add debug
from nanobrag_torch.models import detector as detector_module
from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot

original_calculate_pix0_vector = detector_module.Detector._calculate_pix0_vector

def debug_calculate_pix0_vector(self):
    """Wrapped version with debug output."""
    print("\n=== DEBUG _calculate_pix0_vector ===")
    print(f"self.distance = {self.distance} meters")
    print(f"self.pixel_size = {self.pixel_size} meters")
    print(f"self.beam_center_s = {self.beam_center_s}")
    print(f"self.beam_center_f = {self.beam_center_f}")
    
    # Call original
    original_calculate_pix0_vector(self)
    
    print(f"\nAfter calculation:")
    print(f"self.pix0_vector = {self.pix0_vector}")
    print(f"self.pix0_vector magnitude = {torch.norm(self.pix0_vector).item()}")
    print("=== END DEBUG ===\n")

# Apply monkey patch
detector_module.Detector._calculate_pix0_vector = debug_calculate_pix0_vector

# Now create detector with our problematic config
config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=61.2,
    beam_center_f=61.2,
    detector_convention=DetectorConvention.MOSFLM,
    detector_rotx_deg=5.0,
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=15.0,
    detector_pivot=DetectorPivot.SAMPLE,
)

print("Creating detector with tilted configuration...")
detector = detector_module.Detector(config=config, device=torch.device("cpu"), dtype=torch.float64)

print(f"\nFinal detector state:")
print(f"  pix0_vector: {detector.pix0_vector}")
print(f"  pix0_vector / 1e10: {detector.pix0_vector / 1e10}")
print(f"  get_pixel_coords()[0,0]: {detector.get_pixel_coords()[0,0]}")