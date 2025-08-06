#!/usr/bin/env python
"""Debug F_latt calculation to see the difference between old and new methods."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from nanobrag_torch.utils.physics import sincg

# Test some typical Miller index values
h_values = torch.tensor([0.0, 0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.1, 3.2], dtype=torch.float64)
N = torch.tensor(5.0, dtype=torch.float64)

print("Comparison of F_latt calculation methods:")
print("h      | Old Method (h-h0) | New Method (h)   | Ratio")
print("-------|-------------------|------------------|-------")

for h in h_values:
    h0 = torch.round(h)
    delta_h = h - h0
    
    # Old method: sincg(π*(h-h0), N)
    old_flatt = sincg(torch.pi * delta_h, N)
    
    # New method: sincg(π*h, N)
    new_flatt = sincg(torch.pi * h, N)
    
    ratio = new_flatt / old_flatt if old_flatt != 0 else float('inf')
    
    print(f"{h:6.1f} | {old_flatt:17.6f} | {new_flatt:16.6f} | {ratio:6.2f}")

# Also test with actual crystal simulation values
print("\nTesting with typical triclinic crystal values:")
# These would be typical h,k,l values from a triclinic simulation
test_indices = [
    (3.001, 2.999, 1.002),
    (3.15, 2.85, 1.1),
    (3.5, 2.5, 1.5),
    (4.0, 3.0, 2.0),
]

N_a = torch.tensor(10.0, dtype=torch.float64)
N_b = torch.tensor(10.0, dtype=torch.float64) 
N_c = torch.tensor(10.0, dtype=torch.float64)  # Typical crystal size

for h, k, l in test_indices:
    h_t = torch.tensor(h, dtype=torch.float64)
    k_t = torch.tensor(k, dtype=torch.float64)
    l_t = torch.tensor(l, dtype=torch.float64)
    
    # Old method
    h0, k0, l0 = torch.round(h_t), torch.round(k_t), torch.round(l_t)
    old_f = (sincg(torch.pi * (h_t - h0), N_a) * 
             sincg(torch.pi * (k_t - k0), N_b) * 
             sincg(torch.pi * (l_t - l0), N_c))
    
    # New method
    new_f = (sincg(torch.pi * h_t, N_a) * 
             sincg(torch.pi * k_t, N_b) * 
             sincg(torch.pi * l_t, N_c))
    
    print(f"({h:5.3f},{k:5.3f},{l:5.3f}): Old={old_f:12.6f}, New={new_f:12.6f}")