#!/usr/bin/env python
"""Test the impact of the F_latt fix on a simple example."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from nanobrag_torch.utils.physics import sincg

# Simulate what happens for a reflection near an integer Miller index
# This is the most common case in diffraction

print("Impact of F_latt calculation method on diffraction intensity:\n")

# Crystal with N=10 unit cells in each direction
N = torch.tensor(10.0, dtype=torch.float64)

# Test Miller indices near integers (common in diffraction)
test_cases = [
    (3.0, "Exact integer - on Bragg peak"),
    (3.001, "Very close to integer"),
    (3.01, "Slightly off integer"),
    (3.1, "Moderately off integer"),
    (3.5, "Half-integer"),
]

print("For a crystal with N=10 unit cells:")
print("-" * 60)

for h, description in test_cases:
    h_tensor = torch.tensor(h, dtype=torch.float64)
    h0 = torch.round(h_tensor)
    
    # Old method: sincg(π*(h-h0))
    old_flatt = sincg(torch.pi * (h_tensor - h0), N)
    
    # New method: sincg(π*h)
    new_flatt = sincg(torch.pi * h_tensor, N)
    
    # The intensity is proportional to F_latt^2
    old_intensity = old_flatt ** 2
    new_intensity = new_flatt ** 2
    
    print(f"\nh = {h} ({description}):")
    print(f"  Old F_latt = sincg(π*{h-h0.item():.3f}) = {old_flatt.item():.6f}")
    print(f"  New F_latt = sincg(π*{h:.3f}) = {new_flatt.item():.6f}")
    print(f"  Old Intensity ∝ {old_intensity.item():.6f}")
    print(f"  New Intensity ∝ {new_intensity.item():.6f}")
    
    if old_intensity.item() > 0:
        ratio = new_intensity.item() / old_intensity.item()
        print(f"  Intensity ratio (new/old): {ratio:.3f}")

print("\n" + "="*60)
print("CONCLUSION:")
print("The new method correctly accounts for the full Miller index,")
print("not just the fractional part. This is physically correct")
print("and should improve the accuracy of the simulation.")
print("="*60)