#!/usr/bin/env python3
"""Debug script to identify the source of NaN gradients in nanoBragg PyTorch implementation."""

import os
import torch
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

def test_individual_crystal_properties():
    """Test gradient flow through individual Crystal properties."""
    print("=== Testing Crystal property gradients ===")

    device = torch.device('cpu')
    dtype = torch.float64

    # Create tensor parameter with gradient
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

    # Test each property individually
    properties_to_test = ['a', 'b', 'c', 'a_star', 'b_star', 'c_star', 'V']

    for prop_name in properties_to_test:
        cell_a.grad = None  # Reset gradient

        try:
            prop_value = getattr(crystal, prop_name)
            print(f"\n{prop_name}: shape={prop_value.shape}, requires_grad={prop_value.requires_grad}")
            print(f"{prop_name} values: {prop_value}")
            print(f"{prop_name} contains NaN: {torch.isnan(prop_value).any()}")

            # Test gradient computation
            loss = prop_value.sum()
            loss.backward()

            print(f"cell_a.grad after {prop_name}: {cell_a.grad}")
            print(f"cell_a.grad contains NaN: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'None'}")

        except Exception as e:
            print(f"Error testing {prop_name}: {e}")
            import traceback
            traceback.print_exc()

def test_crystal_computation_stages():
    """Test specific stages of crystal computation to isolate NaN source."""
    print("\n=== Testing Crystal computation stages ===")

    device = torch.device('cpu')
    dtype = torch.float64

    # Create tensor parameter with gradient
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

    # Test compute_cell_tensors directly
    print("\nTesting compute_cell_tensors()...")
    try:
        cell_a.grad = None
        tensors = crystal.compute_cell_tensors()

        print("Cell tensors computed successfully")
        for key, tensor in tensors.items():
            print(f"  {key}: shape={tensor.shape}, requires_grad={tensor.requires_grad}")
            print(f"  {key} contains NaN: {torch.isnan(tensor).any()}")
            print(f"  {key} values: {tensor}")

        # Test backward on volume (simple scalar)
        print("\nTesting backward on volume...")
        loss = tensors['V']
        loss.backward()
        print(f"cell_a.grad after V backward: {cell_a.grad}")
        print(f"V gradient contains NaN: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'None'}")

    except Exception as e:
        print(f"Error in compute_cell_tensors: {e}")
        import traceback
        traceback.print_exc()

def test_simulator_stages():
    """Test each stage of the simulator to find where NaN appears."""
    print("\n=== Testing Simulator stages ===")

    device = torch.device('cpu')
    dtype = torch.float64

    # Create tensor parameter with gradient
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

    # Test pixel coordinates
    print("\nTesting pixel coordinates...")
    pixel_coords = detector.get_pixel_coords()
    print(f"Pixel coords shape: {pixel_coords.shape}")
    print(f"Pixel coords contains NaN: {torch.isnan(pixel_coords).any()}")

    # Test scattering vector calculation
    print("\nTesting scattering vector calculation...")
    pixel_coords_angstroms = pixel_coords * 1e10
    pixel_squared_sum = torch.sum(pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True)
    pixel_squared_sum = torch.clamp(pixel_squared_sum, min=0.0)
    pixel_magnitudes = torch.sqrt(pixel_squared_sum)
    diffracted_beam_unit = pixel_coords_angstroms / pixel_magnitudes

    incident_beam_direction = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
    incident_beam_unit = incident_beam_direction.expand_as(diffracted_beam_unit)
    wavelength = 6.2  # Angstroms

    scattering_vector = (diffracted_beam_unit - incident_beam_unit) / wavelength
    print(f"Scattering vector contains NaN: {torch.isnan(scattering_vector).any()}")

    # Test lattice vector access
    print("\nTesting lattice vector access...")
    try:
        cell_a.grad = None

        # Test getting rotated vectors
        (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = crystal.get_rotated_real_vectors(config)
        print(f"Rotated vectors computed successfully")
        print(f"rot_a contains NaN: {torch.isnan(rot_a).any()}")
        print(f"rot_a requires_grad: {rot_a.requires_grad}")

        # Test Miller index calculation (simplified)
        # Just test with a single pixel
        s_vec = scattering_vector[0, 0, :].unsqueeze(0).unsqueeze(0).unsqueeze(0)  # Shape: [1, 1, 1, 3]
        a_vec = rot_a[0, 0, :].unsqueeze(0).unsqueeze(0).unsqueeze(0)  # Shape: [1, 1, 1, 3]

        h = torch.sum(s_vec * a_vec, dim=-1)  # Dot product
        print(f"Miller index h: {h}")
        print(f"h contains NaN: {torch.isnan(h).any()}")
        print(f"h requires_grad: {h.requires_grad}")

        # Test backward
        h.backward()
        print(f"cell_a.grad after h backward: {cell_a.grad}")
        print(f"h gradient contains NaN: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'None'}")

    except Exception as e:
        print(f"Error in Miller index calculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting NaN gradient debugging...")

    test_individual_crystal_properties()
    test_crystal_computation_stages()
    test_simulator_stages()

    print("\nDebugging complete.")