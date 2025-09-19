#!/usr/bin/env python3
"""
Debug script to check pixel coordinate generation.
"""

import os
import torch

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector

# Simple case configuration
detector_config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=4,  # Small detector for debugging
    fpixels=4
)

# Create detector
detector = Detector(detector_config)

# Get pixel coordinates
pixel_coords = detector.get_pixel_coords()

print(f"Detector: {detector_config.spixels}x{detector_config.fpixels} pixels")
print(f"Pixel size: {detector_config.pixel_size_mm} mm")
print(f"pix0_vector: {detector.pix0_vector}")
print(f"fdet_vec: {detector.fdet_vec}")
print(f"sdet_vec: {detector.sdet_vec}")
print()

# Print all pixel coordinates
for s in range(detector_config.spixels):
    for f in range(detector_config.fpixels):
        pos = pixel_coords[s, f]
        print(f"Pixel [{s},{f}]: {pos.numpy()}")

# Check the indices being generated
print("\nDebug: Creating index grids manually")
s_indices = torch.arange(4, dtype=torch.float64) + 0.5
f_indices = torch.arange(4, dtype=torch.float64) + 0.5
print(f"s_indices: {s_indices}")
print(f"f_indices: {f_indices}")

s_grid, f_grid = torch.meshgrid(s_indices, f_indices, indexing="ij")
print(f"\ns_grid:\n{s_grid}")
print(f"\nf_grid:\n{f_grid}")

# Calculate expected positions manually
print("\nManual calculation for pixel [1, 2]:")
s_idx = 1
f_idx = 2
pix0 = detector.pix0_vector
sdet = detector.sdet_vec
fdet = detector.fdet_vec
pixel_size = detector.pixel_size

manual_pos = pix0 + (s_idx + 0.5) * pixel_size * sdet + (f_idx + 0.5) * pixel_size * fdet
print(f"  pix0_vector: {pix0}")
print(f"  + (1.5 * {pixel_size}) * sdet_vec: {(s_idx + 0.5) * pixel_size * sdet}")
print(f"  + (2.5 * {pixel_size}) * fdet_vec: {(f_idx + 0.5) * pixel_size * fdet}")
print(f"  = {manual_pos}")
print(f"  Actual from array: {pixel_coords[1, 2]}")

if torch.allclose(manual_pos, pixel_coords[1, 2], atol=1e-10):
    print("  ✓ Match!")
else:
    print("  ✗ Mismatch!")
    print(f"    Difference: {pixel_coords[1, 2] - manual_pos}")