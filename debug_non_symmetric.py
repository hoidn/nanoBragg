#!/usr/bin/env python3
"""
Test phi rotation with a non-symmetric crystal to verify it's working
"""

import os
import torch
from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

device = torch.device("cpu")
dtype = torch.float64

# Create a non-symmetric crystal (different cell dimensions)
crystal_config = CrystalConfig(
    cell_a=80.0,  # Different from b and c
    cell_b=100.0,
    cell_c=120.0,
    cell_alpha=90.0,
    cell_beta=90.0, 
    cell_gamma=90.0,
)

crystal = Crystal(config=crystal_config, device=device, dtype=dtype)
detector = Detector(device=device, dtype=dtype)

print("=== Non-symmetric crystal setup ===")
print(f"cell dimensions: a={crystal.cell_a}, b={crystal.cell_b}, c={crystal.cell_c}")
print(f"Lattice vectors:")
print(f"a = {crystal.a}")
print(f"b = {crystal.b}")
print(f"c = {crystal.c}")

# Test with phi=0° and phi=90°
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

print("\n=== Full Simulation Results ===")
max_positions = []
max_values = []

for name, config in configs:
    simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)
    image = simulator.run()
    max_pos = torch.unravel_index(torch.argmax(image), image.shape) 
    max_val = torch.max(image)
    center_val = image[512, 512]
    total_intensity = torch.sum(image)
    
    print(f"{name}:")
    print(f"  Max at pixel {max_pos} with value {max_val:.6e}")
    print(f"  Center pixel value: {center_val:.6e}")
    print(f"  Total intensity: {total_intensity:.6e}")
    
    max_positions.append(max_pos)
    max_values.append(max_val)

# Check if patterns are different
pos_different = (max_positions[0][0] != max_positions[1][0]) or (max_positions[0][1] != max_positions[1][1])
print(f"\nPosition changed: {pos_different}")
print(f"Value ratio: {max_values[1]/max_values[0]:.6f}")

# Also test with a smaller angle to see if there's any change
print("\n=== Testing smaller rotation (10°) ===")
config_small = CrystalConfig(
    phi_start_deg=torch.tensor(10.0, device=device, dtype=dtype),
    phi_steps=1,
    osc_range_deg=torch.tensor(0.0, device=device, dtype=dtype), 
    mosaic_spread_deg=torch.tensor(0.0, device=device, dtype=dtype),
)

simulator_small = Simulator(crystal, detector, crystal_config=config_small, device=device, dtype=dtype)
image_small = simulator_small.run()
max_pos_small = torch.unravel_index(torch.argmax(image_small), image_small.shape)
max_val_small = torch.max(image_small)

print(f"phi=10°: Max at {max_pos_small} with value {max_val_small:.6e}")

# Compare with phi=0°
pos_different_small = (max_positions[0][0] != max_pos_small[0]) or (max_positions[0][1] != max_pos_small[1])
print(f"Position changed from 0° to 10°: {pos_different_small}")