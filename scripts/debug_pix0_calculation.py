#!/usr/bin/env python3
"""Debug pix0_vector calculation to understand the C-code logic."""

import numpy as np

# Values from trace
distance = 0.0974964  # meters (adjusted)
Xbeam = 0.0612  # meters
Ybeam = 0.0612  # meters
pixel_size = 0.0001  # meters
Fbeam = 0.0611719  # meters (expected: Ybeam + 0.5*pixel for MOSFLM)
Sbeam = 0.0618222  # meters (expected: Xbeam + 0.5*pixel for MOSFLM)

# Detector vectors from C-code (after rotations)
fdet = np.array([0.0311947630447082, -0.096650175316428, 0.994829447880333])
sdet = np.array([-0.228539518954453, -0.969636205471835, -0.0870362988312832])
odet = np.array([0.973034724475264, -0.224642766741965, -0.0523359562429438])

# Beam vector for MOSFLM
beam_vector = np.array([1.0, 0.0, 0.0])

# Expected pix0_vector from C-code
c_pix0 = np.array([0.112087366299472, 0.0653100408232811, -0.0556023303792543])

print("Values from trace:")
print(f"distance = {distance} m")
print(f"Xbeam = {Xbeam} m, Ybeam = {Ybeam} m")
print(f"Fbeam = {Fbeam} m, Sbeam = {Sbeam} m")
print(f"pixel_size = {pixel_size} m")

print("\nChecking MOSFLM formula:")
print(f"Expected Fbeam = Ybeam + 0.5*pixel = {Ybeam} + {0.5*pixel_size} = {Ybeam + 0.5*pixel_size}")
print(f"Actual Fbeam = {Fbeam}")
print(f"Difference = {Fbeam - (Ybeam + 0.5*pixel_size)}")

print(f"\nExpected Sbeam = Xbeam + 0.5*pixel = {Xbeam} + {0.5*pixel_size} = {Xbeam + 0.5*pixel_size}")
print(f"Actual Sbeam = {Sbeam}")
print(f"Difference = {Sbeam - (Xbeam + 0.5*pixel_size)}")

# Let's see if there's a pattern
print("\nAnalyzing the differences:")
print(f"Fbeam - Ybeam = {Fbeam - Ybeam} (expected: {0.5*pixel_size})")
print(f"Sbeam - Xbeam = {Sbeam - Xbeam} (expected: {0.5*pixel_size})")

# Calculate pix0_vector using BEAM pivot formula
pix0_calc = -Fbeam * fdet - Sbeam * sdet + distance * beam_vector

print("\nCalculated pix0_vector:")
print(f"pix0 = -Fbeam*fdet - Sbeam*sdet + distance*beam")
print(f"     = -{Fbeam}*{fdet} - {Sbeam}*{sdet} + {distance}*{beam_vector}")
print(f"     = {pix0_calc}")

print(f"\nExpected from C-code: {c_pix0}")
print(f"Difference: {np.linalg.norm(pix0_calc - c_pix0)}")

# Check individual components
print("\nComponent breakdown:")
print(f"-Fbeam*fdet = {-Fbeam * fdet}")
print(f"-Sbeam*sdet = {-Sbeam * sdet}")
print(f"distance*beam = {distance * beam_vector}")

# Maybe check if there's a conversion factor?
print("\nChecking if Fbeam/Sbeam use adjusted coordinates:")
# In MOSFLM, beam center is swapped: Fbeam uses Y, Sbeam uses X
# Also check with original distance
orig_distance = 0.1  # meters
print(f"\nOriginal distance = {orig_distance} m")

# Check different beam center calculations
print("\nTrying different formulas:")

# Direct assignment (matching trace values)
Fbeam_trace = 0.0611719
Sbeam_trace = 0.0618222
pix0_trace = -Fbeam_trace * fdet - Sbeam_trace * sdet + distance * beam_vector
print(f"\nUsing trace values directly:")
print(f"pix0 = {pix0_trace}")
print(f"Match? {np.allclose(pix0_trace, c_pix0, atol=1e-9)}")

# Try understanding the 'odd' values
# Fbeam should be 0.06125 but is 0.0611719
# Difference is -0.0000781
# Sbeam should be 0.06125 but is 0.0618222  
# Difference is 0.0005722

print("\nAnalyzing trace value patterns:")
print(f"Fbeam deficit: {0.06125 - Fbeam_trace}")
print(f"Sbeam excess: {Sbeam_trace - 0.06125}")

# Maybe there's a pixel indexing offset?
# MOSFLM uses 0.5,0.5 as first pixel center
print("\nChecking MOSFLM pixel convention:")
# From C-code comment: "first pixel is at 0.5,0.5 pix and pixel_size/2,pixel_size/2 mm"