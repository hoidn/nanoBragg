#!/usr/bin/env python3
"""Final validation test for pixel-perfect reproduction."""

import os
import sys
import torch
import numpy as np

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def main():
    print("=== Final Validation Test ===")

    # Load golden data
    golden_float_data = torch.from_numpy(
        np.fromfile("tests/golden_data/simple_cubic.bin", dtype=np.float32).reshape(
            500, 500
        )
    ).to(dtype=torch.float64)

    # Create simulator
    device = torch.device("cpu")
    dtype = torch.float64

    crystal = Crystal(device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)
    simulator = Simulator(
        crystal=crystal, detector=detector, device=device, dtype=dtype
    )

    # Load HKL data
    if os.path.exists("simple_cubic.hkl"):
        crystal.load_hkl("simple_cubic.hkl")

    # Run simulation
    result = simulator.run()

    # Compare results
    print(f"PyTorch output: max={torch.max(result):.2e}, mean={torch.mean(result):.2e}")
    print(
        f"Golden data:    max={torch.max(golden_float_data):.2e}, mean={torch.mean(golden_float_data):.2e}"
    )

    # Check if they match within tolerance
    try:
        if torch.allclose(result, golden_float_data, rtol=1e-3, atol=1e-6):
            print("✓ PASS: Results match within tolerance!")
            return True
        else:
            print("✗ FAIL: Results do not match")
            # Show difference statistics
            diff = torch.abs(result - golden_float_data)
            print(f"Max difference: {torch.max(diff):.2e}")
            print(f"Mean difference: {torch.mean(diff):.2e}")

            # Check scaling factor
            ratio = torch.max(golden_float_data) / torch.max(result)
            print(f"Scaling factor: {ratio:.2e}")

            return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
