#!/usr/bin/env python3
"""
Quick verification script to check if the detector geometry correlation issue has been fixed.

This script uses the existing verify_detector_geometry.py to check if the correlation
between PyTorch and C reference implementations has improved from the previous 0.040
for tilted detector configurations.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def main():
    """Run quick correlation check for tilted detector configuration."""
    print("=" * 80)
    print("QUICK CORRELATION CHECK: Verifying SAMPLE pivot fix")
    print("=" * 80)
    
    print("\nRunning verify_detector_geometry.py for tilted case...")
    
    try:
        # Run the verification script with specific parameters for tilted case
        result = subprocess.run([
            'python', 'scripts/verify_detector_geometry.py',
            '--detector-rotx', '5.0',
            '--detector-roty', '3.0', 
            '--detector-rotz', '2.0',
            '--detector-twotheta', '20.0',
            '--beam-center-s', '51.2',
            '--beam-center-f', '51.2',
            '--distance', '100.0',
            '--pixel-size', '0.1',
            '--wavelength', '6.2',
            '--detector-pivot', 'SAMPLE',
            '--detector-convention', 'MOSFLM'
        ], 
        capture_output=True, 
        text=True, 
        cwd=str(Path(__file__).parent.parent)
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        print(f"Return code: {result.returncode}")
        
        # Try to extract correlation value from output
        lines = result.stdout.split('\n')
        correlation_found = False
        for line in lines:
            if 'correlation' in line.lower() or 'corr' in line.lower():
                print(f"CORRELATION INFO: {line}")
                correlation_found = True
                
        if not correlation_found:
            print("No explicit correlation value found in output.")
            print("Check the full output above for comparison results.")
            
    except Exception as e:
        print(f"Error running verification script: {e}")
        print("Trying alternative approach...")
        
        # Fall back to running with simpler parameters
        try:
            result = subprocess.run([
                'python', 'scripts/verify_detector_geometry.py'
            ], 
            capture_output=True, 
            text=True,
            cwd=str(Path(__file__).parent.parent)
            )
            
            print("FALLBACK STDOUT:")
            print(result.stdout)
            
            if result.stderr:
                print("FALLBACK STDERR:")
                print(result.stderr)
                
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nTo manually check correlation:")
    print("1. Run: python scripts/verify_detector_geometry.py")
    print("2. Look for correlation values in the output")
    print("3. Target correlation should be > 0.999 (was previously 0.040)")
    print("4. If still low, the issue persists and needs further debugging")


if __name__ == "__main__":
    main()