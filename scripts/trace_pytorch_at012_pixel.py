#!/usr/bin/env python3
"""Generate PyTorch trace for AT-PARALLEL-012 triclinic case at pixel (368, 262)."""
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

print(f"=== PyTorch Trace for Pixel ({TARGET_PIXEL_S}, {TARGET_PIXEL_F}) ===\n")

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
simulator = Simulator(crystal, detector, crystal_config, beam_config)

# Emit crystal geometry trace
print("=== Crystal Geometry ===")
print(f"Cell: a={crystal_config.cell_a}, b={crystal_config.cell_b}, c={crystal_config.cell_c}")
print(f"Angles: α={crystal_config.cell_alpha}°, β={crystal_config.cell_beta}°, γ={crystal_config.cell_gamma}°")
print(f"Misset: ({crystal_config.misset_deg[0]:.6f}, {crystal_config.misset_deg[1]:.6f}, {crystal_config.misset_deg[2]:.6f}) degrees")
print(f"N_cells: {crystal_config.N_cells}")
print(f"default_F: {crystal_config.default_F}")

# Get reciprocal and real vectors
a_star, b_star, c_star = crystal.a_star, crystal.b_star, crystal.c_star
a, b, c = crystal.a, crystal.b, crystal.c

print(f"\nReciprocal vectors (1/Angstrom):")
print(f"  a_star = [{a_star[0]:.15e}, {a_star[1]:.15e}, {a_star[2]:.15e}]")
print(f"  b_star = [{b_star[0]:.15e}, {b_star[1]:.15e}, {b_star[2]:.15e}]")
print(f"  c_star = [{c_star[0]:.15e}, {c_star[1]:.15e}, {c_star[2]:.15e}]")

print(f"\nReal vectors (meters):")
print(f"  a = [{a[0]:.15e}, {a[1]:.15e}, {a[2]:.15e}]")
print(f"  b = [{b[0]:.15e}, {b[1]:.15e}, {b[2]:.15e}]")
print(f"  c = [{c[0]:.15e}, {c[1]:.15e}, {c[2]:.15e}]")

