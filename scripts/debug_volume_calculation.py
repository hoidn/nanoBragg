#!/usr/bin/env python
"""Debug the volume calculation discrepancy."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import CrystalConfig

def debug_volume():
    """Debug volume calculation."""
    
    # Use the same triclinic cell
    config = CrystalConfig(
        cell_a=73.0,
        cell_b=82.0,
        cell_c=91.0,
        cell_alpha=77.3,
        cell_beta=84.2,
        cell_gamma=96.1,
    )
    
    # Convert angles to radians
    alpha_rad = torch.deg2rad(torch.tensor(config.cell_alpha, dtype=torch.float64))
    beta_rad = torch.deg2rad(torch.tensor(config.cell_beta, dtype=torch.float64))
    gamma_rad = torch.deg2rad(torch.tensor(config.cell_gamma, dtype=torch.float64))
    
    # C-code volume formula
    aavg = (alpha_rad + beta_rad + gamma_rad) / 2.0
    skew = torch.sin(aavg) * torch.sin(aavg - alpha_rad) * torch.sin(aavg - beta_rad) * torch.sin(aavg - gamma_rad)
    skew = torch.abs(skew)
    V_ccode = 2.0 * config.cell_a * config.cell_b * config.cell_c * torch.sqrt(skew)
    
    print(f"=== C-CODE VOLUME FORMULA ===")
    print(f"aavg = {aavg.item():.12f} radians")
    print(f"skew = {skew.item():.12e}")
    print(f"V = {V_ccode.item():.12f} Å³")
    
    # Standard crystallographic volume formula
    cos_alpha = torch.cos(alpha_rad)
    cos_beta = torch.cos(beta_rad)
    cos_gamma = torch.cos(gamma_rad)
    
    # V = abc * sqrt(1 + 2*cos(α)*cos(β)*cos(γ) - cos²(α) - cos²(β) - cos²(γ))
    det = 1 + 2*cos_alpha*cos_beta*cos_gamma - cos_alpha**2 - cos_beta**2 - cos_gamma**2
    V_standard = config.cell_a * config.cell_b * config.cell_c * torch.sqrt(det)
    
    print(f"\n=== STANDARD VOLUME FORMULA ===")
    print(f"det = {det.item():.12e}")
    print(f"V = {V_standard.item():.12f} Å³")
    print(f"Difference from C-code: {abs(V_standard.item() - V_ccode.item()):.12e}")
    
    # Now build the actual vectors using C-code approach
    crystal = Crystal(config=config)
    a, b, c = crystal.a, crystal.b, crystal.c
    
    # Volume from actual vectors
    V_vectors = torch.dot(a, torch.cross(b, c, dim=0)).item()
    print(f"\n=== VOLUME FROM VECTORS ===")
    print(f"V = a·(b×c) = {V_vectors:.12f} Å³")
    print(f"Difference from C-code formula: {abs(V_vectors - V_ccode.item()):.12e}")
    print(f"Relative error: {abs(V_vectors - V_ccode.item()) / V_ccode.item() * 100:.4f}%")
    
    # The issue: which volume should we use?
    print(f"\n=== THE PROBLEM ===")
    print(f"Crystal.V returns: {crystal.V.item():.12f} (from C-code formula)")
    print(f"But a·(b×c) gives: {V_vectors:.12f}")
    print(f"This is a {abs(V_vectors - crystal.V.item()) / crystal.V.item() * 100:.4f}% discrepancy")
    
    # Test what happens if we use the vector-based volume
    V_star_formula = 1.0 / crystal.V
    V_star_vectors = 1.0 / V_vectors
    
    print(f"\n=== RECIPROCAL VOLUME ===")
    print(f"1/V_formula = {V_star_formula.item():.12e}")
    print(f"1/V_vectors = {V_star_vectors:.12e}")
    
    # Check metric duality with corrected volume
    a_star = crystal.a_star
    print(f"\n=== METRIC DUALITY TEST ===")
    print(f"Using V from formula: a·a* = {torch.dot(a, a_star).item():.12f}")
    print(f"Expected if using V_vectors: a·a* would be {torch.dot(a, a_star).item() * V_vectors / crystal.V.item():.12f}")
    
    # The fix would be to use V_vectors
    print(f"\n=== SUGGESTED FIX ===")
    print(f"The C-code must be using V = {V_vectors:.12f} for the final calculations")
    print(f"This would make a·a* = 1.0 exactly")

if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    debug_volume()