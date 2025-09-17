#!/usr/bin/env python3
"""
Test script to debug the tilted detector configuration.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot

# Test tilted configuration (same as problematic case)
config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=51.2,
    beam_center_f=51.2,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM,
    detector_rotx_deg=5.0,   # This makes it non-default
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=15.0,
)

detector = Detector(config=config)

print("TILTED DETECTOR DIAGNOSTIC")
print("=" * 50)
print(f"Is default config: {detector._is_default_config()}")
print(f"Distance: {detector.distance} meters")
print(f"Pixel size: {detector.pixel_size} meters")
print()

print("BASIS VECTORS:")
print(f"  fdet_vec (fast): {detector.fdet_vec}")
print(f"  sdet_vec (slow): {detector.sdet_vec}")
print(f"  odet_vec (normal): {detector.odet_vec}")
print()

print(f"PIX0 VECTOR: {detector.pix0_vector}")
print()

# Check orthonormality (should be preserved after rotation)
fdet_norm = torch.norm(detector.fdet_vec).item()
sdet_norm = torch.norm(detector.sdet_vec).item()
odet_norm = torch.norm(detector.odet_vec).item()

dot_fs = torch.dot(detector.fdet_vec, detector.sdet_vec).item()
dot_fo = torch.dot(detector.fdet_vec, detector.odet_vec).item()
dot_so = torch.dot(detector.sdet_vec, detector.odet_vec).item()

print("ORTHONORMALITY CHECK:")
print(f"  |fdet_vec| = {fdet_norm:.6f} (should be 1.0)")
print(f"  |sdet_vec| = {sdet_norm:.6f} (should be 1.0)")
print(f"  |odet_vec| = {odet_norm:.6f} (should be 1.0)")
print(f"  fdet·sdet = {dot_fs:.6f} (should be 0.0)")
print(f"  fdet·odet = {dot_fo:.6f} (should be 0.0)")
print(f"  sdet·odet = {dot_so:.6f} (should be 0.0)")
print()

# Check if rotation matrices were applied correctly
# For small angles, we expect the vectors to be close to identity
print("DEVIATION FROM IDENTITY:")
identity_fdet = torch.tensor([0.0, 0.0, 1.0])
identity_sdet = torch.tensor([0.0, -1.0, 0.0])
identity_odet = torch.tensor([1.0, 0.0, 0.0])

fdet_diff = torch.norm(detector.fdet_vec - identity_fdet).item()
sdet_diff = torch.norm(detector.sdet_vec - identity_sdet).item()
odet_diff = torch.norm(detector.odet_vec - identity_odet).item()

print(f"  ||fdet - [0,0,1]|| = {fdet_diff:.6f}")
print(f"  ||sdet - [0,-1,0]|| = {sdet_diff:.6f}")
print(f"  ||odet - [1,0,0]|| = {odet_diff:.6f}")
print()

print("Expected rotation effects:")
print("  5° rotx should primarily affect Y,Z components")
print("  3° roty should primarily affect X,Z components") 
print("  2° rotz should primarily affect X,Y components")
print("  15° twotheta around -Z should be the largest rotation")