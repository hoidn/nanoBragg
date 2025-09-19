#!/usr/bin/env python3
"""
Trace all the +0.5 offsets to understand where they're applied.
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
    beam_center_s=3.25,  # mm - this is pixel 32.5 without offset
    beam_center_f=3.25   # mm - this is pixel 32.5 without offset
)

print("=== CONFIGURATION ===")
print(f"beam_center_s (config, mm): {config.beam_center_s}")
print(f"beam_center_f (config, mm): {config.beam_center_f}")
print(f"beam_center_s (pixels, no offset): {config.beam_center_s / config.pixel_size_mm}")
print(f"beam_center_f (pixels, no offset): {config.beam_center_f / config.pixel_size_mm}")

# Create detector
detector = Detector(config)

print("\n=== DETECTOR INITIALIZATION ===")
print(f"beam_center_s (stored, pixels): {detector.beam_center_s}")
print(f"beam_center_f (stored, pixels): {detector.beam_center_f}")
print(f"Note: MOSFLM adds +0.5 in __init__, so 32.5 → 33.0")

print("\n=== PIX0_VECTOR CALCULATION ===")
print(f"pix0_vector: {detector.pix0_vector}")
# For BEAM pivot: pix0 = -Fbeam*fdet - Sbeam*sdet + distance*beam
# Fbeam = beam_center_s * pixel_size (with swap)
# Sbeam = beam_center_f * pixel_size (with swap)
Fbeam = detector.beam_center_s * detector.pixel_size
Sbeam = detector.beam_center_f * detector.pixel_size
print(f"Fbeam (meters): {Fbeam} = beam_center_s({detector.beam_center_s}) * pixel_size({detector.pixel_size})")
print(f"Sbeam (meters): {Sbeam} = beam_center_f({detector.beam_center_f}) * pixel_size({detector.pixel_size})")

print("\n=== PIXEL COORDINATE GENERATION ===")
pixel_coords = detector.get_pixel_coords()
print(f"Pixel indices now use +0.5 for centers:")
print(f"  Pixel 0 is at position 0.5")
print(f"  Pixel 32 is at position 32.5")
print(f"  Pixel 33 is at position 33.5")

print("\n=== POSITION ANALYSIS ===")
print(f"Beam hits at pixel position 33.0 (after MOSFLM +0.5)")
print(f"This is exactly between pixel 32 (at 32.5) and pixel 33 (at 33.5)")
print(f"The C code probably assigns intensity to pixel 33")
print(f"Our code might be assigning it to pixel 32 or using a different rounding")

# Check actual pixel positions around the beam center
print("\n=== PIXEL POSITIONS NEAR BEAM CENTER ===")
for s in range(31, 36):
    for f in range(31, 36):
        if s < pixel_coords.shape[0] and f < pixel_coords.shape[1]:
            pos = pixel_coords[s, f]
            dist_from_origin = torch.norm(pos)
            print(f"Pixel [{s},{f}]: pos={pos.numpy()}, distance={dist_from_origin:.6f}")

# Calculate which pixel should get the maximum intensity
# The beam comes from [1, 0, 0] direction, so pixels closer to the origin
# along the beam axis should get more intensity
print("\n=== EXPECTED MAXIMUM POSITION ===")
print("For a simple cubic crystal with λ=1.0, N=1:")
print("The maximum should be where the beam hits the detector directly")
print("With beam center at (33.0, 33.0) in pixel coordinates")
print("And pixels at 0.5, 1.5, ..., 32.5, 33.5, ...")
print("The beam is exactly between pixels 32 and 33")
print("The C code puts max at [34, 34] - why?")
print("Maybe C uses pixel edges (0, 1, 2, ...) not centers?")