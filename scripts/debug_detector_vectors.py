#!/usr/bin/env python3
"""Debug detector vector calculation to match C-code reference."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
sys.path.insert(0, '/Users/ollie/Documents/nanoBragg')

import torch
import numpy as np
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.utils.geometry import angles_to_rotation_matrix, rotate_axis
from src.nanobrag_torch.utils.units import degrees_to_radians

# C-code reference vectors
c_code_vectors = {
    'fast': np.array([0.0311947630447082, -0.096650175316428, 0.994829447880333]),
    'slow': np.array([-0.228539518954453, -0.969636205471835, -0.0870362988312832]),
    'normal': np.array([0.973034724475264, -0.224642766741965, -0.0523359562429438]),
    'pix0': np.array([0.112087366299472, 0.0653100408232811, -0.0556023303792543])
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
    twotheta_axis=[0.0, 0.0, -1.0]  # MOSFLM default from C-code
)

# Manual step-by-step calculation to debug
print("=== Manual Step-by-Step Calculation ===\n")

# Step 1: Initialize base vectors (MOSFLM convention)
print("Step 1: Initial vectors (MOSFLM convention)")
fdet_vec = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
sdet_vec = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
odet_vec = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
print(f"Fast: {fdet_vec.numpy()}")
print(f"Slow: {sdet_vec.numpy()}")
print(f"Normal: {odet_vec.numpy()}")

# Step 2: Convert angles to radians
detector_rotx = degrees_to_radians(5.0)
detector_roty = degrees_to_radians(3.0)
detector_rotz = degrees_to_radians(2.0)
detector_twotheta = degrees_to_radians(15.0)
print(f"\nStep 2: Rotation angles (radians)")
print(f"rotx: {detector_rotx} (5 degrees)")
print(f"roty: {detector_roty} (3 degrees)")
print(f"rotz: {detector_rotz} (2 degrees)")
print(f"twotheta: {detector_twotheta} (15 degrees)")

# Verify conversion
print(f"\nVerifying angle conversion:")
print(f"5 degrees = {5 * np.pi / 180} radians (numpy)")
print(f"degrees_to_radians(5) = {detector_rotx} (our function)")

# Step 3: Apply detector rotations using C-code logic
print("\nStep 3: Apply detector rotations (X, Y, Z order)")

# First, let me verify the exact C-code values at line 3 of trace
print("\nC-code expected final values:")
print(f"Fast: {c_code_vectors['fast']}")
print(f"Slow: {c_code_vectors['slow']}")
print(f"Normal: {c_code_vectors['normal']}")

# The C-code applies rotations individually in sequence
# Let's follow the exact C-code logic

# Rotate around X axis
if detector_rotx != 0:
    cos_x = np.cos(detector_rotx)
    sin_x = np.sin(detector_rotx)
    # For X rotation: x' = x, y' = y*cos - z*sin, z' = y*sin + z*cos
    
    # Fast vector rotation
    new_fast = fdet_vec.numpy().copy()
    new_fast[1] = fdet_vec[1] * cos_x - fdet_vec[2] * sin_x
    new_fast[2] = fdet_vec[1] * sin_x + fdet_vec[2] * cos_x
    fdet_vec = torch.tensor(new_fast, dtype=torch.float64)
    
    # Slow vector rotation
    new_slow = sdet_vec.numpy().copy()
    new_slow[1] = sdet_vec[1] * cos_x - sdet_vec[2] * sin_x
    new_slow[2] = sdet_vec[1] * sin_x + sdet_vec[2] * cos_x
    sdet_vec = torch.tensor(new_slow, dtype=torch.float64)
    
    # Normal vector rotation
    new_normal = odet_vec.numpy().copy()
    new_normal[1] = odet_vec[1] * cos_x - odet_vec[2] * sin_x
    new_normal[2] = odet_vec[1] * sin_x + odet_vec[2] * cos_x
    odet_vec = torch.tensor(new_normal, dtype=torch.float64)
    
    print(f"After X rotation:")
    print(f"Fast: {fdet_vec.numpy()}")
    print(f"Slow: {sdet_vec.numpy()}")
    print(f"Normal: {odet_vec.numpy()}")

# Rotate around Y axis
if detector_roty != 0:
    cos_y = np.cos(detector_roty)
    sin_y = np.sin(detector_roty)
    # For Y rotation: x' = x*cos + z*sin, y' = y, z' = -x*sin + z*cos
    
    # Fast vector rotation
    new_fast = fdet_vec.numpy().copy()
    new_fast[0] = fdet_vec[0] * cos_y + fdet_vec[2] * sin_y
    new_fast[2] = -fdet_vec[0] * sin_y + fdet_vec[2] * cos_y
    fdet_vec = torch.tensor(new_fast, dtype=torch.float64)
    
    # Slow vector rotation
    new_slow = sdet_vec.numpy().copy()
    new_slow[0] = sdet_vec[0] * cos_y + sdet_vec[2] * sin_y
    new_slow[2] = -sdet_vec[0] * sin_y + sdet_vec[2] * cos_y
    sdet_vec = torch.tensor(new_slow, dtype=torch.float64)
    
    # Normal vector rotation
    new_normal = odet_vec.numpy().copy()
    new_normal[0] = odet_vec[0] * cos_y + odet_vec[2] * sin_y
    new_normal[2] = -odet_vec[0] * sin_y + odet_vec[2] * cos_y
    odet_vec = torch.tensor(new_normal, dtype=torch.float64)
    
    print(f"\nAfter Y rotation:")
    print(f"Fast: {fdet_vec.numpy()}")
    print(f"Slow: {sdet_vec.numpy()}")
    print(f"Normal: {odet_vec.numpy()}")

# Rotate around Z axis
if detector_rotz != 0:
    cos_z = np.cos(detector_rotz)
    sin_z = np.sin(detector_rotz)
    # For Z rotation: x' = x*cos - y*sin, y' = x*sin + y*cos, z' = z
    
    # Fast vector rotation
    new_fast = fdet_vec.numpy().copy()
    new_fast[0] = fdet_vec[0] * cos_z - fdet_vec[1] * sin_z
    new_fast[1] = fdet_vec[0] * sin_z + fdet_vec[1] * cos_z
    fdet_vec = torch.tensor(new_fast, dtype=torch.float64)
    
    # Slow vector rotation
    new_slow = sdet_vec.numpy().copy()
    new_slow[0] = sdet_vec[0] * cos_z - sdet_vec[1] * sin_z
    new_slow[1] = sdet_vec[0] * sin_z + sdet_vec[1] * cos_z
    sdet_vec = torch.tensor(new_slow, dtype=torch.float64)
    
    # Normal vector rotation
    new_normal = odet_vec.numpy().copy()
    new_normal[0] = odet_vec[0] * cos_z - odet_vec[1] * sin_z
    new_normal[1] = odet_vec[0] * sin_z + odet_vec[1] * cos_z
    odet_vec = torch.tensor(new_normal, dtype=torch.float64)
    
    print(f"\nAfter Z rotation:")
    print(f"Fast: {fdet_vec.numpy()}")
    print(f"Slow: {sdet_vec.numpy()}")
    print(f"Normal: {odet_vec.numpy()}")

# Step 4: Apply two-theta rotation
print("\nStep 4: Apply two-theta rotation")
# MOSFLM convention uses [0, 0, -1] as the two-theta axis (C-code line 1194)
twotheta_axis = torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64)
print(f"Two-theta axis (MOSFLM default): {twotheta_axis.numpy()}")

# Manual Rodrigues' formula implementation
def manual_rotate_axis(v, axis, angle):
    """Manual implementation of Rodrigues' formula."""
    # Normalize axis
    axis_mag = np.linalg.norm(axis)
    if axis_mag > 1e-12:
        axis = axis / axis_mag
    
    cos_angle = np.cos(angle)
    sin_angle = np.sin(angle)
    
    # Rodrigues' formula: v_rot = v*cos(phi) + (axis × v)*sin(phi) + axis*(axis·v)*(1-cos(phi))
    axis_dot_v = np.dot(axis, v)
    axis_cross_v = np.cross(axis, v)
    
    v_rot = v * cos_angle + axis_cross_v * sin_angle + axis * axis_dot_v * (1 - cos_angle)
    return v_rot

