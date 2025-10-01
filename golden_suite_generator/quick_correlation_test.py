#!/usr/bin/env python3
"""
Quick correlation test to verify current PyTorch implementation.
"""

import os
import sys
import numpy as np

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add scripts to path
sys.path.insert(0, '/Users/ollie/Documents/nanoBragg/scripts')

def run_quick_correlation_test():
    """Run a quick correlation test with current PyTorch implementation."""
    
    print("=" * 60)
    print("Quick Correlation Test")
    print("=" * 60)
    
    try:
        # Import the verification script
        from verify_detector_geometry import main as verify_main
        
        # Test with simple cubic case (should have high correlation)
        print("Testing simple cubic case...")
        
        # Run with minimal output
        import sys
        from io import StringIO
        
        # Capture output to see the correlation result
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()
        
        try:
            # Run the verification with simple cubic parameters
            verify_main()
            
            # Restore stdout and get output
            output = buffer.getvalue()
            
        finally:
            sys.stdout = old_stdout
            
        # Parse the output for correlation
        lines = output.split('\n')
        correlation_line = None
        for line in lines:
            if 'correlation' in line.lower():
                correlation_line = line
                print(f"Found: {line}")
                
        if correlation_line:
            # Try to extract correlation value
            import re
            match = re.search(r'(\d+\.?\d*)', correlation_line)
            if match:
                correlation = float(match.group(1))
                print(f"\n📊 Correlation Result: {correlation:.6f}")
                
                if correlation > 0.999:
                    print("✅ EXCELLENT: Correlation > 0.999 (perfect match)")
                elif correlation > 0.99:
                    print("✅ GOOD: Correlation > 0.99 (very good match)")
                elif correlation > 0.95:
                    print("⚠️  OK: Correlation > 0.95 (acceptable match)")
                elif correlation > 0.9:
                    print("⚠️  POOR: Correlation > 0.9 (needs improvement)")
                else:
                    print("❌ BAD: Correlation < 0.9 (significant mismatch)")
                    
                return correlation
        else:
            print("Could not find correlation value in output")
            print("Raw output:")
            print(output)
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Trying alternative approach...")
        
        # Try running the script directly
        import subprocess
        result = subprocess.run([
            'python', '/Users/ollie/Documents/nanoBragg/scripts/verify_detector_geometry.py'
        ], capture_output=True, text=True, env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'})
        
        if result.returncode == 0:
            print("Script ran successfully")
            print("Output:")
            print(result.stdout)
            if result.stderr:
                print("Stderr:")
                print(result.stderr)
        else:
            print(f"Script failed with return code {result.returncode}")
            print("Stdout:", result.stdout)
            print("Stderr:", result.stderr)
            
    except Exception as e:
        print(f"❌ Error running verification: {e}")
        import traceback
        traceback.print_exc()
        
    return None

if __name__ == "__main__":
    correlation = run_quick_correlation_test()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if correlation is not None:
        if correlation > 0.999:
            print("🎉 PyTorch implementation appears to be working correctly!")
            print("   The beam center calculations are producing good correlation.")
        else:
            print(f"🔧 Correlation of {correlation:.6f} suggests further tuning needed.")
    else:
        print("❓ Unable to determine correlation - manual verification needed.")