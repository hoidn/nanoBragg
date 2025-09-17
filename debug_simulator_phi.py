#!/usr/bin/env python3
"""
Debug script to understand why phi rotation doesn't affect simulator output
"""

import os
import torch
from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.utils.geometry import dot_product

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

device = torch.device("cpu")
dtype = torch.float64

# Create components 
crystal = Crystal(device=device, dtype=dtype)
detector = Detector(device=device, dtype=dtype)

print("=== Simple cubic crystal setup ===")
print(f"cell_a={crystal.cell_a}, cell_b={crystal.cell_b}, cell_c={crystal.cell_c}")
print(f"Original lattice vectors:")
print(f"a = {crystal.a}")
print(f"b = {crystal.b}")
print(f"c = {crystal.c}")

# Get pixel coordinates for center pixel
pixel_coords_meters = detector.get_pixel_coords()
print(f"\nDetector pixel coords shape: {pixel_coords_meters.shape}")
print(f"Center pixel coord (meters): {pixel_coords_meters[512, 512]}")

# Convert to Angstroms
pixel_coords_angstroms = pixel_coords_meters * 1e10
print(f"Center pixel coord (Angstroms): {pixel_coords_angstroms[512, 512]}")

# Calculate scattering vector for center pixel
incident_beam_direction = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
wavelength = 6.2

# Diffracted beam unit vector (from origin to pixel)
pixel_magnitudes = torch.sqrt(torch.sum(pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True))
diffracted_beam_unit = pixel_coords_angstroms / pixel_magnitudes
print(f"Center pixel diffracted beam unit vector: {diffracted_beam_unit[512, 512]}")

# Scattering vector
scattering_vector = (diffracted_beam_unit - incident_beam_direction) / wavelength
print(f"Center pixel scattering vector: {scattering_vector[512, 512]}")

# Test phi rotation impact on Miller indices
configs = [
    ("phi=0°", CrystalConfig(
        phi_start_deg=torch.tensor(0.0, device=device, dtype=dtype),
        phi_steps=1,
        osc_range_deg=torch.tensor(0.0, device=device, dtype=dtype),
        mosaic_spread_deg=torch.tensor(0.0, device=device, dtype=dtype),
    )),
    ("phi=90°", CrystalConfig(
        phi_start_deg=torch.tensor(90.0, device=device, dtype=dtype), 
        phi_steps=1,
        osc_range_deg=torch.tensor(0.0, device=device, dtype=dtype),
        mosaic_spread_deg=torch.tensor(0.0, device=device, dtype=dtype),
    ))
]

for name, config in configs:
    print(f"\n=== {name} ===")
    
    # Get rotated vectors
    (rot_a, rot_b, rot_c), _ = crystal.get_rotated_real_vectors(config)
    print(f"Rotated a[0,0]: {rot_a[0,0]}")
    print(f"Rotated b[0,0]: {rot_b[0,0]}")
    print(f"Rotated c[0,0]: {rot_c[0,0]}")
    
    # Calculate Miller indices for center pixel
    # Broadcast scattering vector and lattice vectors
    scattering_center = scattering_vector[512, 512].unsqueeze(0).unsqueeze(0).unsqueeze(0)  # (1,1,1,3)
    rot_a_bc = rot_a.unsqueeze(0).unsqueeze(0)  # (1,1,1,1,3)
    rot_b_bc = rot_b.unsqueeze(0).unsqueeze(0) 
    rot_c_bc = rot_c.unsqueeze(0).unsqueeze(0)
    
    h = dot_product(scattering_center, rot_a_bc)
    k = dot_product(scattering_center, rot_b_bc)
    l = dot_product(scattering_center, rot_c_bc)  # noqa: E741
    
    print(f"Miller indices (h,k,l) for center pixel: ({h.item():.6f}, {k.item():.6f}, {l.item():.6f})")
    
    # Get nearest integer indices
    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)
    print(f"Nearest integer (h0,k0,l0): ({h0.item():.0f}, {k0.item():.0f}, {l0.item():.0f})")
    
    # Get structure factor 
    F_cell = crystal.get_structure_factor(h0, k0, l0)
    print(f"F_cell: {F_cell.item()}")
    
    # Calculate lattice form factor using fractional part
    from nanobrag_torch.utils.physics import sincg
    F_latt_a = sincg(torch.pi * (h - h0), crystal.N_cells_a)
    F_latt_b = sincg(torch.pi * (k - k0), crystal.N_cells_b) 
    F_latt_c = sincg(torch.pi * (l - l0), crystal.N_cells_c)
    F_latt = F_latt_a * F_latt_b * F_latt_c
    
    print(f"F_latt components: a={F_latt_a.item():.6f}, b={F_latt_b.item():.6f}, c={F_latt_c.item():.6f}")
    print(f"F_latt total: {F_latt.item():.6f}")
    
    # Total intensity
    F_total = F_cell * F_latt
    intensity = F_total * F_total
    print(f"Final intensity for center pixel: {intensity.item():.6e}")

# Now run full simulation and compare
print("\n=== Full Simulation Comparison ===")
for name, config in configs:
    simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)
    image = simulator.run()
    max_pos = torch.unravel_index(torch.argmax(image), image.shape) 
    max_val = torch.max(image)
    center_val = image[512, 512]
    
    print(f"{name}: max at {max_pos} with value {max_val:.6e}, center pixel value: {center_val:.6e}")