#!/usr/bin/env python
"""Debug the sincg calculation in detail."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np

# Test the specific case
h = 3.2
N = 5

# Using numpy for comparison
pi_h_np = np.pi * h
print(f"NumPy calculation:")
print(f"π * h = {pi_h_np:.12f}")
print(f"sin(N * π * h) = sin({N * pi_h_np:.12f}) = {np.sin(N * pi_h_np):.12e}")
print(f"sin(π * h) = sin({pi_h_np:.12f}) = {np.sin(pi_h_np):.12e}")
print(f"Result = {np.sin(N * pi_h_np) / np.sin(pi_h_np):.12f}")

# Using torch
pi_h_torch = torch.tensor(torch.pi * h, dtype=torch.float64)
print(f"\nPyTorch calculation:")
print(f"π * h = {pi_h_torch.item():.12f}")
print(f"sin(N * π * h) = sin({(N * pi_h_torch).item():.12f}) = {torch.sin(N * pi_h_torch).item():.12e}")
print(f"sin(π * h) = sin({pi_h_torch.item():.12f}) = {torch.sin(pi_h_torch).item():.12e}")
print(f"Result = {(torch.sin(N * pi_h_torch) / torch.sin(pi_h_torch)).item():.12f}")

# Check the expected C-code calculation
# The issue might be in the expected value calculation
print(f"\nExpected C-code calculation:")
print("Using π = 3.14159 (C-code approximation)")
pi_approx = 3.14159
pi_h_c = pi_approx * h
print(f"π * h = {pi_h_c:.12f}")
print(f"sin(N * π * h) = sin({N * pi_h_c:.12f}) = {np.sin(N * pi_h_c):.12e}")
print(f"sin(π * h) = sin({pi_h_c:.12f}) = {np.sin(pi_h_c):.12e}")
print(f"Result = {np.sin(N * pi_h_c) / np.sin(pi_h_c):.12f}")

# The actual issue appears to be that sin(50.265...) is very close to zero!
# Let's check a range of values
print(f"\nChecking different h values:")
for h_test in [0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.2, 3.5, 4.0]:
    pi_h_test = np.pi * h_test
    result = np.sin(N * pi_h_test) / np.sin(pi_h_test)
    print(f"h={h_test:3.1f}: sin({N}*π*{h_test:3.1f})/sin(π*{h_test:3.1f}) = {result:12.6f}")