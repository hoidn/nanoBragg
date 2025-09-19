#!/usr/bin/env python3
"""
Check what happens at pixel [34, 34] vs [33, 33]
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector

# Configuration
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=64,
    fpixels=64,
    # Default beam centers - should be at center of 64x64 detector
)

print("Configuration:")
print(f"  Detector: {config.spixels}x{config.fpixels} pixels")
print(f"  Default beam_center_s: {config.beam_center_s} mm")
print(f"  Default beam_center_f: {config.beam_center_f} mm")
print(f"  In pixels (without +0.5): {config.beam_center_s / config.pixel_size_mm}")

# Create detector
detector = Detector(config)

# Get pixel coordinates
pixel_coords = detector.get_pixel_coords()

print("\n=== BEAM CENTER ANALYSIS ===")
print(f"Stored beam_center_s (with +0.5): {detector.beam_center_s}")
print(f"Stored beam_center_f (with +0.5): {detector.beam_center_f}")

print("\n=== PIXEL POSITIONS ===")
print("Using pixel corners (0, 1, 2, ...)")

# Check positions near the center
positions_to_check = [(32, 32), (32, 33), (33, 32), (33, 33), (34, 34)]
for s, f in positions_to_check:
    if s < config.spixels and f < config.fpixels:
        pos = pixel_coords[s, f]
        # Calculate where this pixel is in detector coordinates
        # Relative to pix0_vector
        rel_s = s * detector.pixel_size
        rel_f = f * detector.pixel_size
        print(f"Pixel [{s:2d},{f:2d}]: detector coords (s={rel_s*1000:4.1f}mm, f={rel_f*1000:4.1f}mm), pos={pos.numpy()}")

print("\n=== UNDERSTANDING THE SHIFT ===")
print("The C code has maximum at pixel [34, 34]")
print("We have maximum at pixel [33, 33]")
print()
print("For a 64x64 detector:")
print("  Center should be at pixel 32 (if 0-indexed, goes from 0 to 63)")
print("  But with MOSFLM +0.5 pixel offset, beam center becomes 32.5")
print("  C code might be rounding this differently")
print()
print("Another possibility:")
print("  The C code's pixel [34, 34] is actually our pixel [33, 33]")
print("  Could be a 1-based vs 0-based indexing issue")