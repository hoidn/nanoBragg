#!/usr/bin/env python3
"""
Test the perfect identity configuration that should use hardcoded path.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot

# Perfect identity configuration matching _is_default_config() requirements
config = DetectorConfig(
    distance_mm=100.0,        # ✓ Required
    pixel_size_mm=0.1,        # ✓ Required  
    spixels=1024,             # ✓ Required
    fpixels=1024,             # ✓ Required
    beam_center_s=51.25,      # ✓ This was the issue - was 51.2
    beam_center_f=51.25,      # ✓ This was the issue - was 51.2
    detector_convention=DetectorConvention.MOSFLM,  # ✓ Required
    detector_pivot=DetectorPivot.BEAM,
    detector_rotx_deg=0.0,    # ✓ Required
    detector_roty_deg=0.0,    # ✓ Required
    detector_rotz_deg=0.0,    # ✓ Required
    detector_twotheta_deg=0.0,  # ✓ Required
)

detector = Detector(config=config)

print("PERFECT IDENTITY CONFIGURATION TEST")
print("=" * 50)
print(f"Is default config: {detector._is_default_config()}")
print()

print("BASIS VECTORS:")
print(f"  fdet_vec (fast): {detector.fdet_vec}")
print(f"  sdet_vec (slow): {detector.sdet_vec}")
print(f"  odet_vec (normal): {detector.odet_vec}")
print()

print(f"PIX0 VECTOR: {detector.pix0_vector}")
print()

# Check deviations
identity_fdet = torch.tensor([0.0, 0.0, 1.0])
identity_sdet = torch.tensor([0.0, -1.0, 0.0])
identity_odet = torch.tensor([1.0, 0.0, 0.0])

fdet_dev = torch.norm(detector.fdet_vec - identity_fdet).item()
sdet_dev = torch.norm(detector.sdet_vec - identity_sdet).item()
odet_dev = torch.norm(detector.odet_vec - identity_odet).item()

print("DEVIATIONS FROM EXPECTED IDENTITY:")
print(f"  ||fdet - [0,0,1]|| = {fdet_dev:.10f}")
print(f"  ||sdet - [0,-1,0]|| = {sdet_dev:.10f}")
print(f"  ||odet - [1,0,0]|| = {odet_dev:.10f}")
print()

if fdet_dev < 1e-10 and sdet_dev < 1e-10 and odet_dev < 1e-10:
    print("✅ PERFECT: Using hardcoded identity basis vectors")
else:
    print("❌ PROBLEM: Still using calculated basis vectors")
    
# Expected pix0 for perfect identity with beam center (51.25, 51.25)
# With MOSFLM convention: +0.5 pixel offset
# Beam center in pixels: 512.5, 512.5  
# Fbeam = Sbeam = 0.05125 m
# pix0 = [distance, Sbeam, -Fbeam] = [0.1, 0.05125, -0.05125]
expected_pix0 = torch.tensor([0.1, 0.05125, -0.05125])
pix0_diff = torch.norm(detector.pix0_vector - expected_pix0).item()
print(f"\nPIX0 DEVIATION: {pix0_diff:.10f}")
if pix0_diff < 1e-10:
    print("✅ PIX0 PERFECT")
else:
    print("❌ PIX0 PROBLEM")