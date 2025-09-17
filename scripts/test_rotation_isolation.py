#!/usr/bin/env python3
"""
Phase 5 Rotation Isolation Test Script

Tests each rotation component individually to isolate which rotation(s) 
cause the 3cm pix0_vector offset between C and Python implementations.

This script systematically tests:
1. Baseline (no rotations)
2. Only rotx=5°
3. Only roty=3°
4. Only rotz=2°
5. Only twotheta=20°

For each case, it generates C and Python traces and compares pix0_vector values.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import numpy as np
import re

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Set environment variable to prevent MKL conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.models.detector import Detector


def extract_pix0_from_c_trace(trace_file):
    """Extract pix0_vector from C trace file."""
    if not trace_file.exists():
        return None
    
    with open(trace_file, 'r') as f:
        for line in f:
            if 'TRACE_C:pix0_vector=' in line:
                # Extract the three numbers after =
                match = re.search(r'pix0_vector=([0-9.-]+)\s+([0-9.-]+)\s+([0-9.-]+)', line)
                if match:
                    return np.array([float(match.group(1)), float(match.group(2)), float(match.group(3))])
    return None


def run_c_trace(rotx=0, roty=0, rotz=0, twotheta=0, output_file="test_rotation_c.log"):
    """Run C implementation with specified rotations."""
    # Navigate to golden_suite_generator directory
    golden_dir = Path(__file__).parent.parent / "golden_suite_generator"
    
    # Build command - use BEAM pivot for simplicity (avoid SAMPLE pivot complexity)
    cmd = [
        "./nanoBragg",
        "-lambda", "6.2",
        "-N", "5",
        "-cell", "100", "100", "100", "90", "90", "90",
        "-default_F", "100",
        "-distance", "100",
        "-detpixels", "1024",
        "-Xbeam", "51.2", "-Ybeam", "51.2",
        "-floatfile", "test_rotation.bin"
    ]
    
    # Add rotations only if non-zero
    if rotx != 0:
        cmd.extend(["-detector_rotx", str(rotx)])
    if roty != 0:
        cmd.extend(["-detector_roty", str(roty)])
    if rotz != 0:
        cmd.extend(["-detector_rotz", str(rotz)])
    if twotheta != 0:
        cmd.extend(["-twotheta", str(twotheta)])
    
    try:
        # Run C code and capture stderr (where TRACE_C prints go)
        result = subprocess.run(
            cmd, 
            cwd=golden_dir,
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        # Save stderr to output file (where traces go)
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            f.write(result.stderr)
        
        # Check if pix0_vector was found
        pix0 = extract_pix0_from_c_trace(output_path)
        return pix0, result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  C code timeout")
        return None, False
    except Exception as e:
        print(f"  ❌ C code error: {e}")
        return None, False


def run_python_trace(rotx=0, roty=0, rotz=0, twotheta=0):
    """Run Python implementation with specified rotations."""
    try:
        # Create detector with BEAM pivot (simpler than SAMPLE pivot)
        detector = Detector(
            distance_mm=100.0,
            beam_center_s=51.2,
            beam_center_f=51.2,
            pixel_size_mm=0.1,
            detector_size_pixels=1024,
            detector_rotx_deg=rotx,
            detector_roty_deg=roty,
            detector_rotz_deg=rotz,
            detector_twotheta_deg=twotheta,
            detector_pivot="beam",  # Use BEAM pivot for simplicity
            detector_convention="mosflm"
        )
        
        return detector.pix0_vector.detach().numpy(), True
        
    except Exception as e:
        print(f"  ❌ Python error: {e}")
        return None, False


def calculate_offset_metrics(c_pix0, py_pix0):
    """Calculate offset metrics between C and Python pix0 vectors."""
    if c_pix0 is None or py_pix0 is None:
        return None, None, None
    
    diff = py_pix0 - c_pix0
    max_diff = np.max(np.abs(diff))
    rms_diff = np.sqrt(np.mean(diff**2))
    offset_magnitude = np.linalg.norm(diff)
    
    return max_diff, rms_diff, offset_magnitude


def run_isolation_test():
    """Run complete rotation isolation test suite."""
    print("=" * 80)
    print("PHASE 5 ROTATION ISOLATION TEST")
    print("=" * 80)
    print()
    print("Testing hypothesis: Rotation logic causes 3cm pix0_vector offset")
    print("Configuration: beam_center_s=51.2, beam_center_f=51.2, distance=100mm, pixel_size=0.1mm")
    print("Pivot Mode: BEAM (simpler than SAMPLE pivot)")
    print()
    
    # Test cases: [name, rotx, roty, rotz, twotheta]
    test_cases = [
        ("Baseline (no rotations)", 0, 0, 0, 0),
        ("Only rotx=5°", 5, 0, 0, 0),
        ("Only roty=3°", 0, 3, 0, 0),
        ("Only rotz=2°", 0, 0, 2, 0),
        ("Only twotheta=20°", 0, 0, 0, 20),
    ]
    
    results = []
    
    for test_name, rotx, roty, rotz, twotheta in test_cases:
        print(f"Testing: {test_name}")
        print(f"  Rotations: rotx={rotx}°, roty={roty}°, rotz={rotz}°, twotheta={twotheta}°")
        
        # Run C implementation
        print("  Running C implementation...")
        c_trace_file = f"c_trace_rot_{rotx}_{roty}_{rotz}_{twotheta}.log"
        c_pix0, c_success = run_c_trace(rotx, roty, rotz, twotheta, c_trace_file)
        
        if not c_success:
            print(f"  ❌ C implementation failed")
            continue
        
        if c_pix0 is None:
            print(f"  ❌ Could not extract pix0_vector from C trace")
            continue
        
        # Run Python implementation
        print("  Running Python implementation...")
        py_pix0, py_success = run_python_trace(rotx, roty, rotz, twotheta)
        
        if not py_success:
            print(f"  ❌ Python implementation failed")
            continue
        
        if py_pix0 is None:
            print(f"  ❌ Could not extract pix0_vector from Python")
            continue
        
        # Calculate metrics
        max_diff, rms_diff, offset_magnitude = calculate_offset_metrics(c_pix0, py_pix0)
        
        # Store results
        result = {
            'name': test_name,
            'rotx': rotx, 'roty': roty, 'rotz': rotz, 'twotheta': twotheta,
            'c_pix0': c_pix0,
            'py_pix0': py_pix0,
            'max_diff': max_diff,
            'rms_diff': rms_diff,
            'offset_magnitude': offset_magnitude,
            'c_trace_file': c_trace_file
        }
        results.append(result)
        
        # Display results
        print(f"  C pix0:      [{c_pix0[0]:10.8f}, {c_pix0[1]:10.8f}, {c_pix0[2]:10.8f}]")
        print(f"  Python pix0: [{py_pix0[0]:10.8f}, {py_pix0[1]:10.8f}, {py_pix0[2]:10.8f}]")
        print(f"  Max diff:    {max_diff:.2e} m")
        print(f"  RMS diff:    {rms_diff:.2e} m")
        print(f"  Offset mag:  {offset_magnitude:.2e} m ({offset_magnitude*100:.1f} cm)")
        
        # Check if this is a significant offset
        if offset_magnitude > 0.01:  # > 1cm
            print(f"  ⚠️  SIGNIFICANT OFFSET DETECTED!")
        elif offset_magnitude > 0.001:  # > 1mm
            print(f"  ⚠️  Moderate offset")
        else:
            print(f"  ✅ Small offset")
        
        print()
    
    # Summary analysis
    print("=" * 80)
    print("ISOLATION TEST SUMMARY")
    print("=" * 80)
    
    if not results:
        print("❌ No test results available")
        return
    
    # Print results table
    print(f"{'Test Case':<25} {'Max Diff (m)':<12} {'RMS Diff (m)':<12} {'Offset (cm)':<12} {'Status':<15}")
    print("-" * 80)
    
    baseline_offset = None
    significant_offsets = []
    
    for result in results:
        status = ""
        if result['offset_magnitude'] > 0.01:
            status = "⚠️  SIGNIFICANT"
            significant_offsets.append(result)
        elif result['offset_magnitude'] > 0.001:
            status = "⚠️  MODERATE"
        else:
            status = "✅ SMALL"
        
        if "Baseline" in result['name']:
            baseline_offset = result['offset_magnitude']
        
        print(f"{result['name']:<25} {result['max_diff']:<12.2e} {result['rms_diff']:<12.2e} "
              f"{result['offset_magnitude']*100:<12.1f} {status:<15}")
    
    print()
    
    # Analysis
    print("ANALYSIS:")
    print(f"• Baseline offset: {baseline_offset*100:.2f} cm" if baseline_offset else "• Baseline: Not available")
    
    if significant_offsets:
        print(f"• Rotations causing significant offset (>1cm):")
        for result in significant_offsets:
            rotations = []
            if result['rotx'] != 0: rotations.append(f"rotx={result['rotx']}°")
            if result['roty'] != 0: rotations.append(f"roty={result['roty']}°")
            if result['rotz'] != 0: rotations.append(f"rotz={result['rotz']}°")
            if result['twotheta'] != 0: rotations.append(f"twotheta={result['twotheta']}°")
            rotation_str = ", ".join(rotations) if rotations else "none"
            print(f"  - {result['name']}: {rotation_str} -> {result['offset_magnitude']*100:.1f} cm offset")
    else:
        print("• No individual rotations cause significant offset (>1cm)")
    
    # Hypothesis assessment
    print()
    print("ROTATION HYPOTHESIS ASSESSMENT:")
    
    # Check if any single rotation causes the 3cm offset
    has_3cm_offset = any(r['offset_magnitude'] > 0.025 for r in results)  # >2.5cm threshold
    
    if has_3cm_offset:
        print("✅ HYPOTHESIS CONFIRMED: Individual rotation(s) cause ~3cm offset")
        print("   → Rotation logic is likely the primary cause of the discrepancy")
    else:
        print("❌ HYPOTHESIS REJECTED: No individual rotation causes ~3cm offset")
        print("   → The 3cm offset likely comes from rotation combinations or other factors")
        print("   → Proceed to combination testing (test_rotation_combinations.py)")
    
    print()
    print("NEXT STEPS:")
    if has_3cm_offset:
        print("1. Focus on the specific rotation(s) causing large offsets")
        print("2. Debug the rotation matrix construction for those rotations")
        print("3. Compare rotation application logic between C and Python")
    else:
        print("1. Run combination tests (test_rotation_combinations.py)")
        print("2. Check if multiple rotations compound the error")
        print("3. Investigate beam center calculation and pivot mode logic")
    
    # Save detailed results
    results_file = "rotation_isolation_results.txt"
    with open(results_file, 'w') as f:
        f.write("Phase 5 Rotation Isolation Test Results\n")
        f.write("=" * 50 + "\n\n")
        
        for result in results:
            f.write(f"Test: {result['name']}\n")
            f.write(f"Rotations: rotx={result['rotx']}, roty={result['roty']}, rotz={result['rotz']}, twotheta={result['twotheta']}\n")
            f.write(f"C pix0: [{result['c_pix0'][0]:.8f}, {result['c_pix0'][1]:.8f}, {result['c_pix0'][2]:.8f}]\n")
            f.write(f"Python pix0: [{result['py_pix0'][0]:.8f}, {result['py_pix0'][1]:.8f}, {result['py_pix0'][2]:.8f}]\n")
            f.write(f"Offset magnitude: {result['offset_magnitude']:.6f} m ({result['offset_magnitude']*100:.2f} cm)\n")
            f.write(f"C trace file: {result['c_trace_file']}\n")
            f.write("\n")
    
    print(f"Detailed results saved to: {results_file}")
    print(f"C trace files saved with pattern: c_trace_rot_*.log")


if __name__ == "__main__":
    run_isolation_test()