#!/usr/bin/env python3
"""
Compare C and Python pix0_vector calculations directly.

This script runs the C code with tracing enabled and extracts the exact
pix0_vector values to compare against Python calculations.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import torch
import numpy as np

from nanobrag_torch.config import (
    BeamConfig,
    CrystalConfig, 
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
)
from nanobrag_torch.models.detector import Detector
from c_reference_utils import build_nanobragg_command, generate_identity_matrix


def extract_c_pix0_vector(c_output: str) -> tuple:
    """Extract pix0_vector from C trace output."""
    lines = c_output.split('\n')
    pix0_vector = None
    
    for line in lines:
        # Look for different possible formats
        if 'DETECTOR_PIX0_VECTOR ' in line:
            # Format: DETECTOR_PIX0_VECTOR x y z
            try:
                parts = line.split('DETECTOR_PIX0_VECTOR ')[1].strip().split()
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                pix0_vector = (x, y, z)
                print(f"Found C pix0_vector (DETECTOR_PIX0_VECTOR): [{x:.6f}, {y:.6f}, {z:.6f}]")
            except (IndexError, ValueError) as e:
                print(f"Error parsing DETECTOR_PIX0_VECTOR: {e}")
                print(f"Line: {line}")
        elif 'TRACE_C:pix0_vector=' in line:
            # Format: TRACE_C:pix0_vector=x y z
            try:
                parts = line.split('TRACE_C:pix0_vector=')[1].strip().split()
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                pix0_vector = (x, y, z)
                print(f"Found C pix0_vector (TRACE_C): [{x:.6f}, {y:.6f}, {z:.6f}]")
            except (IndexError, ValueError) as e:
                print(f"Error parsing TRACE_C pix0_vector: {e}")
                print(f"Line: {line}")
    
    return pix0_vector


def run_c_with_trace(detector_config: DetectorConfig, label: str = "") -> tuple:
    """Run C code with tracing and extract pix0_vector."""
    print(f"\n{'='*60}")
    print(f"RUNNING C CODE WITH TRACE: {label}")
    print(f"{'='*60}")
    
    # Find C executable with tracing
    executable_path = Path("golden_suite_generator/nanoBragg_trace")
    
    if not executable_path.exists():
        print(f"❌ Trace executable not found: {executable_path}")
        return None
    
    print(f"✓ Using trace executable: {executable_path}")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory(prefix="c_trace_") as temp_dir:
        temp_path = Path(temp_dir)
        
        # Generate identity matrix
        matrix_file = temp_path / "identity.mat"
        generate_identity_matrix(str(matrix_file))
        
        # Create configs for C reference
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(5, 5, 5),
        )
        
        beam_config = BeamConfig(
            wavelength_A=6.2,
            N_source_points=1,
            source_distance_mm=10000.0,
            source_size_mm=0.0,
        )
        
        # Build command
        cmd = build_nanobragg_command(
            detector_config,
            crystal_config,
            beam_config,
            matrix_file=str(matrix_file),
            executable_path=str(executable_path.resolve()),
        )
        
        print(f"Command: {' '.join(cmd)}")
        
        # Execute command and capture output
        try:
            # Set environment for deterministic output
            env = os.environ.copy()
            env["LC_NUMERIC"] = "C"
            
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            
            if result.returncode != 0:
                print(f"❌ C code execution failed (return code: {result.returncode})")
                print(f"STDOUT:\n{result.stdout}")
                print(f"STDERR:\n{result.stderr}")
                return None
            
            print(f"✅ C code executed successfully")
            
            # Extract pix0_vector from output
            c_pix0 = extract_c_pix0_vector(result.stdout)
            
            # Also check stderr for additional debug output
            if result.stderr:
                print(f"Checking stderr for additional pix0_vector...")
                c_pix0_stderr = extract_c_pix0_vector(result.stderr)
                if c_pix0_stderr and not c_pix0:
                    c_pix0 = c_pix0_stderr
            
            return c_pix0
            
        except subprocess.TimeoutExpired:
            print(f"❌ C code execution timed out")
            return None
        except Exception as e:
            print(f"❌ Error running C code: {e}")
            return None


def compare_pix0_vectors(python_pix0: torch.Tensor, c_pix0: tuple, label: str = ""):
    """Compare Python and C pix0_vectors."""
    print(f"\n{'='*60}")
    print(f"PIX0_VECTOR COMPARISON: {label}")
    print(f"{'='*60}")
    
    if c_pix0 is None:
        print("❌ C pix0_vector not available for comparison")
        return
    
    # Convert to numpy for comparison
    py_pix0 = python_pix0.detach().numpy()
    c_pix0_array = np.array(c_pix0)
    
    print(f"Python pix0_vector: [{py_pix0[0]:.6f}, {py_pix0[1]:.6f}, {py_pix0[2]:.6f}]")
    print(f"C pix0_vector:      [{c_pix0_array[0]:.6f}, {c_pix0_array[1]:.6f}, {c_pix0_array[2]:.6f}]")
    
    # Calculate differences
    diff = py_pix0 - c_pix0_array
    abs_diff = np.abs(diff)
    rel_diff = abs_diff / (np.abs(c_pix0_array) + 1e-15)
    
    print(f"\nDifferences:")
    print(f"  Absolute: [{diff[0]:.9f}, {diff[1]:.9f}, {diff[2]:.9f}]")
    print(f"  Magnitude: {np.linalg.norm(diff):.9f}")
    print(f"  Relative: [{rel_diff[0]:.2e}, {rel_diff[1]:.2e}, {rel_diff[2]:.2e}]")
    
    # Check if differences are significant
    max_abs_diff = np.max(abs_diff)
    max_rel_diff = np.max(rel_diff)
    
    print(f"\nAssessment:")
    print(f"  Max absolute difference: {max_abs_diff:.9f}")
    print(f"  Max relative difference: {max_rel_diff:.2e}")
    
    if max_abs_diff < 1e-12:
        print("  ✅ EXCELLENT: Differences are at machine precision level")
        status = "EXCELLENT"
    elif max_abs_diff < 1e-6:
        print("  ✅ GOOD: Differences are very small (sub-micron)")
        status = "GOOD"
    elif max_rel_diff < 1e-3:
        print("  ⚠️  ACCEPTABLE: Small relative differences")
        status = "ACCEPTABLE"
    else:
        print("  ❌ SIGNIFICANT: Large differences detected")
        status = "SIGNIFICANT"
        
    return status, max_abs_diff, max_rel_diff


def main():
    """Main function to compare C and Python pix0_vector calculations."""
    print("C vs Python pix0_vector Comparison")
    print("==================================")
    
    # Set environment variable
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    
    device = torch.device("cpu")
    dtype = torch.float64
    
    # Test configurations
    configs = [
        ("Baseline", DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=51.2,
            beam_center_f=51.2,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,  # Default for no rotations
        )),
        ("Tilted", DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=51.2,
            beam_center_f=51.2,
            detector_convention=DetectorConvention.MOSFLM,
            detector_rotx_deg=5.0,
            detector_roty_deg=3.0,
            detector_rotz_deg=2.0,
            detector_twotheta_deg=20.0,
            detector_pivot=DetectorPivot.SAMPLE,  # Forced by twotheta != 0
        )),
    ]
    
    results = {}
    
    for config_name, config in configs:
        print(f"\n{'='*80}")
        print(f"TESTING CONFIGURATION: {config_name}")
        print(f"{'='*80}")
        
        # Create Python detector
        detector = Detector(config=config, device=device, dtype=dtype)
        py_pix0 = detector.pix0_vector
        
        print(f"Python pix0_vector: [{py_pix0[0]:.6f}, {py_pix0[1]:.6f}, {py_pix0[2]:.6f}]")
        
        # Run C code with trace
        c_pix0 = run_c_with_trace(config, config_name)
        
        if c_pix0:
            # Compare results
            status, max_abs_diff, max_rel_diff = compare_pix0_vectors(py_pix0, c_pix0, config_name)
            results[config_name] = {
                'status': status,
                'max_abs_diff': max_abs_diff,
                'max_rel_diff': max_rel_diff,
                'python_pix0': py_pix0.detach().numpy(),
                'c_pix0': np.array(c_pix0)
            }
        else:
            print(f"❌ Could not obtain C pix0_vector for {config_name}")
            results[config_name] = {'status': 'FAILED', 'error': 'C execution failed'}
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    all_good = True
    for config_name, result in results.items():
        if result['status'] in ['EXCELLENT', 'GOOD']:
            print(f"✅ {config_name}: {result['status']} (max_abs_diff: {result.get('max_abs_diff', 'N/A')})")
        elif result['status'] == 'ACCEPTABLE':
            print(f"⚠️  {config_name}: {result['status']} (max_abs_diff: {result.get('max_abs_diff', 'N/A')})")
            all_good = False
        else:
            print(f"❌ {config_name}: {result['status']}")
            all_good = False
    
    if all_good:
        print(f"\n✅ Overall: pix0_vector calculations are consistent between C and Python")
        print(f"   The correlation issue is likely NOT in the pix0_vector calculation.")
        print(f"   Next step: Check basis vector calculations or simulator logic.")
    else:
        print(f"\n❌ Overall: Significant differences found in pix0_vector calculations")
        print(f"   This could be the root cause of the correlation issue.")
        
        # Show the most problematic case
        valid_results = [(name, res) for name, res in results.items() if 'max_abs_diff' in res]
        if valid_results:
            worst_case = max(valid_results, key=lambda x: x[1]['max_abs_diff'])
            name, res = worst_case
            print(f"\n   Worst case: {name} with max_abs_diff = {res['max_abs_diff']:.9f}")
            print(f"   Python: {res['python_pix0']}")
            print(f"   C:      {res['c_pix0']}")
        else:
            print(f"\n   No valid results for comparison.")


if __name__ == "__main__":
    main()