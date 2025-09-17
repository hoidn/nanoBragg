#!/usr/bin/env python3
"""Test to understand the rotation order and twotheta application."""

import os
import sys
import torch
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector

# Set environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def print_detector_state(detector, label):
    """Print detector state for debugging."""
    print(f"\n{label}:")
    print(f"  fdet_vec: {detector.fdet_vec.numpy()}")
    print(f"  sdet_vec: {detector.sdet_vec.numpy()}")
    print(f"  odet_vec: {detector.odet_vec.numpy()}")
    print(f"  pix0_vector (m): {(detector.pix0_vector / 1e10).numpy()}")

# Test configuration matching the tilted case
config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=61.2,
    beam_center_f=61.2,
    detector_convention=DetectorConvention.MOSFLM,
    detector_rotx_deg=5.0,
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=15.0,
    detector_pivot=DetectorPivot.SAMPLE,
)

print("Testing detector rotation order")
print("="*60)

# Create detector
detector = Detector(config=config, device=torch.device("cpu"), dtype=torch.float64)
print_detector_state(detector, "After full rotation")

# Now let's trace through the rotation manually
print("\n" + "="*60)
print("Manual rotation trace:")

# Initial basis vectors (MOSFLM convention)
fdet_initial = torch.tensor([0., 0., 1.], dtype=torch.float64)
sdet_initial = torch.tensor([0., -1., 0.], dtype=torch.float64)
odet_initial = torch.tensor([1., 0., 0.], dtype=torch.float64)

print(f"\nInitial basis vectors:")
print(f"  fdet: {fdet_initial.numpy()}")
print(f"  sdet: {sdet_initial.numpy()}")
print(f"  odet: {odet_initial.numpy()}")

# Apply rotations in order (from detector._calculate_basis_vectors)
from nanobrag_torch.utils.geometry import rotate_around_x, rotate_around_y, rotate_around_z

# Convert degrees to radians
rotx_rad = np.radians(config.detector_rotx_deg)
roty_rad = np.radians(config.detector_roty_deg)
rotz_rad = np.radians(config.detector_rotz_deg)
twotheta_rad = np.radians(config.detector_twotheta_deg)

# Apply rotx, roty, rotz
fdet = rotate_around_x(fdet_initial, rotx_rad)
fdet = rotate_around_y(fdet, roty_rad)
fdet = rotate_around_z(fdet, rotz_rad)

sdet = rotate_around_x(sdet_initial, rotx_rad)
sdet = rotate_around_y(sdet, roty_rad)
sdet = rotate_around_z(sdet, rotz_rad)

odet = rotate_around_x(odet_initial, rotx_rad)
odet = rotate_around_y(odet, roty_rad)
odet = rotate_around_z(odet, rotz_rad)

print(f"\nAfter rotx, roty, rotz:")
print(f"  fdet: {fdet.numpy()}")
print(f"  sdet: {sdet.numpy()}")
print(f"  odet: {odet.numpy()}")

# Apply twotheta rotation
# The C code rotates around twotheta_axis which defaults to [0, 0, -1]
twotheta_axis = config.twotheta_axis if config.twotheta_axis is not None else torch.tensor([0., 0., -1.], dtype=torch.float64)

# Import rotation around axis function
from nanobrag_torch.utils.geometry import rodrigues_rotation

fdet_final = rodrigues_rotation(fdet, twotheta_axis, twotheta_rad)
sdet_final = rodrigues_rotation(sdet, twotheta_axis, twotheta_rad)
odet_final = rodrigues_rotation(odet, twotheta_axis, twotheta_rad)

print(f"\nAfter twotheta rotation (axis={twotheta_axis.numpy()}, angle={np.degrees(twotheta_rad)}°):")
print(f"  fdet: {fdet_final.numpy()}")
print(f"  sdet: {sdet_final.numpy()}")
print(f"  odet: {odet_final.numpy()}")

# Compare with detector's calculated values
print(f"\nDifference from Detector class calculation:")
print(f"  fdet diff: {np.max(np.abs(fdet_final.numpy() - detector.fdet_vec.numpy())):.2e}")
print(f"  sdet diff: {np.max(np.abs(sdet_final.numpy() - detector.sdet_vec.numpy())):.2e}")
print(f"  odet diff: {np.max(np.abs(odet_final.numpy() - detector.odet_vec.numpy())):.2e}")

# Check pix0_vector calculation for SAMPLE pivot
# For SAMPLE pivot, pix0_vector is calculated differently
print(f"\n" + "="*60)
print("Checking pix0_vector calculation (SAMPLE pivot):")

# Get pixel coordinate at (377, 644) - the brightest spot
pixel_coords = detector.get_pixel_coords()
pixel_377_644 = pixel_coords[377, 644]
print(f"\nPixel (377, 644) coordinates:")
print(f"  In meters: {pixel_377_644.numpy()}")
print(f"  In Angstroms: {(pixel_377_644 * 1e10).numpy()}")

# Also check pixel (0,0) 
pixel_0_0 = pixel_coords[0, 0]
print(f"\nPixel (0, 0) coordinates:")
print(f"  In meters: {pixel_0_0.numpy()}")
print(f"  Expected (pix0_vector): {(detector.pix0_vector / 1e10).numpy()}")