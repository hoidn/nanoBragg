#!/usr/bin/env python3
"""Test that detector vectors now match C-code reference."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
sys.path.insert(0, '/Users/ollie/Documents/nanoBragg')

import torch
import numpy as np
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector

# C-code reference vectors from trace
c_code_vectors = {
    'fast': np.array([0.0311947630447082, -0.096650175316428, 0.994829447880333]),
    'slow': np.array([-0.228539518954453, -0.969636205471835, -0.0870362988312832]),
    'normal': np.array([0.973034724475264, -0.224642766741965, -0.0523359562429438]),
}

# Configure detector with cubic_tilted_detector parameters
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
    # Don't specify twotheta_axis - let it use the convention default
)

# Create detector
detector = Detector(config, dtype=torch.float64)

print("Testing Detector Implementation Fix")
print("=" * 40)

print(f"\nConfiguration:")
print(f"  Convention: {config.detector_convention.value}")
print(f"  Rotations: X={config.detector_rotx_deg}°, Y={config.detector_roty_deg}°, Z={config.detector_rotz_deg}°")
print(f"  Two-theta: {config.detector_twotheta_deg}°")
print(f"  Two-theta axis: {config.twotheta_axis.numpy()}")

print(f"\nPyTorch vectors:")
print(f"  Fast:   {detector.fdet_vec.numpy()}")
print(f"  Slow:   {detector.sdet_vec.numpy()}")
print(f"  Normal: {detector.odet_vec.numpy()}")

print(f"\nC-code reference:")
print(f"  Fast:   {c_code_vectors['fast']}")
print(f"  Slow:   {c_code_vectors['slow']}")
print(f"  Normal: {c_code_vectors['normal']}")

print(f"\nDifferences:")
print(f"  Fast:   {np.linalg.norm(detector.fdet_vec.numpy() - c_code_vectors['fast']):.2e}")
print(f"  Slow:   {np.linalg.norm(detector.sdet_vec.numpy() - c_code_vectors['slow']):.2e}")
print(f"  Normal: {np.linalg.norm(detector.odet_vec.numpy() - c_code_vectors['normal']):.2e}")

# Test passes if differences are less than 1e-6
threshold = 1e-6
if (np.linalg.norm(detector.fdet_vec.numpy() - c_code_vectors['fast']) < threshold and
    np.linalg.norm(detector.sdet_vec.numpy() - c_code_vectors['slow']) < threshold and
    np.linalg.norm(detector.odet_vec.numpy() - c_code_vectors['normal']) < threshold):
    print("\n✓ TEST PASSED: Detector vectors match C-code reference!")
else:
    print("\n✗ TEST FAILED: Detector vectors do not match C-code reference")
    
# Also test that basis vectors are orthonormal
print(f"\nOrthonormality check:")
print(f"  |fast|   = {torch.norm(detector.fdet_vec).item():.6f}")
print(f"  |slow|   = {torch.norm(detector.sdet_vec).item():.6f}")
print(f"  |normal| = {torch.norm(detector.odet_vec).item():.6f}")
print(f"  fast·slow   = {torch.dot(detector.fdet_vec, detector.sdet_vec).item():.2e}")
print(f"  fast·normal = {torch.dot(detector.fdet_vec, detector.odet_vec).item():.2e}")
print(f"  slow·normal = {torch.dot(detector.sdet_vec, detector.odet_vec).item():.2e}")