#!/usr/bin/env python3
"""
Calculate the exact difference between C and Python pix0_vector calculations.
"""
import numpy as np

# Values from traces
c_pix0 = np.array([0.114852723866983, 0.0536099933640348, -0.0465697885462163])
py_pix0 = np.array([0.0979762214638082, 0.00559973608567561, -0.00426756092015474])

# Calculate difference
diff = c_pix0 - py_pix0
diff_magnitude = np.linalg.norm(diff)

print("=== PIX0_VECTOR DIFFERENCE ANALYSIS ===")
print(f"C  pix0_vector: [{c_pix0[0]:.15g}, {c_pix0[1]:.15g}, {c_pix0[2]:.15g}]")
print(f"Py pix0_vector: [{py_pix0[0]:.15g}, {py_pix0[1]:.15g}, {py_pix0[2]:.15g}]")
print(f"Difference:     [{diff[0]:.15g}, {diff[1]:.15g}, {diff[2]:.15g}]")
print(f"Difference magnitude: {diff_magnitude:.15g}")

# Convert to mm for easier interpretation
diff_mm = diff * 1000  # Convert from meters to mm
diff_magnitude_mm = diff_magnitude * 1000

print(f"\nIn millimeters:")
print(f"Difference:     [{diff_mm[0]:.6f}, {diff_mm[1]:.6f}, {diff_mm[2]:.6f}] mm")
print(f"Difference magnitude: {diff_magnitude_mm:.6f} mm")

# Check which axis shows the largest error
max_axis = np.argmax(np.abs(diff))
axis_names = ['X', 'Y', 'Z']
print(f"\nLargest difference is in {axis_names[max_axis]} axis: {diff[max_axis]:.15g} m ({diff_mm[max_axis]:.6f} mm)")

# Compare to target problem (28mm offset)
print(f"\nTarget problem magnitude was 28mm")
print(f"Current error magnitude is {diff_magnitude_mm:.6f} mm")
print(f"This is {diff_magnitude_mm/28.0:.2%} of the target problem")
