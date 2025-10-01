#!/usr/bin/env python3
"""
Test script to investigate CUSTOM convention behavior in C code.

This script tests C behavior with and without -twotheta_axis to understand
the differences between MOSFLM and CUSTOM conventions, particularly for
pix0_vector calculations.
"""

import os
import sys
import subprocess
import tempfile
import numpy as np
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.c_reference_runner import CReferenceRunner
from scripts.c_reference_utils import build_nanobragg_command, generate_identity_matrix
from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention, DetectorPivot

def test_convention_switching():
    """Test how C code behaves with and without explicit twotheta_axis."""
    
    print("=== Testing CUSTOM Convention Switching ===\n")
    
    # Create configurations using the proper config classes
    # Base configuration for tilted detector
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
    
    # Test 1: MOSFLM convention (no explicit twotheta_axis)
    print("Test 1: MOSFLM convention (no explicit twotheta_axis)")
    mosflm_detector = DetectorConfig(
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
    
    # Test 2: CUSTOM convention (explicit twotheta_axis)
    print("\nTest 2: CUSTOM convention (explicit twotheta_axis)")
    import torch
    custom_detector = DetectorConfig(
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
    
    # Run both configurations and capture detailed traces
    runner = CReferenceRunner()
    
    if not runner.is_available():
        print("❌ nanoBragg executable not available")
        return
    
    print("\n=== Running C simulations to get traces ===")
    
    results = {}
    
    # For each configuration, we need to manually run with tracing
    configurations = [
        ("MOSFLM", mosflm_detector),
        ("CUSTOM", custom_detector)
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for name, detector_config in configurations:
            print(f"\n--- Running {name} configuration ---")
            
            try:
                # Build command with tracing
                matrix_file = os.path.join(tmpdir, "identity.mat")
                generate_identity_matrix(matrix_file)
                
                cmd = build_nanobragg_command(
                    detector_config, crystal_config, beam_config,
                    matrix_file=matrix_file
                )
                
                print(f"Command: {' '.join(cmd)}")
                
                # Execute with detailed tracing (add debugging to C code)
                result = run_detailed_c_trace(cmd, tmpdir)
                results[name] = result
                
                print(f"✓ {name} completed")
                
            except Exception as e:
                print(f"✗ {name} failed: {e}")
                results[name] = None
    
    # Analyze results
    analyze_convention_differences(results)


def run_detailed_c_trace(cmd, work_dir):
    """Run C command and capture any available trace output."""
    
    # Convert relative executable path to absolute if needed
    if not Path(cmd[0]).is_absolute():
        abs_executable = (Path.cwd() / cmd[0]).resolve()
        cmd[0] = str(abs_executable)
    
    # Set environment for consistent output
    env = os.environ.copy()
    env["LC_NUMERIC"] = "C"
    
    try:
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        
        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        return {
            'returncode': -1,
            'stdout': '',
            'stderr': 'Timeout after 60 seconds',
            'success': False
        }
    except Exception as e:
        return {
            'returncode': -1,
            'stdout': '',
            'stderr': f'Exception: {str(e)}',
            'success': False
        }


def analyze_convention_differences(results):
    """Analyze differences between MOSFLM and CUSTOM convention results."""
    
    print("\n=== Analysis of Convention Differences ===")
    
    mosflm_result = results.get("MOSFLM")
    custom_result = results.get("CUSTOM")
    
    if not mosflm_result or not custom_result:
        print("❌ Could not compare - one or both runs failed")
        return
    
    if not mosflm_result['success']:
        print(f"❌ MOSFLM run failed: {mosflm_result['stderr']}")
        return
        
    if not custom_result['success']:
        print(f"❌ CUSTOM run failed: {custom_result['stderr']}")
        return
    
    print("✅ Both runs completed successfully")
    
    # Look for differences in stdout/stderr
    print("\n--- Comparing stdout ---")
    if mosflm_result['stdout'] == custom_result['stdout']:
        print("stdout outputs are identical")
    else:
        print("stdout outputs differ:")
        print("MOSFLM stdout:", mosflm_result['stdout'][:200] + "..." if len(mosflm_result['stdout']) > 200 else mosflm_result['stdout'])
        print("CUSTOM stdout:", custom_result['stdout'][:200] + "..." if len(custom_result['stdout']) > 200 else custom_result['stdout'])
    
    print("\n--- Comparing stderr ---")
    if mosflm_result['stderr'] == custom_result['stderr']:
        print("stderr outputs are identical")
    else:
        print("stderr outputs differ:")
        print("MOSFLM stderr:", mosflm_result['stderr'])
        print("CUSTOM stderr:", custom_result['stderr'])
        
        # Look for specific trace information
        find_trace_differences(mosflm_result['stderr'], custom_result['stderr'])


def find_trace_differences(mosflm_trace, custom_trace):
    """Find specific differences in trace output."""
    
    print("\n--- Searching for specific trace differences ---")
    
    # Look for key variables that might differ
    key_variables = [
        "pix0_vector",
        "close_distance", 
        "far_distance",
        "beam_center",
        "pixel_size",
        "detector_normal",
        "detector_fast", 
        "detector_slow",
        "convention"
    ]
    
    mosflm_lines = mosflm_trace.splitlines()
    custom_lines = custom_trace.splitlines()
    
    for var in key_variables:
        mosflm_val = find_variable_in_trace(mosflm_lines, var)
        custom_val = find_variable_in_trace(custom_lines, var)
        
        if mosflm_val != custom_val:
            print(f"  {var}: MOSFLM={mosflm_val}, CUSTOM={custom_val}")


def extract_pix0_vector(trace_output):
    """Extract pix0_vector from trace output."""
    lines = trace_output.splitlines()
    for line in lines:
        if "pix0_vector:" in line:
            # Extract the vector values
            parts = line.split("pix0_vector:")
            if len(parts) > 1:
                vector_str = parts[1].strip()
                # Parse (x, y, z) format
                if vector_str.startswith('(') and vector_str.endswith(')'):
                    coords = vector_str[1:-1].split(',')
                    if len(coords) == 3:
                        try:
                            return [float(x.strip()) for x in coords]
                        except ValueError:
                            pass
    return None

def compare_trace_outputs(trace1, trace2):
    """Compare two trace outputs and highlight differences."""
    lines1 = trace1.splitlines()
    lines2 = trace2.splitlines()
    
    # Look for key variables that might differ
    key_variables = [
        "pix0_vector",
        "close_distance",
        "far_distance", 
        "beam_center",
        "pixel_size",
        "detector_normal",
        "detector_fast",
        "detector_slow",
        "convention"
    ]
    
    differences_found = False
    
    for var in key_variables:
        val1 = find_variable_in_trace(lines1, var)
        val2 = find_variable_in_trace(lines2, var)
        
        if val1 != val2:
            print(f"  {var}: MOSFLM={val1}, CUSTOM={val2}")
            differences_found = True
    
    if not differences_found:
        print("  No obvious differences found in key variables")

def find_variable_in_trace(lines, variable):
    """Find a variable value in trace lines."""
    for line in lines:
        if f"{variable}:" in line:
            parts = line.split(f"{variable}:")
            if len(parts) > 1:
                return parts[1].strip()
    return None

if __name__ == "__main__":
    # Set environment variable for PyTorch
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    test_convention_switching()