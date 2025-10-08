#!/usr/bin/env python3
"""
CLI-FLAGS-003 Phase M2h.3: Gradcheck Probe for Phi Carryover Cache

Purpose: Verify that the phi carryover cache maintains gradient connectivity
through the store/retrieve cycle in c-parity mode.

This probe tests a minimal 2×2 ROI cache to confirm:
1. Gradient flow from cell parameters through cached rotation vectors
2. No .detach()/.clone() breaks in the cache implementation
3. Device/dtype neutrality (CUDA + CPU)

Expected behavior: cell_a.grad should be non-null after backprop through
the cache retrieval and dummy loss computation.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import torch
from nanobrag_torch.config import BeamConfig
from nanobrag_torch.models.crystal import Crystal, CrystalConfig


def run_gradcheck(device_str: str, dtype_str: str) -> dict:
    """Run gradcheck probe and return status dict"""

    # Parse device/dtype
    if device_str == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_str)

    dtype = torch.float64 if dtype_str == "float64" else torch.float32

    print(f"Device: {device}, dtype: {dtype}")

    # Create crystal config with differentiable cell_a
    cell_a = torch.tensor(100.0, requires_grad=True, dtype=dtype, device=device)

    crystal_config = CrystalConfig(
        cell_a=cell_a,
        cell_b=torch.tensor(100.0, dtype=dtype, device=device),
        cell_c=torch.tensor(100.0, dtype=dtype, device=device),
        cell_alpha=torch.tensor(90.0, dtype=dtype, device=device),
        cell_beta=torch.tensor(90.0, dtype=dtype, device=device),
        cell_gamma=torch.tensor(90.0, dtype=dtype, device=device),
        N_cells=(5, 5, 5),
        phi_start_deg=torch.tensor(0.0, dtype=dtype, device=device),
        osc_range_deg=torch.tensor(0.1, dtype=dtype, device=device),
        phi_steps=10,
        phi_carryover_mode="c-parity",  # Enable carryover cache
        mosaic_domains=1,
        mosaic_spread_deg=torch.tensor(0.0, dtype=dtype, device=device),
        default_F=100.0
    )

    beam_config = BeamConfig(
        wavelength_A=torch.tensor(6.2, dtype=dtype, device=device)
    )

    crystal = Crystal(crystal_config, beam_config=beam_config, device=device, dtype=dtype)

    # Initialize 2×2 pixel cache
    print("Initializing 2×2 phi cache...")
    crystal.initialize_phi_cache(spixels=2, fpixels=2)

    # Create dummy rotation vectors with gradients
    slow_indices = torch.tensor([0, 0, 1, 1], dtype=torch.long, device=device)
    fast_indices = torch.tensor([0, 1, 0, 1], dtype=torch.long, device=device)

    # Generate dummy vectors via crystal computation (to ensure grad connectivity)
    # We'll use a small perturbation on the base reciprocal vectors
    dummy_real_a = crystal.a * 1.001
    dummy_real_b = crystal.b * 1.001
    dummy_real_c = crystal.c * 1.001

    dummy_recip_a = crystal.a_star * 1.001
    dummy_recip_b = crystal.b_star * 1.001
    dummy_recip_c = crystal.c_star * 1.001

    # Stack into (batch, mosaic, 3) shape for 4 pixels
    dummy_real_vecs_a = dummy_real_a.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()
    dummy_real_vecs_b = dummy_real_b.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()
    dummy_real_vecs_c = dummy_real_c.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()

    dummy_recip_vecs_a = dummy_recip_a.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()
    dummy_recip_vecs_b = dummy_recip_b.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()
    dummy_recip_vecs_c = dummy_recip_c.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()

    # Store final phi vectors in cache
    print("Storing phi final vectors...")
    real_tuple = (dummy_real_vecs_a, dummy_real_vecs_b, dummy_real_vecs_c)
    recip_tuple = (dummy_recip_vecs_a, dummy_recip_vecs_b, dummy_recip_vecs_c)
    crystal.store_phi_final(slow_indices, fast_indices, real_tuple, recip_tuple)

    # Create fresh vectors (to be replaced by carryover)
    fresh_real_a = crystal.a * 0.999
    fresh_real_b = crystal.b * 0.999
    fresh_real_c = crystal.c * 0.999
    fresh_recip_a = crystal.a_star * 0.999
    fresh_recip_b = crystal.b_star * 0.999
    fresh_recip_c = crystal.c_star * 0.999

    fresh_real_vecs_a = fresh_real_a.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()
    fresh_real_vecs_b = fresh_real_b.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()
    fresh_real_vecs_c = fresh_real_c.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()
    fresh_recip_vecs_a = fresh_recip_a.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()
    fresh_recip_vecs_b = fresh_recip_b.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()
    fresh_recip_vecs_c = fresh_recip_c.unsqueeze(0).unsqueeze(0).expand(4, 1, 3).contiguous()

    fresh_real_tuple = (fresh_real_vecs_a, fresh_real_vecs_b, fresh_real_vecs_c)
    fresh_recip_tuple = (fresh_recip_vecs_a, fresh_recip_vecs_b, fresh_recip_vecs_c)

    # Retrieve cached vectors
    print("Retrieving cached vectors via apply_phi_carryover...")
    # apply_phi_carryover takes fresh vectors and replaces φ=0 with cached values
    retrieved_real, retrieved_recip = crystal.apply_phi_carryover(
        slow_indices, fast_indices, fresh_real_tuple, fresh_recip_tuple
    )
    retrieved_real_a, retrieved_real_b, retrieved_real_c = retrieved_real
    retrieved_recip_a, retrieved_recip_b, retrieved_recip_c = retrieved_recip

    # Compute dummy loss
    loss = (retrieved_real_a.sum() + retrieved_real_b.sum() + retrieved_real_c.sum() +
            retrieved_recip_a.sum() + retrieved_recip_b.sum() + retrieved_recip_c.sum())
    print(f"Loss: {loss.item():.6e}")

    # Backpropagate
    print("Backpropagating...")
    loss.backward()

    # Check gradient on cell_a
    grad_present = cell_a.grad is not None and not torch.all(cell_a.grad == 0)

    result = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "device": str(device),
        "dtype": str(dtype),
        "grad_present": grad_present,
        "loss": float(loss.item()),
        "grad_value": float(cell_a.grad.item()) if grad_present else None,
        "success": grad_present
    }

    print(f"\nGradient present: {grad_present}")
    if grad_present:
        print(f"cell_a.grad: {cell_a.grad.item():.6e}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Gradcheck probe for phi carryover cache")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto",
                      help="Device to run on (default: auto)")
    parser.add_argument("--dtype", choices=["float64", "float32"], default="float64",
                      help="Data type (default: float64)")
    args = parser.parse_args()

    print("=" * 80)
    print("CLI-FLAGS-003 Phase M2h.3: Gradcheck Probe")
    print("=" * 80)
    print()

    try:
        result = run_gradcheck(args.device, args.dtype)

        # Print JSON result
        print()
        print("Result JSON:")
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        if result["success"]:
            print("\n✓ GRADCHECK PASS: Gradient flow maintained through cache")
            sys.exit(0)
        else:
            print("\n✗ GRADCHECK FAIL: Gradient lost through cache")
            print("This indicates .detach(), .clone(), or .item() broke the computation graph")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
