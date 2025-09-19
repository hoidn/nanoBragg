#!/usr/bin/env python3
"""
Test Y-component calculation without rotations to isolate the error.

This script tests pix0_vector calculation with all rotations set to 0
to determine if the 43mm Y-component error is in the base calculation
or in the rotation application.
"""

import os
import sys
import torch
import numpy as np
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set PyTorch environment for MKL compatibility
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot, BeamConfig, CrystalConfig
from nanobrag_torch.models.detector import Detector
from c_reference_utils import build_nanobragg_command, generate_identity_matrix

def run_c_reference_simple(detector_config, crystal_config, beam_config):
    """Run C reference and return output text"""
    # Generate temp matrix file
    matrix_file = "temp_identity.mat"
    generate_identity_matrix(matrix_file)
    
    # Build command
    cmd = build_nanobragg_command(
        detector_config, crystal_config, beam_config, 
        matrix_file=matrix_file,
        executable_path="golden_suite_generator/nanoBragg"
    )
    
    print(f"C Command: {' '.join(cmd)}")
    
    # Execute
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Clean up temp file
    Path(matrix_file).unlink(missing_ok=True)
    
    if result.returncode != 0:
        print(f"❌ C execution failed: {result.returncode}")
        print(f"STDERR: {result.stderr}")
        return None, None
    
    return result.stdout, result.stderr

def test_y_without_rotations():
    """Test pix0_vector Y-component with all rotations = 0"""
    
    print("=== Testing Y-component WITHOUT rotations ===")
    
    # Configuration with NO rotations
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=61.2,  # mm
        beam_center_f=61.2,  # mm
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.SAMPLE,
        # ALL ROTATIONS SET TO ZERO
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=0.0,
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
        N_source_points=1,
        source_distance_mm=10000.0,
        source_size_mm=0.0,
    )
    
    # Create detector
    detector = Detector(detector_config)
    
    print(f"PyTorch pix0_vector: {detector.pix0_vector}")
    print(f"  X: {detector.pix0_vector[0].item():.6f} m")
    print(f"  Y: {detector.pix0_vector[1].item():.6f} m")
    print(f"  Z: {detector.pix0_vector[2].item():.6f} m")
    
    print("\n=== Running C reference (no rotations) ===")
    c_output, c_stderr = run_c_reference_simple(detector_config, crystal_config, beam_config)
    
    if c_output is None:
        print("❌ C execution failed")
        return
    
    # Extract pix0_vector from C output (look in both stdout and stderr)
    c_pix0 = None
    all_output = (c_output or '') + '\n' + (c_stderr or '')
    
    for line in all_output.split('\n'):
        if 'DETECTOR_PIX0_VECTOR' in line and not 'before' in line.lower():
            parts = line.split()
            if len(parts) >= 4:
                try:
                    x = float(parts[1])
                    y = float(parts[2]) 
                    z = float(parts[3])
                    c_pix0 = np.array([x, y, z])
                    print(f"Found C pix0_vector in line: {line.strip()}")
                    break
                except (ValueError, IndexError):
                    continue
    
    if c_pix0 is not None:
        print(f"C pix0_vector: [{c_pix0[0]:.6f}, {c_pix0[1]:.6f}, {c_pix0[2]:.6f}]")
        print(f"  X: {c_pix0[0]:.6f} m")
        print(f"  Y: {c_pix0[1]:.6f} m") 
        print(f"  Z: {c_pix0[2]:.6f} m")
        
        # Calculate differences
        py_pix0 = detector.pix0_vector.detach().numpy()
        diff = py_pix0 - c_pix0
        
        print(f"\n=== DIFFERENCES ===")
        print(f"X diff: {diff[0]*1000:.3f} mm")
        print(f"Y diff: {diff[1]*1000:.3f} mm  <-- KEY ERROR")
        print(f"Z diff: {diff[2]*1000:.3f} mm")
        
        # Check if Y error still exists without rotations
        if abs(diff[1]*1000) > 20:  # > 20mm is huge error
            print(f"\n❌ Y ERROR STILL EXISTS without rotations: {diff[1]*1000:.1f}mm")
            print("   This means the error is in the BASE calculation, not rotations")
        else:
            print(f"\n✅ Y error is small without rotations: {diff[1]*1000:.1f}mm")
            print("   The error must be introduced by rotations")
            
    else:
        print("❌ Could not extract C pix0_vector from output")
        print("First 10 lines of C stderr:")
        if c_stderr:
            for i, line in enumerate(c_stderr.split('\n')[:10]):
                if line.strip():
                    print(f"  {i+1}: {line}")
        print("\nFirst 10 lines of C stdout:")
        if c_output:
            for i, line in enumerate(c_output.split('\n')[:10]):
                if line.strip():
                    print(f"  {i+1}: {line}")

if __name__ == "__main__":
    test_y_without_rotations()