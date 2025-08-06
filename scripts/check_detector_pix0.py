#!/usr/bin/env python3
"""Check what pix0_vector value the detector is actually producing."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from src.nanobrag_torch.models.detector import Detector

# Create detector config
config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=61.2,  # mm
    beam_center_f=61.2,  # mm
    detector_convention=DetectorConvention.MOSFLM,
    detector_rotx_deg=5.0,
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=15.0,
    detector_pivot=DetectorPivot.BEAM,
    oversample=1
)

# Create detector
detector = Detector(config=config, dtype=torch.float64)

print(f"Detector pix0_vector: {detector.pix0_vector.tolist()}")
print(f"Expected (Angstroms): [1120873728.0, 653100416.0, -556023296.0]")

# The values seem to be 1000x too small
# Let's check what the pix0_vector formula should produce step by step

# According to the MOSFLM BEAM pivot code:
# Fbeam = Ybeam + 0.5*pixel_size (in mm)
# Sbeam = Xbeam + 0.5*pixel_size (in mm)

Ybeam_mm = 61.2  # beam_center_s in mm
Xbeam_mm = 61.2  # beam_center_f in mm
pixel_size_mm = 0.1

Fbeam_mm = Ybeam_mm + 0.5 * pixel_size_mm  # 61.25 mm
Sbeam_mm = Xbeam_mm + 0.5 * pixel_size_mm  # 61.25 mm

print(f"\nMOSFLM convention:")
print(f"  Xbeam = {Xbeam_mm} mm")
print(f"  Ybeam = {Ybeam_mm} mm")
print(f"  Fbeam = Ybeam + 0.5*pixel_size = {Fbeam_mm} mm")
print(f"  Sbeam = Xbeam + 0.5*pixel_size = {Sbeam_mm} mm")

# These need to be converted to meters for the C-code formula
Fbeam_m = Fbeam_mm / 1000  # 0.06125 m
Sbeam_m = Sbeam_mm / 1000  # 0.06125 m
distance_m = 100.0 / 1000   # 0.1 m

print(f"\nIn meters:")
print(f"  Fbeam = {Fbeam_m} m")
print(f"  Sbeam = {Sbeam_m} m")
print(f"  distance = {distance_m} m")

# The C-code formula works in meters
beam_vector = torch.tensor([1.0, 0.0, 0.0])
pix0_meters = (-Fbeam_m * detector.fdet_vec - 
               Sbeam_m * detector.sdet_vec + 
               distance_m * beam_vector)

print(f"\nC-code formula (meters):")
print(f"  pix0 = -Fbeam*fdet - Sbeam*sdet + distance*beam")
print(f"       = {pix0_meters.tolist()} m")

# Convert to Angstroms
pix0_angstroms = pix0_meters * 1e10
print(f"\nConverted to Angstroms:")
print(f"  pix0 = {pix0_angstroms.tolist()} Å")
print(f"\nActual detector.pix0_vector: {detector.pix0_vector.tolist()} Å")

# Check ratio
ratio = pix0_angstroms / detector.pix0_vector
print(f"\nRatio (expected/actual): {ratio.tolist()}")