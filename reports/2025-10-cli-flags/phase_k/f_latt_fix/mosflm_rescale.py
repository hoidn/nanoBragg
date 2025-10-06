#!/usr/bin/env python3
"""
CLI-FLAGS-003 Phase K2b: MOSFLM Lattice Vector Rescaling Mismatch

This script demonstrates the discrepancy between C and PyTorch lattice vector
calculation when using MOSFLM A.mat orientation matrices.

Issue: PyTorch always rescales cross products to match cell parameters, but C
       only does this when user_cell=1 (i.e., when -cell was explicitly provided).
       When using -matrix A.mat without -cell, C skips the rescale step.

C Reference: golden_suite_generator/nanoBragg.c:2140-2149
```c
if(user_cell)
{
    /* a,b,c and V_cell were generated above */

    /* force the cross-product vectors to have proper magnitude: b_star X c_star = a*V_cell */
    vector_rescale(b_star_cross_c_star,b_star_cross_c_star,a[0]/V_cell);
    vector_rescale(c_star_cross_a_star,c_star_cross_a_star,b[0]/V_cell);
    vector_rescale(a_star_cross_b_star,a_star_cross_b_star,c[0]/V_cell);
    V_star = 1.0/V_cell;
}
```

When `-matrix A.mat` is used without `-cell`, user_cell=0, so the cross products
are NOT rescaled and the actual magnitudes from the reciprocal vectors are used.
"""

import os
import sys
import torch
from pathlib import Path

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'src'))

from nanobrag_torch.io.mosflm import read_mosflm_matrix, reciprocal_to_real_cell
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import CrystalConfig

