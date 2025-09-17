#!/usr/bin/env python3
"""
Test script to validate the CUSTOM convention pix0_vector fix.

This script tests that our PyTorch Detector now correctly matches the C reference
for pix0_vector calculations in both MOSFLM and CUSTOM conventions.
"""

import os
import sys
import subprocess
import tempfile
import numpy as np
from pathlib import Path
import torch

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector
from scripts.c_reference_utils import build_nanobragg_command, generate_identity_matrix

def test_pix0_vector_fix():
    """Test that PyTorch pix0_vector now matches C reference for both conventions."""
    
    print("=== Testing pix0_vector Fix for CUSTOM Convention ===\n")
    
    # Set up common configuration
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5)
    )
    
    beam_config = BeamConfig(
        wavelength_A=6.2,
        N_source_points=1,
        source_distance_mm=10000.0,
        source_size_mm=0.0
    )
    
    test_cases = [
        {
            'name': 'MOSFLM_convention',
            'description': 'No explicit twotheta_axis (should use MOSFLM convention with +0.5 offset)',
            'detector_config': DetectorConfig(
                distance_mm=100.0,
                pixel_size_mm=0.1,
                spixels=1024,
                fpixels=1024,
                beam_center_s=61.2,
                beam_center_f=61.2,
                detector_rotx_deg=5.0,
                detector_roty_deg=3.0,
                detector_rotz_deg=2.0,
                detector_twotheta_deg=15.0,
                detector_convention=DetectorConvention.MOSFLM,
                detector_pivot=DetectorPivot.SAMPLE,
                twotheta_axis=None  # No explicit axis -> MOSFLM convention
            )
        },
        {
            'name': 'CUSTOM_convention',
            'description': 'Explicit twotheta_axis [0,1,0] (should use CUSTOM convention without +0.5 offset)',
            'detector_config': DetectorConfig(
                distance_mm=100.0,
                pixel_size_mm=0.1,
                spixels=1024,
                fpixels=1024,
                beam_center_s=61.2,
                beam_center_f=61.2,
                detector_rotx_deg=5.0,
                detector_roty_deg=3.0,
                detector_rotz_deg=2.0,
                detector_twotheta_deg=15.0,
                detector_convention=DetectorConvention.MOSFLM,
                detector_pivot=DetectorPivot.SAMPLE,
                twotheta_axis=torch.tensor([0.0, 1.0, 0.0])  # Explicit Y-axis -> CUSTOM convention
            )
        }
    ]
    
    results = {}
    
    # Test each configuration
    for case in test_cases:
        name = case['name']
        detector_config = case['detector_config']
        
        print(f"--- Testing {name} ---")
        print(f"Description: {case['description']}")
        
        # Get C reference pix0_vector
        c_pix0_vector = get_c_pix0_vector(detector_config, crystal_config, beam_config)
        
        # Get PyTorch pix0_vector
        pytorch_pix0_vector = get_pytorch_pix0_vector(detector_config)
        
        results[name] = {
            'c_pix0_vector': c_pix0_vector,
            'pytorch_pix0_vector': pytorch_pix0_vector,
            'detector_config': detector_config
        }
        
        if c_pix0_vector is not None and pytorch_pix0_vector is not None:
            # Compare the vectors
            c_vec = np.array(c_pix0_vector)
            py_vec = pytorch_pix0_vector.detach().numpy()
            
            diff = py_vec - c_vec
            diff_magnitude = np.linalg.norm(diff)
            
            print(f"C reference pix0_vector:   {c_vec}")
            print(f"PyTorch pix0_vector:       {py_vec}")
            print(f"Difference (PyTorch - C):  {diff}")
            print(f"Difference magnitude:      {diff_magnitude:.6e} m")
            
            # Check if the difference is acceptably small (< 1e-12 m as requested)
            if diff_magnitude < 1e-12:
                print(f"✅ {name}: pix0_vector matches C reference (diff < 1e-12 m)")
            else:
                print(f"❌ {name}: pix0_vector does not match C reference (diff = {diff_magnitude:.6e} m)")
        else:
            print(f"❌ {name}: Could not compare - failed to get pix0_vector from C or PyTorch")
        
        print()
    
    # Summary comparison
    print("=== Summary ===")
    
    if 'MOSFLM_convention' in results and 'CUSTOM_convention' in results:
        mosflm_result = results['MOSFLM_convention']
        custom_result = results['CUSTOM_convention']
        
        if (mosflm_result['c_pix0_vector'] is not None and 
            mosflm_result['pytorch_pix0_vector'] is not None and
            custom_result['c_pix0_vector'] is not None and
            custom_result['pytorch_pix0_vector'] is not None):
            
            # Check that MOSFLM and CUSTOM C results are different (as expected)
            c_mosflm = np.array(mosflm_result['c_pix0_vector'])
            c_custom = np.array(custom_result['c_pix0_vector'])
            c_diff = np.linalg.norm(c_custom - c_mosflm)
            
            print(f"C reference difference between MOSFLM and CUSTOM: {c_diff:.6e} m")
            if c_diff > 1e-3:  # Should be ~18-39mm difference
                print(f"✅ C code correctly shows significant difference between conventions")
            else:
                print(f"⚠️  C code shows unexpectedly small difference between conventions")
            
            # Check that PyTorch results also differ appropriately
            py_mosflm = mosflm_result['pytorch_pix0_vector'].detach().numpy()
            py_custom = custom_result['pytorch_pix0_vector'].detach().numpy()
            py_diff = np.linalg.norm(py_custom - py_mosflm)
            
            print(f"PyTorch difference between MOSFLM and CUSTOM: {py_diff:.6e} m")
            
            # The key test: both PyTorch results should match their respective C references
            mosflm_match = np.linalg.norm(py_mosflm - c_mosflm) < 1e-12
            custom_match = np.linalg.norm(py_custom - c_custom) < 1e-12
            
            print(f"\nFinal Results:")
            print(f"MOSFLM PyTorch matches C: {'✅ Yes' if mosflm_match else '❌ No'}")
            print(f"CUSTOM PyTorch matches C: {'✅ Yes' if custom_match else '❌ No'}")
            
            if mosflm_match and custom_match:
                print(f"\n🎉 SUCCESS: CUSTOM convention fix implemented correctly!")
                print(f"   Both MOSFLM and CUSTOM conventions now match C reference exactly.")
            else:
                print(f"\n❌ FAILURE: Fix not complete - some configurations still don't match.")


