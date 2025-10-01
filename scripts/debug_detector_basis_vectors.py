#!/usr/bin/env python3
"""Debug script to compare C and Python detector basis vector calculations."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from src.nanobrag_torch.utils.geometry import angles_to_rotation_matrix, rotate_axis
from src.nanobrag_torch.utils.units import degrees_to_radians

# Parameters from cubic_tilted_detector test
detector_rotx_deg = 5.0
detector_roty_deg = 3.0
detector_rotz_deg = 2.0
detector_twotheta_deg = 15.0
twotheta_axis = [0.0, 0.0, -1.0]  # Default from C-code MOSFLM convention (negative Z-axis)

# Initial MOSFLM vectors from C-code
fdet_vector_init = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
sdet_vector_init = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
odet_vector_init = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)

print("Initial detector vectors (MOSFLM convention):")
print(f"  Fast: {fdet_vector_init.tolist()}")
print(f"  Slow: {sdet_vector_init.tolist()}")
print(f"  Normal: {odet_vector_init.tolist()}")

# Convert angles to radians
rotx_rad = torch.tensor(degrees_to_radians(detector_rotx_deg), dtype=torch.float64)
roty_rad = torch.tensor(degrees_to_radians(detector_roty_deg), dtype=torch.float64)
rotz_rad = torch.tensor(degrees_to_radians(detector_rotz_deg), dtype=torch.float64)
twotheta_rad = torch.tensor(degrees_to_radians(detector_twotheta_deg), dtype=torch.float64)

print(f"\nRotation angles:")
print(f"  detector_rotx: {detector_rotx_deg}° = {rotx_rad:.6f} rad")
print(f"  detector_roty: {detector_roty_deg}° = {roty_rad:.6f} rad")
print(f"  detector_rotz: {detector_rotz_deg}° = {rotz_rad:.6f} rad")
print(f"  twotheta: {detector_twotheta_deg}° = {twotheta_rad:.6f} rad")

# Apply rotations using angles_to_rotation_matrix (Python approach)
print("\n=== Python approach (angles_to_rotation_matrix) ===")
rotation_matrix = angles_to_rotation_matrix(rotx_rad, roty_rad, rotz_rad)
print("Rotation matrix:")
print(rotation_matrix.numpy())

fdet_python = torch.matmul(rotation_matrix, fdet_vector_init)
sdet_python = torch.matmul(rotation_matrix, sdet_vector_init)
odet_python = torch.matmul(rotation_matrix, odet_vector_init)

print("\nAfter XYZ rotations:")
print(f"  Fast: {fdet_python.tolist()}")
print(f"  Slow: {sdet_python.tolist()}")
print(f"  Normal: {odet_python.tolist()}")

# Apply twotheta rotation
twotheta_axis_tensor = torch.tensor(twotheta_axis, dtype=torch.float64)
fdet_python = rotate_axis(fdet_python, twotheta_axis_tensor, twotheta_rad)
sdet_python = rotate_axis(sdet_python, twotheta_axis_tensor, twotheta_rad)
odet_python = rotate_axis(odet_python, twotheta_axis_tensor, twotheta_rad)

print("\nAfter twotheta rotation:")
print(f"  Fast: {fdet_python.tolist()}")
print(f"  Slow: {sdet_python.tolist()}")
print(f"  Normal: {odet_python.tolist()}")

# Expected values from C-code trace
print("\n=== Expected C-code values ===")
print("  Fast: [0.0311948, -0.0966502, 0.9948294]")
print("  Slow: [-0.2285395, -0.9696362, -0.0870363]")
print("  Normal: [0.9730347, -0.2246428, -0.0523360]")

# Compare differences
print("\n=== Differences (Python - C) ===")
c_fast = torch.tensor([0.0311948, -0.0966502, 0.9948294], dtype=torch.float64)
c_slow = torch.tensor([-0.2285395, -0.9696362, -0.0870363], dtype=torch.float64)
c_normal = torch.tensor([0.9730347, -0.2246428, -0.0523360], dtype=torch.float64)

print(f"  Fast diff: {(fdet_python - c_fast).tolist()}")
print(f"  Slow diff: {(sdet_python - c_slow).tolist()}")
print(f"  Normal diff: {(odet_python - c_normal).tolist()}")

# Let's also manually apply rotations step by step to match C-code
print("\n=== Manual step-by-step rotation (matching C rotate function) ===")

def rotate_c_style(v, phix, phiy, phiz):
    """Apply rotations in C-code style: X first, then Y, then Z."""
    new_v = v.clone()
    
    # Rotate around X-axis
    if abs(phix) > 1e-12:
        cos_x = torch.cos(phix)
        sin_x = torch.sin(phix)
        y = new_v[1]
        z = new_v[2]
        new_v[1] = y * cos_x + z * (-sin_x)
        new_v[2] = y * sin_x + z * cos_x
    
    # Rotate around Y-axis
    if abs(phiy) > 1e-12:
        cos_y = torch.cos(phiy)
        sin_y = torch.sin(phiy)
        x = new_v[0]
        z = new_v[2]
        new_v[0] = x * cos_y + z * sin_y
        new_v[2] = x * (-sin_y) + z * cos_y
    
    # Rotate around Z-axis
    if abs(phiz) > 1e-12:
        cos_z = torch.cos(phiz)
        sin_z = torch.sin(phiz)
        x = new_v[0]
        y = new_v[1]
        new_v[0] = x * cos_z + y * (-sin_z)
        new_v[1] = x * sin_z + y * cos_z
    
    return new_v

# Apply manual rotations
fdet_manual = rotate_c_style(fdet_vector_init, rotx_rad, roty_rad, rotz_rad)
sdet_manual = rotate_c_style(sdet_vector_init, rotx_rad, roty_rad, rotz_rad)
odet_manual = rotate_c_style(odet_vector_init, rotx_rad, roty_rad, rotz_rad)

print("\nAfter manual XYZ rotations:")
print(f"  Fast: {fdet_manual.tolist()}")
print(f"  Slow: {sdet_manual.tolist()}")
print(f"  Normal: {odet_manual.tolist()}")

# Apply twotheta
fdet_manual = rotate_axis(fdet_manual, twotheta_axis_tensor, twotheta_rad)
sdet_manual = rotate_axis(sdet_manual, twotheta_axis_tensor, twotheta_rad)
odet_manual = rotate_axis(odet_manual, twotheta_axis_tensor, twotheta_rad)

print("\nAfter manual twotheta rotation:")
print(f"  Fast: {fdet_manual.tolist()}")
print(f"  Slow: {sdet_manual.tolist()}")
print(f"  Normal: {odet_manual.tolist()}")

print("\n=== Manual differences (Manual - C) ===")
print(f"  Fast diff: {(fdet_manual - c_fast).tolist()}")
print(f"  Slow diff: {(sdet_manual - c_slow).tolist()}")
print(f"  Normal diff: {(odet_manual - c_normal).tolist()}")