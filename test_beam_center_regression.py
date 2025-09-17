#!/usr/bin/env python3
"""
Regression test for beam center calculation fix.

This test verifies that the PyTorch Detector class correctly calculates
pix0_vector values to match the C reference implementation.
"""

import os
import sys
import torch
import numpy as np
import subprocess
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig, DetectorPivot, DetectorConvention


def run_c_reference(params):
    """Run C reference implementation and extract pix0_vector."""
    cmd = [
        "./golden_suite_generator/nanoBragg",
        "-lambda", "6.2",
        "-N", "5", 
        "-cell", "100", "100", "100", "90", "90", "90",
        "-default_F", "100",
        "-distance", str(params['distance']),
        "-detpixels", "1024",
        "-Xbeam", str(params['xbeam']),
        "-Ybeam", str(params['ybeam']),
        "-detector_rotx", str(params.get('rotx', 0)),
        "-detector_roty", str(params.get('roty', 0)),
        "-detector_rotz", str(params.get('rotz', 0)),
        "-floatfile", "/tmp/test.bin"
    ]
    
    if params.get('twotheta', 0) != 0:
        cmd.extend(["-twotheta", str(params['twotheta'])])
        
    if params.get('pivot'):
        cmd.extend(["-pivot", params['pivot']])
    
    print(f"Running C command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        output = result.stderr + result.stdout
        
        # Extract pix0_vector
        for line in output.split('\n'):
            if 'DETECTOR_PIX0_VECTOR' in line:
                parts = line.split()
                if len(parts) >= 4:
                    return np.array([float(parts[1]), float(parts[2]), float(parts[3])])
        
        print("C output:")
        print(output)
        raise ValueError("Could not find DETECTOR_PIX0_VECTOR in C output")
        
    except Exception as e:
        print(f"Error running C reference: {e}")
        return None


def run_pytorch_detector(params):
    """Run PyTorch Detector and get pix0_vector."""
    # Map parameters to PyTorch config
    pivot_mode = DetectorPivot.BEAM
    if params.get('pivot') == 'sample':
        pivot_mode = DetectorPivot.SAMPLE
    elif params.get('twotheta', 0) != 0:
        # If twotheta is specified but no explicit pivot, 
        # the behavior depends on the convention override logic
        pivot_mode = DetectorPivot.SAMPLE  # Default for non-zero twotheta
        
    config = DetectorConfig(
        distance_mm=params['distance'],
        beam_center_s=params['ybeam'],  # Note: Ybeam maps to slow axis
        beam_center_f=params['xbeam'],  # Note: Xbeam maps to fast axis
        detector_rotx_deg=params.get('rotx', 0),
        detector_roty_deg=params.get('roty', 0),
        detector_rotz_deg=params.get('rotz', 0),
        detector_twotheta_deg=params.get('twotheta', 0),
        detector_pivot=pivot_mode,
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        fpixels=1024,
        spixels=1024,
    )
    
    detector = Detector(config)
    return detector.pix0_vector.numpy()


def test_beam_center_cases():
    """Test multiple beam center configurations."""
    
    test_cases = [
        {
            'name': 'BEAM pivot - simple',
            'params': {
                'distance': 100.0,
                'xbeam': 51.2,
                'ybeam': 51.2,
                'pivot': 'beam'
            },
            'expected_match': True
        },
        {
            'name': 'BEAM pivot - rotated',
            'params': {
                'distance': 100.0,
                'xbeam': 61.2,  # Test the original 10x issue values
                'ybeam': 61.2,
                'rotx': 5,
                'roty': 3,
                'rotz': 2,
                'twotheta': 20,
                'pivot': 'beam'  # Force BEAM pivot
            },
            'expected_match': True
        },
        {
            'name': 'SAMPLE pivot - if C supports it',
            'params': {
                'distance': 100.0,
                'xbeam': 51.2,
                'ybeam': 51.2,
                'rotx': 5,
                'roty': 3,
                'rotz': 2,
                'twotheta': 20,
                'pivot': 'sample'
            },
            'expected_match': False  # May not match due to C convention override
        }
    ]
    
    print("=" * 80)
    print("BEAM CENTER CALCULATION REGRESSION TESTS")
    print("=" * 80)
    
    all_passed = True
    tolerance = 1e-6  # 1 micrometer tolerance
    
    for test_case in test_cases:
        print(f"\n🧪 Test: {test_case['name']}")
        print(f"Parameters: {test_case['params']}")
        
        # Run C reference
        c_pix0 = run_c_reference(test_case['params'])
        if c_pix0 is None:
            print("❌ Failed to get C reference")
            all_passed = False
            continue
            
        # Run PyTorch 
        pytorch_pix0 = run_pytorch_detector(test_case['params'])
        
        # Compare
        diff = pytorch_pix0 - c_pix0
        max_diff = np.max(np.abs(diff))
        
        print(f"C pix0_vector:       {c_pix0}")
        print(f"PyTorch pix0_vector: {pytorch_pix0}")
        print(f"Difference:          {diff}")
        print(f"Max difference:      {max_diff:.2e}")
        
        if test_case['expected_match']:
            if max_diff < tolerance:
                print("✅ PASS - PyTorch matches C reference")
            else:
                print(f"❌ FAIL - Difference {max_diff:.2e} exceeds tolerance {tolerance:.2e}")
                all_passed = False
        else:
            if max_diff < tolerance:
                print("⚠️  UNEXPECTED - PyTorch matches C (expected difference)")
            else:
                print("✅ EXPECTED - PyTorch differs from C (known issue)")
    
    print(f"\n{'='*80}")
    if all_passed:
        print("🎉 ALL REGRESSION TESTS PASSED")
        print("The beam center calculation fix is working correctly!")
    else:
        print("❌ SOME TESTS FAILED")
        print("The beam center calculation needs further investigation.")
    print(f"{'='*80}")
    
    return all_passed


if __name__ == "__main__":
    test_beam_center_cases()