#!/usr/bin/env python3
"""
Debug the compute_cell_tensors method step by step to find NaN source.
"""

import os
import torch

# Set environment variable for MKL compatibility
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal


def debug_compute_cell_tensors():
    """Step through compute_cell_tensors to find NaN source."""
    device = torch.device("cpu")
    dtype = torch.float64

    # Create test input with requires_grad
    cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)
    cell_b = torch.tensor(100.0, dtype=dtype, requires_grad=True)
    cell_c = torch.tensor(100.0, dtype=dtype, requires_grad=True)
    cell_alpha = torch.tensor(90.0, dtype=dtype, requires_grad=True)
    cell_beta = torch.tensor(90.0, dtype=dtype, requires_grad=True)
    cell_gamma = torch.tensor(90.0, dtype=dtype, requires_grad=True)

    # Manually recreate the compute_cell_tensors logic step by step
    print("=== Manual compute_cell_tensors debugging ===")

    # Convert angles to radians
    alpha_rad = torch.deg2rad(cell_alpha)
    beta_rad = torch.deg2rad(cell_beta)
    gamma_rad = torch.deg2rad(cell_gamma)
    print(f"Angles in radians: α={alpha_rad}, β={beta_rad}, γ={gamma_rad}")

    # Calculate trigonometric values
    cos_alpha = torch.cos(alpha_rad)
    cos_beta = torch.cos(beta_rad)
    cos_gamma = torch.cos(gamma_rad)
    sin_gamma = torch.sin(gamma_rad)
    print(f"Trigonometric values:")
    print(f"  cos_alpha: {cos_alpha}")
    print(f"  cos_beta: {cos_beta}")
    print(f"  cos_gamma: {cos_gamma}")
    print(f"  sin_gamma: {sin_gamma}")

    # Calculate cell volume using C-code formula
    aavg = (alpha_rad + beta_rad + gamma_rad) / 2.0
    print(f"aavg: {aavg}")

    skew = (
        torch.sin(aavg)
        * torch.sin(aavg - alpha_rad)
        * torch.sin(aavg - beta_rad)
        * torch.sin(aavg - gamma_rad)
    )
    print(f"skew before abs: {skew}")
    skew = torch.abs(skew)
    print(f"skew after abs: {skew}")

    # Handle degenerate cases where skew approaches zero
    skew = torch.clamp(skew, min=1e-12)
    print(f"skew after clamp: {skew}")

    V = 2.0 * cell_a * cell_b * cell_c * torch.sqrt(skew)
    print(f"Volume: {V}")

    # Ensure volume is not too small
    V = torch.clamp(V, min=1e-6)
    V_star = 1.0 / V
    print(f"V_star: {V_star}")

    # Calculate reciprocal cell lengths
    sin_alpha = torch.sin(alpha_rad)
    sin_beta = torch.sin(beta_rad)

    a_star_length = cell_b * cell_c * sin_alpha * V_star
    b_star_length = cell_c * cell_a * sin_beta * V_star
    c_star_length = cell_a * cell_b * sin_gamma * V_star
    print(f"Reciprocal lengths: a*={a_star_length}, b*={b_star_length}, c*={c_star_length}")

    # Calculate reciprocal angles - THIS IS LIKELY THE PROBLEM FOR 90° angles
    print("\n=== Reciprocal angle calculations (potential NaN source) ===")

    # Clamp denominators to avoid division by zero
    denom1 = torch.clamp(sin_beta * sin_gamma, min=1e-12)
    denom2 = torch.clamp(sin_gamma * sin_alpha, min=1e-12)
    denom3 = torch.clamp(sin_alpha * sin_beta, min=1e-12)
    print(f"Denominators: {denom1}, {denom2}, {denom3}")

    cos_alpha_star = (cos_beta * cos_gamma - cos_alpha) / denom1
    cos_beta_star = (cos_gamma * cos_alpha - cos_beta) / denom2
    cos_gamma_star = (cos_alpha * cos_beta - cos_gamma) / denom3
    print(f"Reciprocal cosines:")
    print(f"  cos_alpha_star: {cos_alpha_star}")
    print(f"  cos_beta_star: {cos_beta_star}")
    print(f"  cos_gamma_star: {cos_gamma_star}")

    # For 90-degree angles, cos_alpha = cos_beta = cos_gamma ≈ 0
    # So cos_alpha_star = (0 * 0 - 0) / 1 = 0
    # This should be fine...

    # Check the sin_gamma_star calculation
    cos_gamma_star_clamped = torch.clamp(cos_gamma_star, min=-1.0, max=1.0)
    sin_gamma_star_input = torch.clamp(1.0 - torch.pow(cos_gamma_star_clamped, 2), min=0.0)
    sin_gamma_star = torch.sqrt(sin_gamma_star_input)
    print(f"sin_gamma_star calculation:")
    print(f"  cos_gamma_star_clamped: {cos_gamma_star_clamped}")
    print(f"  1 - cos²: {sin_gamma_star_input}")
    print(f"  sin_gamma_star: {sin_gamma_star}")

    # Now test backward pass on individual pieces
    print("\n=== Testing backward passes on individual operations ===")

    # Test each potentially problematic operation
    test_tensors = [
        ("V", V),
        ("V_star", V_star),
        ("cos_alpha_star", cos_alpha_star),
        ("cos_beta_star", cos_beta_star),
        ("cos_gamma_star", cos_gamma_star),
        ("sin_gamma_star", sin_gamma_star),
    ]

    for name, tensor in test_tensors:
        if tensor.requires_grad:
            try:
                # Test if this tensor can compute gradients
                loss = tensor.sum() if tensor.numel() > 1 else tensor
                loss.backward(retain_graph=True)

                # Check if any of the input gradients are NaN
                grads = [cell_a.grad, cell_b.grad, cell_c.grad, cell_alpha.grad, cell_beta.grad, cell_gamma.grad]
                nan_found = any(g is not None and torch.isnan(g).any() for g in grads)

                print(f"{name}: {'NaN gradients detected!' if nan_found else 'OK'}")

                # Clear gradients for next test
                for param in [cell_a, cell_b, cell_c, cell_alpha, cell_beta, cell_gamma]:
                    if param.grad is not None:
                        param.grad.zero_()

            except Exception as e:
                print(f"{name}: Error during backward: {e}")
        else:
            print(f"{name}: No gradients (requires_grad=False)")

    return V, V_star, cos_alpha_star, cos_beta_star, cos_gamma_star, sin_gamma_star


