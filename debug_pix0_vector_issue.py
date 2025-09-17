#!/usr/bin/env python3
"""
Debug the 39mm pix0_vector offset issue identified in PHASE_6_FINAL_REPORT.md
"""

import os
import sys
import torch
import numpy as np
from pathlib import Path

# Set environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector

def test_pix0_vector_calculation():
    """Test pix0_vector calculation for the specific case that has issues."""
    
    print("Debugging pix0_vector Calculation Issue")
    print("=" * 50)
    print()
    
    # Test cases based on PHASE_6_FINAL_REPORT.md
    test_cases = [
        {
            "name": "Baseline (should work per report)",
            "rotx": 0.0, "roty": 0.0, "rotz": 0.0, "twotheta": 0.0,
            "expected_correlation": ">99%"
        },
        {
            "name": "Problematic case from report", 
            "rotx": 5.0, "roty": 3.0, "rotz": 2.0, "twotheta": 20.0,
            "expected_pix0": [0.095234, 0.058827, -0.051702],  # C reference from report
            "python_pix0": [0.109814, 0.022698, -0.051758],   # Python from report
            "expected_correlation": "4%"
        }
    ]
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        print(f"  Rotations: rotx={test_case['rotx']}°, roty={test_case['roty']}°, rotz={test_case['rotz']}°")
        print(f"  Two-theta: {test_case['twotheta']}°")
        print(f"  Expected correlation: {test_case['expected_correlation']}")
        
        # Create detector configuration
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=51.25,  # Use exact value from report
            beam_center_f=51.25,
            detector_convention=DetectorConvention.MOSFLM,
            detector_rotx_deg=test_case['rotx'],
            detector_roty_deg=test_case['roty'],
            detector_rotz_deg=test_case['rotz'],
            detector_twotheta_deg=test_case['twotheta'],
            detector_pivot=DetectorPivot.SAMPLE if test_case['twotheta'] != 0 else DetectorPivot.BEAM,
        )
        
        # Create detector
        detector = Detector(detector_config)
        
        # Extract key values
        pix0_vector = detector.pix0_vector.detach().numpy()
        fdet_vec = detector.fdet_vec.detach().numpy()
        sdet_vec = detector.sdet_vec.detach().numpy() 
        odet_vec = detector.odet_vec.detach().numpy()
        
        print(f"  Results:")
        print(f"    pix0_vector: [{pix0_vector[0]:.6f}, {pix0_vector[1]:.6f}, {pix0_vector[2]:.6f}] m")
        print(f"    fdet_vec:    [{fdet_vec[0]:.6f}, {fdet_vec[1]:.6f}, {fdet_vec[2]:.6f}]")
        print(f"    sdet_vec:    [{sdet_vec[0]:.6f}, {sdet_vec[1]:.6f}, {sdet_vec[2]:.6f}]")
        print(f"    odet_vec:    [{odet_vec[0]:.6f}, {odet_vec[1]:.6f}, {odet_vec[2]:.6f}]")
        
        # For the problematic case, compare with expected values
        if 'expected_pix0' in test_case:
            expected = np.array(test_case['expected_pix0'])
            python_reported = np.array(test_case['python_pix0'])
            
            diff_from_c = pix0_vector - expected
            diff_magnitude_mm = np.linalg.norm(diff_from_c) * 1000  # Convert to mm
            
            print(f"    Expected (C):    [{expected[0]:.6f}, {expected[1]:.6f}, {expected[2]:.6f}] m")
            print(f"    Difference:      [{diff_from_c[0]:.6f}, {diff_from_c[1]:.6f}, {diff_from_c[2]:.6f}] m")
            print(f"    Magnitude diff:  {diff_magnitude_mm:.1f} mm")
            
            # Check if we match the Python value from the report
            matches_report = np.allclose(pix0_vector, python_reported, atol=1e-6)
            print(f"    Matches report Python value: {matches_report}")
        
        print()

def main():
    test_pix0_vector_calculation()

if __name__ == "__main__":
    main()