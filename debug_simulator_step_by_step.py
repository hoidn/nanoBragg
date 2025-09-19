#!/usr/bin/env python3
"""
Debug the simulator run method step by step to find NaN source.
"""

import os
import torch

# Set environment variable for MKL compatibility
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def debug_simulator_step_by_step():
    """Debug simulator step by step to isolate NaN source."""
    device = torch.device("cpu")
    dtype = torch.float64

    # Create test input with requires_grad (exactly like the failing test)
    cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)

    # Create config exactly as in the failing test
    config_kwargs = {
        "cell_a": cell_a,
        "cell_b": 100.0,
        "cell_c": 100.0,
        "cell_alpha": 90.0,
        "cell_beta": 90.0,
        "cell_gamma": 90.0,
        "mosaic_spread_deg": 0.0,
        "mosaic_domains": 1,
        "N_cells": (5, 5, 5),
    }

    config = CrystalConfig(**config_kwargs)
    crystal = Crystal(config=config, device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)
    simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)

    print("=== Debugging Simulator Step by Step ===")

    # Manually step through the run() method to isolate the issue

    # Step 1: Get pixel coordinates
    print("1. Getting pixel coordinates...")
    pixel_coords_meters = detector.get_pixel_coords()
    pixel_coords_angstroms = pixel_coords_meters * 1e10  # Convert to Angstroms
    print(f"   Pixel coords shape: {pixel_coords_angstroms.shape}")
    print(f"   Pixel coords requires_grad: {pixel_coords_angstroms.requires_grad}")
    print(f"   NaN in pixel coords: {torch.isnan(pixel_coords_angstroms).any()}")

    # Step 2: Calculate diffracted beam direction
    print("2. Calculating diffracted beam direction...")
    sample_to_pixel = pixel_coords_angstroms  # Sample is at origin
    pixel_distances = torch.norm(sample_to_pixel, dim=-1, keepdim=True)
    diffracted_beam_unit = sample_to_pixel / pixel_distances
    print(f"   Diffracted beam shape: {diffracted_beam_unit.shape}")
    print(f"   NaN in diffracted beam: {torch.isnan(diffracted_beam_unit).any()}")

    # Step 3: Calculate scattering vector
    print("3. Calculating scattering vector...")
    incident_beam_unit = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
    wavelength = 6.2  # From test case
    scattering_vector = (diffracted_beam_unit - incident_beam_unit) / wavelength
    print(f"   Scattering vector shape: {scattering_vector.shape}")
    print(f"   NaN in scattering vector: {torch.isnan(scattering_vector).any()}")

    # Step 4: Get rotated lattice vectors
    print("4. Getting rotated lattice vectors...")
    try:
        (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = crystal.get_rotated_real_vectors(config)
        print(f"   Rotated vectors shape: {rot_a.shape}")
        print(f"   rot_a: {rot_a}")
        print(f"   rot_a requires_grad: {rot_a.requires_grad}")
        print(f"   NaN in rot_a: {torch.isnan(rot_a).any()}")
        print(f"   NaN in rot_b: {torch.isnan(rot_b).any()}")
        print(f"   NaN in rot_c: {torch.isnan(rot_c).any()}")
    except Exception as e:
        print(f"   ERROR in get_rotated_real_vectors: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 5: Calculate Miller indices
    print("5. Calculating Miller indices...")
    # Broadcast for dot products
    scattering_broadcast = scattering_vector.unsqueeze(-2).unsqueeze(-2)
    rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0)
    rot_b_broadcast = rot_b.unsqueeze(0).unsqueeze(0)
    rot_c_broadcast = rot_c.unsqueeze(0).unsqueeze(0)

    # Calculate Miller indices
    from nanobrag_torch.utils.geometry import dot_product
    h = dot_product(scattering_broadcast, rot_a_broadcast)
    k = dot_product(scattering_broadcast, rot_b_broadcast)
    l = dot_product(scattering_broadcast, rot_c_broadcast)

    print(f"   h shape: {h.shape}")
    print(f"   h requires_grad: {h.requires_grad}")
    print(f"   NaN in h: {torch.isnan(h).any()}")
    print(f"   NaN in k: {torch.isnan(k).any()}")
    print(f"   NaN in l: {torch.isnan(l).any()}")

    # Step 6: Test backward pass on Miller indices
    print("6. Testing backward pass on Miller indices...")
    try:
        loss_h = h.sum()
        print(f"   loss_h: {loss_h}")
        print(f"   loss_h requires_grad: {loss_h.requires_grad}")

        if cell_a.grad is not None:
            cell_a.grad.zero_()

        loss_h.backward(retain_graph=True)
        print(f"   cell_a.grad after h backward: {cell_a.grad}")
        print(f"   NaN in cell_a.grad: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    except Exception as e:
        print(f"   ERROR in Miller indices backward: {e}")
        import traceback
        traceback.print_exc()

    # Step 7: Get structure factors
    print("7. Getting structure factors...")
    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)

    try:
        F_cell = crystal.get_structure_factor(h0, k0, l0)
        print(f"   F_cell shape: {F_cell.shape}")
        print(f"   F_cell requires_grad: {F_cell.requires_grad}")
        print(f"   NaN in F_cell: {torch.isnan(F_cell).any()}")
    except Exception as e:
        print(f"   ERROR in get_structure_factor: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 8: Calculate lattice structure factor
    print("8. Calculating lattice structure factor...")
    try:
        from nanobrag_torch.utils.physics import sincg
        from nanobrag_torch.config import CrystalShape

        Na = crystal.N_cells_a
        Nb = crystal.N_cells_b
        Nc = crystal.N_cells_c

        # Use SQUARE shape (default)
        F_latt_a = sincg(torch.pi * (h - h0), Na)
        F_latt_b = sincg(torch.pi * (k - k0), Nb)
        F_latt_c = sincg(torch.pi * (l - l0), Nc)
        F_latt = F_latt_a * F_latt_b * F_latt_c

        print(f"   F_latt shape: {F_latt.shape}")
        print(f"   F_latt requires_grad: {F_latt.requires_grad}")
        print(f"   NaN in F_latt: {torch.isnan(F_latt).any()}")

    except Exception as e:
        print(f"   ERROR in lattice structure factor: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 9: Calculate intensity
    print("9. Calculating intensity...")
    try:
        I_pixel = F_cell * F_cell * F_latt * F_latt
        print(f"   I_pixel shape: {I_pixel.shape}")
        print(f"   I_pixel requires_grad: {I_pixel.requires_grad}")
        print(f"   NaN in I_pixel: {torch.isnan(I_pixel).any()}")

        # Sum over phi and mosaic dimensions
        I_final = I_pixel.sum(dim=(-2, -1))  # Sum over phi and mosaic
        print(f"   I_final shape: {I_final.shape}")
        print(f"   I_final requires_grad: {I_final.requires_grad}")
        print(f"   NaN in I_final: {torch.isnan(I_final).any()}")

    except Exception as e:
        print(f"   ERROR in intensity calculation: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 10: Test backward pass on final intensity
    print("10. Testing backward pass on final intensity...")
    try:
        loss = I_final.sum()
        print(f"   loss: {loss}")
        print(f"   loss requires_grad: {loss.requires_grad}")

        if cell_a.grad is not None:
            cell_a.grad.zero_()

        loss.backward()
        print(f"   cell_a.grad after final backward: {cell_a.grad}")
        print(f"   NaN in final cell_a.grad: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    except Exception as e:
        print(f"   ERROR in final backward pass: {e}")
        import traceback
        traceback.print_exc()

    return loss, cell_a.grad


if __name__ == "__main__":
    print("=== Debugging Simulator Step by Step ===")

    try:
        loss, grad = debug_simulator_step_by_step()

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