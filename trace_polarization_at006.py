#!/usr/bin/env python3
"""
Generate parallel traces for AT-PARALLEL-006 focusing on polarization.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import (
    CrystalConfig, DetectorConfig, BeamConfig,
    CrystalShape, DetectorConvention
)

# Test pixel: center (128, 128) and off-center (128, 64)
test_pixels = [(128, 128), (128, 64)]

# AT-PARALLEL-006 configuration (N=1, oversample=2)
crystal_config = CrystalConfig(
    cell_a_A=100.0,
    cell_b_A=100.0,
    cell_c_A=100.0,
    cell_alpha_deg=90.0,
    cell_beta_deg=90.0,
    cell_gamma_deg=90.0,
    N_cells_a=1,
    N_cells_b=1,
    N_cells_c=1,
    shape=CrystalShape.SQUARE,
    default_F=100.0,
    phi_start_deg=0.0,
    phi_range_deg=0.0,
    phi_steps=1,
    mosaic_spread_deg=0.0,
    mosaic_domains=1,
)

detector_config = DetectorConfig(
    detpixels_slow=256,
    detpixels_fast=256,
    pixel_size_mm=0.1,
    distance_mm=50.0,
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_F_mm=None,  # Auto from detsize
    beam_center_S_mm=None,
)

beam_config = BeamConfig(
    wavelength_A=1.0,
    fluence=1e12,
    polarization_factor=0.0,  # Unpolarized
    nopolar=False,
)

# sources_config not needed for this test

device = torch.device('cpu')
dtype = torch.float64

simulator = Simulator(
    crystal_config=crystal_config,
    detector_config=detector_config,
    beam_config=beam_config,
    device=device,
    dtype=dtype,
    seed=1
)

print("AT-PARALLEL-006 Polarization Trace (N=1, oversample=2)")
print("="*70)
print(f"Incident beam direction: {simulator.incident_beam_direction}")
print(f"Polarization axis: {simulator.polarization_axis}")
print(f"Kahn factor: {simulator.kahn_factor}")
print()

# Get pixel coordinates
pixel_coords_meters = simulator.detector.get_pixel_coordinates()  # (S, F, 3)
pixel_coords_angstroms = pixel_coords_meters * 1e10

for test_pixel in test_pixels:
    s, f = test_pixel
    pixel_coord = pixel_coords_angstroms[s, f]  # Shape: (3,)

    # Calculate diffracted direction (FROM sample TO pixel)
    pixel_magnitude = torch.sqrt(torch.sum(pixel_coord * pixel_coord))
    diffracted_unit = pixel_coord / pixel_magnitude

    # Incident direction (FROM source TO sample)
    incident_unit = -simulator.incident_beam_direction

    # Calculate scattering angle (2theta)
    cos_2theta = torch.sum(incident_unit * diffracted_unit)
    two_theta_rad = torch.acos(cos_2theta)
    two_theta_deg = torch.rad2deg(two_theta_rad)

    # Calculate polarization factor manually
    from nanobrag_torch.utils.physics import polarization_factor
    polar = polarization_factor(
        simulator.kahn_factor,
        incident_unit.unsqueeze(0),
        diffracted_unit.unsqueeze(0),
        simulator.polarization_axis
    )

    print(f"Pixel {test_pixel}:")
    print(f"  Pixel coord (Å): {pixel_coord.numpy()}")
    print(f"  Pixel magnitude (Å): {pixel_magnitude.item():.6f}")
    print(f"  Incident unit: {incident_unit.numpy()}")
    print(f"  Diffracted unit: {diffracted_unit.numpy()}")
    print(f"  cos(2θ): {cos_2theta.item():.9f}")
    print(f"  2θ (deg): {two_theta_deg.item():.6f}")
    print(f"  Polarization factor: {polar.item():.9f}")
    print()

print("\nNow let's check what happens with subpixel sampling (oversample=2):")
print("-"*70)

# Generate subpixel offsets for oversample=2
oversample = 2
subpixel_step = 1.0 / oversample
offset_start = -0.5 + subpixel_step / 2.0
subpixel_offsets = offset_start + torch.arange(oversample, device=device, dtype=dtype) * subpixel_step

print(f"Subpixel offsets (fractional pixels): {subpixel_offsets.numpy()}")

# Create grid
sub_s, sub_f = torch.meshgrid(subpixel_offsets, subpixel_offsets, indexing='ij')
sub_s_flat = sub_s.flatten()
sub_f_flat = sub_f.flatten()

print(f"Subpixel grid (S, F): {list(zip(sub_s_flat.numpy(), sub_f_flat.numpy()))}")
print(f"Last subpixel (index -1): S={sub_s_flat[-1].item():.3f}, F={sub_f_flat[-1].item():.3f}")
print()

# Check polarization for the last subpixel of pixel (128, 64)
s, f = (128, 64)
pixel_coord_center = pixel_coords_angstroms[s, f]

# Get detector basis vectors
f_axis = simulator.detector.fdet_vec
s_axis = simulator.detector.sdet_vec
pixel_size_m = simulator.detector.pixel_size

# Calculate last subpixel position
delta_s = sub_s_flat[-1] * pixel_size_m
delta_f = sub_f_flat[-1] * pixel_size_m
offset_vector = delta_s * s_axis + delta_f * f_axis

# Subpixel coordinate in meters
subpixel_coord_m = pixel_coords_meters[s, f] + offset_vector
subpixel_coord_ang = subpixel_coord_m * 1e10

# Calculate diffracted direction for subpixel
subpixel_magnitude = torch.sqrt(torch.sum(subpixel_coord_ang * subpixel_coord_ang))
diffracted_subpixel = subpixel_coord_ang / subpixel_magnitude

# Polarization for subpixel
polar_subpixel = polarization_factor(
    simulator.kahn_factor,
    incident_unit.unsqueeze(0),
    diffracted_subpixel.unsqueeze(0),
    simulator.polarization_axis
)

print(f"Last subpixel of pixel (128, 64):")
print(f"  Offset vector (m): {offset_vector.numpy()}")
print(f"  Subpixel coord (Å): {subpixel_coord_ang.numpy()}")
print(f"  Subpixel magnitude (Å): {subpixel_magnitude.item():.6f}")
print(f"  Diffracted unit: {diffracted_subpixel.numpy()}")
print(f"  Polarization factor: {polar_subpixel.item():.9f}")
print()
print(f"Difference from pixel center polar: {(polar_subpixel - polar).item():.9f}")