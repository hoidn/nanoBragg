#!/usr/bin/env python3
"""
Full trace of crystal tensor computation for triclinic case.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import sys
sys.path.insert(0, '/home/ollie/Documents/nanoBragg/src')

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import CrystalConfig

# Triclinic P1 configuration
config = CrystalConfig(
    cell_a=70.0,
    cell_b=80.0,
    cell_c=90.0,
    cell_alpha=75.0,
    cell_beta=85.0,
    cell_gamma=95.0,
    misset_deg=(-89.968546, -31.328953, 177.753396),
    phi_start_deg=0.0,
    osc_range_deg=0.0,
    phi_steps=1,
    spindle_axis=(0.0, 1.0, 0.0),
    mosaic_spread_deg=0.0,
    mosaic_domains=1,
    N_cells=(5, 5, 5),
    default_F=100.0,
)

crystal = Crystal(config)

print("="*70)
print("Triclinic P1 Cell Tensor Trace")
print("="*70)
print(f"Cell parameters: a={config.cell_a}, b={config.cell_b}, c={config.cell_c}")
print(f"                α={config.cell_alpha}°, β={config.cell_beta}°, γ={config.cell_gamma}°")
print(f"Misset angles: {config.misset_deg}")
print()

# Get final vectors
a_star = crystal.a_star
b_star = crystal.b_star
c_star = crystal.c_star

print("Final reciprocal vectors (after misset):")
print(f"  a* = [{a_star[0]:.12f}, {a_star[1]:.12f}, {a_star[2]:.12f}]  |a*| = {torch.norm(a_star):.12f}")
print(f"  b* = [{b_star[0]:.12f}, {b_star[1]:.12f}, {b_star[2]:.12f}]  |b*| = {torch.norm(b_star):.12f}")
print(f"  c* = [{c_star[0]:.12f}, {c_star[1]:.12f}, {c_star[2]:.12f}]  |c*| = {torch.norm(c_star):.12f}")
print()

# Compare with C values from FIRST_DIVERGENCE.md
print("Expected C values (after misset & regen):")
print("  a* = [-0.0123226000000, 0.0004834240000, 0.0075065500000]  |a*| = 0.014437")
print("  b* = [-0.0079915900000, 0.0003064060000, -0.0102821000000]  |b*| = 0.0130262")
print("  c* = [0.0022344600000, -0.0112079000000, 0.0018572300000]  |c*| = 0.0115784")
print()

c_a_star = torch.tensor([-0.0123226, 0.000483424, 0.00750655], dtype=torch.float64)
c_b_star = torch.tensor([-0.00799159, 0.000306406, -0.0102821], dtype=torch.float64)
c_c_star = torch.tensor([0.00223446, -0.0112079, 0.00185723], dtype=torch.float64)

diff_a = a_star - c_a_star
diff_b = b_star - c_b_star
diff_c = c_star - c_c_star

print("Differences (PyTorch - C):")
print(f"  Δa* = [{diff_a[0]:.12f}, {diff_a[1]:.12f}, {diff_a[2]:.12f}]")
print(f"  Δb* = [{diff_b[0]:.12f}, {diff_b[1]:.12f}, {diff_b[2]:.12f}]")
print(f"  Δc* = [{diff_c[0]:.12f}, {diff_c[1]:.12f}, {diff_c[2]:.12f}]")
print()

print("Relative errors (%):")
print(f"  a*: [{abs(diff_a[0]/c_a_star[0]*100):.4f}, {abs(diff_a[1]/c_a_star[1]*100):.4f}, {abs(diff_a[2]/c_a_star[2]*100):.4f}]")
print(f"  b*: [{abs(diff_b[0]/c_b_star[0]*100):.4f}, {abs(diff_b[1]/c_b_star[1]*100):.4f}, {abs(diff_b[2]/c_b_star[2]*100):.4f}]")
print(f"  c*: [{abs(diff_c[0]/c_c_star[0]*100):.4f}, {abs(diff_c[1]/c_c_star[1]*100):.4f}, {abs(diff_c[2]/c_c_star[2]*100):.4f}]")
print()

# Check metric duality
a = crystal.a
dot_a_astar = torch.dot(a, a_star)
dot_b_bstar = torch.dot(crystal.b, b_star)
dot_c_cstar = torch.dot(crystal.c, c_star)
print(f"Metric duality check:")
print(f"  a·a* = {dot_a_astar:.15f}")
print(f"  b·b* = {dot_b_bstar:.15f}")
print(f"  c·c* = {dot_c_cstar:.15f}")
