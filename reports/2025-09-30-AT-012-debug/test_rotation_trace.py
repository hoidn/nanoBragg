#!/usr/bin/env python3
"""
Trace rotation application step-by-step and compare with C.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import sys
sys.path.insert(0, '/home/ollie/Documents/nanoBragg/src')

from nanobrag_torch.utils.geometry import angles_to_rotation_matrix

# Triclinic P1 misset angles
misset_deg = [-89.968546, -31.328953, 177.753396]
misset_rad = [torch.deg2rad(torch.tensor(a, dtype=torch.float64)) for a in misset_deg]

print(f"Misset angles (deg): {misset_deg}")
print(f"Misset angles (rad): [{misset_rad[0].item():.12f}, {misset_rad[1].item():.12f}, {misset_rad[2].item():.12f}]")
print()

# Build rotation matrix
R = angles_to_rotation_matrix(misset_rad[0], misset_rad[1], misset_rad[2])

print("Rotation matrix R:")
for i in range(3):
    print(f"  [{R[i,0]:20.15f} {R[i,1]:20.15f} {R[i,2]:20.15f}]")
print()

# Test on the initial a_star vector from C trace
# From FIRST_DIVERGENCE.md: Before misset = [0.0144344, 0, 0]
a_star_init = torch.tensor([0.0144344, 0.0, 0.0], dtype=torch.float64)

# Apply rotation
a_star_rotated = torch.matmul(R, a_star_init)

print(f"Initial a_star:  [{a_star_init[0]:.10f}, {a_star_init[1]:.10f}, {a_star_init[2]:.10f}]")
print(f"Rotated a_star:  [{a_star_rotated[0]:.10f}, {a_star_rotated[1]:.10f}, {a_star_rotated[2]:.10f}]")
print()

# Expected from C (from FIRST_DIVERGENCE.md):
# After rotation: [-0.0123203, 0.000483336, 0.00750519]
c_expected = torch.tensor([-0.0123203, 0.000483336, 0.00750519], dtype=torch.float64)
diff = a_star_rotated - c_expected
print(f"C expected:      [{c_expected[0]:.10f}, {c_expected[1]:.10f}, {c_expected[2]:.10f}]")
print(f"Difference:      [{diff[0]:.10f}, {diff[1]:.10f}, {diff[2]:.10f}]")
print(f"Rel error (%):   [{abs(diff[0]/c_expected[0]*100):.4f}, {abs(diff[1]/c_expected[1]*100):.4f}, {abs(diff[2]/c_expected[2]*100):.4f}]")