if detector_twotheta != 0:
    fdet_vec_np = manual_rotate_axis(fdet_vec.numpy(), twotheta_axis.numpy(), detector_twotheta)
    sdet_vec_np = manual_rotate_axis(sdet_vec.numpy(), twotheta_axis.numpy(), detector_twotheta)
    odet_vec_np = manual_rotate_axis(odet_vec.numpy(), twotheta_axis.numpy(), detector_twotheta)
    
    fdet_vec = torch.tensor(fdet_vec_np, dtype=torch.float64)
    sdet_vec = torch.tensor(sdet_vec_np, dtype=torch.float64)
    odet_vec = torch.tensor(odet_vec_np, dtype=torch.float64)
    
    print(f"After two-theta rotation:")
    print(f"Fast: {fdet_vec.numpy()}")
    print(f"Slow: {sdet_vec.numpy()}")
    print(f"Normal: {odet_vec.numpy()}")

# Compare with C-code reference
print("\n=== Comparison with C-code ===")
print(f"Fast axis difference: {np.linalg.norm(fdet_vec.numpy() - c_code_vectors['fast']):.6e}")
print(f"Slow axis difference: {np.linalg.norm(sdet_vec.numpy() - c_code_vectors['slow']):.6e}")
print(f"Normal axis difference: {np.linalg.norm(odet_vec.numpy() - c_code_vectors['normal']):.6e}")

