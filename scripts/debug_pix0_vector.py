#!/usr/bin/env python3
"""Debug pix0_vector calculation."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from src.nanobrag_torch.models.detector import Detector

# Create detector config for cubic_tilted_detector test
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

print("Configuration:")
print(f"  distance_mm: {config.distance_mm}")
print(f"  pixel_size_mm: {config.pixel_size_mm}")
print(f"  beam_center_s: {config.beam_center_s} mm")
print(f"  beam_center_f: {config.beam_center_f} mm")
print(f"  detector_pivot: {config.detector_pivot}")

# Create detector
detector = Detector(config=config, dtype=torch.float64)

print("\nInternal values (Angstroms):")
print(f"  distance: {detector.distance} Å")
print(f"  pixel_size: {detector.pixel_size} Å")
print(f"  beam_center_s: {detector.beam_center_s} pixels")
print(f"  beam_center_f: {detector.beam_center_f} pixels")

print("\nBasis vectors:")
print(f"  fdet_vec: {detector.fdet_vec.tolist()}")
print(f"  sdet_vec: {detector.sdet_vec.tolist()}")
print(f"  odet_vec: {detector.odet_vec.tolist()}")

print("\nPix0 vector calculation:")
# From detector.py _calculate_pix0_vector():
# detector_origin = distance * odet_vec
detector_origin = detector.distance * detector.odet_vec
print(f"  detector_origin = distance * odet_vec")
print(f"                  = {detector.distance} * {detector.odet_vec.tolist()}")
print(f"                  = {detector_origin.tolist()} Å")

# s_offset = (0.0 - beam_center_s) * pixel_size
s_offset = (0.0 - detector.beam_center_s) * detector.pixel_size
print(f"\n  s_offset = (0.0 - beam_center_s) * pixel_size")
print(f"           = (0.0 - {detector.beam_center_s}) * {detector.pixel_size}")
print(f"           = {s_offset} Å")

# f_offset = (0.0 - beam_center_f) * pixel_size
f_offset = (0.0 - detector.beam_center_f) * detector.pixel_size
print(f"\n  f_offset = (0.0 - beam_center_f) * pixel_size")
print(f"           = (0.0 - {detector.beam_center_f}) * {detector.pixel_size}")
print(f"           = {f_offset} Å")

print(f"\n  pix0_vector = detector_origin + s_offset * sdet_vec + f_offset * fdet_vec")
print(f"              = {detector_origin.tolist()}")
print(f"              + {s_offset} * {detector.sdet_vec.tolist()}")
print(f"              + {f_offset} * {detector.fdet_vec.tolist()}")
print(f"              = {detector.pix0_vector.tolist()} Å")

print("\nExpected C-code value:")
c_pix0_meters = torch.tensor([0.112087366299472, 0.0653100408232811, -0.0556023303792543])
c_pix0_angstroms = c_pix0_meters * 1e10
print(f"  C-code (meters): {c_pix0_meters.tolist()}")
print(f"  C-code (Angstroms): {c_pix0_angstroms.tolist()}")

print("\nDifference:")
diff = detector.pix0_vector - c_pix0_angstroms
print(f"  PyTorch - C-code: {diff.tolist()} Å")
print(f"  Relative error: {(diff / c_pix0_angstroms).tolist()}")

# Let's check the C-code calculation
# From C-code line 1742-1744 (BEAM pivot):
# pix0_vector[1] = -Fbeam*fdet_vector[1]-Sbeam*sdet_vector[1]+distance*beam_vector[1];
# pix0_vector[2] = -Fbeam*fdet_vector[2]-Sbeam*sdet_vector[2]+distance*beam_vector[2];
# pix0_vector[3] = -Fbeam*fdet_vector[3]-Sbeam*sdet_vector[3]+distance*beam_vector[3];

print("\nC-code calculation check:")
# From MOSFLM convention setup:
# Fbeam = Ybeam + 0.5*pixel_size = 61.2e-3 + 0.5*0.1e-3 = 0.06125 meters
# Sbeam = Xbeam + 0.5*pixel_size = 61.2e-3 + 0.5*0.1e-3 = 0.06125 meters
Fbeam_meters = 61.2e-3 + 0.5*0.1e-3
Sbeam_meters = 61.2e-3 + 0.5*0.1e-3
distance_meters = 100e-3
beam_vector = torch.tensor([1.0, 0.0, 0.0])  # MOSFLM convention

print(f"  Fbeam = {Fbeam_meters} meters")
print(f"  Sbeam = {Sbeam_meters} meters")
print(f"  distance = {distance_meters} meters")
print(f"  beam_vector = {beam_vector.tolist()}")

# Calculate using C-code formula
pix0_c_style = (-Fbeam_meters * detector.fdet_vec 
                -Sbeam_meters * detector.sdet_vec 
                + distance_meters * beam_vector)
print(f"\n  pix0_vector (C-style) = -Fbeam*fdet_vec - Sbeam*sdet_vec + distance*beam_vector")
print(f"                        = {pix0_c_style.tolist()} meters")
print(f"                        = {(pix0_c_style * 1e10).tolist()} Angstroms")

print("\nCompare with expected C-code value:")
print(f"  Calculated: {pix0_c_style.tolist()} meters")
print(f"  Expected:   {c_pix0_meters.tolist()} meters")
print(f"  Difference: {(pix0_c_style - c_pix0_meters).tolist()} meters")