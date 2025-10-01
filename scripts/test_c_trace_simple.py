#!/usr/bin/env python3
"""
Simple test to capture C trace output for CUSTOM convention investigation.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def test_both_conventions():
    """Test both MOSFLM and CUSTOM conventions with trace output."""
    
    print("=== Testing C Trace Output ===\n")
    
    # Test commands
    base_cmd = [
        "golden_suite_generator/nanoBragg",
        "-default_F", "100.0",
        "-lambda", "6.2",
        "-distance", "100.0",
        "-pixel", "0.1",
        "-detpixels", "1024",
        "-Xbeam", "61.2",
        "-Ybeam", "61.2",
        "-cell", "100.0", "100.0", "100.0", "90.0", "90.0", "90.0",
        "-N", "5",
        "-detector_rotx", "5.0",
        "-detector_roty", "3.0",
        "-detector_rotz", "2.0",
        "-twotheta", "15.0",
        "-pivot", "sample"
    ]
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate identity matrix
        matrix_file = os.path.join(tmpdir, "identity.mat")
        with open(matrix_file, "w") as f:
            f.write("1.0 0.0 0.0\n")
            f.write("0.0 1.0 0.0\n")
            f.write("0.0 0.0 1.0\n")
        
        # Test 1: No explicit twotheta_axis (MOSFLM convention)
        print("--- Test 1: MOSFLM convention (no explicit twotheta_axis) ---")
        mosflm_cmd = base_cmd + ["-matrix", matrix_file]
        
        result1 = run_c_command(mosflm_cmd, tmpdir, "MOSFLM")
        
        # Test 2: Explicit twotheta_axis (CUSTOM convention)  
        print("\n--- Test 2: CUSTOM convention (explicit twotheta_axis) ---")
        custom_cmd = base_cmd + ["-matrix", matrix_file, "-twotheta_axis", "0.0", "1.0", "0.0"]
        
        result2 = run_c_command(custom_cmd, tmpdir, "CUSTOM")
        
        # Compare results
        compare_trace_outputs(result1, result2)


def run_c_command(cmd, work_dir, label):
    """Run C command and capture output."""
    
    print(f"Command: {' '.join(cmd)}")
    
    # Convert relative path to absolute
    abs_executable = (Path.cwd() / cmd[0]).resolve()
    cmd[0] = str(abs_executable)
    
    try:
        env = os.environ.copy()
        env["LC_NUMERIC"] = "C"
        
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        
        print(f"Return code: {result.returncode}")
        print(f"stdout length: {len(result.stdout)} chars")
        print(f"stderr length: {len(result.stderr)} chars")
        
        if result.stdout:
            print(f"First 200 chars of stdout: {result.stdout[:200]}...")
            
        if result.stderr:
            print(f"First 500 chars of stderr:\n{result.stderr[:500]}")
            print("...")
            
        return {
            'label': label,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
        
    except Exception as e:
        print(f"Error running {label}: {e}")
        return None


def compare_trace_outputs(result1, result2):
    """Compare trace outputs between MOSFLM and CUSTOM."""
    
    print("\n=== Comparison Analysis ===")
    
    if not result1 or not result2:
        print("❌ Cannot compare - one or both runs failed")
        return
        
    if not result1['success']:
        print(f"❌ {result1['label']} failed: {result1['stderr']}")
        return
        
    if not result2['success']:
        print(f"❌ {result2['label']} failed: {result2['stderr']}")
        return
    
    print(f"✅ Both {result1['label']} and {result2['label']} completed successfully")
    
    # Look for specific differences in stdout (where trace output goes)
    stdout1 = result1['stdout']
    stdout2 = result2['stdout']
    
    print("\n--- Searching for pix0_vector values ---")
    
    pix0_1 = extract_final_pix0_vector(stdout1)
    pix0_2 = extract_final_pix0_vector(stdout2)
    
    if pix0_1 and pix0_2:
        print(f"{result1['label']} pix0_vector: {pix0_1}")
        print(f"{result2['label']} pix0_vector: {pix0_2}")
        
        import numpy as np
        diff = np.array(pix0_2) - np.array(pix0_1)
        print(f"Difference ({result2['label']} - {result1['label']}): {diff}")
        print(f"Magnitude of difference: {np.linalg.norm(diff):.6e} m")
        
        # Also check if this is the significant 39mm difference
        diff_mm = diff * 1000  # Convert to mm
        print(f"Difference in mm: {diff_mm}")
        if np.linalg.norm(diff_mm) > 30:  # If > 30mm difference
            print(f"🎯 This appears to be the significant pix0_vector difference!")
    else:
        print("Could not extract pix0_vector from traces")
        
    # Look for convention-specific traces
    print("\n--- Searching for convention traces ---")
    
    if "MOSFLM_convention" in stdout1:
        print(f"✓ {result1['label']} shows MOSFLM_convention traces")
    if "CUSTOM_convention" in stdout2:
        print(f"✓ {result2['label']} shows CUSTOM_convention traces")
    if "CUSTOM_convention" in stdout1:
        print(f"! {result1['label']} unexpectedly shows CUSTOM_convention traces")
    if "MOSFLM_convention" in stdout2:
        print(f"! {result2['label']} unexpectedly shows MOSFLM_convention traces")


def extract_final_pix0_vector(stdout_text):
    """Extract the final pix0_vector value from stdout."""
    
    lines = stdout_text.splitlines()
    
    # Look for the final pix0_vector trace
    for line in reversed(lines):  # Search from end
        if "DETECTOR_PIX0_VECTOR" in line:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    return [float(parts[1]), float(parts[2]), float(parts[3])]
                except ValueError:
                    continue
                    
    # Fallback: look for any pix0_vector trace
    for line in lines:
        if "pix0_vector=[" in line:
            # Extract [x y z] format
            start = line.find("[")
            end = line.find("]")
            if start != -1 and end != -1:
                coords_str = line[start+1:end]
                coords = coords_str.split()
                if len(coords) == 3:
                    try:
                        return [float(coords[0]), float(coords[1]), float(coords[2])]
                    except ValueError:
                        continue
    
    return None


if __name__ == "__main__":
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    test_both_conventions()