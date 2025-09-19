#!/usr/bin/env python
"""Compare detector geometry between hard-coded and triclinic test."""

import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import numpy as np

print("Detector Geometry Comparison:")
print("=" * 60)

# Hard-coded values in Detector class
print("HARD-CODED (Simple Cubic):")
print("  Distance: 100 mm = 1e9 Å")
print("  Pixel size: 0.1 mm = 1e6 Å")
print("  Detector size: 1024 x 1024 pixels")
print("  Beam center: (512.5, 512.5) pixels")
print("  Detector vectors:")
print("    Fast (X): [0, 0, 1]")
print("    Slow (Y): [0, -1, 0]")
print("    Normal (Z): [1, 0, 0]")

# Triclinic test values (from test file)
print("\nTRICLINIC TEST:")
print("  Distance: 85 mm = 8.5e8 Å")
print("  Pixel size: 0.08 mm = 8e5 Å")
print("  Detector size: 512 x 512 pixels")
print("  Beam center: (256.5, 256.5) pixels")
print("  Detector vectors: (probably different)")

# The issue is that the detector basis vectors might be different
print("\nIMPACT OF GEOMETRY MISMATCH:")
print("-" * 40)

# Calculate the pixel position error
# For a spot at angle theta, distance d, the position error is:
# delta_pos = d * tan(delta_theta)

# Example: 1 degree rotation error at 85mm
theta_error = 1.0  # degrees
d = 85.0  # mm
pos_error = d * np.tan(np.radians(theta_error))
pixel_error = pos_error / 0.08  # pixels

print(f"1° detector rotation at 85mm distance:")
print(f"  Position error: {pos_error:.2f} mm")
print(f"  Pixel error: {pixel_error:.1f} pixels")

# The detector basis vectors determine how (h,k,l) maps to (x,y) on detector
# If these are wrong, every spot will be in the wrong place

print("\nDETECTOR BASIS VECTOR IMPACT:")
# The scattering vector S maps to detector coordinates as:
# x_detector = S · fast_axis
# y_detector = S · slow_axis

# If the basis vectors are rotated, this creates a systematic shift
print("If detector basis is rotated by angle θ:")
print("  All spots rotate by θ around beam center")
print("  Correlation drops as 1 - (θ²/2) for small θ")
print("  For 0.957 correlation, θ ≈ 10-15 degrees")

# Check what rotation would give 0.957 correlation
# corr ≈ cos(θ) for rotation error
theta_implied = np.arccos(0.957) * 180 / np.pi
print(f"\nImplied rotation error for 0.957 correlation: {theta_implied:.1f}°")

# The C-code for triclinic likely uses different detector orientation
print("\nCONCLUSION:")
print("The 0.957 correlation strongly suggests the detector basis vectors")
print("are incorrect for the triclinic test. The hard-coded vectors from")
print("simple_cubic don't match what was used to generate triclinic_P1.")
