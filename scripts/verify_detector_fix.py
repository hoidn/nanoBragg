#!/usr/bin/env python3
"""Verify the detector basis vector calculation fix."""

import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
from src.nanobrag_torch.config import DetectorConfig
from src.nanobrag_torch.models.detector import Detector

# Create detector config for cubic_tilted_detector test
config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=61.2,  # mm
    beam_center_f=61.2,  # mm
    detector_rotx_deg=5.0,
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=15.0,
    oversample=1,
)

print("DetectorConfig created:")
print(f"  detector_convention: {config.detector_convention}")
print(f"  twotheta_axis (after __post_init__): {config.twotheta_axis.tolist()}")

# Create detector
detector = Detector(config=config, dtype=torch.float64)

print("\nDetector basis vectors:")
print(f"  Fast axis: {detector.fdet_vec.tolist()}")
print(f"  Slow axis: {detector.sdet_vec.tolist()}")
print(f"  Normal axis: {detector.odet_vec.tolist()}")

print("\nExpected C-code values:")
print("  Fast axis: [0.0311948, -0.0966502, 0.9948294]")
print("  Slow axis: [-0.2285395, -0.9696362, -0.0870363]")
print("  Normal axis: [0.9730347, -0.2246428, -0.0523360]")

# Calculate differences
c_fast = torch.tensor([0.0311948, -0.0966502, 0.9948294], dtype=torch.float64)
c_slow = torch.tensor([-0.2285395, -0.9696362, -0.0870363], dtype=torch.float64)
c_normal = torch.tensor([0.9730347, -0.2246428, -0.0523360], dtype=torch.float64)

print("\nDifferences (PyTorch - C):")
print(f"  Fast diff: {(detector.fdet_vec - c_fast).tolist()}")
print(f"  Slow diff: {(detector.sdet_vec - c_slow).tolist()}")
print(f"  Normal diff: {(detector.odet_vec - c_normal).tolist()}")

# Check if differences are within tolerance
tolerance = 1e-7
fast_match = torch.allclose(detector.fdet_vec, c_fast, rtol=tolerance, atol=tolerance)
slow_match = torch.allclose(detector.sdet_vec, c_slow, rtol=tolerance, atol=tolerance)
normal_match = torch.allclose(
    detector.odet_vec, c_normal, rtol=tolerance, atol=tolerance
)

print(f"\nMatch within tolerance ({tolerance}):")
print(f"  Fast axis: {fast_match}")
print(f"  Slow axis: {slow_match}")
print(f"  Normal axis: {normal_match}")
print(f"  All match: {fast_match and slow_match and normal_match}")
