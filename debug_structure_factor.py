#!/usr/bin/env python3
"""
Debug the structure factor calculation step by step.
"""

import os
import torch

# Set environment variable for MKL compatibility
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.utils.physics import sincg


def debug_structure_factor_path():
    """Debug the exact computation that causes NaN gradients."""
    device = torch.device("cpu")
    dtype = torch.float64

    # Create test input with requires_grad (exactly like the failing test)
    cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)

    config = CrystalConfig(
        cell_a=cell_a,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        mosaic_spread_deg=0.0,
        mosaic_domains=1,
        N_cells=(5, 5, 5),
    )
    crystal = Crystal(config=config, device=device, dtype=dtype)

    print("=== Debugging Structure Factor Path ===")

    # Create simple test Miller indices that would be typical
    # For a cubic crystal with 100 Å cell, we'd expect h,k,l around 0 at the center
    h = torch.tensor([[0.1], [0.0], [0.2]], dtype=dtype, requires_grad=True)
    k = torch.tensor([[0.0], [0.1], [0.0]], dtype=dtype, requires_grad=True)
    l = torch.tensor([[0.0], [0.0], [0.1]], dtype=dtype, requires_grad=True)

    print(f"Test Miller indices:")
    print(f"  h: {h.flatten()}")
    print(f"  k: {k.flatten()}")
    print(f"  l: {l.flatten()}")

    # Get integer parts
    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)

    print(f"Integer parts:")
    print(f"  h0: {h0.flatten()}")
    print(f"  k0: {k0.flatten()}")
    print(f"  l0: {l0.flatten()}")

    # Test structure factor lookup
    print("\n1. Testing structure factor lookup...")
    F_cell = crystal.get_structure_factor(h0, k0, l0)
    print(f"   F_cell: {F_cell.flatten()}")
    print(f"   F_cell requires_grad: {F_cell.requires_grad}")

    # Test lattice factor calculation step by step
    print("\n2. Testing lattice factor calculation...")

    # Get crystal dimensions
    Na = crystal.N_cells_a
    Nb = crystal.N_cells_b
    Nc = crystal.N_cells_c
    print(f"   Crystal dimensions: Na={Na}, Nb={Nb}, Nc={Nc}")

    # Calculate fractional parts
    h_frac = h - h0
    k_frac = k - k0
    l_frac = l - l0
    print(f"   Fractional parts:")
    print(f"     h_frac: {h_frac.flatten()}")
    print(f"     k_frac: {k_frac.flatten()}")
    print(f"     l_frac: {l_frac.flatten()}")

    # Calculate sincg arguments
    u_h = torch.pi * h_frac
    u_k = torch.pi * k_frac
    u_l = torch.pi * l_frac
    print(f"   sincg arguments:")
    print(f"     u_h: {u_h.flatten()}")
    print(f"     u_k: {u_k.flatten()}")
    print(f"     u_l: {u_l.flatten()}")

    # Test each sincg call individually
    print("\n3. Testing individual sincg calls...")

    try:
        F_latt_a = sincg(u_h, Na)
        print(f"   F_latt_a: {F_latt_a.flatten()}")
        print(f"   F_latt_a requires_grad: {F_latt_a.requires_grad}")
        print(f"   NaN in F_latt_a: {torch.isnan(F_latt_a).any()}")

        # Test backward on F_latt_a alone
        if cell_a.grad is not None:
            cell_a.grad.zero_()
        loss_a = F_latt_a.sum()
        loss_a.backward(retain_graph=True)
        print(f"   cell_a.grad after F_latt_a: {cell_a.grad}")
        print(f"   NaN in F_latt_a grad: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    except Exception as e:
        print(f"   ERROR in F_latt_a: {e}")
        import traceback
        traceback.print_exc()

    try:
        F_latt_b = sincg(u_k, Nb)
        print(f"   F_latt_b: {F_latt_b.flatten()}")
        print(f"   NaN in F_latt_b: {torch.isnan(F_latt_b).any()}")

        F_latt_c = sincg(u_l, Nc)
        print(f"   F_latt_c: {F_latt_c.flatten()}")
        print(f"   NaN in F_latt_c: {torch.isnan(F_latt_c).any()}")

    except Exception as e:
        print(f"   ERROR in F_latt_b/c: {e}")
        import traceback
        traceback.print_exc()

    # Test combined lattice factor
    print("\n4. Testing combined lattice factor...")
    try:
        F_latt = F_latt_a * F_latt_b * F_latt_c
        print(f"   F_latt: {F_latt.flatten()}")
        print(f"   F_latt requires_grad: {F_latt.requires_grad}")
        print(f"   NaN in F_latt: {torch.isnan(F_latt).any()}")

        # Test backward on combined F_latt
        if cell_a.grad is not None:
            cell_a.grad.zero_()
        loss_latt = F_latt.sum()
        loss_latt.backward(retain_graph=True)
        print(f"   cell_a.grad after F_latt: {cell_a.grad}")
        print(f"   NaN in F_latt grad: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    except Exception as e:
        print(f"   ERROR in combined F_latt: {e}")
        import traceback
        traceback.print_exc()

    # Test final intensity calculation
    print("\n5. Testing final intensity calculation...")
    try:
        I = F_cell * F_cell * F_latt * F_latt
        print(f"   I: {I.flatten()}")
        print(f"   I requires_grad: {I.requires_grad}")
        print(f"   NaN in I: {torch.isnan(I).any()}")

        # Test backward on final intensity
        if cell_a.grad is not None:
            cell_a.grad.zero_()
        loss_final = I.sum()
        loss_final.backward()
        print(f"   cell_a.grad after final: {cell_a.grad}")
        print(f"   NaN in final grad: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    except Exception as e:
        print(f"   ERROR in final intensity: {e}")
        import traceback
        traceback.print_exc()


def debug_with_realistic_miller_indices():
    """Test with Miller indices that are more realistic to the actual simulation."""
    print("\n=== Testing with realistic Miller indices ===")

    device = torch.device("cpu")
    dtype = torch.float64

    # Create the same setup as the failing test
    cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)
    config = CrystalConfig(
        cell_a=cell_a,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        mosaic_spread_deg=0.0,
        mosaic_domains=1,
        N_cells=(5, 5, 5),
    )
    crystal = Crystal(config=config, device=device, dtype=dtype)

    # Create Miller indices that include exactly zero fractional parts
    # This might be what's causing the issue
    h = torch.tensor([[0.0], [1.0], [0.0]], dtype=dtype, requires_grad=True)
    k = torch.tensor([[0.0], [0.0], [1.0]], dtype=dtype, requires_grad=True)
    l = torch.tensor([[0.0], [0.0], [0.0]], dtype=dtype, requires_grad=True)

    print(f"Realistic Miller indices:")
    print(f"  h: {h.flatten()}")
    print(f"  k: {k.flatten()}")
    print(f"  l: {l.flatten()}")

    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)

    # Calculate fractional parts (these will be exactly zero!)
    h_frac = h - h0
    k_frac = k - k0
    l_frac = l - l0

    print(f"Fractional parts (note the zeros!):")
    print(f"  h_frac: {h_frac.flatten()}")
    print(f"  k_frac: {k_frac.flatten()}")
    print(f"  l_frac: {l_frac.flatten()}")

    # These will be exactly zero or multiples of π
    u_h = torch.pi * h_frac
    u_k = torch.pi * k_frac
    u_l = torch.pi * l_frac

    print(f"sincg arguments (many zeros!):")
    print(f"  u_h: {u_h.flatten()}")
    print(f"  u_k: {u_k.flatten()}")
    print(f"  u_l: {u_l.flatten()}")

    # This is likely where the NaN comes from!
    print("\nTesting sincg with exact zeros...")

    Na = crystal.N_cells_a
    Nb = crystal.N_cells_b
    Nc = crystal.N_cells_c

    try:
        F_latt_a = sincg(u_h, Na)
        F_latt_b = sincg(u_k, Nb)
        F_latt_c = sincg(u_l, Nc)
        F_latt = F_latt_a * F_latt_b * F_latt_c

        print(f"F_latt_a: {F_latt_a.flatten()}")
        print(f"F_latt_b: {F_latt_b.flatten()}")
        print(f"F_latt_c: {F_latt_c.flatten()}")
        print(f"F_latt: {F_latt.flatten()}")

        # Get structure factor
        F_cell = crystal.get_structure_factor(h0, k0, l0)
        I = F_cell * F_cell * F_latt * F_latt

        # Test backward pass
        if cell_a.grad is not None:
            cell_a.grad.zero_()

        loss = I.sum()
        loss.backward()

        print(f"Final cell_a.grad: {cell_a.grad}")
        print(f"NaN in gradient: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=== Debugging Structure Factor Calculation ===")

    try:
        debug_structure_factor_path()
        debug_with_realistic_miller_indices()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()