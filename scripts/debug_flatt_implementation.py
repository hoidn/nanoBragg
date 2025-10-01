#!/usr/bin/env python
"""Debug the F_latt implementation to ensure it's working correctly."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from nanobrag_torch.utils.physics import sincg

# Test the sincg function with values that would occur in triclinic simulation
print("Testing sincg implementation for triclinic case:")
print("=" * 60)

# Typical Miller indices from triclinic simulation
test_h_values = [10.0, 10.1, 10.27, 10.5, 10.99, 11.0, 11.001]
N = 10.0  # Typical N_cells value

for h in test_h_values:
    # What we should calculate (full Miller index)
    pi_h = np.pi * h
    
    # C-code calculation: sin(N*π*h)/sin(π*h)
    expected = np.sin(N * pi_h) / np.sin(pi_h) if np.sin(pi_h) != 0 else N
    
    # PyTorch calculation
    h_tensor = torch.tensor(h, dtype=torch.float64)
    N_tensor = torch.tensor(N, dtype=torch.float64)
    result = sincg(torch.pi * h_tensor, N_tensor)
    
    print(f"h = {h:6.3f}:")
    print(f"  sin({N}*π*{h:.3f})/sin(π*{h:.3f}) = {expected:12.6f}")
    print(f"  PyTorch sincg result = {result.item():12.6f}")
    print(f"  Match? {np.abs(result.item() - expected) < 1e-10}")
    
    # Also show what the old (wrong) method would have given
    h0 = round(h)
    delta_h = h - h0
    old_result = np.sin(N * np.pi * delta_h) / np.sin(np.pi * delta_h) if delta_h != 0 else N
    print(f"  Old method (delta_h={delta_h:5.2f}): {old_result:12.6f}")
    print()

# Test edge cases
print("\nEdge case testing:")
print("-" * 40)

# Test near-zero values
for h in [0.0, 1e-15, 1e-10, 1e-8]:
    h_tensor = torch.tensor(h, dtype=torch.float64)
    result = sincg(torch.pi * h_tensor, torch.tensor(5.0, dtype=torch.float64))
    print(f"sincg(π*{h:1.0e}, 5) = {result.item():.6f}")

# Test the zero check precision
print("\nTesting zero detection:")
h_tiny = torch.tensor(1e-300, dtype=torch.float64) * torch.pi
print(f"Is π*1e-300 == 0.0? {(h_tiny == 0.0).item()}")
print(f"sincg(π*1e-300, 5) = {sincg(h_tiny, torch.tensor(5.0)).item()}")

# Now test a full F_latt calculation
print("\n" + "=" * 60)
print("Full F_latt calculation for a typical triclinic reflection:")
h, k, l = 10.27, 8.13, 5.91
Na, Nb, Nc = 10, 10, 10

# Convert to tensors
h_t = torch.tensor(h, dtype=torch.float64)
k_t = torch.tensor(k, dtype=torch.float64)
l_t = torch.tensor(l, dtype=torch.float64)
Na_t = torch.tensor(float(Na), dtype=torch.float64)
Nb_t = torch.tensor(float(Nb), dtype=torch.float64)
Nc_t = torch.tensor(float(Nc), dtype=torch.float64)

# Calculate F_latt components
F_latt_a = sincg(torch.pi * h_t, Na_t)
F_latt_b = sincg(torch.pi * k_t, Nb_t)
F_latt_c = sincg(torch.pi * l_t, Nc_t)
F_latt = F_latt_a * F_latt_b * F_latt_c

print(f"Miller indices: ({h}, {k}, {l})")
print(f"Crystal size: ({Na}, {Nb}, {Nc})")
print(f"F_latt_a = {F_latt_a.item():.6f}")
print(f"F_latt_b = {F_latt_b.item():.6f}")
print(f"F_latt_c = {F_latt_c.item():.6f}")
print(f"F_latt total = {F_latt.item():.6e}")
print(f"Intensity ∝ F_latt² = {(F_latt**2).item():.6e}")