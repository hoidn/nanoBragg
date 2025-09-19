#!/usr/bin/env python3
"""
Test C pivot flag directly with minimal configurations.
"""

import os
import subprocess
import tempfile
from pathlib import Path

def test_c_pivot_flag():
    """Test that C code respects -pivot flag."""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Generate identity matrix
        matrix_file = temp_path / "identity.mat"
        with open(matrix_file, "w") as f:
            f.write("1.0 0.0 0.0\n")
            f.write("0.0 1.0 0.0\n")
            f.write("0.0 0.0 1.0\n")
        
        # Test configurations
        tests = [
            {
                "name": "Baseline (no twotheta, explicit beam pivot)",
                "cmd": [
                    "golden_suite_generator/nanoBragg_golden",
                    "-default_F", "100.0",
                    "-lambda", "6.2",
                    "-distance", "100.0",
                    "-pixel", "0.1",
                    "-detpixels", "50",  # Small for speed
                    "-Xbeam", "2.5",
                    "-Ybeam", "2.5",
                    "-cell", "100", "100", "100", "90", "90", "90",
                    "-N", "2",
                    "-matrix", str(matrix_file),
                    "-pivot", "beam"
                ]
            },
            {
                "name": "Twotheta with explicit sample pivot",
                "cmd": [
                    "golden_suite_generator/nanoBragg_golden",
                    "-default_F", "100.0",
                    "-lambda", "6.2",
                    "-distance", "100.0",
                    "-pixel", "0.1",
                    "-detpixels", "50",  # Small for speed
                    "-Xbeam", "2.5",
                    "-Ybeam", "2.5",
                    "-cell", "100", "100", "100", "90", "90", "90",
                    "-N", "2",
                    "-matrix", str(matrix_file),
                    "-twotheta", "15.0",
                    "-pivot", "sample"
                ]
            },
            {
                "name": "Twotheta with explicit beam pivot (should override automatic SAMPLE)",
                "cmd": [
                    "golden_suite_generator/nanoBragg_golden",
                    "-default_F", "100.0",
                    "-lambda", "6.2",
                    "-distance", "100.0",
                    "-pixel", "0.1",
                    "-detpixels", "50",  # Small for speed
                    "-Xbeam", "2.5",
                    "-Ybeam", "2.5",
                    "-cell", "100", "100", "100", "90", "90", "90",
                    "-N", "2",
                    "-matrix", str(matrix_file),
                    "-twotheta", "15.0",
                    "-pivot", "beam"
                ]
            }
        ]
        
        print("Testing C pivot flag behavior")
        print("=" * 50)
        
        for test in tests:
            print(f"\n{test['name']}:")
            print(f"Command: {' '.join(test['cmd'])}")
            
            # Set environment for deterministic output
            env = os.environ.copy()
            env["LC_NUMERIC"] = "C"
            
            try:
                result = subprocess.run(
                    test['cmd'],
                    cwd=Path.cwd(),  # Run from project root
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env,
                )
                
                if result.returncode == 0:
                    print("✅ Execution successful")
                    
                    # Check for pivot messages in output
                    output = result.stdout + result.stderr
                    if "pivoting detector around direct beam spot" in output:
                        print("   Detected: BEAM pivot mode")
                    elif "pivoting detector around sample" in output:
                        print("   Detected: SAMPLE pivot mode")
                    else:
                        print("   No pivot mode message found")
                        print(f"   Full output: {output[:200]}...")
                else:
                    print(f"❌ Execution failed (code {result.returncode})")
                    print(f"   STDERR: {result.stderr[:200]}")
                    
            except subprocess.TimeoutExpired:
                print("❌ Execution timed out")
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_c_pivot_flag()