def debug_with_crystal_class():
    """Test the actual Crystal class method."""
    print("\n=== Testing Crystal class method ===")

    device = torch.device("cpu")
    dtype = torch.float64

    # Create test input with requires_grad
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

    # Call compute_cell_tensors directly
    cell_tensors = crystal.compute_cell_tensors()

    # Check each tensor in the result
    for key, tensor in cell_tensors.items():
        print(f"{key}: {tensor}, requires_grad: {tensor.requires_grad}, has_nan: {torch.isnan(tensor).any()}")

    # Test backward pass on each tensor individually
    print("\nTesting backward pass on each tensor:")

    for key, tensor in cell_tensors.items():
        if tensor.requires_grad:
            try:
                # Clear gradients
                if cell_a.grad is not None:
                    cell_a.grad.zero_()

                # Test backward pass
                loss = tensor.sum() if tensor.numel() > 1 else tensor
                loss.backward(retain_graph=True)

                # Check gradient
                if cell_a.grad is not None:
                    nan_in_grad = torch.isnan(cell_a.grad).any()
                    print(f"  {key}: gradient={'NaN' if nan_in_grad else cell_a.grad}")
                else:
                    print(f"  {key}: No gradient computed")

            except Exception as e:
                print(f"  {key}: Error: {e}")


if __name__ == "__main__":
    print("=== Debugging compute_cell_tensors ===")

    try:
        # Manual step-by-step debugging
        debug_compute_cell_tensors()

        # Test actual Crystal class
        debug_with_crystal_class()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()