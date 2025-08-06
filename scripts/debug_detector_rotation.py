#!/usr/bin/env python3
"""Debug detector rotation calculation to match C-code."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from nanobrag_torch.utils.geometry import angles_to_rotation_matrix, rotate_axis
from nanobrag_torch.utils.units import degrees_to_radians

# Initial MOSFLM vectors
fdet_vec = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
sdet_vec = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
odet_vec = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)

print("Initial vectors (MOSFLM convention):")
print(f"fdet: {fdet_vec}")
print(f"sdet: {sdet_vec}")
print(f"odet: {odet_vec}")

# Rotation angles (in degrees, then convert to radians)
rotx_deg = 5.0
roty_deg = 3.0
rotz_deg = 2.0
twotheta_deg = 15.0

rotx = degrees_to_radians(torch.tensor(rotx_deg, dtype=torch.float64))
roty = degrees_to_radians(torch.tensor(roty_deg, dtype=torch.float64)) 
rotz = degrees_to_radians(torch.tensor(rotz_deg, dtype=torch.float64))
twotheta = degrees_to_radians(torch.tensor(twotheta_deg, dtype=torch.float64))

print(f"\nRotation angles (degrees): rotx={rotx_deg}, roty={roty_deg}, rotz={rotz_deg}, twotheta={twotheta_deg}")
print(f"Rotation angles (radians): rotx={rotx:.6f}, roty={roty:.6f}, rotz={rotz:.6f}, twotheta={twotheta:.6f}")

# Apply XYZ rotations using our function
rotation_matrix = angles_to_rotation_matrix(rotx, roty, rotz)
print(f"\nRotation matrix from angles_to_rotation_matrix:")
print(rotation_matrix)

# Apply rotation to vectors
fdet_rotated = torch.matmul(rotation_matrix, fdet_vec)
sdet_rotated = torch.matmul(rotation_matrix, sdet_vec)
odet_rotated = torch.matmul(rotation_matrix, odet_vec)

print(f"\nAfter XYZ rotations:")
print(f"fdet: {fdet_rotated}")
print(f"sdet: {sdet_rotated}")
print(f"odet: {odet_rotated}")

# Apply two-theta rotation around Y axis
twotheta_axis = torch.tensor([0.0, 1.0, 0.0], dtype=torch.float64)
fdet_final = rotate_axis(fdet_rotated, twotheta_axis, twotheta)
sdet_final = rotate_axis(sdet_rotated, twotheta_axis, twotheta)
odet_final = rotate_axis(odet_rotated, twotheta_axis, twotheta)

print(f"\nAfter two-theta rotation around Y axis:")
print(f"fdet: {fdet_final}")
print(f"sdet: {sdet_final}")
print(f"odet: {odet_final}")

# Expected values from C-code
print(f"\nExpected C-code values:")
print(f"fdet: [0.0311947630447082, -0.096650175316428, 0.994829447880333]")
print(f"sdet: [-0.228539518954453, -0.969636205471835, -0.0870362988312832]")
print(f"odet: [0.973034724475264, -0.224642766741965, -0.0523359562429438]")

# Check differences
c_fdet = torch.tensor([0.0311947630447082, -0.096650175316428, 0.994829447880333], dtype=torch.float64)
c_sdet = torch.tensor([-0.228539518954453, -0.969636205471835, -0.0870362988312832], dtype=torch.float64)
c_odet = torch.tensor([0.973034724475264, -0.224642766741965, -0.0523359562429438], dtype=torch.float64)

print(f"\nDifferences (PyTorch - C):")
print(f"fdet diff: {fdet_final - c_fdet}")
print(f"sdet diff: {sdet_final - c_sdet}")
print(f"odet diff: {odet_final - c_odet}")
print(f"\nMax absolute differences:")
print(f"fdet: {torch.max(torch.abs(fdet_final - c_fdet)):.2e}")
print(f"sdet: {torch.max(torch.abs(sdet_final - c_sdet)):.2e}")
print(f"odet: {torch.max(torch.abs(odet_final - c_odet)):.2e}")

print(f"\n\nDifferences after XYZ only (no two-theta):")
print(f"fdet diff: {fdet_rotated - c_fdet}")
print(f"Max: {torch.max(torch.abs(fdet_rotated - c_fdet)):.2e}")