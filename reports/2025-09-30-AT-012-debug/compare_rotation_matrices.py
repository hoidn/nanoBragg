#!/usr/bin/env python3
"""
Compare rotation matrices between C and PyTorch for triclinic misset case.
This addresses AT-012 plan tasks A1-A3.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import sys
sys.path.insert(0, '/home/ollie/Documents/nanoBragg/src')

from nanobrag_torch.utils.geometry import angles_to_rotation_matrix

# Triclinic P1 misset angles from AT-012
misset_angles_deg = [-89.968546, -31.328953, 177.753396]
print(f"Misset angles (degrees): {misset_angles_deg}")
print()

# Convert to radians
misset_rad = [torch.deg2rad(torch.tensor(angle, dtype=torch.float64))
              for angle in misset_angles_deg]

# Compute PyTorch rotation matrix
R_pytorch = angles_to_rotation_matrix(misset_rad[0], misset_rad[1], misset_rad[2])

print("PyTorch Rotation Matrix (angles_to_rotation_matrix):")
print(f"R[0,:] = [{R_pytorch[0,0]:.10f}, {R_pytorch[0,1]:.10f}, {R_pytorch[0,2]:.10f}]")
print(f"R[1,:] = [{R_pytorch[1,0]:.10f}, {R_pytorch[1,1]:.10f}, {R_pytorch[1,2]:.10f}]")
print(f"R[2,:] = [{R_pytorch[2,0]:.10f}, {R_pytorch[2,1]:.10f}, {R_pytorch[2,2]:.10f}]")
print()

# Compute determinant
det = torch.det(R_pytorch)
print(f"Determinant: {det:.15f}")
print()

# Check orthonormality
RTR = torch.matmul(R_pytorch.T, R_pytorch)
I = torch.eye(3, dtype=torch.float64)
ortho_error = torch.max(torch.abs(RTR - I))
print(f"Orthonormality check (max|R^T*R - I|): {ortho_error:.2e}")
print()

# Test on a simple vector
test_vec = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
rotated = torch.matmul(R_pytorch, test_vec)
print(f"Test: Rotate [1,0,0] -> [{rotated[0]:.10f}, {rotated[1]:.10f}, {rotated[2]:.10f}]")
print()

print("="*70)
print("To get C rotation matrix, add instrumentation to nanoBragg.c:")
print("After line 2034 (rotate calls for misset), add:")
print('    printf("C_ROTATION_MATRIX_ROW0: %.15f %.15f %.15f\\n", ...');
print("Then rebuild and run the C binary with the triclinic parameters.")
print("="*70)
