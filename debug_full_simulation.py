#!/usr/bin/env python3
"""
Debug the full simulation to reproduce the exact NaN gradient issue.
"""

import os
import torch

# Set environment variable for MKL compatibility
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from nanobrag_torch.config import CrystalConfig, DetectorConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def debug_full_simulation():
    """Run the exact same simulation as the failing test but with debugging."""
    device = torch.device("cpu")
    dtype = torch.float64

    # Create test input exactly like the failing test
    cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)

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

    print("=== Debugging Full Simulation ===")
    print(f"Detector size: {detector.config.spixels} x {detector.config.fpixels}")

    # Run the simulation exactly as in the failing test
    print("Running full simulation...")
    image = simulator.run()

    print(f"Image shape: {image.shape}")
    print(f"Image requires_grad: {image.requires_grad}")
    print(f"Image sum: {image.sum()}")
    print(f"NaN in image: {torch.isnan(image).any()}")

    # Test backward pass
    print("Testing backward pass...")
    loss = image.sum()
    print(f"Loss: {loss}")

    if cell_a.grad is not None:
        cell_a.grad.zero_()

    loss.backward()

    print(f"cell_a.grad: {cell_a.grad}")
    print(f"NaN in gradient: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")

    return loss, cell_a.grad


def debug_reduced_simulation():
    """Test with a much smaller detector to isolate the issue."""
    print("\n=== Testing with reduced detector size ===")

    device = torch.device("cpu")
    dtype = torch.float64

    cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)

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

    # Create a much smaller detector
    detector_config = DetectorConfig(
        spixels=16,  # Much smaller
        fpixels=16,
        pixel_size_mm=0.1,
        distance_mm=100.0
    )
    detector = Detector(config=detector_config, device=device, dtype=dtype)
    simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)

    print(f"Reduced detector size: {detector.config.spixels} x {detector.config.fpixels}")

    # Run simulation
    image = simulator.run()
    print(f"Image shape: {image.shape}")
    print(f"Image sum: {image.sum()}")
    print(f"NaN in image: {torch.isnan(image).any()}")

    # Test backward pass
    loss = image.sum()
    if cell_a.grad is not None:
        cell_a.grad.zero_()

    loss.backward()

    print(f"cell_a.grad (reduced): {cell_a.grad}")
    print(f"NaN in reduced gradient: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No grad'}")


def debug_edge_pixels():
    """Check if edge pixels might contain problematic values."""
    print("\n=== Debugging edge pixels ===")

    device = torch.device("cpu")
    dtype = torch.float64

    # Create detector and get pixel coordinates
    detector = Detector(device=device, dtype=dtype)
    pixel_coords = detector.get_pixel_coords()

    print(f"Pixel coordinates shape: {pixel_coords.shape}")
    print(f"Min pixel coord: {pixel_coords.min()}")
    print(f"Max pixel coord: {pixel_coords.max()}")

    # Check for any problematic values
    print(f"NaN in pixel coords: {torch.isnan(pixel_coords).any()}")
    print(f"Inf in pixel coords: {torch.isinf(pixel_coords).any()}")

    # Convert to Angstroms
    pixel_coords_angstroms = pixel_coords * 1e10
    print(f"Min pixel coord (Å): {pixel_coords_angstroms.min()}")
    print(f"Max pixel coord (Å): {pixel_coords_angstroms.max()}")

    # Calculate distances
    distances = torch.norm(pixel_coords_angstroms, dim=-1)
    print(f"Min distance: {distances.min()}")
    print(f"Max distance: {distances.max()}")
    print(f"NaN in distances: {torch.isnan(distances).any()}")

    # Calculate scattering vectors
    diffracted_beam = pixel_coords_angstroms / distances.unsqueeze(-1)
    incident_beam = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
    wavelength = 6.2

    scattering_vector = (diffracted_beam - incident_beam) / wavelength
    print(f"Min scattering vector: {scattering_vector.min()}")
    print(f"Max scattering vector: {scattering_vector.max()}")
    print(f"NaN in scattering vector: {torch.isnan(scattering_vector).any()}")

    # Check corner pixels specifically
    corners = [
        (0, 0),           # Top-left
        (0, -1),          # Top-right
        (-1, 0),          # Bottom-left
        (-1, -1),         # Bottom-right
    ]

    for i, (s, f) in enumerate(corners):
        corner_coord = pixel_coords_angstroms[s, f, :]
        corner_dist = torch.norm(corner_coord)
        corner_scatter = (corner_coord / corner_dist - incident_beam) / wavelength
        print(f"Corner {i+1} ({s}, {f}): coord={corner_coord}, dist={corner_dist}, scatter={corner_scatter}")


if __name__ == "__main__":
    print("=== Debugging Full Simulation for NaN Gradients ===")

    try:
        # Test edge pixels first
        debug_edge_pixels()

        # Test reduced simulation
        debug_reduced_simulation()

        # Test full simulation
        loss, grad = debug_full_simulation()

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