#\!/usr/bin/env python3
"""Debug pix0_vector calculation for SAMPLE pivot mode."""

import os
import sys
import torch
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector

# Set environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Test configuration
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

print("Debugging pix0_vector calculation for SAMPLE pivot")
print("="*60)

# Create detector
detector = Detector(config=config, device=torch.device("cpu"), dtype=torch.float64)

# Print internal values
print(f"\nDetector internal values:")
print(f"  distance: {detector.distance} meters")
print(f"  pixel_size: {detector.pixel_size} meters")
print(f"  beam_center_s: {detector.beam_center_s} pixels")
print(f"  beam_center_f: {detector.beam_center_f} pixels")

# Manual calculation following detector code
print(f"\nManual pix0_vector calculation (SAMPLE pivot):")

# Detector origin
detector_origin = detector.distance * detector.odet_vec
print(f"  detector_origin = distance * odet_vec")
print(f"  detector_origin = {detector.distance} * {detector.odet_vec.numpy()}")
print(f"  detector_origin = {detector_origin.numpy()} meters")

# Offsets
s_offset = (0.5 - detector.beam_center_s) * detector.pixel_size
f_offset = (0.5 - detector.beam_center_f) * detector.pixel_size
print(f"\n  s_offset = (0.5 - {detector.beam_center_s}) * {detector.pixel_size}")
print(f"  s_offset = {s_offset} meters")
print(f"  f_offset = (0.5 - {detector.beam_center_f}) * {detector.pixel_size}")
print(f"  f_offset = {f_offset} meters")

# Calculate pix0_vector
pix0_manual = detector_origin + s_offset * detector.sdet_vec + f_offset * detector.fdet_vec
print(f"\n  pix0_vector = detector_origin + s_offset * sdet_vec + f_offset * fdet_vec")
print(f"  pix0_vector = {pix0_manual.numpy()} meters")
print(f"  pix0_vector = {(pix0_manual * 1e10).numpy()} Angstroms")

# Compare with detector's value
print(f"\nDetector's calculated pix0_vector:")
print(f"  In meters: {(detector.pix0_vector / 1e10).numpy()}")
print(f"  In Angstroms: {detector.pix0_vector.numpy()}")

# Check if they match
diff = torch.abs(pix0_manual - detector.pix0_vector / 1e10)
print(f"\nDifference: {diff.numpy()} meters")

# Let's also check what happens with integers vs floats
print(f"\n" + "="*60)
print("Checking beam_center type issue:")
print(f"  config.beam_center_s: {config.beam_center_s} (type: {type(config.beam_center_s)})")
print(f"  config.beam_center_f: {config.beam_center_f} (type: {type(config.beam_center_f)})")
print(f"  detector.beam_center_s: {detector.beam_center_s} (type: {type(detector.beam_center_s)})")
print(f"  detector.beam_center_f: {detector.beam_center_f} (type: {type(detector.beam_center_f)})")

# If beam_center is a tensor, check its value
if torch.is_tensor(detector.beam_center_s):
    print(f"  detector.beam_center_s value: {detector.beam_center_s.item()}")
    print(f"  detector.beam_center_f value: {detector.beam_center_f.item()}")