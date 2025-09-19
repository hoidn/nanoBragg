#!/usr/bin/env python3
"""Debug pixel positions for tilted detector."""

import os
import torch
import numpy as np

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector

# Create detector with tilted configuration
device = torch.device("cpu")
dtype = torch.float64

detector_config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=61.2,  # offset by 10mm
    beam_center_f=61.2,  # offset by 10mm
    detector_convention=DetectorConvention.MOSFLM,
    detector_rotx_deg=5.0,
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=15.0,
    twotheta_axis=[0.0, 1.0, 0.0],
    detector_pivot=DetectorPivot.BEAM
)
detector = Detector(config=detector_config, device=device, dtype=dtype)

print("Detector configuration summary:")
print(f"  Distance: {detector.distance/1e7:.1f} meters")
print(f"  Beam center: ({detector_config.beam_center_s}, {detector_config.beam_center_f}) mm")
print(f"  Beam center pixels: ({detector.beam_center_s:.1f}, {detector.beam_center_f:.1f})")
print(f"  Pixel size: {detector.pixel_size} Angstroms")

print("\nDetector basis vectors (should match C-code):")
print(f"  fdet_vec: {detector.fdet_vec.tolist()}")
print(f"  sdet_vec: {detector.sdet_vec.tolist()}")
print(f"  odet_vec: {detector.odet_vec.tolist()}")

print(f"\nPix0 vector:")
print(f"  PyTorch (Angstroms): {detector.pix0_vector.tolist()}")
print(f"  PyTorch (meters): {[x/1e10 for x in detector.pix0_vector.tolist()]}")

# Get pixel coordinates
pixel_coords = detector.get_pixel_coords()

# Check key pixels
print("\nKey pixel positions (meters):")
print(f"  Pixel (0,0): {[x/1e10 for x in pixel_coords[0, 0, :].tolist()]}")
print(f"  Pixel (512,512): {[x/1e10 for x in pixel_coords[512, 512, :].tolist()]}")
print(f"  Pixel (612,612): {[x/1e10 for x in pixel_coords[612, 612, :].tolist()]}")

# For BEAM pivot, the beam should hit at the specified beam center coordinates
# Beam center is at (612, 612) pixels
beam_pixel_s = int(detector.beam_center_s.item())
beam_pixel_f = int(detector.beam_center_f.item())
print(f"\nBeam center pixel ({beam_pixel_s}, {beam_pixel_f}):")
print(f"  Position (meters): {[x/1e10 for x in pixel_coords[beam_pixel_s, beam_pixel_f, :].tolist()]}")

# The beam travels along [1, 0, 0] and should hit the detector at distance
expected_beam_hit = detector.distance * torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
print(f"\nExpected beam hit position (meters): {[x/1e10 for x in expected_beam_hit.tolist()]}")

# Find closest pixel to expected beam position
distances = torch.norm(pixel_coords - expected_beam_hit.unsqueeze(0).unsqueeze(0), dim=2)
min_idx = torch.argmin(distances.flatten())
min_s = min_idx // detector.fpixels
min_f = min_idx % detector.fpixels
print(f"\nClosest pixel to beam: ({min_s}, {min_f})")
print(f"  Distance from beam (Angstroms): {distances[min_s, min_f].item():.2f}")
print(f"  Position (meters): {[x/1e10 for x in pixel_coords[min_s, min_f, :].tolist()]}")

# Check if pix0_vector matches pixel (0,0)
pix00_diff = pixel_coords[0, 0, :] - detector.pix0_vector
print(f"\nDifference between pixel(0,0) and pix0_vector:")
print(f"  Angstroms: {pix00_diff.tolist()}")
print(f"  Magnitude: {torch.norm(pix00_diff).item():.2e}")