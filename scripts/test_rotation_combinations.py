#!/usr/bin/env python3
"""
Phase 5 Rotation Combination Test Script

Tests combinations of rotations to see if the 3cm pix0_vector offset 
emerges from interactions between multiple rotations.

This script systematically tests:
1. All pairwise combinations
2. Three-rotation combinations 
3. Full four-rotation combination (matching tilted detector case)

Focus: Understanding if rotation combinations compound errors.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import numpy as np
import re
import itertools

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


def run_c_trace(rotx=0, roty=0, rotz=0, twotheta=0, output_file="test_rotation_combo_c.log"):
    """Run C implementation with specified rotation combination."""
    # Navigate to golden_suite_generator directory
    golden_dir = Path(__file__).parent.parent / "golden_suite_generator"
    
    # Build command - use consistent configuration
    cmd = [
        "./nanoBragg",
        "-lambda", "6.2",
        "-N", "5",
        "-cell", "100", "100", "100", "90", "90", "90",
        "-default_F", "100",
        "-distance", "100",
        "-detpixels", "1024",
        "-Xbeam", "51.2", "-Ybeam", "51.2",
        "-floatfile", "test_rotation_combo.bin"
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
    """Run Python implementation with specified rotation combination."""
    try:
        # Use BEAM pivot for consistency (simpler logic)
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
            detector_pivot="beam",  # Use BEAM pivot
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


def generate_rotation_combinations():
    """Generate systematic rotation combinations to test."""
    # Base rotation values from tilted detector case
    rotations = {
        'rotx': 5,
        'roty': 3,
        'rotz': 2,
        'twotheta': 20
    }
    
    combinations = []
    
    # 1. Pairwise combinations
    rotation_keys = list(rotations.keys())
    for combo in itertools.combinations(rotation_keys, 2):
        combo_dict = {k: 0 for k in rotation_keys}
        for k in combo:
            combo_dict[k] = rotations[k]
        combo_name = " + ".join([f"{k}={rotations[k]}°" for k in combo])
        combinations.append((f"Pair: {combo_name}", combo_dict))
    
    # 2. Three-rotation combinations
    for combo in itertools.combinations(rotation_keys, 3):
        combo_dict = {k: 0 for k in rotation_keys}
        for k in combo:
            combo_dict[k] = rotations[k]
        combo_name = " + ".join([f"{k}={rotations[k]}°" for k in combo])
        combinations.append((f"Triple: {combo_name}", combo_dict))
    
    # 3. Full combination (all four rotations)
    combinations.append(("Full: All rotations", rotations))
    
    # 4. Incremental builds (to see where offset starts)
    combinations.extend([
        ("Incremental: rotx", {'rotx': 5, 'roty': 0, 'rotz': 0, 'twotheta': 0}),
        ("Incremental: rotx+roty", {'rotx': 5, 'roty': 3, 'rotz': 0, 'twotheta': 0}),
        ("Incremental: rotx+roty+rotz", {'rotx': 5, 'roty': 3, 'rotz': 2, 'twotheta': 0}),
        ("Incremental: rotx+roty+rotz+twotheta", {'rotx': 5, 'roty': 3, 'rotz': 2, 'twotheta': 20}),
    ])
    
    # 5. Scale testing (half angles)
    combinations.extend([
        ("Scale: Half angles", {'rotx': 2.5, 'roty': 1.5, 'rotz': 1.0, 'twotheta': 10}),
        ("Scale: Double angles", {'rotx': 10, 'roty': 6, 'rotz': 4, 'twotheta': 40}),
    ])
    
    return combinations


def run_combination_test():
    """Run complete rotation combination test suite."""
    print("=" * 80)
    print("PHASE 5 ROTATION COMBINATION TEST")
    print("=" * 80)
    print()
    print("Testing hypothesis: Rotation combinations cause 3cm pix0_vector offset")
    print("Configuration: beam_center_s=51.2, beam_center_f=51.2, distance=100mm, pixel_size=0.1mm")
    print("Pivot Mode: BEAM (consistent with isolation test)")
    print()
    
    # Generate test combinations
    combinations = generate_rotation_combinations()
    print(f"Testing {len(combinations)} rotation combinations...")
    print()
    
    results = []
    
    for test_name, rotation_params in combinations:
        print(f"Testing: {test_name}")
        rotx = rotation_params['rotx']
        roty = rotation_params['roty']
        rotz = rotation_params['rotz']
        twotheta = rotation_params['twotheta']
        
        print(f"  Rotations: rotx={rotx}°, roty={roty}°, rotz={rotz}°, twotheta={twotheta}°")
        
        # Generate unique filename for C trace
        combo_id = f"{rotx}_{roty}_{rotz}_{twotheta}".replace(".", "p")
        c_trace_file = f"c_trace_combo_{combo_id}.log"
        
        # Run C implementation
        print("  Running C implementation...")
        c_pix0, c_success = run_c_trace(rotx, roty, rotz, twotheta, c_trace_file)
        
        if not c_success or c_pix0 is None:
            print(f"  ❌ C implementation failed")
            continue
        
        # Run Python implementation
        print("  Running Python implementation...")
        py_pix0, py_success = run_python_trace(rotx, roty, rotz, twotheta)
        
        if not py_success or py_pix0 is None:
            print(f"  ❌ Python implementation failed")
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
            'c_trace_file': c_trace_file,
            'num_rotations': sum([1 for r in [rotx, roty, rotz, twotheta] if r != 0])
        }
        results.append(result)
        
        # Display results
        print(f"  C pix0:      [{c_pix0[0]:10.8f}, {c_pix0[1]:10.8f}, {c_pix0[2]:10.8f}]")
        print(f"  Python pix0: [{py_pix0[0]:10.8f}, {py_pix0[1]:10.8f}, {py_pix0[2]:10.8f}]")
        print(f"  Max diff:    {max_diff:.2e} m")
        print(f"  RMS diff:    {rms_diff:.2e} m")
        print(f"  Offset mag:  {offset_magnitude:.2e} m ({offset_magnitude*100:.1f} cm)")
        
        # Check if this is a significant offset
        if offset_magnitude > 0.025:  # > 2.5cm (approaching 3cm)
            print(f"  🔴 LARGE OFFSET! (~3cm range)")
        elif offset_magnitude > 0.01:  # > 1cm
            print(f"  ⚠️  SIGNIFICANT OFFSET")
        elif offset_magnitude > 0.001:  # > 1mm
            print(f"  ⚠️  Moderate offset")
        else:
            print(f"  ✅ Small offset")
        
        print()
    
    # Summary analysis
    print("=" * 80)
    print("COMBINATION TEST SUMMARY")
    print("=" * 80)
    
    if not results:
        print("❌ No test results available")
        return
    
    # Sort results by offset magnitude
    results_sorted = sorted(results, key=lambda x: x['offset_magnitude'], reverse=True)
    
    # Print results table
    print(f"{'Test Case':<35} {'Num Rot':<8} {'Offset (cm)':<12} {'Max Diff':<12} {'Status':<15}")
    print("-" * 88)
    
    large_offsets = []
    significant_offsets = []
    
    for result in results_sorted:
        status = ""
        if result['offset_magnitude'] > 0.025:  # > 2.5cm
            status = "🔴 LARGE"
            large_offsets.append(result)
        elif result['offset_magnitude'] > 0.01:  # > 1cm
            status = "⚠️  SIGNIFICANT"
            significant_offsets.append(result)
        elif result['offset_magnitude'] > 0.001:  # > 1mm
            status = "⚠️  MODERATE"
        else:
            status = "✅ SMALL"
        
        print(f"{result['name']:<35} {result['num_rotations']:<8} {result['offset_magnitude']*100:<12.1f} "
              f"{result['max_diff']:<12.2e} {status:<15}")
    
    print()
    
    # Detailed analysis
    print("DETAILED ANALYSIS:")
    
    # 1. Check if full combination causes 3cm offset
    full_combo_result = next((r for r in results if "Full:" in r['name']), None)
    if full_combo_result:
        print(f"• Full combination offset: {full_combo_result['offset_magnitude']*100:.2f} cm")
        if full_combo_result['offset_magnitude'] > 0.025:
            print("  → This matches the expected ~3cm offset from tilted detector case!")
        else:
            print("  → This does NOT match the expected ~3cm offset")
    
    # 2. Check scaling behavior
    print()
    print("• Offset vs Number of Rotations:")
    for num_rot in range(1, 5):
        matching_results = [r for r in results if r['num_rotations'] == num_rot and "Incremental" in r['name']]
        if matching_results:
            avg_offset = np.mean([r['offset_magnitude'] for r in matching_results])
            print(f"  {num_rot} rotation(s): {avg_offset*100:.2f} cm average")
    
    # 3. Identify worst combinations
    if large_offsets:
        print()
        print("• Combinations causing LARGE offsets (>2.5cm):")
        for result in large_offsets:
            active_rotations = []
            if result['rotx'] != 0: active_rotations.append(f"rotx={result['rotx']}°")
            if result['roty'] != 0: active_rotations.append(f"roty={result['roty']}°")
            if result['rotz'] != 0: active_rotations.append(f"rotz={result['rotz']}°")
            if result['twotheta'] != 0: active_rotations.append(f"twotheta={result['twotheta']}°")
            rotation_str = ", ".join(active_rotations)
            print(f"  - {result['name']}: {rotation_str} -> {result['offset_magnitude']*100:.1f} cm")
    
    # 4. Progressive analysis (incremental builds)
    print()
    print("• Progressive Build Analysis:")
    incremental_results = [r for r in results if "Incremental:" in r['name']]
    incremental_results.sort(key=lambda x: x['num_rotations'])
    
    for result in incremental_results:
        print(f"  {result['name']}: {result['offset_magnitude']*100:.2f} cm")
    
    # 5. Scale analysis
    print()
    print("• Scale Analysis:")
    scale_results = [r for r in results if "Scale:" in r['name']]
    for result in scale_results:
        print(f"  {result['name']}: {result['offset_magnitude']*100:.2f} cm")
    
    # Hypothesis assessment
    print()
    print("COMBINATION HYPOTHESIS ASSESSMENT:")
    
    # Check if any combination causes the 3cm offset
    has_3cm_offset = any(r['offset_magnitude'] > 0.025 for r in results)
    progressive_trend = len(incremental_results) > 2
    
    if has_3cm_offset:
        print("✅ HYPOTHESIS CONFIRMED: Rotation combinations cause ~3cm offset")
        
        # Find the critical point where offset becomes large
        if incremental_results:
            critical_point = None
            for i, result in enumerate(incremental_results):
                if result['offset_magnitude'] > 0.02:  # >2cm threshold
                    critical_point = result
                    break
            
            if critical_point:
                print(f"   → Critical point: {critical_point['name']} ({critical_point['offset_magnitude']*100:.1f} cm)")
                print("   → This combination introduces the large offset")
        
        print("   → Rotation logic interactions are the primary cause")
        
    elif progressive_trend and incremental_results:
        # Check if there's a clear progressive increase
        offsets = [r['offset_magnitude'] for r in incremental_results]
        if len(offsets) > 2 and all(offsets[i] <= offsets[i+1] for i in range(len(offsets)-1)):
            print("⚠️  PARTIAL CONFIRMATION: Rotations progressively increase offset")
            print("   → May reach 3cm with more rotations or different pivot mode")
        else:
            print("❌ HYPOTHESIS REJECTED: No clear combination pattern for 3cm offset")
    else:
        print("❌ HYPOTHESIS REJECTED: Rotation combinations don't cause 3cm offset")
        print("   → Issue likely in rotation matrix construction or pivot mode logic")
    
    print()
    print("NEXT STEPS:")
    if has_3cm_offset:
        print("1. Focus on the critical rotation combination that introduces large offset")
        print("2. Debug the combined rotation matrix construction")
        print("3. Compare C vs Python rotation application order")
    else:
        print("1. Test with SAMPLE pivot mode (may be more sensitive)")
        print("2. Run matrix comparison test (test_rotation_matrices.py)")
        print("3. Debug rotation matrix construction element-by-element")
    
    # Save detailed results
    results_file = "rotation_combination_results.txt"
    with open(results_file, 'w') as f:
        f.write("Phase 5 Rotation Combination Test Results\n")
        f.write("=" * 50 + "\n\n")
        
        for result in results_sorted:
            f.write(f"Test: {result['name']}\n")
            f.write(f"Rotations: rotx={result['rotx']}, roty={result['roty']}, rotz={result['rotz']}, twotheta={result['twotheta']}\n")
            f.write(f"Number of rotations: {result['num_rotations']}\n")
            f.write(f"C pix0: [{result['c_pix0'][0]:.8f}, {result['c_pix0'][1]:.8f}, {result['c_pix0'][2]:.8f}]\n")
            f.write(f"Python pix0: [{result['py_pix0'][0]:.8f}, {result['py_pix0'][1]:.8f}, {result['py_pix0'][2]:.8f}]\n")
            f.write(f"Offset magnitude: {result['offset_magnitude']:.6f} m ({result['offset_magnitude']*100:.2f} cm)\n")
            f.write(f"C trace file: {result['c_trace_file']}\n")
            f.write("\n")
    
    print(f"Detailed results saved to: {results_file}")
    print(f"C trace files saved with pattern: c_trace_combo_*.log")


if __name__ == "__main__":
    run_combination_test()