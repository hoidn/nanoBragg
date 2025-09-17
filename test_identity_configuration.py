#!/usr/bin/env python3
"""
Test Hypothesis 4: Missing Coordinate Transformation
Test identity configuration (all rotations = 0) to isolate transformation issues.
"""

import os
import subprocess
import numpy as np

# Set environment variable for PyTorch  
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def run_identity_test():
    """Run with all rotations = 0 to test basic coordinate transformations"""
    print("Testing IDENTITY configuration (all rotations = 0)")
    print("=" * 60)
    
    # Run with no rotations at all
    cmd = [
        'python', 'scripts/verify_detector_geometry.py',
        '--distance', '100',  
        '--detector_rotx', '0',
        '--detector_roty', '0', 
        '--detector_rotz', '0',
        '--detector_twotheta', '0',
        '--quiet'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")  
        print(result.stderr)
        
        # Extract correlation
        for line in result.stdout.split('\n'):
            if 'correlation:' in line.lower():
                print(f"\nFOUND: {line}")
        
        return result.stdout
    except Exception as e:
        print(f"Error running identity test: {e}")
        return None

def test_minimal_transformation():
    """Test with minimal single axis rotation to isolate coordinate issues"""
    print("\n" + "=" * 60)  
    print("Testing MINIMAL transformation (single 1° rotation)")
    print("=" * 60)
    
    # Test tiny rotation on single axis
    cmd = [
        'python', 'scripts/verify_detector_geometry.py',
        '--distance', '100',
        '--detector_rotx', '1',  # 1 degree only
        '--detector_roty', '0',
        '--detector_rotz', '0', 
        '--detector_twotheta', '0',
        '--quiet'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print("STDOUT:")
        print(result.stdout)
        
        # Extract correlation  
        for line in result.stdout.split('\n'):
            if 'correlation:' in line.lower():
                print(f"\nFOUND: {line}")
                
        return result.stdout
    except Exception as e:
        print(f"Error running minimal test: {e}")
        return None

def analyze_c_coordinate_system():
    """Analyze the C code coordinate system setup"""
    print("\n" + "=" * 60)
    print("ANALYZING C COORDINATE SYSTEM SETUP")  
    print("=" * 60)
    
    # Look for coordinate system definitions
    with open('/Users/ollie/Documents/nanoBragg/golden_suite_generator/nanoBragg.c', 'r') as f:
        content = f.read()
        
    # Extract key coordinate system lines
    lines = content.split('\n')
    coord_lines = []
    
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in [
            'fdet_vector', 'sdet_vector', 'odet_vector', 
            'beam_vector', 'pix0_vector', 'coordinate'
        ]):
            # Get some context around the line
            start = max(0, i-1) 
            end = min(len(lines), i+2)
            context = lines[start:end]
            coord_lines.extend(context)
            coord_lines.append("---")
    
    print("Key coordinate system setup lines from C code:")
    for line in coord_lines[:50]:  # Limit output
        if line.strip():
            print(f"  {line}")

def main():
    print("HYPOTHESIS 4: Missing Coordinate Transformation Test")
    print("Testing for coordinate transformation discrepancies")
    
    # Test 1: Identity configuration
    identity_result = run_identity_test()
    
    # Test 2: Minimal transformation
    minimal_result = test_minimal_transformation()  
    
    # Test 3: Analyze coordinate system
    analyze_c_coordinate_system()
    
    print("\n" + "=" * 60)
    print("HYPOTHESIS 4 ANALYSIS SUMMARY:")
    print("=" * 60)
    
    if identity_result and "correlation" in identity_result.lower():
        print("✓ Identity test completed - check correlation above")
    else:
        print("✗ Identity test failed to run")
        
    if minimal_result and "correlation" in minimal_result.lower(): 
        print("✓ Minimal rotation test completed - check correlation above")
    else:
        print("✗ Minimal rotation test failed to run")
        
    print("\nIf identity configuration shows poor correlation,")
    print("this suggests a fundamental coordinate transformation issue.")

if __name__ == "__main__":
    main()