def main():
    """Compare C-style (no rescale) vs PyTorch (rescale) lattice vectors."""

    repo_root = Path(__file__).parent.parent.parent.parent.parent
    mat_file = repo_root / "A.mat"
    wavelength_A = 0.976800  # From supervisor command

    print("="*80)
    print("MOSFLM Lattice Vector Rescaling Comparison")
    print("="*80)
    print()

    # Load MOSFLM matrix
    a_star, b_star, c_star = read_mosflm_matrix(str(mat_file), wavelength_A)
    cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)

    print("MOSFLM A.mat Reciprocal Vectors:")
    print(f"  a* = {a_star}")
    print(f"  b* = {b_star}")
    print(f"  c* = {c_star}")
    print()

    print("Derived Cell Parameters:")
    print(f"  a = {cell_params[0]:.6f} Å")
    print(f"  b = {cell_params[1]:.6f} Å")
    print(f"  c = {cell_params[2]:.6f} Å")
    print(f"  α = {cell_params[3]:.6f}°")
    print(f"  β = {cell_params[4]:.6f}°")
    print(f"  γ = {cell_params[5]:.6f}°")
    print()

    # Manual C-style calculation (no rescale)
    print("-"*80)
    print("C-Style Calculation (user_cell=0, NO rescale)")
    print("-"*80)

    # Convert to tensors for cross products
    a_star_t = torch.tensor(a_star, dtype=torch.float64)
    b_star_t = torch.tensor(b_star, dtype=torch.float64)
    c_star_t = torch.tensor(c_star, dtype=torch.float64)

    # Compute cross products (C-style, no rescaling)
    b_cross_c = torch.cross(b_star_t, c_star_t)
    c_cross_a = torch.cross(c_star_t, a_star_t)
    a_cross_b = torch.cross(a_star_t, b_star_t)

    # Volume (from cross product, actual volume)
    V_star = torch.dot(a_star_t, b_cross_c).item()
    V_cell_c = 1.0 / V_star

    # Real vectors from cross products (NO rescaling in C when user_cell=0)
    a_vec_c_no_rescale = b_cross_c * V_cell_c
    b_vec_c_no_rescale = c_cross_a * V_cell_c
    c_vec_c_no_rescale = a_cross_b * V_cell_c

    print(f"  V* = {V_star:.15f} Å⁻³")
    print(f"  V_cell = {V_cell_c:.6f} Å³")
    print()
    print("Real space vectors (unrescaled):")
    print(f"  a = [{a_vec_c_no_rescale[0]:.10f}, {a_vec_c_no_rescale[1]:.10f}, {a_vec_c_no_rescale[2]:.10f}]")
    print(f"  b = [{b_vec_c_no_rescale[0]:.10f}, {b_vec_c_no_rescale[1]:.10f}, {b_vec_c_no_rescale[2]:.10f}]")
    print(f"  c = [{c_vec_c_no_rescale[0]:.10f}, {c_vec_c_no_rescale[1]:.10f}, {c_vec_c_no_rescale[2]:.10f}]")
    print()
    print(f"  |a| = {torch.norm(a_vec_c_no_rescale).item():.10f} Å")
    print(f"  |b| = {torch.norm(b_vec_c_no_rescale).item():.10f} Å")
    print(f"  |c| = {torch.norm(c_vec_c_no_rescale).item():.10f} Å")
    print()

    # Now apply C-style rescaling (when user_cell=1)
    print("If user_cell=1 (C would rescale):")
    # vector_rescale(b_star_cross_c_star, b_star_cross_c_star, a[0]/V_cell)
    a_vec_c_rescaled = (b_cross_c / torch.norm(b_cross_c)) * cell_params[0]
    b_vec_c_rescaled = (c_cross_a / torch.norm(c_cross_a)) * cell_params[1]
    c_vec_c_rescaled = (a_cross_b / torch.norm(a_cross_b)) * cell_params[2]

    print(f"  a = [{a_vec_c_rescaled[0]:.10f}, {a_vec_c_rescaled[1]:.10f}, {a_vec_c_rescaled[2]:.10f}]")
    print(f"  b = [{b_vec_c_rescaled[0]:.10f}, {b_vec_c_rescaled[1]:.10f}, {b_vec_c_rescaled[2]:.10f}]")
    print(f"  c = [{c_vec_c_rescaled[0]:.10f}, {c_vec_c_rescaled[1]:.10f}, {c_vec_c_rescaled[2]:.10f}]")
    print()
    print(f"  |a| = {torch.norm(a_vec_c_rescaled).item():.10f} Å")
    print(f"  |b| = {torch.norm(b_vec_c_rescaled).item():.10f} Å")
    print(f"  |c| = {torch.norm(c_vec_c_rescaled).item():.10f} Å")
    print()

    # PyTorch calculation (with rescale)
    print("-"*80)
    print("PyTorch Calculation (current implementation, WITH rescale)")
    print("-"*80)

    # Create Crystal with MOSFLM orientation
    crystal_config = CrystalConfig(
        cell_a=cell_params[0],
        cell_b=cell_params[1],
        cell_c=cell_params[2],
        cell_alpha=cell_params[3],
        cell_beta=cell_params[4],
        cell_gamma=cell_params[5],
        N_cells=(36, 47, 29),
        default_F=0.0,
        mosflm_a_star=a_star,
        mosflm_b_star=b_star,
        mosflm_c_star=c_star
    )

    crystal = Crystal(crystal_config, device='cpu', dtype=torch.float64)

    # Get real vectors from Crystal (which applies rescaling)
    a_vec_py = crystal.a
    b_vec_py = crystal.b
    c_vec_py = crystal.c

    print("Real space vectors (rescaled to match cell params):")
    print(f"  a = [{a_vec_py[0]:.10f}, {a_vec_py[1]:.10f}, {a_vec_py[2]:.10f}]")
    print(f"  b = [{b_vec_py[0]:.10f}, {b_vec_py[1]:.10f}, {b_vec_py[2]:.10f}]")
    print(f"  c = [{c_vec_py[0]:.10f}, {c_vec_py[1]:.10f}, {c_vec_py[2]:.10f}]")
    print()
    print(f"  |a| = {torch.norm(a_vec_py).item():.10f} Å")
    print(f"  |b| = {torch.norm(b_vec_py).item():.10f} Å")
    print(f"  |c| = {torch.norm(c_vec_py).item():.10f} Å")
    print()

    # Compute deltas - PyTorch effectively always rescales like user_cell=1 case
    print("-"*80)
    print("Delta Analysis")
    print("-"*80)
    print()
    print("Case 1: PyTorch vs C with user_cell=0 (current supervisor command)")
    print()

    delta_a = a_vec_py - a_vec_c_no_rescale
    delta_b = b_vec_py - b_vec_c_no_rescale
    delta_c = c_vec_py - c_vec_c_no_rescale

    print("Vector differences (PyTorch - C_no_rescale):")
    print(f"  Δa = [{delta_a[0]:.10f}, {delta_a[1]:.10f}, {delta_a[2]:.10f}]")
    print(f"  Δb = [{delta_b[0]:.10f}, {delta_b[1]:.10f}, {delta_b[2]:.10f}]")
    print(f"  Δc = [{delta_c[0]:.10f}, {delta_c[1]:.10f}, {delta_c[2]:.10f}]")
    print()
    print(f"  |Δa| = {torch.norm(delta_a).item():.10f} Å")
    print(f"  |Δb| = {torch.norm(delta_b).item():.10f} Å")
    print(f"  |Δc| = {torch.norm(delta_c).item():.10f} Å")
    print()

    # Magnitude deltas
    mag_a_c_no = torch.norm(a_vec_c_no_rescale).item()
    mag_b_c_no = torch.norm(b_vec_c_no_rescale).item()
    mag_c_c_no = torch.norm(c_vec_c_no_rescale).item()

    mag_a_py = torch.norm(a_vec_py).item()
    mag_b_py = torch.norm(b_vec_py).item()
    mag_c_py = torch.norm(c_vec_py).item()

    print("Magnitude comparison (PyTorch vs C_no_rescale):")
    print(f"  a: C={mag_a_c_no:.10f} Å, PyTorch={mag_a_py:.10f} Å, Δ={mag_a_py-mag_a_c_no:.10f} Å ({100*(mag_a_py-mag_a_c_no)/mag_a_c_no:.4f}%)")
    print(f"  b: C={mag_b_c_no:.10f} Å, PyTorch={mag_b_py:.10f} Å, Δ={mag_b_py-mag_b_c_no:.10f} Å ({100*(mag_b_py-mag_b_c_no)/mag_b_c_no:.4f}%)")
    print(f"  c: C={mag_c_c_no:.10f} Å, PyTorch={mag_c_py:.10f} Å, Δ={mag_c_py-mag_c_c_no:.10f} Å ({100*(mag_c_py-mag_c_c_no)/mag_c_c_no:.4f}%)")
    print()

    print("Case 2: PyTorch vs C with user_cell=1 (if -cell was provided)")
    print()

    mag_a_c_res = torch.norm(a_vec_c_rescaled).item()
    mag_b_c_res = torch.norm(b_vec_c_rescaled).item()
    mag_c_c_res = torch.norm(c_vec_c_rescaled).item()

    delta_a_res = a_vec_py - a_vec_c_rescaled
    delta_b_res = b_vec_py - b_vec_c_rescaled
    delta_c_res = c_vec_py - c_vec_c_rescaled

    print("Magnitude comparison (PyTorch vs C_rescaled):")
    print(f"  a: C={mag_a_c_res:.10f} Å, PyTorch={mag_a_py:.10f} Å, Δ={mag_a_py-mag_a_c_res:.10f} Å ({100*(mag_a_py-mag_a_c_res)/mag_a_c_res:.4f}%)")
    print(f"  b: C={mag_b_c_res:.10f} Å, PyTorch={mag_b_py:.10f} Å, Δ={mag_b_py-mag_b_c_res:.10f} Å ({100*(mag_b_py-mag_b_c_res)/mag_b_c_res:.4f}%)")
    print(f"  c: C={mag_c_c_res:.10f} Å, PyTorch={mag_c_py:.10f} Å, Δ={mag_c_py-mag_c_c_res:.10f} Å ({100*(mag_c_py-mag_c_c_res)/mag_c_c_res:.4f}%)")
    print()

    # Component-wise analysis for b (the problematic one)
    print("-"*80)
    print("Detailed b-vector Component Analysis")
    print("-"*80)
    print(f"  b_x: C_no_rescale={b_vec_c_no_rescale[0]:.10f}, PyTorch={b_vec_py[0]:.10f}, Δ={delta_b[0]:.10f}")
    print(f"  b_y: C_no_rescale={b_vec_c_no_rescale[1]:.10f}, PyTorch={b_vec_py[1]:.10f}, Δ={delta_b[1]:.10f}")
    print(f"  b_z: C_no_rescale={b_vec_c_no_rescale[2]:.10f}, PyTorch={b_vec_py[2]:.10f}, Δ={delta_b[2]:.10f}")
    print()

    # Check expected cell parameters vs actual
    print("="*80)
    print("Summary")
    print("="*80)
    print()
    print("Expected cell parameters (from reciprocal_to_real_cell):")
    print(f"  a = {cell_params[0]:.6f} Å")
    print(f"  b = {cell_params[1]:.6f} Å")
    print(f"  c = {cell_params[2]:.6f} Å")
    print()
    print("C-style magnitudes (NO rescale, user_cell=0 - current supervisor command):")
    print(f"  |a| = {mag_a_c_no:.10f} Å")
    print(f"  |b| = {mag_b_c_no:.10f} Å")
    print(f"  |c| = {mag_c_c_no:.10f} Å")
    print()
    print("C-style magnitudes (WITH rescale, user_cell=1 - if -cell provided):")
    print(f"  |a| = {mag_a_c_res:.10f} Å")
    print(f"  |b| = {mag_b_c_res:.10f} Å")
    print(f"  |c| = {mag_c_c_res:.10f} Å")
    print()
    print("PyTorch magnitudes (current implementation - always rescales):")
    print(f"  |a| = {mag_a_py:.10f} Å")
    print(f"  |b| = {mag_b_py:.10f} Å")
    print(f"  |c| = {mag_c_py:.10f} Å")
    print()
    print("Conclusion:")
    print(f"  PyTorch matches C with user_cell=1 (rescaled): Δb = {torch.norm(delta_b_res).item():.10f} Å")
    print(f"  PyTorch differs from C with user_cell=0 (not rescaled): Δb = {torch.norm(delta_b).item():.6f} Å")
    print()
    print("  The current supervisor command uses -matrix A.mat WITHOUT -cell, so C has")
    print("  user_cell=0 and does NOT rescale. PyTorch always rescales (as if user_cell=1),")
    print("  causing a mismatch in the real-space lattice vectors.")
    print()
    print("  Expected impact on F_latt_b:")
    if mag_a_c_no == mag_a_py:
        print("  The magnitude match suggests rescaling is NOT the root cause of the")
        print("  F_latt_b discrepancy (21.6%). The issue must lie elsewhere (Miller")
        print("  index calculation, sincg evaluation, or orientation differences).")
    else:
        print("  The magnitude difference propagates to the Miller index calculations")
        print("  and subsequently to the sincg lattice shape factor, contributing to")
        print("  the observed 21.6% F_latt_b error in Phase K2 metrics.")
    print()

if __name__ == '__main__':
    main()
