#!/usr/bin/env python3
"""
Verify the rotation by reconstructing the unitary matrix from misset angles.
This tests if the umat2misset -> rotate sequence preserves the rotation.
"""

import numpy as np

# Misset angles from misset_angles.txt (in degrees)
misset_deg = [-89.968546, -31.328953, 177.753396]
misset_rad = [angle * np.pi / 180.0 for angle in misset_deg]
phix, phiy, phiz = misset_rad

# Unrotated reciprocal vectors from unrotated_vectors.txt
a_star_unrot = np.array([0.01428571, 0.00124984, -0.00164578])
b_star_unrot = np.array([0.00000000, 0.01254775, -0.00349686])
c_star_unrot = np.array([0.00000000, -0.00000000, 0.01157858])

# Expected rotated vectors from trace.log
a_star_expected = np.array([-0.01232259, 0.00048342, 0.00750655])
b_star_expected = np.array([-0.00799159, 0.00030641, -0.01028210])
c_star_expected = np.array([0.00223446, -0.01120794, 0.00185723])

# Let's try to find the unitary matrix directly by solving for it
# We have: rotated = U @ unrotated
# So: U = rotated @ unrotated^T @ (unrotated @ unrotated^T)^-1

# Stack vectors as columns
unrot_matrix = np.column_stack([a_star_unrot, b_star_unrot, c_star_unrot])
expected_matrix = np.column_stack([a_star_expected, b_star_expected, c_star_expected])

# Calculate the rotation matrix directly
# U @ unrot_matrix = expected_matrix
# U = expected_matrix @ inv(unrot_matrix)
U_direct = expected_matrix @ np.linalg.inv(unrot_matrix)

print("Direct calculation of rotation matrix from vectors:")
print("=" * 60)
print("\nRotation matrix U (calculated from vectors):")
for i, row in enumerate(U_direct):
    print(f"  [{row[0]:10.6f}, {row[1]:10.6f}, {row[2]:10.6f}]")

# Check if it's unitary (orthogonal)
U_U_T = U_direct @ U_direct.T
print("\nU @ U^T (should be identity):")
for i, row in enumerate(U_U_T):
    print(f"  [{row[0]:10.6f}, {row[1]:10.6f}, {row[2]:10.6f}]")

det = np.linalg.det(U_direct)
print(f"\nDeterminant of U: {det:.6f} (should be 1 or -1)")

# Now let's verify by applying this matrix
a_star_check = U_direct @ a_star_unrot
b_star_check = U_direct @ b_star_unrot  
c_star_check = U_direct @ c_star_unrot

print("\nVerification - applying U to unrotated vectors:")
print(f"a* calculated: [{a_star_check[0]:.8f}, {a_star_check[1]:.8f}, {a_star_check[2]:.8f}]")
print(f"a* expected:   [{a_star_expected[0]:.8f}, {a_star_expected[1]:.8f}, {a_star_expected[2]:.8f}]")
print(f"b* calculated: [{b_star_check[0]:.8f}, {b_star_check[1]:.8f}, {b_star_check[2]:.8f}]")
print(f"b* expected:   [{b_star_expected[0]:.8f}, {b_star_expected[1]:.8f}, {b_star_expected[2]:.8f}]")
print(f"c* calculated: [{c_star_check[0]:.8f}, {c_star_check[1]:.8f}, {c_star_check[2]:.8f}]")
print(f"c* expected:   [{c_star_expected[0]:.8f}, {c_star_expected[1]:.8f}, {c_star_expected[2]:.8f}]")

# Now let's try to reconstruct the misset angles from this matrix
# This is reverse-engineering the umat2misset function
# Based on the rotation order X-Y-Z, we have:
# U = Rz @ Ry @ Rx
# We need to extract phix, phiy, phiz

# For a ZYX Euler angle decomposition:
# If U = Rz @ Ry @ Rx, then we can extract angles as:
# sin(phiy) = -U[2,0]
# If cos(phiy) != 0:
#   phix = atan2(U[2,1], U[2,2])
#   phiz = atan2(U[1,0], U[0,0])

print("\n" + "="*60)
print("Attempting to extract Euler angles from rotation matrix:")

# Extract angles (assuming X-Y-Z rotation order)
# U = Rz @ Ry @ Rx
# This is a complex decomposition - there might be multiple solutions

# One possible extraction (there are singularities to handle)
sin_y = U_direct[0, 2]  # For X-Y-Z order, this is sin(phiy)
if abs(sin_y) < 0.99999:  # Not at gimbal lock
    phiy_extracted = np.arcsin(sin_y)
    cos_y = np.cos(phiy_extracted)
    phix_extracted = np.arctan2(-U_direct[1, 2]/cos_y, U_direct[2, 2]/cos_y)
    phiz_extracted = np.arctan2(-U_direct[0, 1]/cos_y, U_direct[0, 0]/cos_y)
else:
    # Gimbal lock case
    print("Warning: Near gimbal lock!")
    phiy_extracted = np.pi/2 if sin_y > 0 else -np.pi/2
    phix_extracted = 0
    phiz_extracted = np.arctan2(U_direct[1, 0], U_direct[1, 1])

print(f"\nExtracted angles (radians): phix={phix_extracted:.6f}, phiy={phiy_extracted:.6f}, phiz={phiz_extracted:.6f}")
print(f"Extracted angles (degrees): phix={phix_extracted*180/np.pi:.6f}, phiy={phiy_extracted*180/np.pi:.6f}, phiz={phiz_extracted*180/np.pi:.6f}")
print(f"Original angles (degrees):  phix={misset_deg[0]:.6f}, phiy={misset_deg[1]:.6f}, phiz={misset_deg[2]:.6f}")

# The key insight: the C code likely generates a random unitary matrix first,
# then extracts Euler angles from it. The conversion might not be perfectly
# reversible due to multiple valid Euler angle representations for the same rotation.