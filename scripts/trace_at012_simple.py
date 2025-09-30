#!/usr/bin/env python3
"""Simple PyTorch trace for AT-PARALLEL-012 triclinic case at pixel (368, 262)."""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import torch
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot

# Target pixel (slow, fast) = (368, 262)
TARGET_PIXEL_S = 368
TARGET_PIXEL_F = 262

print(f"TRACE_PY: === PIXEL ({TARGET_PIXEL_F}, {TARGET_PIXEL_S}) TRACE START ===\n")

# Setup configuration matching C command
crystal_config = CrystalConfig(
    cell_a=70.0, cell_b=80.0, cell_c=90.0,
    cell_alpha=75.0, cell_beta=85.0, cell_gamma=95.0,
    N_cells=(5, 5, 5),
    misset_deg=(-89.968546, -31.328953, 177.753396),
    default_F=100.0
)

detector_config = DetectorConfig(
    spixels=512,
    fpixels=512,
    pixel_size_mm=0.1,
    distance_mm=100.0,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM
)

beam_config = BeamConfig(
    wavelength_A=1.0
)

# Create components
crystal = Crystal(crystal_config)
detector = Detector(detector_config)

# Get reciprocal vectors (after misset)
a_star = crystal.a_star.cpu().numpy()
b_star = crystal.b_star.cpu().numpy()
c_star = crystal.c_star.cpu().numpy()

print("TRACE_PY: === Crystal Reciprocal Vectors (1/Å) ===")
print(f"TRACE_PY: a_star = [{a_star[0]:.15e}, {a_star[1]:.15e}, {a_star[2]:.15e}]")
print(f"TRACE_PY: b_star = [{b_star[0]:.15e}, {b_star[1]:.15e}, {b_star[2]:.15e}]")
print(f"TRACE_PY: c_star = [{c_star[0]:.15e}, {c_star[1]:.15e}, {c_star[2]:.15e}]")

# Get real vectors (after misset + recalculation)
a = crystal.a.cpu().numpy()
b = crystal.b.cpu().numpy()
c = crystal.c.cpu().numpy()

print("\nTRACE_PY: === Crystal Real Vectors (Å) ===")
print(f"TRACE_PY: a = [{a[0]:.15e}, {a[1]:.15e}, {a[2]:.15e}]")
print(f"TRACE_PY: b = [{b[0]:.15e}, {b[1]:.15e}, {b[2]:.15e}]")
print(f"TRACE_PY: c = [{c[0]:.15e}, {c[1]:.15e}, {c[2]:.15e}]")

# Get pixel coordinates for target pixel
pixel_coords_m = detector.get_pixel_coords()

# Extract target pixel coordinates
target_coords = pixel_coords_m[TARGET_PIXEL_S, TARGET_PIXEL_F].cpu().numpy()
print(f"\nTRACE_PY: === Target Pixel ({TARGET_PIXEL_F}, {TARGET_PIXEL_S}) ===")
print(f"TRACE_PY: pixel_pos = [{target_coords[0]:.15e}, {target_coords[1]:.15e}, {target_coords[2]:.15e}] m")

# Calculate airpath (distance from origin to pixel)
airpath = np.linalg.norm(target_coords)
print(f"TRACE_PY: airpath = {airpath:.15e} m")

# Calculate diffracted direction (unit vector)
diffracted = target_coords / airpath
print(f"TRACE_PY: diffracted = [{diffracted[0]:.15e}, {diffracted[1]:.15e}, {diffracted[2]:.15e}]")

# Incident beam direction (MOSFLM: beam along +X)
incident = np.array([1.0, 0.0, 0.0])
print(f"TRACE_PY: incident = [{incident[0]:.15e}, {incident[1]:.15e}, {incident[2]:.15e}]")

# Scattering vector S = (diffracted - incident) / lambda
wavelength_m = beam_config.wavelength_A * 1e-10
S = (diffracted - incident) / wavelength_m
print(f"TRACE_PY: scattering_vector = [{S[0]:.15e}, {S[1]:.15e}, {S[2]:.15e}] 1/Å")

# Convert scattering vector to Miller indices (h,k,l = S·(a,b,c))
# Need to use reciprocal vectors in 1/m for dot product
a_star_m = a_star * 1e10  # 1/Å → 1/m
b_star_m = b_star * 1e10
c_star_m = c_star * 1e10

h_float = np.dot(S, a_star_m)
k_float = np.dot(S, b_star_m)
l_float = np.dot(S, c_star_m)

print(f"\nTRACE_PY: === Miller Indices ===")
print(f"TRACE_PY: h_float = {h_float:.15e}")
print(f"TRACE_PY: k_float = {k_float:.15e}")
print(f"TRACE_PY: l_float = {l_float:.15e}")

h_int = int(np.round(h_float))
k_int = int(np.round(k_float))
l_int = int(np.round(l_float))

print(f"TRACE_PY: h_int = {h_int}")
print(f"TRACE_PY: k_int = {k_int}")
print(f"TRACE_PY: l_int = {l_int}")

# F_cell (structure factor)
F_cell = crystal_config.default_F
print(f"\nTRACE_PY: === Structure Factor ===")
print(f"TRACE_PY: F_cell = {F_cell:.15e}")
print(f"TRACE_PY: F_cell^2 = {F_cell**2:.15e}")

# F_latt (lattice shape factor)
# This requires the full simulator calculation
# For now, run a minimal simulation to get this value
simulator = Simulator(crystal, detector, crystal_config, beam_config)
result_image = simulator.run()
intensity = result_image[TARGET_PIXEL_S, TARGET_PIXEL_F].item()

print(f"\nTRACE_PY: === Final Intensity ===")
print(f"TRACE_PY: final_intensity = {intensity:.15e}")

print(f"\nTRACE_PY: === PIXEL ({TARGET_PIXEL_F}, {TARGET_PIXEL_S}) TRACE END ===")