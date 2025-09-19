#!/usr/bin/env python3
"""
Test single rotations to isolate which rotation introduces the Y error.

This will test each rotation individually to find the source of the 43mm Y error.
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
    
    # Execute
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Clean up temp file
    Path(matrix_file).unlink(missing_ok=True)
    
    if result.returncode != 0:
        print(f"❌ C execution failed: {result.returncode}")
        return None, None
    
    return result.stdout, result.stderr

def extract_pix0_vector(c_output, c_stderr):
    """Extract pix0_vector from C output"""
    all_output = (c_output or '') + '\n' + (c_stderr or '')
    
    for line in all_output.split('\n'):
        if 'DETECTOR_PIX0_VECTOR' in line and not 'before' in line.lower():
            parts = line.split()
            if len(parts) >= 4:
                try:
                    x = float(parts[1])
                    y = float(parts[2]) 
                    z = float(parts[3])
                    return np.array([x, y, z])
                except (ValueError, IndexError):
                    continue
    return None

def run_single_rotation_test(rotation_name, rotation_value, rotx=0.0, roty=0.0, rotz=0.0, twotheta=0.0):
    """Test a single rotation to see its effect on Y-component"""
    print(f"\n=== Testing {rotation_name} = {rotation_value} ===")
    
    # Configuration with only one rotation
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=61.2,  # mm
        beam_center_f=61.2,  # mm
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.SAMPLE,
        # Single rotation only
        detector_rotx_deg=rotx,
        detector_roty_deg=roty,
        detector_rotz_deg=rotz,
        detector_twotheta_deg=twotheta,
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
    py_y = detector.pix0_vector[1].item()
    
    # Run C reference
    c_output, c_stderr = run_c_reference_simple(detector_config, crystal_config, beam_config)
    
    if c_output is None:
        print(f"❌ C execution failed for {rotation_name}")
        return None
    
    # Extract C pix0_vector
    c_pix0 = extract_pix0_vector(c_output, c_stderr)
    
    if c_pix0 is not None:
        c_y = c_pix0[1]
        y_diff_mm = (py_y - c_y) * 1000
        
        print(f"PyTorch Y: {py_y:.6f} m")
        print(f"C Y:       {c_y:.6f} m")
        print(f"Y diff:    {y_diff_mm:.3f} mm")
        
        return y_diff_mm
    else:
        print(f"❌ Could not extract C pix0_vector for {rotation_name}")
        return None

def test_all_single_rotations():
    """Test each rotation individually"""
    
    print("=== SINGLE ROTATION Y-COMPONENT TEST ===")
    print("Testing each rotation individually to find the Y error source...")
    
    # Test individual rotations from the tilted case
    rotations = [
        ("detector_rotx", 5.0, 5.0, 0.0, 0.0, 0.0),
        ("detector_roty", 3.0, 0.0, 3.0, 0.0, 0.0),
        ("detector_rotz", 2.0, 0.0, 0.0, 2.0, 0.0),
        ("detector_twotheta", 15.0, 0.0, 0.0, 0.0, 15.0),
    ]
    
    results = {}
    
    for rotation_name, rotation_value, rotx, roty, rotz, twotheta in rotations:
        y_diff_mm = run_single_rotation_test(rotation_name, rotation_value, rotx, roty, rotz, twotheta)
        if y_diff_mm is not None:
            results[rotation_name] = y_diff_mm
            
            # Check if this rotation introduces significant Y error
            if abs(y_diff_mm) > 20:  # > 20mm is significant
                print(f"🚨 {rotation_name} introduces LARGE Y error: {y_diff_mm:.1f}mm")
            elif abs(y_diff_mm) > 1:  # > 1mm is noticeable
                print(f"⚠️  {rotation_name} introduces small Y error: {y_diff_mm:.1f}mm")
            else:
                print(f"✅ {rotation_name} Y error is minimal: {y_diff_mm:.1f}mm")
    
    print(f"\n=== SUMMARY ===")
    print("Y-component errors by rotation:")
    for rotation_name, y_diff_mm in results.items():
        if abs(y_diff_mm) > 20:
            status = "🚨 CRITICAL"
        elif abs(y_diff_mm) > 1:
            status = "⚠️  WARNING"
        else:
            status = "✅ OK"
        print(f"  {rotation_name:20}: {y_diff_mm:8.1f}mm  {status}")
    
    # Find the worst offender
    if results:
        worst_rotation = max(results.items(), key=lambda x: abs(x[1]))
        print(f"\nWorst offender: {worst_rotation[0]} with {worst_rotation[1]:.1f}mm Y error")

if __name__ == "__main__":
    test_all_single_rotations()