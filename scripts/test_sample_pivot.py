#!/usr/bin/env python3
"""
Test SAMPLE pivot mode implementation.

This script explicitly tests the SAMPLE pivot mode by:
1. Running C code with -pivot sample
2. Running PyTorch with SAMPLE pivot
3. Comparing the results
"""

import os
import sys
import subprocess
import numpy as np
import torch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention, DetectorPivot
)
from nanobrag_torch.utils.units import mm_to_angstroms

def run_c_simulation_with_sample_pivot(output_file):
    """Run C simulation with explicit SAMPLE pivot."""
    cmd = [
        "./nanoBragg",
        "-lambda", "6.2",
        "-N", "5",
        "-cell", "100", "100", "100", "90", "90", "90",
        "-default_F", "100",
        "-distance", "100",
        "-detsize", "102.4",
        "-detpixels", "1024",
        "-Xbeam", "61.2", "-Ybeam", "61.2",
        "-detector_rotx", "5", "-detector_roty", "3", "-detector_rotz", "2",
        "-twotheta", "15",
        "-pivot", "sample",  # Explicitly set SAMPLE pivot
        "-oversample", "1",
        "-floatfile", output_file
    ]
    
    print("Running C simulation with command:")
    print(" ".join(cmd))
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("\nC output:")
    for line in result.stdout.split('\n'):
        if 'pivot' in line.lower() or 'DETECTOR_PIX0_VECTOR' in line:
            print(f"  {line}")
    
    # Load the output
    if os.path.exists(output_file):
        c_data = np.fromfile(output_file, dtype=np.float32).reshape(1024, 1024)
        return c_data
    else:
        raise RuntimeError(f"C simulation failed to create {output_file}")

def run_pytorch_simulation_with_sample_pivot():
    """Run PyTorch simulation with SAMPLE pivot."""
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    
    # Initialize configuration with SAMPLE pivot
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=61.2,
        beam_center_f=61.2,
        detector_convention=DetectorConvention.MOSFLM,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=15.0,
        detector_pivot=DetectorPivot.SAMPLE,  # Explicitly set SAMPLE pivot
    )
    
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
    )
    
    beam_config = BeamConfig(
        wavelength_A=6.2,
    )
    
    # No simulator config needed, default_F is handled differently
    
    # Initialize components
    detector = Detector(config=detector_config, device=torch.device("cpu"), dtype=torch.float64)
    crystal = Crystal(config=crystal_config, device=torch.device("cpu"), dtype=torch.float64)
    
    print(f"\nPyTorch detector configuration:")
    print(f"  Pivot mode: {detector_config.detector_pivot.name}")
    print(f"  Pix0 vector (meters): {detector.pix0_vector.numpy() / 1e10}")
    
    # Create simulator
    simulator = Simulator(
        detector=detector,
        crystal=crystal,
        wavelength_A=beam_config.wavelength_A,
        device=torch.device("cpu"),
        dtype=torch.float64,
    )
    
    # Run simulation with default F=100
    pytorch_data = simulator.simulate(default_F=100.0).numpy()
    
    return pytorch_data

def main():
    """Main test function."""
    print("="*60)
    print("SAMPLE PIVOT MODE TEST")
    print("="*60)
    
    # Run C simulation
    c_output_file = "test_sample_pivot_c.bin"
    try:
        c_data = run_c_simulation_with_sample_pivot(c_output_file)
        print(f"\nC simulation complete. Shape: {c_data.shape}")
    except Exception as e:
        print(f"ERROR running C simulation: {e}")
        return
    
    # Run PyTorch simulation
    try:
        pytorch_data = run_pytorch_simulation_with_sample_pivot()
        print(f"\nPyTorch simulation complete. Shape: {pytorch_data.shape}")
    except Exception as e:
        print(f"ERROR running PyTorch simulation: {e}")
        return
    
    # Compare results
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    
    # Calculate correlation
    c_flat = c_data.flatten()
    py_flat = pytorch_data.flatten()
    
    # Only compare non-zero pixels
    mask = (c_flat > 1e-10) | (py_flat > 1e-10)
    if mask.sum() > 0:
        correlation = np.corrcoef(c_flat[mask], py_flat[mask])[0, 1]
        print(f"Correlation coefficient: {correlation:.6f}")
        
        # Find brightest spots
        c_max_idx = np.unravel_index(np.argmax(c_data), c_data.shape)
        py_max_idx = np.unravel_index(np.argmax(pytorch_data), pytorch_data.shape)
        
        print(f"\nBrightest spot comparison:")
        print(f"  C: pixel {c_max_idx}, intensity {c_data[c_max_idx]:.2f}")
        print(f"  PyTorch: pixel {py_max_idx}, intensity {pytorch_data[py_max_idx]:.2f}")
        
        if correlation > 0.99:
            print("\n✅ SAMPLE pivot implementation is correct!")
        else:
            print(f"\n❌ SAMPLE pivot implementation has issues (correlation = {correlation:.6f})")
    else:
        print("ERROR: No non-zero pixels found in either image")
    
    # Cleanup
    if os.path.exists(c_output_file):
        os.remove(c_output_file)

if __name__ == "__main__":
    main()