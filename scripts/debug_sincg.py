#!/usr/bin/env python
"""Debug the sincg calculation."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from nanobrag_torch.utils.physics import sincg

# Test the specific case
h = 3.2
N = 5

# Calculate step by step
pi_h = torch.pi * torch.tensor(h, dtype=torch.float64)
print(f"π * h = {pi_h.item():.12f}")

# Direct calculation
sin_N_pi_h = torch.sin(N * pi_h)
sin_pi_h = torch.sin(pi_h)
print(f"sin(N * π * h) = sin({(N * pi_h).item():.12f}) = {sin_N_pi_h.item():.12e}")
print(f"sin(π * h) = sin({pi_h.item():.12f}) = {sin_pi_h.item():.12e}")
print(f"Direct calculation: {sin_N_pi_h.item()} / {sin_pi_h.item()} = {(sin_N_pi_h / sin_pi_h).item():.12f}")

# Using sincg
result = sincg(pi_h, torch.tensor(N, dtype=torch.float64))
print(f"\nsincg result: {result.item():.12e}")

# Check if we're hitting the zero threshold
print(f"\nIs |π * h| < 1e-9? {(pi_h.abs() < 1e-9).item()}")

# Let's check the actual implementation
print("\nTesting with smaller h values:")
for h_test in [0.0, 1e-10, 1e-8, 0.1, 1.0, 3.2]:
    pi_h_test = torch.pi * h_test
    result_test = sincg(pi_h_test, torch.tensor(5.0, dtype=torch.float64))
    print(f"h={h_test:8.2e}, π*h={pi_h_test.item():12.6e}, sincg={result_test.item():12.6e}")