# Now test the actual implementation
print("\n=== Testing actual Detector implementation ===")
detector = Detector(config, dtype=torch.float64)

print(f"\nPyTorch implementation vectors:")
print(f"Fast: {detector.fdet_vec.numpy()}")
print(f"Slow: {detector.sdet_vec.numpy()}")
print(f"Normal: {detector.odet_vec.numpy()}")

print(f"\nDifference from C-code:")
print(f"Fast axis difference: {np.linalg.norm(detector.fdet_vec.numpy() - c_code_vectors['fast']):.6e}")
print(f"Slow axis difference: {np.linalg.norm(detector.sdet_vec.numpy() - c_code_vectors['slow']):.6e}")
print(f"Normal axis difference: {np.linalg.norm(detector.odet_vec.numpy() - c_code_vectors['normal']):.6e}")

# Test with matrix approach
print("\n=== Testing matrix multiplication approach ===")
rotation_matrix = angles_to_rotation_matrix(
    torch.tensor(detector_rotx, dtype=torch.float64),
    torch.tensor(detector_roty, dtype=torch.float64),
    torch.tensor(detector_rotz, dtype=torch.float64)
)
print(f"Rotation matrix:\n{rotation_matrix.numpy()}")

# Apply to initial vectors
fdet_init = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
sdet_init = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
odet_init = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)

fdet_rotated = torch.matmul(rotation_matrix, fdet_init)
sdet_rotated = torch.matmul(rotation_matrix, sdet_init)
odet_rotated = torch.matmul(rotation_matrix, odet_init)

print(f"\nAfter matrix rotation:")
print(f"Fast: {fdet_rotated.numpy()}")
print(f"Slow: {sdet_rotated.numpy()}")
print(f"Normal: {odet_rotated.numpy()}")

# Apply two-theta
if detector_twotheta != 0:
    # Use the same MOSFLM default axis
    twotheta_axis_torch = torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64)
    fdet_final = rotate_axis(fdet_rotated, twotheta_axis_torch, torch.tensor(detector_twotheta, dtype=torch.float64))
    sdet_final = rotate_axis(sdet_rotated, twotheta_axis_torch, torch.tensor(detector_twotheta, dtype=torch.float64))
    odet_final = rotate_axis(odet_rotated, twotheta_axis_torch, torch.tensor(detector_twotheta, dtype=torch.float64))
    
    print(f"\nAfter two-theta rotation (matrix approach):")
    print(f"Fast: {fdet_final.numpy()}")
    print(f"Slow: {sdet_final.numpy()}")
    print(f"Normal: {odet_final.numpy()}")
    
    print(f"\nDifference from C-code (matrix approach):")
    print(f"Fast axis difference: {np.linalg.norm(fdet_final.numpy() - c_code_vectors['fast']):.6e}")
    print(f"Slow axis difference: {np.linalg.norm(sdet_final.numpy() - c_code_vectors['slow']):.6e}")
    print(f"Normal axis difference: {np.linalg.norm(odet_final.numpy() - c_code_vectors['normal']):.6e}")