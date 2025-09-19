#!/usr/bin/env python3
"""
Minimal debugging script to isolate NaN gradients in Crystal class.
"""

import os
import torch
import numpy as np

# Set environment variable for MKL compatibility
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def debug_crystal_creation():
    """Debug Crystal creation with requires_grad tensors."""
    print("=== Testing Crystal Creation ===")

    device = torch.device("cpu")
    dtype = torch.float64

    # Create test input with requires_grad
    cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)

    # Create config with the parameter as a tensor
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

    # Create config
    config = CrystalConfig(**config_kwargs)
    print(f"Config created successfully")
    print(f"cell_a in config: {config.cell_a}, requires_grad: {config.cell_a.requires_grad}")

    # Create crystal with this config
    crystal = Crystal(config=config, device=device, dtype=dtype)
    print(f"Crystal created successfully")

    # Check key properties
    print(f"crystal.a: {crystal.a}")
    print(f"crystal.a requires_grad: {crystal.a.requires_grad}")
    print(f"crystal.a_star: {crystal.a_star}")
    print(f"crystal.a_star requires_grad: {crystal.a_star.requires_grad}")
    print(f"crystal.volume: {crystal.volume}")
    print(f"crystal.volume requires_grad: {crystal.volume.requires_grad}")

    # Check for NaNs in key tensors
    print("\n=== Checking for NaNs ===")
    print(f"NaN in crystal.a: {torch.isnan(crystal.a).any()}")
    print(f"NaN in crystal.a_star: {torch.isnan(crystal.a_star).any()}")
    print(f"NaN in crystal.volume: {torch.isnan(crystal.volume).any()}")

    return crystal, cell_a


def debug_simulation_step_by_step():
    """Debug simulation creation step by step."""
    print("\n=== Testing Simulation Creation ===")

    crystal, cell_a = debug_crystal_creation()

    device = torch.device("cpu")
    dtype = torch.float64

    # Create minimal detector
    detector = Detector(device=device, dtype=dtype)
    print(f"Detector created successfully")

    # Check detector properties
    pixel_coords = detector.get_pixel_coords()
    print(f"detector pixel coords: {pixel_coords.shape}")
    print(f"detector pixel coords requires_grad: {pixel_coords.requires_grad}")
    print(f"NaN in detector pixel coords: {torch.isnan(pixel_coords).any()}")

    # Create config for simulator
    config = crystal.config

    # Create simulator
    simulator = Simulator(
        crystal, detector, crystal_config=config, device=device, dtype=dtype
    )
    print(f"Simulator created successfully")

    return simulator, cell_a


def debug_forward_pass():
    """Debug forward pass to find where NaN appears."""
    print("\n=== Testing Forward Pass ===")

    simulator, cell_a = debug_simulation_step_by_step()

    # Run simulation
    print("Running simulation...")
    image = simulator.run()
    print(f"Simulation completed")
    print(f"Image shape: {image.shape}")
    print(f"Image requires_grad: {image.requires_grad}")
    print(f"NaN in image: {torch.isnan(image).any()}")
    print(f"Image sum: {image.sum()}")
    print(f"Image sum requires_grad: {image.sum().requires_grad}")

    return image, cell_a


def debug_backward_pass():
    """Debug backward pass to find where NaN gradients appear."""
    print("\n=== Testing Backward Pass ===")

    image, cell_a = debug_forward_pass()

    # Compute loss
    loss = image.sum()
    print(f"Loss: {loss}")
    print(f"Loss requires_grad: {loss.requires_grad}")

    # Run backward pass
    print("Running backward pass...")
    loss.backward()

    # Check gradients
    print(f"cell_a.grad: {cell_a.grad}")
    print(f"NaN in cell_a.grad: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'No gradient'}")

    return cell_a.grad


def debug_individual_operations():
    """Debug individual mathematical operations to find NaN source."""
    print("\n=== Testing Individual Operations ===")

    device = torch.device("cpu")
    dtype = torch.float64

    # Test basic tensor operations
    cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)

    # Test conversion to radians (common source of issues)
    deg_to_rad = torch.pi / 180.0
    angle_deg = torch.tensor(90.0, dtype=dtype, requires_grad=True)
    angle_rad = angle_deg * deg_to_rad
    print(f"Angle conversion: {angle_deg} deg -> {angle_rad} rad")

    # Test trigonometric functions
    cos_val = torch.cos(angle_rad)
    sin_val = torch.sin(angle_rad)
    print(f"cos(90°): {cos_val}")
    print(f"sin(90°): {sin_val}")
    print(f"NaN in cos: {torch.isnan(cos_val)}")
    print(f"NaN in sin: {torch.isnan(sin_val)}")

    # Test division operations (potential source of NaN)
    test_denom = sin_val  # This could be near zero
    if torch.abs(test_denom) < 1e-10:
        print(f"WARNING: Very small denominator detected: {test_denom}")

    # Test volume calculation components
    print("\n--- Testing volume calculation ---")
    a = torch.tensor([100.0, 0.0, 0.0], dtype=dtype, requires_grad=True)
    b = torch.tensor([0.0, 100.0, 0.0], dtype=dtype, requires_grad=True)
    c = torch.tensor([0.0, 0.0, 100.0], dtype=dtype, requires_grad=True)

    cross_product = torch.cross(b, c, dim=0)
    dot_product = torch.dot(a, cross_product)
    volume = torch.abs(dot_product)

    print(f"Cross product b x c: {cross_product}")
    print(f"Dot product a · (b x c): {dot_product}")
    print(f"Volume: {volume}")
    print(f"NaN in volume: {torch.isnan(volume)}")

    # Test reciprocal calculation
    print("\n--- Testing reciprocal calculation ---")
    volume_expanded = volume.expand(3)
    print(f"Volume expanded: {volume_expanded}")

    # This could be a source of NaN if volume becomes zero
    reciprocal_scale = cross_product / volume_expanded
    print(f"Reciprocal scale: {reciprocal_scale}")
    print(f"NaN in reciprocal scale: {torch.isnan(reciprocal_scale).any()}")


if __name__ == "__main__":
    print("=== Debugging NaN Gradients ===")

    try:
        # Test individual operations first
        debug_individual_operations()

        # Test backward pass
        grad = debug_backward_pass()

        print(f"\n=== Summary ===")
        if grad is not None and torch.isnan(grad).any():
            print("ERROR: NaN gradient detected!")
        else:
            print("No NaN gradients detected in this simple test")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()