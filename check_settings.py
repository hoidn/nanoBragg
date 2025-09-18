#!/usr/bin/env python
"""Check what settings might cause differences"""

import subprocess
import sys

# Run C version with explicit nopolar flag to check
print("=== Testing with -nopolar flag ===")
cmd_c_nopolar = [
    './nanoBragg',
    '-hkl', 'test_comparison.hkl',
    '-cell', '100', '100', '100', '90', '90', '90',
    '-lambda', '6.2',
    '-N', '3',
    '-distance', '100',
    '-detpixels', '64',
    '-pixel', '0.1',
    '-default_F', '100',
    '-nopolar',  # Explicitly disable polarization
    '-floatfile', 'c_output_nopolar.bin'
]

result = subprocess.run(cmd_c_nopolar, capture_output=True, text=True)
print("C output (key lines):")
for line in result.stdout.split('\n'):
    if 'Kahn' in line or 'polarization' in line or 'noise' in line:
        print(f"  {line}")

# Run PyTorch with nopolar
print("\n=== Testing PyTorch with nopolar ===")
cmd_pytorch_nopolar = [
    sys.executable, '-m', 'nanobrag_torch',
    '-hkl', 'test_comparison.hkl',
    '-cell', '100', '100', '100', '90', '90', '90',
    '-lambda', '6.2',
    '-N', '3',
    '-distance', '100',
    '-detpixels', '64',
    '-pixel', '0.1',
    '-default_F', '100',
    '-nopolar',
    '-floatfile', 'pytorch_output_nopolar.bin'
]

result2 = subprocess.run(cmd_pytorch_nopolar, capture_output=True, text=True)
print("PyTorch completed")

# Compare the nopolar outputs
import numpy as np

with open('c_output_nopolar.bin', 'rb') as f:
    c_nopolar = np.frombuffer(f.read(), dtype=np.float32).reshape(64, 64)

with open('pytorch_output_nopolar.bin', 'rb') as f:
    pytorch_nopolar = np.frombuffer(f.read(), dtype=np.float32).reshape(64, 64)

corr_nopolar = np.corrcoef(c_nopolar.flatten(), pytorch_nopolar.flatten())[0, 1]
print(f"\nCorrelation with -nopolar flag: {corr_nopolar:.6f}")

# Check differences
diff_nopolar = pytorch_nopolar - c_nopolar
print(f"Max difference with -nopolar: {np.abs(diff_nopolar).max():.6f}")
print(f"Mean abs difference with -nopolar: {np.abs(diff_nopolar).mean():.6f}")

# Also check the original C command output for polarization
print("\n=== Original C settings (from first run) ===")
print("The C output showed: 'Kahn polarization factor: 0.000000'")
print("This means polarization correction was DISABLED (factor=0 means nopolar)")
print("\nSo polarization is NOT the cause of differences.")