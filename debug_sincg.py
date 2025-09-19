#!/usr/bin/env python3
"""
Debug the sincg function to find NaN gradients.
"""

import os
import torch

# Set environment variable for MKL compatibility
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from nanobrag_torch.utils.physics import sincg


def debug_sincg():
    """Test sincg function with differentiable inputs."""
    device = torch.device("cpu")
    dtype = torch.float64

    # Create test parameters similar to what's used in the simulator
    cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)

    # Test various inputs to sincg
    print("=== Testing sincg function ===")

    # Test case 1: Normal case (should work)
    print("1. Testing normal case...")
    u1 = torch.tensor(0.5, dtype=dtype, requires_grad=True)
    N1 = torch.tensor(5.0, dtype=dtype, requires_grad=True)
    result1 = sincg(u1, N1)
    print(f"   u1: {u1}, N1: {N1}")
    print(f"   result1: {result1}")
    print(f"   result1 requires_grad: {result1.requires_grad}")

    try:
        result1.backward()
        print(f"   u1.grad: {u1.grad}")
        print(f"   N1.grad: {N1.grad}")
        print("   Normal case: OK")
    except Exception as e:
        print(f"   Normal case ERROR: {e}")

    # Test case 2: Near-zero case (potential problem)
    print("\n2. Testing near-zero case...")
    u2 = torch.tensor(1e-12, dtype=dtype, requires_grad=True)
    N2 = torch.tensor(5.0, dtype=dtype, requires_grad=True)
    result2 = sincg(u2, N2)
    print(f"   u2: {u2}, N2: {N2}")
    print(f"   result2: {result2}")
    print(f"   sin(u2): {torch.sin(u2)}")

    try:
        result2.backward()
        print(f"   u2.grad: {u2.grad}")
        print(f"   N2.grad: {N2.grad}")
        print("   Near-zero case: OK")
    except Exception as e:
        print(f"   Near-zero case ERROR: {e}")

    # Test case 3: Exactly zero case
    print("\n3. Testing exactly zero case...")
    u3 = torch.tensor(0.0, dtype=dtype, requires_grad=True)
    N3 = torch.tensor(5.0, dtype=dtype, requires_grad=True)
    result3 = sincg(u3, N3)
    print(f"   u3: {u3}, N3: {N3}")
    print(f"   result3: {result3}")
    print(f"   sin(u3): {torch.sin(u3)}")

    try:
        result3.backward()
        print(f"   u3.grad: {u3.grad}")
        print(f"   N3.grad: {N3.grad}")
        print("   Exactly zero case: OK")
    except Exception as e:
        print(f"   Exactly zero case ERROR: {e}")

    # Test case 4: π multiple (sin(π) = 0, problematic)
    print("\n4. Testing π multiple case...")
    u4 = torch.tensor(torch.pi, dtype=dtype, requires_grad=True)
    N4 = torch.tensor(5.0, dtype=dtype, requires_grad=True)
    result4 = sincg(u4, N4)
    print(f"   u4: {u4}, N4: {N4}")
    print(f"   result4: {result4}")
    print(f"   sin(u4): {torch.sin(u4)}")

    try:
        result4.backward()
        print(f"   u4.grad: {u4.grad}")
        print(f"   N4.grad: {N4.grad}")
        print("   π multiple case: OK")
    except Exception as e:
        print(f"   π multiple case ERROR: {e}")

    # Test case 5: Large array like in the simulator
    print("\n5. Testing large array case...")
    # Create array that might contain problematic values
    h_values = torch.linspace(-2.0, 2.0, 100, dtype=dtype, requires_grad=True)
    u5 = torch.pi * h_values  # This will include multiples of π
    N5 = torch.tensor(5.0, dtype=dtype, requires_grad=True)

    result5 = sincg(u5, N5)
    print(f"   u5 shape: {u5.shape}")
    print(f"   result5 shape: {result5.shape}")
    print(f"   NaN in result5: {torch.isnan(result5).any()}")
    print(f"   Min sin(u5): {torch.sin(u5).min()}")
    print(f"   Max sin(u5): {torch.sin(u5).max()}")

    try:
        loss5 = result5.sum()
        loss5.backward()
        print(f"   h_values.grad NaN: {torch.isnan(h_values.grad).any() if h_values.grad is not None else 'No grad'}")
        print(f"   N5.grad: {N5.grad}")
        print("   Large array case: OK")
    except Exception as e:
        print(f"   Large array case ERROR: {e}")


def test_alternative_sincg():
    """Test an improved sincg implementation."""
    print("\n=== Testing improved sincg ===")

    def sincg_improved(u: torch.Tensor, N: torch.Tensor) -> torch.Tensor:
        """Improved sincg with better gradient handling."""
        # Handle both scalar and tensor N - expand to broadcast with u
        if N.ndim == 0:
            N = N.expand_as(u)

        # Use larger epsilon and more careful handling
        eps = 1e-8
        sin_u = torch.sin(u)

        # For very small u, use Taylor series: sincg(u) ≈ N - N·u²/6 + ...
        # This avoids the division entirely for small values
        is_small = torch.abs(u) < eps

        # Normal case: sin(Nu)/sin(u)
        normal_result = torch.sin(N * u) / sin_u

        # Small case: use Taylor expansion
        # sincg(u) = sin(Nu)/sin(u) ≈ N - (N³-N)u²/6 for small u
        small_result = N - (N * N * N - N) * u * u / 6.0

        result = torch.where(is_small, small_result, normal_result)
        return result

    # Test the improved version
    u = torch.linspace(-2.0, 2.0, 100, dtype=torch.float64, requires_grad=True)
    u_pi = torch.pi * u
    N = torch.tensor(5.0, dtype=torch.float64, requires_grad=True)

    result = sincg_improved(u_pi, N)
    print(f"Improved sincg result shape: {result.shape}")
    print(f"NaN in improved result: {torch.isnan(result).any()}")

    try:
        loss = result.sum()
        loss.backward()
        print(f"u.grad NaN: {torch.isnan(u.grad).any() if u.grad is not None else 'No grad'}")
        print(f"N.grad: {N.grad}")
        print("Improved sincg: OK")
    except Exception as e:
        print(f"Improved sincg ERROR: {e}")


if __name__ == "__main__":
    print("=== Debugging sincg function ===")

    try:
        debug_sincg()
        test_alternative_sincg()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()