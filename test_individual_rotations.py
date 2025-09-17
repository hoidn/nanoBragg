#!/usr/bin/env python3
"""
Test individual detector rotations to isolate the rotation bug.
"""

import os
import sys
import subprocess
import json
import numpy as np
from typing import Dict, Any

# Set environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def run_correlation_test(rotx: float = 0, roty: float = 0, rotz: float = 0, twotheta: float = 0) -> Dict[str, Any]:
    """Run correlation test with specific rotation parameters."""
    
    # Build command
    cmd = [
        sys.executable, 
        'scripts/verify_detector_geometry.py',
        '--rotx', str(rotx),
        '--roty', str(roty), 
        '--rotz', str(rotz),
        '--twotheta', str(twotheta),
        '--output', 'temp_test.json'
    ]
    
    # Run the command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # Extract correlation from the output text
        lines = result.stdout.split('\n')
        baseline_corr = None
        tilted_corr = None
        
        for line in lines:
            if 'Baseline correlation:' in line:
                baseline_corr = float(line.split(':')[1].strip())
            elif 'Tilted correlation:' in line:
                tilted_corr = float(line.split(':')[1].strip())
                
        return {
            'rotx': rotx,
            'roty': roty,
            'rotz': rotz,
            'twotheta': twotheta,
            'baseline_correlation': baseline_corr,
            'tilted_correlation': tilted_corr,
            'success': result.returncode == 0,
            'stdout': result.stdout[-500:] if result.stdout else '',  # Last 500 chars
            'stderr': result.stderr[-500:] if result.stderr else ''
        }
        
    except subprocess.TimeoutExpired:
        return {
            'rotx': rotx, 'roty': roty, 'rotz': rotz, 'twotheta': twotheta,
            'baseline_correlation': None, 'tilted_correlation': None,
            'success': False, 'error': 'Timeout'
        }
    except Exception as e:
        return {
            'rotx': rotx, 'roty': roty, 'rotz': rotz, 'twotheta': twotheta,
            'baseline_correlation': None, 'tilted_correlation': None,
            'success': False, 'error': str(e)
        }

def main():
    """Test individual rotations and combinations."""
    
    print("Testing Individual Detector Rotations")
    print("=" * 50)
    
    # Test configurations
    test_cases = [
        # Baseline
        (0, 0, 0, 0, "Baseline (no rotations)"),
        
        # Individual rotations  
        (5, 0, 0, 0, "Only rotx=5°"),
        (0, 3, 0, 0, "Only roty=3°"),
        (0, 0, 2, 0, "Only rotz=2°"),
        (0, 0, 0, 15, "Only twotheta=15°"),
        
        # Combinations
        (5, 3, 0, 0, "rotx=5° + roty=3°"),
        (5, 0, 2, 0, "rotx=5° + rotz=2°"),
        (0, 3, 2, 0, "roty=3° + rotz=2°"),
        (5, 3, 2, 0, "All rotations, no twotheta"),
        (5, 3, 2, 15, "Full configuration"),
    ]
    
    results = []
    
    for rotx, roty, rotz, twotheta, description in test_cases:
        print(f"\n🔬 Testing: {description}")
        print(f"   Parameters: rotx={rotx}°, roty={roty}°, rotz={rotz}°, twotheta={twotheta}°")
        
        result = run_correlation_test(rotx, roty, rotz, twotheta)
        results.append(result)
        
        if result['success']:
            baseline = result.get('baseline_correlation', 'N/A')
            tilted = result.get('tilted_correlation', 'N/A')
            print(f"   ✓ Baseline correlation: {baseline}")
            print(f"   ✓ Tilted correlation: {tilted}")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            
    # Summary report
    print("\n" + "=" * 70)
    print("ROTATION ISOLATION SUMMARY")
    print("=" * 70)
    print(f"{'Description':<30} {'Baseline':<12} {'Tilted':<12} {'Status'}")
    print("-" * 70)
    
    for i, (rotx, roty, rotz, twotheta, description) in enumerate(test_cases):
        result = results[i]
        
        if result['success']:
            baseline = f"{result['baseline_correlation']:.6f}" if result['baseline_correlation'] else "N/A"
            tilted = f"{result['tilted_correlation']:.6f}" if result['tilted_correlation'] else "N/A"
            status = "✓"
        else:
            baseline = "FAILED"
            tilted = "FAILED"
            status = "❌"
            
        print(f"{description:<30} {baseline:<12} {tilted:<12} {status}")
    
    # Analysis
    print("\n" + "=" * 50)
    print("ANALYSIS")
    print("=" * 50)
    
    # Find which rotation causes the worst correlation drop
    valid_results = [r for r in results if r['success'] and r['tilted_correlation'] is not None]
    
    if valid_results:
        baseline_ref = valid_results[0]['baseline_correlation']  # No rotation reference
        
        print(f"Reference correlation (no rotations): {baseline_ref:.6f}")
        print("\nCorrelation drops from baseline:")
        
        for i, (rotx, roty, rotz, twotheta, description) in enumerate(test_cases[1:], 1):
            result = results[i]
            if result['success'] and result['tilted_correlation'] is not None:
                drop = baseline_ref - result['tilted_correlation']
                print(f"  {description:<30}: {drop:+.6f}")

if __name__ == "__main__":
    main()
