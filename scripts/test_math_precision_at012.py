#!/usr/bin/env python3
"""
Test math library precision for AT-PARALLEL-012 triclinic case.

Compares sin/cos/exp precision between PyTorch and NumPy for extreme angles
used in the triclinic misset case (-89.968546°, -31.328953°, 177.753396°).

Per fix_plan Attempt #10 hypothesis #3: large misset angles near ±90° and ±180°
may hit less-precise regions of sin/cos implementations.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
import math

# Triclinic misset angles from golden data
misset_deg = [-89.968546, -31.328953, 177.753396]
misset_rad = [math.radians(d) for d in misset_deg]

print("Math Library Precision Comparison")
print("=" * 60)
print(f"Misset angles (deg): {misset_deg}")
print(f"Misset angles (rad): {misset_rad}")
print()

print("Testing sin/cos precision:")
print("-" * 60)
for i, (deg, rad) in enumerate(zip(misset_deg, misset_rad)):
    print(f"\nAngle {i+1}: {deg:12.6f}° = {rad:18.15f} rad")

    # Math library (C libm via Python)
    sin_math = math.sin(rad)
    cos_math = math.cos(rad)

    # NumPy (typically uses BLAS/LAPACK)
    sin_np = np.sin(rad)
    cos_np = np.cos(rad)

    # PyTorch float64
    rad_torch = torch.tensor(rad, dtype=torch.float64)
    sin_torch = torch.sin(rad_torch).item()
    cos_torch = torch.cos(rad_torch).item()

    print(f"  sin(θ):")
    print(f"    math:    {sin_math:23.18f}")
    print(f"    numpy:   {sin_np:23.18f}")
    print(f"    torch:   {sin_torch:23.18f}")
    print(f"    Δ(torch-math): {abs(sin_torch - sin_math):18.15e}")
    print(f"    Δ(torch-np):   {abs(sin_torch - sin_np):18.15e}")

    print(f"  cos(θ):")
    print(f"    math:    {cos_math:23.18f}")
    print(f"    numpy:   {cos_np:23.18f}")
    print(f"    torch:   {cos_torch:23.18f}")
    print(f"    Δ(torch-math): {abs(cos_torch - cos_math):18.15e}")
    print(f"    Δ(torch-np):   {abs(cos_torch - cos_np):18.15e}")

print("\n" + "=" * 60)
print("\nTesting complex phase factor exp(i·θ) precision:")
print("-" * 60)

# Typical phase angles in lattice shape factor calculation
# For h,k,l in [-5,5] and N=5, phase = 2π·h·i/N where i in [0,N)
# Maximum phase = 2π·5·4/5 = 8π
test_phases = [0.0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi, 4*np.pi, 8*np.pi]

for phase in test_phases:
    print(f"\nPhase: {phase/np.pi:6.3f}π = {phase:12.9f} rad")

    # Complex exponential via math
    cos_m = math.cos(phase)
    sin_m = math.sin(phase)
    exp_m_real = cos_m
    exp_m_imag = sin_m

    # NumPy complex exponential
    exp_np = np.exp(1j * phase)

    # PyTorch complex exponential
    phase_torch = torch.tensor(phase, dtype=torch.float64)
    exp_torch = torch.exp(1j * phase_torch)

    print(f"  exp(i·θ) real part:")
    print(f"    math:    {exp_m_real:23.18f}")
    print(f"    numpy:   {exp_np.real:23.18f}")
    print(f"    torch:   {exp_torch.real.item():23.18f}")
    print(f"    Δ(torch-math): {abs(exp_torch.real.item() - exp_m_real):18.15e}")

    print(f"  exp(i·θ) imag part:")
    print(f"    math:    {exp_m_imag:23.18f}")
    print(f"    numpy:   {exp_np.imag:23.18f}")
    print(f"    torch:   {exp_torch.imag.item():23.18f}")
    print(f"    Δ(torch-math): {abs(exp_torch.imag.item() - exp_m_imag):18.15e}")

print("\n" + "=" * 60)
print("\nConclusion:")
print("-" * 60)
print("If Δ(torch-math) or Δ(torch-np) are > 1e-15 for these angles,")
print("math library differences may contribute to the ~1% intensity error.")
print("Typical float64 machine epsilon is ~2.22e-16.")
print("Accumulated over N=5³=125 unit cells with phase terms, even")
print("1e-15 per-operation errors could compound to ~1e-13 relative error.")
print("However, the observed 1% error (1e-2) is much larger than this.")
print("This suggests math library precision is NOT the root cause.")