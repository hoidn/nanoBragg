#!/usr/bin/env python3
"""
Examine C code behavior with twotheta to understand the discrepancy.

This script will test different twotheta values and see what C outputs.
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

def run_c_with_twotheta(twotheta_deg):
    """Run C code with specific twotheta value and extract pix0_vector"""
    
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=61.2,  # mm
        beam_center_f=61.2,  # mm
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.SAMPLE,
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=twotheta_deg,
    )
    
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
    )
    
    beam_config = BeamConfig(
        wavelength_A=6.2, N_source_points=1,
        source_distance_mm=10000.0, source_size_mm=0.0,
    )
    
    # Generate temp matrix file
    matrix_file = "temp_identity.mat"
    generate_identity_matrix(matrix_file)
    
    # Build command
    cmd = build_nanobragg_command(
        detector_config, crystal_config, beam_config, 
        matrix_file=matrix_file,
        executable_path="golden_suite_generator/nanoBragg"
    )
    
    # Execute C code
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    Path(matrix_file).unlink(missing_ok=True)
    
    if result.returncode != 0:
        print(f"❌ C execution failed for twotheta={twotheta_deg}")
        return None, None
    
    # Extract pix0_vector
    all_output = (result.stdout or '') + '\n' + (result.stderr or '')
    c_pix0 = None
    
    for line in all_output.split('\n'):
        if 'DETECTOR_PIX0_VECTOR' in line and not 'before' in line.lower():
            parts = line.split()
            if len(parts) >= 4:
                try:
                    x = float(parts[1])
                    y = float(parts[2]) 
                    z = float(parts[3])
                    c_pix0 = np.array([x, y, z])
                    break
                except (ValueError, IndexError):
                    continue
    
    # Get PyTorch result for comparison
    detector = Detector(detector_config)
    py_pix0 = detector.pix0_vector.detach().numpy()
    
    return c_pix0, py_pix0

def test_twotheta_behavior():
    """Test C behavior with different twotheta values"""
    
    print("=== EXAMINING C TWOTHETA BEHAVIOR ===")
    print("Testing different twotheta values to understand C behavior...")
    
    # Test different twotheta values
    twotheta_values = [0.0, 5.0, 10.0, 15.0, 30.0, 45.0]
    
    print(f"{'TwoTheta':>8} {'C_Y':>10} {'PyTorch_Y':>12} {'Diff_mm':>10} {'Match':>8}")
    print("-" * 60)
    
    results = []
    
    for twotheta in twotheta_values:
        c_pix0, py_pix0 = run_c_with_twotheta(twotheta)
        
        if c_pix0 is not None and py_pix0 is not None:
            c_y = c_pix0[1]
            py_y = py_pix0[1]
            diff_mm = (py_y - c_y) * 1000
            
            match = "✅" if abs(diff_mm) < 1 else "❌"
            
            print(f"{twotheta:8.1f}° {c_y:10.6f} {py_y:12.6f} {diff_mm:10.1f} {match:>8}")
            
            results.append({
                'twotheta': twotheta,
                'c_y': c_y,
                'py_y': py_y,
                'diff_mm': diff_mm
            })
        else:
            print(f"{twotheta:8.1f}° {'FAILED':>10} {'FAILED':>12} {'N/A':>10} {'❌':>8}")
    
    # Analysis
    print(f"\n=== ANALYSIS ===")
    
    if len(results) >= 2:
        # Check if C Y values change at all
        c_y_values = [r['c_y'] for r in results]
        c_y_constant = all(abs(y - c_y_values[0]) < 1e-6 for y in c_y_values)
        
        if c_y_constant:
            print(f"🚨 C Y-component is CONSTANT at {c_y_values[0]:.6f} m across all twotheta values!")
            print("   This suggests C code is NOT rotating pix0_vector with twotheta")
        else:
            print("✅ C Y-component varies with twotheta (as expected)")
        
        # Check PyTorch behavior 
        py_y_values = [r['py_y'] for r in results]
        py_y_constant = all(abs(y - py_y_values[0]) < 1e-6 for y in py_y_values)
        
        if py_y_constant:
            print(f"❌ PyTorch Y-component is CONSTANT at {py_y_values[0]:.6f} m")
            print("   This would be a bug in PyTorch")
        else:
            print("✅ PyTorch Y-component varies with twotheta (as expected)")
    
        print(f"\nKey insight:")
        if c_y_constant and not py_y_constant:
            print("C is NOT applying twotheta rotation to pix0_vector")
            print("PyTorch IS applying twotheta rotation to pix0_vector")
            print("This explains the Y-component mismatch!")
        
        # Let's check the 0° case specifically
        zero_result = next((r for r in results if r['twotheta'] == 0.0), None)
        if zero_result and abs(zero_result['diff_mm']) < 1:
            print(f"\n✅ At twotheta=0°, C and PyTorch agree: {zero_result['diff_mm']:.1f}mm diff")
            print("   This confirms the base calculation is correct")
            
        # Check if C Y matches the 0° case
        if zero_result and c_y_constant:
            if abs(c_y_values[-1] - zero_result['c_y']) < 1e-6:
                print(f"✅ C Y-component at twotheta=45° matches twotheta=0°")
                print("   CONFIRMED: C is not rotating pix0_vector with twotheta")

if __name__ == "__main__":
    test_twotheta_behavior()