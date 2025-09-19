#!/usr/bin/env python3
"""
Debug the gradient dependency chain to find where NaN is introduced.
"""

import os
import torch

# Set environment variable for MKL compatibility
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def debug_dependency_chain():
    """Trace the gradient flow from cell_a to final loss."""
    device = torch.device("cpu")
    dtype = torch.float64

    # Create test input exactly like the failing test
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
    detector = Detector(device=device, dtype=dtype)
    simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)

    print("=== Debugging Gradient Dependency Chain ===")

    # Check if cell_a is properly connected to crystal properties
    print("1. Testing crystal property connections...")
    print(f"   cell_a: {cell_a}, requires_grad: {cell_a.requires_grad}")
    print(f"   crystal.cell_a: {crystal.cell_a}, requires_grad: {crystal.cell_a.requires_grad}")
    print(f"   crystal.cell_a is cell_a: {crystal.cell_a is cell_a}")

    # Test if crystal.a depends on cell_a
    a_vec = crystal.a
    print(f"   crystal.a: {a_vec}, requires_grad: {a_vec.requires_grad}")

    # Test backward pass on crystal.a
    if cell_a.grad is not None:
        cell_a.grad.zero_()

    loss_a = a_vec.sum()
    loss_a.backward(retain_graph=True)
    print(f"   cell_a.grad after crystal.a: {cell_a.grad}")
    print(f"   NaN in crystal.a grad: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    # Now test the exact computation from the simulator but with minimal data
    print("\n2. Testing minimal simulator computation...")

    # Get a small subset of pixel coordinates (just center pixel)
    pixel_coords = detector.get_pixel_coords()
    center_pixel = pixel_coords[512:513, 512:513, :]  # Shape: (1, 1, 3)
    print(f"   Center pixel coords: {center_pixel.shape}")

    # Convert to Angstroms and calculate scattering vector
    pixel_coords_angstroms = center_pixel * 1e10
    sample_to_pixel = pixel_coords_angstroms
    pixel_distances = torch.norm(sample_to_pixel, dim=-1, keepdim=True)
    diffracted_beam_unit = sample_to_pixel / pixel_distances

    incident_beam_unit = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
    wavelength = 6.2
    scattering_vector = (diffracted_beam_unit - incident_beam_unit) / wavelength

    print(f"   Scattering vector: {scattering_vector.shape}")

    # Get rotated lattice vectors
    (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = crystal.get_rotated_real_vectors(config)

    print(f"   rot_a: {rot_a.shape}, requires_grad: {rot_a.requires_grad}")
    print(f"   rot_a values: {rot_a}")

    # Test Miller index calculation
    from nanobrag_torch.utils.geometry import dot_product

    scattering_broadcast = scattering_vector.unsqueeze(-2).unsqueeze(-2)
    rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0)

    h = dot_product(scattering_broadcast, rot_a_broadcast)
    print(f"   h: {h.shape}, value: {h}, requires_grad: {h.requires_grad}")

    # Test backward on h
    if cell_a.grad is not None:
        cell_a.grad.zero_()

    loss_h = h.sum()
    loss_h.backward(retain_graph=True)
    print(f"   cell_a.grad after h: {cell_a.grad}")
    print(f"   NaN in h grad: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    # Now add the structure factor and see what happens
    print("\n3. Adding structure factor...")

    h0 = torch.round(h)
    F_cell = crystal.get_structure_factor(h0, torch.zeros_like(h0), torch.zeros_like(h0))
    print(f"   F_cell: {F_cell}, requires_grad: {F_cell.requires_grad}")

    # Test with just F_cell multiplication
    if cell_a.grad is not None:
        cell_a.grad.zero_()

    loss_with_fcell = (h * F_cell).sum()
    loss_with_fcell.backward(retain_graph=True)
    print(f"   cell_a.grad after h*F_cell: {cell_a.grad}")
    print(f"   NaN in h*F_cell grad: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    # Now add sincg calculation
    print("\n4. Adding sincg (lattice factor)...")

    from nanobrag_torch.utils.physics import sincg

    Na = crystal.N_cells_a
    h_frac = h - h0
    u_h = torch.pi * h_frac

    print(f"   h_frac: {h_frac}")
    print(f"   u_h: {u_h}")

    F_latt_a = sincg(u_h, Na)
    print(f"   F_latt_a: {F_latt_a}, requires_grad: {F_latt_a.requires_grad}")

    # Test with F_latt_a
    if cell_a.grad is not None:
        cell_a.grad.zero_()

    loss_with_flatt = (h * F_latt_a).sum()
    loss_with_flatt.backward(retain_graph=True)
    print(f"   cell_a.grad after h*F_latt_a: {cell_a.grad}")
    print(f"   NaN in h*F_latt_a grad: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    # Finally, test the full intensity calculation
    print("\n5. Testing full intensity calculation...")

    # Get all three lattice factors
    k = dot_product(scattering_broadcast, rot_b.unsqueeze(0).unsqueeze(0))
    l = dot_product(scattering_broadcast, rot_c.unsqueeze(0).unsqueeze(0))

    k0 = torch.round(k)
    l0 = torch.round(l)

    k_frac = k - k0
    l_frac = l - l0

    u_k = torch.pi * k_frac
    u_l = torch.pi * l_frac

    F_latt_b = sincg(u_k, crystal.N_cells_b)
    F_latt_c = sincg(u_l, crystal.N_cells_c)

    F_latt = F_latt_a * F_latt_b * F_latt_c
    F_cell_full = crystal.get_structure_factor(h0, k0, l0)

    print(f"   F_latt: {F_latt}")
    print(f"   F_cell_full: {F_cell_full}")

    # Final intensity
    I = F_cell_full * F_cell_full * F_latt * F_latt

    if cell_a.grad is not None:
        cell_a.grad.zero_()

    loss_final = I.sum()
    print(f"   Final loss: {loss_final}")

    loss_final.backward()
    print(f"   Final cell_a.grad: {cell_a.grad}")
    print(f"   Final NaN check: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    return loss_final, cell_a.grad


if __name__ == "__main__":
    print("=== Debugging Gradient Dependency Chain ===")

    try:
        loss, grad = debug_dependency_chain()

        print("\n=== Summary ===")
        print(f"Final loss: {loss}")
        print(f"Final gradient: {grad}")
        if grad is not None and torch.isnan(grad).any():
            print("ERROR: NaN gradient detected!")
        else:
            print("Success: No NaN gradients found")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()