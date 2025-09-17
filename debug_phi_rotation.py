#!/usr/bin/env python3
"""
Debug script to understand phi rotation behavior in Crystal.get_rotated_real_vectors()
"""

import os
import torch
from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

device = torch.device("cpu")
dtype = torch.float64

# Create crystal
crystal = Crystal(device=device, dtype=dtype)

print("=== Original Lattice Vectors ===")
print(f"a = {crystal.a}")
print(f"b = {crystal.b}") 
print(f"c = {crystal.c}")

# Test phi=0
config_0 = CrystalConfig(
    phi_start_deg=torch.tensor(0.0, device=device, dtype=dtype),
    phi_steps=1,
    osc_range_deg=torch.tensor(0.0, device=device, dtype=dtype),
    mosaic_spread_deg=torch.tensor(0.0, device=device, dtype=dtype),
    spindle_axis=(0.0, 0.0, 1.0),
)

(a_rot_0, b_rot_0, c_rot_0), _ = crystal.get_rotated_real_vectors(config_0)

print("\n=== Phi = 0° ===")
print(f"a_rot shape: {a_rot_0.shape}")
print(f"a_rot[0,0] = {a_rot_0[0,0]}")
print(f"b_rot[0,0] = {b_rot_0[0,0]}")
print(f"c_rot[0,0] = {c_rot_0[0,0]}")

# Test phi=90
config_90 = CrystalConfig(
    phi_start_deg=torch.tensor(90.0, device=device, dtype=dtype),
    phi_steps=1,
    osc_range_deg=torch.tensor(0.0, device=device, dtype=dtype),
    mosaic_spread_deg=torch.tensor(0.0, device=device, dtype=dtype),
    spindle_axis=(0.0, 0.0, 1.0),
)

(a_rot_90, b_rot_90, c_rot_90), _ = crystal.get_rotated_real_vectors(config_90)

print("\n=== Phi = 90° ===")
print(f"a_rot[0,0] = {a_rot_90[0,0]}")
print(f"b_rot[0,0] = {b_rot_90[0,0]}")
print(f"c_rot[0,0] = {c_rot_90[0,0]}")

# Check differences
print("\n=== Differences (90° - 0°) ===")
print(f"Δa = {a_rot_90[0,0] - a_rot_0[0,0]}")
print(f"Δb = {b_rot_90[0,0] - b_rot_0[0,0]}")
print(f"Δc = {c_rot_90[0,0] - c_rot_0[0,0]}")

# Test with osc_range
config_osc = CrystalConfig(
    phi_start_deg=torch.tensor(0.0, device=device, dtype=dtype),
    phi_steps=1,
    osc_range_deg=torch.tensor(90.0, device=device, dtype=dtype),  # This should use midpoint = 45°
    mosaic_spread_deg=torch.tensor(0.0, device=device, dtype=dtype),
    spindle_axis=(0.0, 0.0, 1.0),
)

(a_rot_osc, b_rot_osc, c_rot_osc), _ = crystal.get_rotated_real_vectors(config_osc)

print("\n=== Phi start=0°, osc_range=90° (midpoint should be 45°) ===")
print(f"a_rot[0,0] = {a_rot_osc[0,0]}")
print(f"b_rot[0,0] = {b_rot_osc[0,0]}")
print(f"c_rot[0,0] = {c_rot_osc[0,0]}")

# Expected for 45° rotation around Z-axis:
# a = [100, 0, 0] → [cos45*100, sin45*100, 0] = [70.71, 70.71, 0]
# b = [0, 100, 0] → [-sin45*100, cos45*100, 0] = [-70.71, 70.71, 0]
cos45 = torch.cos(torch.tensor(torch.pi / 4, dtype=dtype))
sin45 = torch.sin(torch.tensor(torch.pi / 4, dtype=dtype))

expected_a_45 = torch.tensor([100 * cos45, 100 * sin45, 0.0], dtype=dtype)
expected_b_45 = torch.tensor([-100 * sin45, 100 * cos45, 0.0], dtype=dtype)
expected_c_45 = torch.tensor([0.0, 0.0, 100.0], dtype=dtype)

print(f"\nExpected a at 45°: {expected_a_45}")
print(f"Expected b at 45°: {expected_b_45}")
print(f"Expected c at 45°: {expected_c_45}")

print(f"\nActual vs Expected differences:")
print(f"Δa = {a_rot_osc[0,0] - expected_a_45}")
print(f"Δb = {b_rot_osc[0,0] - expected_b_45}")
print(f"Δc = {c_rot_osc[0,0] - expected_c_45}")