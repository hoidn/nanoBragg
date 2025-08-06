#!/usr/bin/env python
"""Debug script to investigate geometry precision errors.

This script traces through the compute_cell_tensors calculation step by step
to identify where precision is lost.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import CrystalConfig

def debug_metric_duality():
    """Debug the metric duality test to find precision loss."""
    
    # Use the same triclinic cell as the failing test
    config = CrystalConfig(
        cell_a=73.0,
        cell_b=82.0,
        cell_c=91.0,
        cell_alpha=77.3,
        cell_beta=84.2,
        cell_gamma=96.1,
    )
    
    crystal = Crystal(config=config)
    
    # Get vectors
    a, b, c = crystal.a, crystal.b, crystal.c
    a_star, b_star, c_star = crystal.a_star, crystal.b_star, crystal.c_star
    
    print("=== CELL PARAMETERS ===")
    print(f"a={config.cell_a}, b={config.cell_b}, c={config.cell_c}")
    print(f"α={config.cell_alpha}°, β={config.cell_beta}°, γ={config.cell_gamma}°")
    print(f"Volume: {crystal.V.item():.12f} Å³")
    
    print("\n=== REAL SPACE VECTORS ===")
    print(f"a = {a.numpy()}")
    print(f"b = {b.numpy()}")
    print(f"c = {c.numpy()}")
    
    print("\n=== RECIPROCAL SPACE VECTORS ===")
    print(f"a* = {a_star.numpy()}")
    print(f"b* = {b_star.numpy()}")
    print(f"c* = {c_star.numpy()}")
    
    print("\n=== METRIC DUALITY CHECK ===")
    # The critical relationships that should be exact
    a_dot_a_star = torch.dot(a, a_star).item()
    b_dot_b_star = torch.dot(b, b_star).item()
    c_dot_c_star = torch.dot(c, c_star).item()
    
    print(f"a · a* = {a_dot_a_star:.12f} (should be 1.0, error = {abs(a_dot_a_star - 1.0):.12e})")
    print(f"b · b* = {b_dot_b_star:.12f} (should be 1.0, error = {abs(b_dot_b_star - 1.0):.12e})")
    print(f"c · c* = {c_dot_c_star:.12f} (should be 1.0, error = {abs(c_dot_c_star - 1.0):.12e})")
    
    # Check orthogonality relationships
    print("\n=== ORTHOGONALITY CHECK ===")
    print(f"a · b* = {torch.dot(a, b_star).item():.12e} (should be 0)")
    print(f"a · c* = {torch.dot(a, c_star).item():.12e} (should be 0)")
    print(f"b · a* = {torch.dot(b, a_star).item():.12e} (should be 0)")
    print(f"b · c* = {torch.dot(b, c_star).item():.12e} (should be 0)")
    print(f"c · a* = {torch.dot(c, a_star).item():.12e} (should be 0)")
    print(f"c · b* = {torch.dot(c, b_star).item():.12e} (should be 0)")
    
    # Manual check: recalculate real vectors from reciprocal
    print("\n=== MANUAL RECALCULATION CHECK ===")
    V = crystal.V
    
    # Cross products of reciprocal vectors
    b_star_cross_c_star = torch.cross(b_star, c_star, dim=0)
    c_star_cross_a_star = torch.cross(c_star, a_star, dim=0)
    a_star_cross_b_star = torch.cross(a_star, b_star, dim=0)
    
    # Real vectors from reciprocal (should match a, b, c)
    a_calc = b_star_cross_c_star * V
    b_calc = c_star_cross_a_star * V
    c_calc = a_star_cross_b_star * V
    
    print(f"a_calc = {a_calc.numpy()}")
    print(f"a_diff = {(a - a_calc).numpy()} (max error: {torch.max(torch.abs(a - a_calc)).item():.12e})")
    
    print(f"\nb_calc = {b_calc.numpy()}")
    print(f"b_diff = {(b - b_calc).numpy()} (max error: {torch.max(torch.abs(b - b_calc)).item():.12e})")
    
    print(f"\nc_calc = {c_calc.numpy()}")
    print(f"c_diff = {(c - c_calc).numpy()} (max error: {torch.max(torch.abs(c - c_calc)).item():.12e})")
    
    # Check if the issue is in the volume calculation
    print("\n=== VOLUME CONSISTENCY CHECK ===")
    V_from_vectors = torch.dot(a, torch.cross(b, c, dim=0)).item()
    print(f"V from a·(b×c) = {V_from_vectors:.12f}")
    print(f"V from formula = {V.item():.12f}")
    print(f"Difference = {abs(V_from_vectors - V.item()):.12e}")
    
    # Check reciprocal volume relationship
    V_star = 1.0 / V
    V_star_from_vectors = torch.dot(a_star, torch.cross(b_star, c_star, dim=0)).item()
    print(f"\nV* from a*·(b*×c*) = {V_star_from_vectors:.12f}")
    print(f"V* = 1/V = {V_star.item():.12f}")
    print(f"Difference = {abs(V_star_from_vectors - V_star.item()):.12e}")
    
    # Test the standard crystallographic relationship
    print("\n=== STANDARD CRYSTALLOGRAPHIC CHECK ===")
    # In standard crystallography: a* = (b × c) / V
    a_star_standard = torch.cross(b, c, dim=0) / V
    b_star_standard = torch.cross(c, a, dim=0) / V
    c_star_standard = torch.cross(a, b, dim=0) / V
    
    print(f"a*_standard = {a_star_standard.numpy()}")
    print(f"a*_diff = {(a_star - a_star_standard).numpy()} (max: {torch.max(torch.abs(a_star - a_star_standard)).item():.12e})")
    
    # Check if standard calculation gives perfect metric duality
    print("\n=== METRIC DUALITY WITH STANDARD CALCULATION ===")
    print(f"a · a*_standard = {torch.dot(a, a_star_standard).item():.12f}")
    print(f"b · b*_standard = {torch.dot(b, b_star_standard).item():.12f}")
    print(f"c · c*_standard = {torch.dot(c, c_star_standard).item():.12f}")

if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    debug_metric_duality()