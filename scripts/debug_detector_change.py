#!/usr/bin/env python3
"""Debug script to understand detector coordinate changes."""

import os
import torch
import numpy as np

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.models.detector import Detector

# Create detector with default config
device = torch.device("cpu")
dtype = torch.float64
detector = Detector(device=device, dtype=dtype)

print("Detector configuration:")
print(f"  distance_mm: {detector.config.distance_mm}")
print(f"  pixel_size_mm: {detector.config.pixel_size_mm}")
print(f"  spixels: {detector.spixels}")
print(f"  fpixels: {detector.fpixels}")
print(f"  beam_center_s: {detector.config.beam_center_s}")
print(f"  beam_center_f: {detector.config.beam_center_f}")

print(f"\nBeam center in pixels:")
print(f"  beam_center_s (pixels): {detector.beam_center_s}")
print(f"  beam_center_f (pixels): {detector.beam_center_f}")

print(f"\nBasis vectors:")
print(f"  fdet_vec: {detector.fdet_vec}")
print(f"  sdet_vec: {detector.sdet_vec}")
print(f"  odet_vec: {detector.odet_vec}")

print(f"\nCalculated values:")
print(f"  distance (Angstroms): {detector.distance}")
print(f"  pixel_size (Angstroms): {detector.pixel_size}")
print(f"  pix0_vector: {detector.pix0_vector}")

# Calculate what pixel (0,0) position should be
detector_origin = detector.distance * detector.odet_vec
s_offset = (0.5 - detector.beam_center_s) * detector.pixel_size
f_offset = (0.5 - detector.beam_center_f) * detector.pixel_size

print(f"\nManual calculation:")
print(f"  detector_origin: {detector_origin}")
print(f"  s_offset: {s_offset}")
print(f"  f_offset: {f_offset}")

# Get pixel coordinates
pixel_coords = detector.get_pixel_coords()
print(f"\nPixel (0,0) position: {pixel_coords[0, 0, :]}")
print(f"Pixel (511,511) position: {pixel_coords[511, 511, :]}")
print(f"Pixel (512,512) position: {pixel_coords[512, 512, :]}")

# Check center pixel - should be close to beam position
center_s = 512
center_f = 512
center_pixel = pixel_coords[center_s, center_f, :]
print(f"\nCenter pixel ({center_s},{center_f}) position: {center_pixel}")

# Expected position for center pixel with beam at (512, 512)
# Since beam_center is 51.2mm = 512 pixels, pixel 512 should be at the beam position
expected_center = detector.distance * detector.odet_vec
print(f"Expected center position: {expected_center}")
print(f"Difference: {center_pixel - expected_center}")