# Get rotated real vectors (phi=0)
(rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = crystal.get_rotated_real_vectors(crystal_config)
print(f"\nRotated real vectors at phi=0 (meters):")
print(f"  rot_a = [{rot_a[0].item():.15e}, {rot_a[1].item():.15e}, {rot_a[2].item():.15e}]")
print(f"  rot_b = [{rot_b[0].item():.15e}, {rot_b[1].item():.15e}, {rot_b[2].item():.15e}]")
print(f"  rot_c = [{rot_c[0].item():.15e}, {rot_c[1].item():.15e}, {rot_c[2].item():.15e}]")

# Detector geometry
print("\n=== Detector Geometry ===")
print(f"Convention: {detector_config.detector_convention}")
print(f"Pivot: {detector_config.detector_pivot}")
print(f"Distance: {detector_config.distance_mm} mm = {detector_config.distance_mm/1000} m")
print(f"Pixel size: {detector_config.pixel_size_mm} mm = {detector_config.pixel_size_mm/1000} m")
print(f"Detector size: {detector_config.spixels} x {detector_config.fpixels} pixels")

# Get pixel coordinates for target pixel
pixel_coords_m = detector.get_pixel_coords(
    detector_config.distance_mm / 1000,
    oversample=1
)

# Extract target pixel coordinates
target_coords = pixel_coords_m[TARGET_PIXEL_S, TARGET_PIXEL_F]
print(f"\nTarget pixel ({TARGET_PIXEL_S}, {TARGET_PIXEL_F}) coordinates (meters):")
print(f"  [X, Y, Z] = [{target_coords[0]:.15e}, {target_coords[1]:.15e}, {target_coords[2]:.15e}]")

# Calculate airpath and diffracted direction
R = torch.norm(target_coords)
print(f"  R (airpath) = {R:.15e} m")

diffracted_unit = target_coords / R
print(f"  diffracted_unit = [{diffracted_unit[0]:.15e}, {diffracted_unit[1]:.15e}, {diffracted_unit[2]:.15e}]")

# Calculate close_distance
close_distance_m = detector.close_distance_m
obliquity_factor = close_distance_m / R
print(f"  close_distance = {close_distance_m:.15e} m")
print(f"  obliquity_factor = {obliquity_factor:.15e}")

# Calculate omega (solid angle)
pixel_size_m = detector_config.pixel_size_mm / 1000
omega = (pixel_size_m ** 2 * close_distance_m) / (R ** 3)
print(f"  omega (solid angle) = {omega:.15e} sr")

# Beam
print("\n=== Beam ===")
print(f"Wavelength: {beam_config.wavelength_A} Å = {beam_config.wavelength_A * 1e-10} m")
incident_vec = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
print(f"  incident_vec = [{incident_vec[0]:.15e}, {incident_vec[1]:.15e}, {incident_vec[2]:.15e}]")

# Scattering vector
lambda_m = beam_config.wavelength_A * 1e-10
S = (diffracted_unit - incident_vec) / lambda_m  # in 1/m, convert to 1/Angstrom
S_inv_A = S * 1e-10
print(f"  scattering_vec (1/Angstrom) = [{S_inv_A[0]:.15e}, {S_inv_A[1]:.15e}, {S_inv_A[2]:.15e}]")

# Miller indices
h = torch.dot(rot_a, S)
k = torch.dot(rot_b, S)
l = torch.dot(rot_c, S)
print(f"\n=== Miller Indices ===")
print(f"  h_float = {h:.15e}")
print(f"  k_float = {k:.15e}")
print(f"  l_float = {l:.15e}")

h_int = torch.round(h).int()
k_int = torch.round(k).int()
l_int = torch.round(l).int()
print(f"  h_int = {h_int}")
print(f"  k_int = {k_int}")
print(f"  l_int = {l_int}")

# F_latt calculation
# For oversample=2, we need to calculate for 4 subpixels
print("\n=== F_latt Calculation (oversample=2) ===")
oversample = 2
subpixel_size = pixel_size_m / oversample

F_latt_list = []
for subS in range(oversample):
    for subF in range(oversample):
        # Subpixel position
        Fdet = (TARGET_PIXEL_F * oversample + subF + 0.5) * subpixel_size
        Sdet = (TARGET_PIXEL_S * oversample + subS + 0.5) * subpixel_size

        # Get detector basis
        fdet_vec = detector.fdet_vec
        sdet_vec = detector.sdet_vec
        pix0_vec = detector.pix0_vector

        # Subpixel coordinates
        subpix_coords = Fdet * fdet_vec + Sdet * sdet_vec + pix0_vec

        # Diffracted direction for this subpixel
        sub_R = torch.norm(subpix_coords)
        sub_diffracted = subpix_coords / sub_R

        # Scattering vector for this subpixel
        sub_S = (sub_diffracted - incident_vec) / lambda_m

        # Miller indices for this subpixel
        sub_h = torch.dot(rot_a, sub_S)
        sub_k = torch.dot(rot_b, sub_S)
        sub_l = torch.dot(rot_c, sub_S)

        # F_latt components
        Na, Nb, Nc = crystal_config.N_cells
        F_latt_a = torch.sinc(sub_h) / torch.sinc(sub_h / Na) if Na > 1 else torch.tensor(1.0, dtype=torch.float64)
        F_latt_b = torch.sinc(sub_k) / torch.sinc(sub_k / Nb) if Nb > 1 else torch.tensor(1.0, dtype=torch.float64)
        F_latt_c = torch.sinc(sub_l) / torch.sinc(sub_l / Nc) if Nc > 1 else torch.tensor(1.0, dtype=torch.float64)
        F_latt = F_latt_a * F_latt_b * F_latt_c

        F_latt_list.append(F_latt.item())
        print(f"  Subpixel ({subS},{subF}): h={sub_h:.15e}, k={sub_k:.15e}, l={sub_l:.15e}")
        print(f"    F_latt_a={F_latt_a:.15e}, F_latt_b={F_latt_b:.15e}, F_latt_c={F_latt_c:.15e}")
        print(f"    F_latt={F_latt:.15e}")

print(f"\nF_latt values: {F_latt_list}")

# Polarization
print("\n=== Polarization ===")
print(f"Kahn factor: {beam_config.polarization_factor} (0.0 = unpolarized)")
polarization_axis = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
print(f"Polarization axis: [{polarization_axis[0]:.15e}, {polarization_axis[1]:.15e}, {polarization_axis[2]:.15e}]")

# Calculate polarization factor (from polarization_factor function)
# For unpolarized (kahn=0): 0.5 * (1 + cos²(2θ))
cos_2theta = torch.dot(incident_vec, diffracted_unit)
polar = 0.5 * (1 + cos_2theta**2)
print(f"Polarization factor: {polar:.15e}")

print("\n=== Run Full Simulation ===")
# Run full simulation
pytorch_image = simulator.run().cpu().numpy()
final_intensity = pytorch_image[TARGET_PIXEL_S, TARGET_PIXEL_F]
print(f"Final intensity at pixel ({TARGET_PIXEL_S}, {TARGET_PIXEL_F}): {final_intensity:.15e}")

# Save output
output_path = "reports/2025-09-29-debug-traces-012/py_trace_pixel_368_262.txt"
with open(output_path, "w") as f:
    f.write(f"PyTorch Trace for Pixel ({TARGET_PIXEL_S}, {TARGET_PIXEL_F})\\n")
    f.write(f"Final intensity: {final_intensity:.15e}\\n")
    f.write(f"F_latt values: {F_latt_list}\\n")
    f.write(f"Polarization: {polar:.15e}\\n")
    f.write(f"Omega: {omega:.15e}\\n")

print(f"\nTrace saved to: {output_path}")
print(f"\\n=== COMPARISON ===")
print(f"C final intensity: 138.216")
print(f"PyTorch final intensity: {final_intensity:.6f}")
print(f"Ratio (Py/C): {final_intensity/138.216:.6f}")