#!/usr/bin/env python3
"""Test gradients of the sincg function which might be causing NaN issues."""

import os
import torch
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from nanobrag_torch.utils.physics import sincg

def test_sincg_gradients():
    """Test sincg function gradient behavior."""
    print("=== Testing sincg function gradients ===")

    # Test with simple parameter
    cell_a = torch.tensor(100.0, dtype=torch.float64, requires_grad=True)
    N = torch.tensor(5.0, dtype=torch.float64)

    # Test different input ranges for u
    test_cases = [
        torch.tensor(0.0, dtype=torch.float64),     # Zero case
        torch.tensor(1e-12, dtype=torch.float64),   # Very small
        torch.tensor(1e-6, dtype=torch.float64),    # Small
        torch.tensor(0.1, dtype=torch.float64),     # Normal
        torch.pi,                                   # π case
        torch.tensor(10.0, dtype=torch.float64),    # Large
    ]

    for i, u_base in enumerate(test_cases):
        print(f"\nTest case {i}: u_base = {u_base}")

        # Make u depend on cell_a to test gradients
        u = u_base * cell_a / 100.0  # Scale by cell_a
        u.retain_grad()

        try:
            result = sincg(u, N)
            print(f"  sincg({u.item():.2e}, {N.item()}) = {result.item():.6e}")
            print(f"  result requires_grad: {result.requires_grad}")
            print(f"  result contains NaN: {torch.isnan(result).any()}")

            # Test backward
            cell_a.grad = None
            result.backward()

            print(f"  cell_a.grad: {cell_a.grad}")
            print(f"  cell_a.grad contains NaN: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'None'}")

            if u.grad is not None:
                print(f"  u.grad: {u.grad}")
                print(f"  u.grad contains NaN: {torch.isnan(u.grad).any()}")

        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()

def test_sincg_realistic_values():
    """Test sincg with realistic values from simulation."""
    print("\n=== Testing sincg with realistic simulation values ===")

    # Values based on typical Miller indices
    cell_a = torch.tensor(100.0, dtype=torch.float64, requires_grad=True)
    N = torch.tensor(5.0, dtype=torch.float64)

    # Test with fractional Miller indices (h - h0)
    h_fractional_values = [
        0.0,      # Exact Bragg condition
        0.1,      # Small deviation
        0.5,      # Half-way between Bragg peaks
        0.9,      # Near next Bragg peak
        -0.1,     # Negative deviation
        -0.5,     # Negative half-way
    ]

    for h_frac in h_fractional_values:
        print(f"\nTesting h_frac = {h_frac}")

        # This mimics the actual calculation in simulator
        u = torch.pi * h_frac * cell_a / 100.0  # Scale factor to make it depend on cell_a

        try:
            result = sincg(u, N)
            print(f"  u = π * {h_frac} * (cell_a/100) = {u.item():.6e}")
            print(f"  sincg result = {result.item():.6e}")
            print(f"  result contains NaN: {torch.isnan(result).any()}")

            # Test backward
            cell_a.grad = None
            result.backward()

            print(f"  cell_a.grad: {cell_a.grad}")
            print(f"  gradient contains NaN: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'None'}")

        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()

def test_sincg_eps_sensitivity():
    """Test how sensitive sincg is to the epsilon value."""
    print("\n=== Testing sincg epsilon sensitivity ===")

    cell_a = torch.tensor(100.0, dtype=torch.float64, requires_grad=True)
    N = torch.tensor(5.0, dtype=torch.float64)

    # Test with values around the epsilon threshold
    eps_values = [1e-15, 1e-12, 1e-10, 1e-8, 1e-6]
    u_base = 1e-11  # Very small value

    for eps in eps_values:
        print(f"\nTesting with eps = {eps}")

        # Create a version of sincg with different epsilon
        def sincg_with_eps(u_val, N_val, eps_val):
            sin_u = torch.sin(u_val)
            is_near_zero = torch.abs(sin_u) < eps_val
            result = torch.where(is_near_zero, N_val, torch.sin(N_val * u_val) / sin_u)
            return result

        u = u_base * cell_a / 100.0

        try:
            result = sincg_with_eps(u, N, eps)
            print(f"  result = {result.item():.6e}")

            cell_a.grad = None
            result.backward()

            print(f"  cell_a.grad: {cell_a.grad}")
            print(f"  gradient contains NaN: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'None'}")

        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_sincg_gradients()
    test_sincg_realistic_values()
    test_sincg_eps_sensitivity()