#!/usr/bin/env python3
"""
Verify the rotation of reciprocal vectors for the triclinic test case.
This implements the exact rotation sequence from nanoBragg.c
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


def rotate_xyz(v, phix, phiy, phiz):
    """
    Apply rotation in X-Y-Z order as done in nanoBragg.c rotate() function.

    From nanoBragg.c lines 3295-3344:
    - First rotate around X axis
    - Then rotate around Y axis
    - Finally rotate around Z axis
    """
    new_v = v.copy()

    # Rotate around X axis
    if phix != 0:
        Rx = np.array(
            [
                [1, 0, 0],
                [0, np.cos(phix), -np.sin(phix)],
                [0, np.sin(phix), np.cos(phix)],
            ]
        )
        new_v = Rx @ new_v

    # Rotate around Y axis
    if phiy != 0:
        Ry = np.array(
            [
                [np.cos(phiy), 0, np.sin(phiy)],
                [0, 1, 0],
                [-np.sin(phiy), 0, np.cos(phiy)],
            ]
        )
        new_v = Ry @ new_v

    # Rotate around Z axis
    if phiz != 0:
        Rz = np.array(
            [
                [np.cos(phiz), -np.sin(phiz), 0],
                [np.sin(phiz), np.cos(phiz), 0],
                [0, 0, 1],
            ]
        )
        new_v = Rz @ new_v

    return new_v


# Apply rotation to each vector
a_star_rot = rotate_xyz(a_star_unrot, phix, phiy, phiz)
b_star_rot = rotate_xyz(b_star_unrot, phix, phiy, phiz)
c_star_rot = rotate_xyz(c_star_unrot, phix, phiy, phiz)

print("Rotation verification for triclinic test case")
print("=" * 60)
print(
    f"\nMisset angles: {misset_deg[0]:.6f}, {misset_deg[1]:.6f}, {misset_deg[2]:.6f} degrees"
)
print(f"In radians: {phix:.8f}, {phiy:.8f}, {phiz:.8f}")

print("\n1. Unrotated reciprocal vectors:")
print(f"   a* = [{a_star_unrot[0]:.8f}, {a_star_unrot[1]:.8f}, {a_star_unrot[2]:.8f}]")
print(f"   b* = [{b_star_unrot[0]:.8f}, {b_star_unrot[1]:.8f}, {b_star_unrot[2]:.8f}]")
print(f"   c* = [{c_star_unrot[0]:.8f}, {c_star_unrot[1]:.8f}, {c_star_unrot[2]:.8f}]")

print("\n2. Expected rotated vectors (from trace.log):")
print(
    f"   a* = [{a_star_expected[0]:.8f}, {a_star_expected[1]:.8f}, {a_star_expected[2]:.8f}]"
)
print(
    f"   b* = [{b_star_expected[0]:.8f}, {b_star_expected[1]:.8f}, {b_star_expected[2]:.8f}]"
)
print(
    f"   c* = [{c_star_expected[0]:.8f}, {c_star_expected[1]:.8f}, {c_star_expected[2]:.8f}]"
)

print("\n3. Our calculated rotated vectors:")
print(f"   a* = [{a_star_rot[0]:.8f}, {a_star_rot[1]:.8f}, {a_star_rot[2]:.8f}]")
print(f"   b* = [{b_star_rot[0]:.8f}, {b_star_rot[1]:.8f}, {b_star_rot[2]:.8f}]")
print(f"   c* = [{c_star_rot[0]:.8f}, {c_star_rot[1]:.8f}, {c_star_rot[2]:.8f}]")

print("\n4. Differences (calculated - expected):")
print(
    f"   Δa* = [{a_star_rot[0]-a_star_expected[0]:.2e}, {a_star_rot[1]-a_star_expected[1]:.2e}, {a_star_rot[2]-a_star_expected[2]:.2e}]"
)
print(
    f"   Δb* = [{b_star_rot[0]-b_star_expected[0]:.2e}, {b_star_rot[1]-b_star_expected[1]:.2e}, {b_star_rot[2]-b_star_expected[2]:.2e}]"
)
print(
    f"   Δc* = [{c_star_rot[0]-c_star_expected[0]:.2e}, {c_star_rot[1]-c_star_expected[1]:.2e}, {c_star_rot[2]-c_star_expected[2]:.2e}]"
)

# Check if we match within numerical precision
tolerance = 1e-8
matches = True
for name, calc, expected in [
    ("a*", a_star_rot, a_star_expected),
    ("b*", b_star_rot, b_star_expected),
    ("c*", c_star_rot, c_star_expected),
]:
    if not np.allclose(calc, expected, atol=tolerance):
        matches = False
        print(f"\n⚠️  {name} does not match within tolerance {tolerance}")
    else:
        print(f"\n✓ {name} matches within tolerance")

if matches:
    print("\n✅ All vectors match! The rotation is correctly implemented.")
else:
    print(
        "\n❌ Vectors do not match. There may be an issue with the rotation implementation."
    )

# Let's also check the combined rotation matrix
print("\n5. Combined rotation matrix (R = Rz @ Ry @ Rx):")
Rx = np.array(
    [[1, 0, 0], [0, np.cos(phix), -np.sin(phix)], [0, np.sin(phix), np.cos(phix)]]
)
Ry = np.array(
    [[np.cos(phiy), 0, np.sin(phiy)], [0, 1, 0], [-np.sin(phiy), 0, np.cos(phiy)]]
)
Rz = np.array(
    [[np.cos(phiz), -np.sin(phiz), 0], [np.sin(phiz), np.cos(phiz), 0], [0, 0, 1]]
)
R_combined = Rz @ Ry @ Rx
print("R =")
for row in R_combined:
    print(f"    [{row[0]:10.6f}, {row[1]:10.6f}, {row[2]:10.6f}]")
