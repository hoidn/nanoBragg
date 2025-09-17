#!/usr/bin/env python3
"""
Simple diagnostic script to check detector geometry implementation.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot

# Test simple identity configuration
config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=51.2,
    beam_center_f=51.2,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM,
    detector_rotx_deg=0.0,
    detector_roty_deg=0.0,
    detector_rotz_deg=0.0,
    detector_twotheta_deg=0.0,
)

detector = Detector(config=config)

print("DETECTOR DIAGNOSTIC")
print("=" * 50)
print(f"Is default config: {detector._is_default_config()}")
print()
print("=" * 50)
print(f"Distance: {detector.distance} meters")
print(f"Pixel size: {detector.pixel_size} meters")
print(f"Beam center (pixels): s={detector.beam_center_s.item():.1f}, f={detector.beam_center_f.item():.1f}")
print()

print("BASIS VECTORS:")
print(f"  fdet_vec (fast): {detector.fdet_vec}")
print(f"  sdet_vec (slow): {detector.sdet_vec}")
print(f"  odet_vec (normal): {detector.odet_vec}")
print()

print(f"PIX0 VECTOR: {detector.pix0_vector}")
print()

# Test a few specific pixels
test_pixels = [
    (0, 0),      # Corner
    (512, 512),  # Center
    (51, 51),    # Near beam center (if beam center is ~512)
]

positions = detector.get_pixel_coords()
print("PIXEL POSITIONS (first few):")
for s, f in test_pixels:
    if s < positions.shape[0] and f < positions.shape[1]:
        pos = positions[s, f]
        print(f"  Pixel ({s:3d}, {f:3d}): [{pos[0]:8.5f}, {pos[1]:8.5f}, {pos[2]:8.5f}] m")
print()

# Expected for identity configuration:
# - fdet_vec should be [0, 0, 1] 
# - sdet_vec should be [0, -1, 0]
# - odet_vec should be [1, 0, 0]
# - Pixel (0,0) should be at pix0_vector
# - Pixel (512,512) should be roughly at [distance, 0, 0] for beam center at (512, 512)

print("EXPECTED vs ACTUAL:")
print("For MOSFLM identity configuration:")
print("  Expected fdet_vec: [0, 0, 1]")
print("  Expected sdet_vec: [0, -1, 0]") 
print("  Expected odet_vec: [1, 0, 0]")
print()

# Check beam center calculation
beam_s_pixels = config.beam_center_s / config.pixel_size_mm
beam_f_pixels = config.beam_center_f / config.pixel_size_mm  
print(f"Beam center in pixels: s={beam_s_pixels:.1f}, f={beam_f_pixels:.1f}")

# For MOSFLM, we add 0.5 to beam center
expected_beam_s = beam_s_pixels + 0.5  # = 512.5
expected_beam_f = beam_f_pixels + 0.5  # = 512.5
print(f"Expected beam center (MOSFLM): s={expected_beam_s:.1f}, f={expected_beam_f:.1f}")
print()

# Expected pix0 for identity case:
# pix0 = -Fbeam * fdet_vec - Sbeam * sdet_vec + distance * odet_vec
# With MOSFLM convention: Fbeam = Sbeam = (512.5 * 0.1mm) = 0.05125 m
# So: pix0 = -0.05125 * [0,0,1] - 0.05125 * [0,-1,0] + 0.1 * [1,0,0]
#          = [0,0,-0.05125] + [0,0.05125,0] + [0.1,0,0]
#          = [0.1, 0.05125, -0.05125]

Fbeam = (beam_f_pixels + 0.5) * config.pixel_size_mm / 1000.0  # to meters
Sbeam = (beam_s_pixels + 0.5) * config.pixel_size_mm / 1000.0  # to meters
expected_pix0 = torch.tensor([0.1, 0.05125, -0.05125])
print(f"Expected pix0: {expected_pix0}")
print(f"Actual pix0:   {detector.pix0_vector}")
print(f"Difference:    {detector.pix0_vector - expected_pix0}")