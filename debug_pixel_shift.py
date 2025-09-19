#!/usr/bin/env python3
"""
Debug script to understand the 1-pixel diagonal shift issue.
"""

import os
import torch
import numpy as np

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector

# Simple case configuration
detector_config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=64,
    fpixels=64
)

print("Detector Configuration:")
print(f"  spixels: {detector_config.spixels}")
print(f"  fpixels: {detector_config.fpixels}")
print(f"  pixel_size_mm: {detector_config.pixel_size_mm}")
print(f"  beam_center_s: {detector_config.beam_center_s}")
print(f"  beam_center_f: {detector_config.beam_center_f}")

# Create detector
detector = Detector(detector_config)

print("\nDetector Internal State:")
print(f"  beam_center_s (pixels): {detector.beam_center_s}")
print(f"  beam_center_f (pixels): {detector.beam_center_f}")
print(f"  pixel_size (meters): {detector.pixel_size}")
print(f"  distance (meters): {detector.distance}")

# Get pixel coordinates
pixel_coords = detector.get_pixel_coords()
print(f"\nPixel coordinates shape: {pixel_coords.shape}")

# Check a few specific pixel coordinates
print("\nPixel coordinates at key positions:")
print(f"  Pixel [0, 0]: {pixel_coords[0, 0]}")
print(f"  Pixel [1, 1]: {pixel_coords[1, 1]}")
print(f"  Pixel [32, 32]: {pixel_coords[32, 32]}")
print(f"  Pixel [33, 33]: {pixel_coords[33, 33]}")
print(f"  Pixel [34, 34]: {pixel_coords[34, 34] if 34 < pixel_coords.shape[0] else 'Out of bounds'}")

# Check pix0_vector
print(f"\npix0_vector: {detector.pix0_vector}")

# Calculate what pixel [33, 33] position should be
# Using the formula: pixel_coords = pix0_vector + s * pixel_size * sdet_vec + f * pixel_size * fdet_vec
s_idx = 33
f_idx = 33
expected_pos = (detector.pix0_vector +
                (s_idx + 0.5) * detector.pixel_size * detector.sdet_vec +
                (f_idx + 0.5) * detector.pixel_size * detector.fdet_vec)
print(f"\nExpected position for pixel [33, 33] (with +0.5 offset): {expected_pos}")
print(f"Actual position for pixel [33, 33]: {pixel_coords[33, 33]}")

# Check if they match
if torch.allclose(expected_pos, pixel_coords[33, 33], atol=1e-10):
    print("✓ Positions match!")
else:
    print("✗ Positions don't match!")
    print(f"  Difference: {pixel_coords[33, 33] - expected_pos}")

# Check the beam center position
# The beam should hit at position (beam_center_s, beam_center_f) in pixel coordinates
# For default 64x64 detector, center is at 32, 32 in pixel indices (or 31.5, 31.5 without offset)
print(f"\n\nBeam center analysis:")
print(f"  Config beam_center_s (mm): {detector_config.beam_center_s}")
print(f"  Config beam_center_f (mm): {detector_config.beam_center_f}")
print(f"  Stored beam_center_s (pixels): {detector.beam_center_s}")
print(f"  Stored beam_center_f (pixels): {detector.beam_center_f}")

# Calculate which pixel index the beam center falls into
beam_s_pixels = detector_config.beam_center_s / detector_config.pixel_size_mm
beam_f_pixels = detector_config.beam_center_f / detector_config.pixel_size_mm
print(f"  Beam center in pixels (no offset): s={beam_s_pixels}, f={beam_f_pixels}")
print(f"  Beam center in pixels (with +0.5): s={beam_s_pixels+0.5}, f={beam_f_pixels+0.5}")

# Which pixel index does this correspond to?
# If pixels are at 0.5, 1.5, 2.5, ... then beam at 32.0 falls between pixels 31 and 32
# But with the +0.5 offset, beam at 32.5 is exactly at pixel 32
print(f"  Expected pixel index for beam center: [{int(beam_s_pixels+0.5)}, {int(beam_f_pixels+0.5)}]")