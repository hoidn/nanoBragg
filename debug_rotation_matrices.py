import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from src.nanobrag_torch.models.detector import Detector
import torch
import numpy as np

# Match exact C configuration  
config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024, 
    beam_center_s=51.2,  # mm
    beam_center_f=51.2,  # mm
    detector_rotx_deg=5.0,
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=15.0,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM
)

detector = Detector(config)

# Get the combined rotation matrix from detector
# The detector should have computed the total rotation matrix
print("Python R_total matrix:")
# We need to look at how the detector computes the combined rotation
# Let's access the rotation components

from src.nanobrag_torch.utils.units import degrees_to_radians
import torch

# Compute individual rotation matrices manually
rotx_rad = degrees_to_radians(torch.tensor(5.0))
roty_rad = degrees_to_radians(torch.tensor(3.0))
rotz_rad = degrees_to_radians(torch.tensor(2.0))
twotheta_rad = degrees_to_radians(torch.tensor(15.0))

print(f"Rotation angles (radians):")
print(f"  rotx: {rotx_rad}")
print(f"  roty: {roty_rad}") 
print(f"  rotz: {rotz_rad}")
print(f"  twotheta: {twotheta_rad}")

# Build individual matrices like detector does
Rx = torch.tensor([
    [1, 0, 0],
    [0, torch.cos(rotx_rad), -torch.sin(rotx_rad)],
    [0, torch.sin(rotx_rad), torch.cos(rotx_rad)]
], dtype=torch.float64)

Ry = torch.tensor([
    [torch.cos(roty_rad), 0, torch.sin(roty_rad)],
    [0, 1, 0],
    [-torch.sin(roty_rad), 0, torch.cos(roty_rad)]
], dtype=torch.float64)

Rz = torch.tensor([
    [torch.cos(rotz_rad), -torch.sin(rotz_rad), 0],
    [torch.sin(rotz_rad), torch.cos(rotz_rad), 0], 
    [0, 0, 1]
], dtype=torch.float64)

# Two-theta rotation around Z-axis for MOSFLM
Rtwotheta = torch.tensor([
    [torch.cos(twotheta_rad), -torch.sin(twotheta_rad), 0],
    [torch.sin(twotheta_rad), torch.cos(twotheta_rad), 0],
    [0, 0, 1]
], dtype=torch.float64)

print(f"\nIndividual matrices:")
print(f"Rx:\n{Rx}")
print(f"Ry:\n{Ry}")
print(f"Rz:\n{Rz}")
print(f"Rtwotheta:\n{Rtwotheta}")

# Try different composition orders
R_xyz_twotheta = Rtwotheta @ Rz @ Ry @ Rx
R_zyx_twotheta = Rtwotheta @ Rx @ Ry @ Rz

print(f"\nPython composition order 1 (twotheta @ z @ y @ x):")
print(R_xyz_twotheta)

print(f"\nPython composition order 2 (twotheta @ x @ y @ z):")  
print(R_zyx_twotheta)

# From trace - C R_total matrix
c_matrix = np.array([
    [0.998021196624068, -0.0302080931112661,  0.0551467333542405],
    [0.0348516681551873,  0.99574703303416,   -0.0852831016700733],
    [-0.0523359562429438, 0.0870362988312832,  0.994829447880333]
])

print(f"\nC R_total matrix:")
print(c_matrix)

# Check which Python order matches C
diff1 = np.abs(R_xyz_twotheta.numpy() - c_matrix)
diff2 = np.abs(R_zyx_twotheta.numpy() - c_matrix)

print(f"\nDifference from C (order 1 - twotheta @ z @ y @ x):")
print(f"Max diff: {np.max(diff1):.2e}")

print(f"\nDifference from C (order 2 - twotheta @ x @ y @ z):")
print(f"Max diff: {np.max(diff2):.2e}")

if np.max(diff1) < 1e-10:
    print("✅ ORDER 1 MATCHES C")
elif np.max(diff2) < 1e-10:
    print("✅ ORDER 2 MATCHES C")
else:
    print("❌ NEITHER ORDER MATCHES C - need to investigate composition")