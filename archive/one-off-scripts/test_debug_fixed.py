#!/usr/bin/env python3
"""Quick debug script to test the fixed simulator."""

import torch
import sys
import os
sys.path.insert(0, 'src')

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

def main():
    print("=== Testing Fixed Simulator ===")
    
    # Create components
    device = torch.device("cpu")
    dtype = torch.float64
    
    crystal = Crystal(device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)
    simulator = Simulator(crystal, detector, device=device, dtype=dtype)
    
    print(f"Wavelength: {simulator.wavelength}")
    print(f"Crystal a_star: {crystal.a_star}")
    print(f"Detector distance: {detector.distance}")
    print(f"Detector pixel_size: {detector.pixel_size}")
    
    # Test single pixel coordinates
    pixel_coords = detector.get_pixel_coords()
    print(f"Pixel coords shape: {pixel_coords.shape}")
    print(f"Sample pixel coord [250, 250]: {pixel_coords[250, 250]}")
    print(f"Sample pixel coord [250, 350]: {pixel_coords[250, 350]}")
    
    # Run simulation on small subset
    detector.spixels = 3
    detector.fpixels = 3
    detector.invalidate_cache()
    
    small_simulator = Simulator(crystal, detector, device=device, dtype=dtype)
    result = small_simulator.run()
    
    print(f"Small result shape: {result.shape}")
    print(f"Small result:\n{result}")
    print(f"Small result max: {torch.max(result):.2e}")
    
if __name__ == "__main__":
    main()