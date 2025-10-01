#!/usr/bin/env python3
"""Implement C-code rotation logic exactly to debug differences."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from math import cos, sin, pi

def rotate_c_style(v, phix, phiy, phiz):
    """Implement the C-code's rotate function exactly."""
    # C-code uses 1-indexed arrays, we'll use 0-indexed
    new_x = v[0]
    new_y = v[1]
    new_z = v[2]
    
    if phix != 0:
        # rotate around x axis
        ryy = cos(phix)
        ryz = -sin(phix)
        rzy = sin(phix)
        rzz = cos(phix)
        
        rotated_x = new_x
        rotated_y = new_y*ryy + new_z*ryz
        rotated_z = new_y*rzy + new_z*rzz
        new_x = rotated_x
        new_y = rotated_y
        new_z = rotated_z
    
    if phiy != 0:
        # rotate around y axis
        rxx = cos(phiy)
        rxz = sin(phiy)
        rzx = -sin(phiy)
        rzz = cos(phiy)
        
        rotated_x = new_x*rxx + new_z*rxz
        rotated_y = new_y
        rotated_z = new_x*rzx + new_z*rzz
        new_x = rotated_x
        new_y = rotated_y
        new_z = rotated_z
    
    if phiz != 0:
        # rotate around z axis
        rxx = cos(phiz)
        rxy = -sin(phiz)
        ryx = sin(phiz)
        ryy = cos(phiz)
        
        rotated_x = new_x*rxx + new_y*rxy
        rotated_y = new_x*ryx + new_y*ryy
        rotated_z = new_z
        new_x = rotated_x
        new_y = rotated_y
        new_z = rotated_z
    
    return [new_x, new_y, new_z]

def rotate_axis_c_style(v, axis, phi):
    """Implement the C-code's rotate_axis function (Rodrigues' formula)."""
    sinphi = sin(phi)
    cosphi = cos(phi)
    dot = (axis[0]*v[0] + axis[1]*v[1] + axis[2]*v[2]) * (1.0 - cosphi)
    
    # Cross product components
    cross_x = axis[1]*v[2] - axis[2]*v[1]
    cross_y = axis[2]*v[0] - axis[0]*v[2]
    cross_z = axis[0]*v[1] - axis[1]*v[0]
    
    new_x = v[0]*cosphi + cross_x*sinphi + axis[0]*dot
    new_y = v[1]*cosphi + cross_y*sinphi + axis[1]*dot
    new_z = v[2]*cosphi + cross_z*sinphi + axis[2]*dot
    
    return [new_x, new_y, new_z]

# Initial MOSFLM vectors
fdet_vec = [0.0, 0.0, 1.0]
sdet_vec = [0.0, -1.0, 0.0]
odet_vec = [1.0, 0.0, 0.0]

print("Initial vectors (MOSFLM convention):")
print(f"fdet: {fdet_vec}")
print(f"sdet: {sdet_vec}")
print(f"odet: {odet_vec}")

# Rotation angles (convert to radians)
rotx = 5.0 * pi / 180.0
roty = 3.0 * pi / 180.0
rotz = 2.0 * pi / 180.0
twotheta = 15.0 * pi / 180.0

# Apply XYZ rotations
fdet_vec = rotate_c_style(fdet_vec, rotx, roty, rotz)
sdet_vec = rotate_c_style(sdet_vec, rotx, roty, rotz)
odet_vec = rotate_c_style(odet_vec, rotx, roty, rotz)

print(f"\nAfter XYZ rotations:")
print(f"fdet: {fdet_vec}")
print(f"sdet: {sdet_vec}")
print(f"odet: {odet_vec}")

# Apply two-theta rotation around Y axis
twotheta_axis = [0.0, 1.0, 0.0]
fdet_vec = rotate_axis_c_style(fdet_vec, twotheta_axis, twotheta)
sdet_vec = rotate_axis_c_style(sdet_vec, twotheta_axis, twotheta)
odet_vec = rotate_axis_c_style(odet_vec, twotheta_axis, twotheta)

print(f"\nAfter two-theta rotation:")
print(f"fdet: {fdet_vec}")
print(f"sdet: {sdet_vec}")
print(f"odet: {odet_vec}")

# Expected values from C-code
print(f"\nExpected C-code values:")
print(f"fdet: [0.0311947630447082, -0.096650175316428, 0.994829447880333]")
print(f"sdet: [-0.228539518954453, -0.969636205471835, -0.0870362988312832]") 
print(f"odet: [0.973034724475264, -0.224642766741965, -0.0523359562429438]")

# Check differences
c_fdet = [0.0311947630447082, -0.096650175316428, 0.994829447880333]
c_sdet = [-0.228539518954453, -0.969636205471835, -0.0870362988312832]
c_odet = [0.973034724475264, -0.224642766741965, -0.0523359562429438]

print(f"\nDifferences (Python - C):")
print(f"fdet: [{fdet_vec[0]-c_fdet[0]:.6f}, {fdet_vec[1]-c_fdet[1]:.6f}, {fdet_vec[2]-c_fdet[2]:.6f}]")
print(f"sdet: [{sdet_vec[0]-c_sdet[0]:.6f}, {sdet_vec[1]-c_sdet[1]:.6f}, {sdet_vec[2]-c_sdet[2]:.6f}]")
print(f"odet: [{odet_vec[0]-c_odet[0]:.6f}, {odet_vec[1]-c_odet[1]:.6f}, {odet_vec[2]-c_odet[2]:.6f}]")