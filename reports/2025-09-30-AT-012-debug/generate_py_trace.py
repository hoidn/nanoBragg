#!/usr/bin/env python3
"""
Generate PyTorch trace for AT-012 triclinic P1 case.
Target pixel: (368, 262) - C max intensity location
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from nanobrag_torch.models.crystal import Crystal, CrystalConfig
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot, BeamConfig
from nanobrag_torch.simulator import Simulator

# Canonical triclinic P1 parameters
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

beam_config = BeamConfig(wavelength_A=1.0)

# Create objects
crystal = Crystal(crystal_config)
detector = Detector(detector_config)

print("=" * 80)
print("PYTORCH TRACE - AT-012 Triclinic P1")
print("=" * 80)

# Trace crystal vectors before and after misset
print("\nTRACE: Before misset rotation:")
print(f"TRACE:   a_star = {crystal.a_star.tolist()} |a_star| = {torch.norm(crystal.a_star).item():.7g}")
print(f"TRACE:   b_star = {crystal.b_star.tolist()} |b_star| = {torch.norm(crystal.b_star).item():.7g}")
print(f"TRACE:   c_star = {crystal.c_star.tolist()} |c_star| = {torch.norm(crystal.c_star).item():.7g}")

# Get misset-rotated vectors
misset_deg = crystal_config.misset_deg
print(f"TRACE:   misset angles = {misset_deg} degrees")

# The Crystal class should have rotated vectors stored; access them
# If misset was applied, the stored a_star/b_star/c_star should be rotated
print("\nTRACE: After misset rotation:")
print(f"TRACE:   a_star = {crystal.a_star.tolist()} |a_star| = {torch.norm(crystal.a_star).item():.7g}")
print(f"TRACE:   b_star = {crystal.b_star.tolist()} |b_star| = {torch.norm(crystal.b_star).item():.7g}")
print(f"TRACE:   c_star = {crystal.c_star.tolist()} |c_star| = {torch.norm(crystal.c_star).item():.7g}")

# Get real-space vectors
print("\nTRACE: Real-space vectors (Angstroms):")
print(f"TRACE:   a = {crystal.a.tolist()} |a| = {torch.norm(crystal.a).item():.7g}")
print(f"TRACE:   b = {crystal.b.tolist()} |b| = {torch.norm(crystal.b).item():.7g}")
print(f"TRACE:   c = {crystal.c.tolist()} |c| = {torch.norm(crystal.c).item():.7g}")

# Check volume
volume = torch.dot(crystal.a, torch.cross(crystal.b, crystal.c))
print(f"\nTRACE: Direct-space cell volume: V_cell = {volume.item():.6g} Å³")

# Convert to meters
a_m = crystal.a * 1e-10
b_m = crystal.b * 1e-10
c_m = crystal.c * 1e-10
print("\nTRACE: Real-space vectors (meters):")
print(f"TRACE:   a = {a_m.tolist()} |a| = {torch.norm(a_m).item():.7g} meters")
print(f"TRACE:   b = {b_m.tolist()} |b| = {torch.norm(b_m).item():.7g} meters")
print(f"TRACE:   c = {c_m.tolist()} |c| = {torch.norm(c_m).item():.7g} meters")

# Verify metric duality
print("\nTRACE: Metric duality check (a·a* should = 1):")
a_dot_astar = torch.dot(crystal.a, crystal.a_star)
b_dot_bstar = torch.dot(crystal.b, crystal.b_star)
c_dot_cstar = torch.dot(crystal.c, crystal.c_star)
print(f"TRACE:   a·a* = {a_dot_astar.item():.12f}")
print(f"TRACE:   b·b* = {b_dot_bstar.item():.12f}")
print(f"TRACE:   c·c* = {c_dot_cstar.item():.12f}")

# Now trace a single pixel through the physics
target_pixel = (368, 262)  # C max intensity location (slow, fast)
print(f"\n{'=' * 80}")
print(f"PIXEL TRACE FOR ({target_pixel[0]}, {target_pixel[1]}) - C Max Intensity Location")
print(f"{'=' * 80}")

# Get pixel position vector
s_idx, f_idx = target_pixel
pix0_vector = detector.pix0_vector
fdet = detector.fdet_vector
sdet = detector.sdet_vector

pixel_vector = pix0_vector + f_idx * detector.pixel_size_m * fdet + s_idx * detector.pixel_size_m * sdet
R = torch.norm(pixel_vector)
pixel_unit = pixel_vector / R

print(f"\nDetector geometry:")
print(f"  pixel_size_m: {detector.pixel_size_m:.6e}")
print(f"  pix0_vector: {pix0_vector.tolist()}")
print(f"  fdet: {fdet.tolist()}")
print(f"  sdet: {sdet.tolist()}")
print(f"\nPixel vector calculation:")
print(f"  pixel_vector = {pixel_vector.tolist()}")
print(f"  R (distance) = {R.item():.7g} meters")
print(f"  pixel_unit = {pixel_unit.tolist()}")

# Get incident beam direction
incident = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)  # MOSFLM convention
print(f"\nIncident beam:")
print(f"  incident = {incident.tolist()}")

# Scattering vector S
S = (pixel_unit - incident) / beam_config.wavelength_m
S_magnitude = torch.norm(S)
print(f"\nScattering vector:")
print(f"  S = {S.tolist()}")
print(f"  |S| = {S_magnitude.item():.7g} 1/m")

# Miller indices (float)
h_float = torch.dot(S, a_m)
k_float = torch.dot(S, b_m)
l_float = torch.dot(S, c_m)
print(f"\nMiller indices (float):")
print(f"  h = {h_float.item():.7g}")
print(f"  k = {k_float.item():.7g}")
print(f"  l = {l_float.item():.7g}")

# Miller indices (rounded)
h = torch.round(h_float).to(torch.int64)
k = torch.round(k_float).to(torch.int64)
l = torch.round(l_float).to(torch.int64)
print(f"\nMiller indices (rounded):")
print(f"  h = {h.item()}")
print(f"  k = {k.item()}")
print(f"  l = {l.item()}")

print("\n" + "=" * 80)
print("End of PyTorch trace")
print("=" * 80)