def get_c_pix0_vector(detector_config, crystal_config, beam_config):
    """Get pix0_vector from C reference implementation."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Generate identity matrix
            matrix_file = os.path.join(tmpdir, "identity.mat")
            generate_identity_matrix(matrix_file)
            
            # Build C command
            cmd = build_nanobragg_command(
                detector_config, crystal_config, beam_config,
                matrix_file=matrix_file
            )
            
            print(f"C command: {' '.join(cmd)}")
            
            # Convert relative path to absolute
            abs_executable = (Path.cwd() / cmd[0]).resolve()
            cmd[0] = str(abs_executable)
            
            # Run C code
            env = os.environ.copy()
            env["LC_NUMERIC"] = "C"
            
            result = subprocess.run(
                cmd,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            
            if result.returncode != 0:
                print(f"C code failed: {result.stderr}")
                return None
                
            # Extract pix0_vector from stdout
            return extract_pix0_vector_from_output(result.stdout)
            
        except Exception as e:
            print(f"Error running C code: {e}")
            return None


def get_pytorch_pix0_vector(detector_config):
    """Get pix0_vector from PyTorch Detector implementation."""
    
    try:
        detector = Detector(detector_config)
        return detector.pix0_vector
    except Exception as e:
        print(f"Error creating PyTorch detector: {e}")
        return None


def extract_pix0_vector_from_output(stdout_text):
    """Extract final pix0_vector from C output."""
    
    lines = stdout_text.splitlines()
    
    # Look for the final DETECTOR_PIX0_VECTOR trace
    for line in reversed(lines):
        if "DETECTOR_PIX0_VECTOR" in line:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    return [float(parts[1]), float(parts[2]), float(parts[3])]
                except ValueError:
                    continue
    
    return None


if __name__ == "__main__":
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    test_pix0_vector_fix()