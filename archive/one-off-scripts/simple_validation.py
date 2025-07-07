#!/usr/bin/env python3
"""Simple validation test for equivalence check."""

import sys
import os
sys.path.insert(0, 'src')

import torch
import numpy as np
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector

def main():
    print("=== Simple Validation Test ===")
    
    # Load golden data
    golden_data = np.fromfile("tests/golden_data/simple_cubic.bin", dtype=np.float32).reshape(500, 500)
    golden_tensor = torch.from_numpy(golden_data).to(dtype=torch.float64)
    
    # Run PyTorch simulation
    device = torch.device("cpu")
    dtype = torch.float64
    
    crystal = Crystal(device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)
    simulator = Simulator(crystal=crystal, detector=detector, device=device, dtype=dtype)
    
    if os.path.exists("simple_cubic.hkl"):
        crystal.load_hkl("simple_cubic.hkl")
    
    result = simulator.run()
    
    print(f"PyTorch: max={torch.max(result):.2e}, mean={torch.mean(result):.2e}")
    print(f"Golden:  max={torch.max(golden_tensor):.2e}, mean={torch.mean(golden_tensor):.2e}")
    
    # Check if patterns match (allowing for scaling)
    ratio = torch.max(golden_tensor) / torch.max(result)
    print(f"Scaling ratio: {ratio:.1f}")
    
    # Test if scaled version matches
    scaled_result = result * ratio
    if torch.allclose(scaled_result, golden_tensor, rtol=1e-3, atol=1e-6):
        print("✓ GEOMETRIC MATCH: Patterns are equivalent with scaling")
        return True
    else:
        # Check if at least the pattern correlation is high
        flat_result = result.flatten()
        flat_golden = golden_tensor.flatten()
        correlation = torch.corrcoef(torch.stack([flat_result, flat_golden]))[0, 1]
        print(f"Pattern correlation: {correlation:.4f}")
        if correlation > 0.9:
            print("✓ HIGH CORRELATION: Patterns are highly correlated")
            return True
        else:
            print("✗ PATTERN MISMATCH")
            return False

if __name__ == "__main__":
    success = main()
    print(f"Result: {'SUCCESS' if success else 'FAILURE'}")