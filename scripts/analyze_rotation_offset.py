#!/usr/bin/env python3
"""
Phase 5 Rotation Offset Analysis Script

Analyzes the mathematical relationship between rotation angles and the 3cm offset.
Tests if the offset scales with angle magnitude and investigates geometric patterns.

This script:
1. Tests different angle magnitudes systematically
2. Plots offset vs angle relationships
3. Looks for mathematical patterns (linear, quadratic, etc.)
4. Checks if 3cm = f(angles, distance, pixel_size)
"""

import os
import sys
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import re
from pathlib import Path
import json

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
                match = re.search(r'pix0_vector=([0-9.-]+)\s+([0-9.-]+)\s+([0-9.-]+)', line)
                if match:
                    return np.array([float(match.group(1)), float(match.group(2)), float(match.group(3))])
    return None


def run_c_trace(rotx=0, roty=0, rotz=0, twotheta=0, output_file="test_offset_c.log"):
    """Run C implementation with specified rotations."""
    golden_dir = Path(__file__).parent.parent / "golden_suite_generator"
    
    cmd = [
        "./nanoBragg",
        "-lambda", "6.2",
        "-N", "5",
        "-cell", "100", "100", "100", "90", "90", "90",
        "-default_F", "100",
        "-distance", "100",
        "-detpixels", "1024",
        "-Xbeam", "51.2", "-Ybeam", "51.2",
        "-floatfile", "test_offset.bin"
    ]
    
    if rotx != 0:
        cmd.extend(["-detector_rotx", str(rotx)])
    if roty != 0:
        cmd.extend(["-detector_roty", str(roty)])
    if rotz != 0:
        cmd.extend(["-detector_rotz", str(rotz)])
    if twotheta != 0:
        cmd.extend(["-twotheta", str(twotheta)])
    
    try:
        result = subprocess.run(cmd, cwd=golden_dir, capture_output=True, text=True, timeout=30)
        
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            f.write(result.stderr)
        
        pix0 = extract_pix0_from_c_trace(output_path)
        return pix0, result.returncode == 0
        
    except Exception as e:
        return None, False


def run_python_trace(rotx=0, roty=0, rotz=0, twotheta=0):
    """Run Python implementation with specified rotations."""
    try:
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
            detector_pivot="beam",
            detector_convention="mosflm"
        )
        
        return detector.pix0_vector.detach().numpy(), True
        
    except Exception as e:
        return None, False


def test_angle_scaling():
    """Test how offset scales with rotation angle magnitude."""
    print("=" * 80)
    print("ANGLE SCALING ANALYSIS")
    print("=" * 80)
    print()
    
    # Test each rotation type individually with different magnitudes
    rotation_types = [
        ('rotx', [0, 1, 2, 5, 10, 15, 20]),
        ('roty', [0, 1, 2, 3, 6, 10, 15]),
        ('rotz', [0, 1, 2, 4, 8, 15]),
        ('twotheta', [0, 5, 10, 15, 20, 30, 45])
    ]
    
    all_results = {}
    
    for rot_type, angles in rotation_types:
        print(f"Testing {rot_type} scaling...")
        results = []
        
        for angle in angles:
            print(f"  Testing {rot_type}={angle}°...")
            
            # Set up rotation parameters
            rotx = angle if rot_type == 'rotx' else 0
            roty = angle if rot_type == 'roty' else 0
            rotz = angle if rot_type == 'rotz' else 0
            twotheta = angle if rot_type == 'twotheta' else 0
            
            # Run both implementations
            c_pix0, c_success = run_c_trace(rotx, roty, rotz, twotheta, f"c_offset_{rot_type}_{angle}.log")
            py_pix0, py_success = run_python_trace(rotx, roty, rotz, twotheta)
            
            if c_success and py_success and c_pix0 is not None and py_pix0 is not None:
                offset = np.linalg.norm(py_pix0 - c_pix0)
                results.append({
                    'angle': angle,
                    'offset_m': offset,
                    'offset_cm': offset * 100,
                    'c_pix0': c_pix0,
                    'py_pix0': py_pix0
                })
                print(f"    Offset: {offset*100:.2f} cm")
            else:
                print(f"    ❌ Failed")
        
        all_results[rot_type] = results
        print()
    
    return all_results


def test_geometric_relationships():
    """Test geometric relationships and patterns."""
    print("=" * 80)
    print("GEOMETRIC RELATIONSHIP ANALYSIS")
    print("=" * 80)
    print()
    
    # Test if offset is related to geometric parameters
    distance_mm = 100
    pixel_size_mm = 0.1
    beam_center = 51.2
    
    print(f"System parameters:")
    print(f"  Distance: {distance_mm} mm")
    print(f"  Pixel size: {pixel_size_mm} mm")
    print(f"  Beam center: {beam_center} mm")
    print()
    
    # Calculate some expected geometric scales
    detector_size_mm = 1024 * pixel_size_mm  # 102.4 mm
    beam_offset_mm = abs(beam_center - detector_size_mm/2)  # Distance from center
    
    print(f"Derived scales:")
    print(f"  Detector size: {detector_size_mm} mm")
    print(f"  Beam offset from center: {beam_offset_mm} mm")
    print()
    
    # Test the full tilted configuration
    print("Testing full tilted configuration (rotx=5°, roty=3°, rotz=2°, twotheta=20°)...")
    c_pix0, c_success = run_c_trace(5, 3, 2, 20, "c_offset_full.log")
    py_pix0, py_success = run_python_trace(5, 3, 2, 20)
    
    if c_success and py_success and c_pix0 is not None and py_pix0 is not None:
        offset = np.linalg.norm(py_pix0 - c_pix0)
        print(f"  Full configuration offset: {offset*100:.2f} cm")
        
        # Check if offset relates to system parameters
        offset_ratio_to_distance = offset / (distance_mm / 1000)  # ratio to distance in meters
        offset_ratio_to_detector = (offset * 1000) / detector_size_mm  # ratio to detector size
        
        print(f"  Offset/distance ratio: {offset_ratio_to_distance:.4f}")
        print(f"  Offset/detector_size ratio: {offset_ratio_to_detector:.4f}")
        
        # Check if it's related to angular scales
        total_angle_magnitude = np.sqrt(5**2 + 3**2 + 2**2 + 20**2)  # degrees
        angle_radians = np.radians(total_angle_magnitude)
        
        print(f"  Total angle magnitude: {total_angle_magnitude:.2f}°")
        print(f"  Offset per degree: {(offset*100)/total_angle_magnitude:.3f} cm/deg")
        
        # Check if it's approximately: offset ≈ distance * sin(angle)
        expected_offset_sin = distance_mm / 1000 * np.sin(angle_radians)
        print(f"  Expected offset (distance*sin(total_angle)): {expected_offset_sin*100:.2f} cm")
        
        return {
            'measured_offset_cm': offset * 100,
            'expected_sin_cm': expected_offset_sin * 100,
            'offset_distance_ratio': offset_ratio_to_distance,
            'offset_detector_ratio': offset_ratio_to_detector,
            'offset_per_degree': (offset*100)/total_angle_magnitude
        }
    else:
        print("  ❌ Failed to run full configuration")
        return None


def analyze_component_contributions():
    """Analyze which pix0 components contribute most to the offset."""
    print("=" * 80)
    print("PIX0 COMPONENT CONTRIBUTION ANALYSIS")
    print("=" * 80)
    print()
    
    # Test full configuration and analyze each component
    print("Analyzing pix0 components for full tilted configuration...")
    
    c_pix0, c_success = run_c_trace(5, 3, 2, 20, "c_component_analysis.log")
    py_pix0, py_success = run_python_trace(5, 3, 2, 20)
    
    if not (c_success and py_success and c_pix0 is not None and py_pix0 is not None):
        print("❌ Failed to get pix0 vectors")
        return None
    
    print(f"C pix0:      [{c_pix0[0]:10.6f}, {c_pix0[1]:10.6f}, {c_pix0[2]:10.6f}]")
    print(f"Python pix0: [{py_pix0[0]:10.6f}, {py_pix0[1]:10.6f}, {py_pix0[2]:10.6f}]")
    
    diff = py_pix0 - c_pix0
    print(f"Difference:  [{diff[0]:10.6f}, {diff[1]:10.6f}, {diff[2]:10.6f}]")
    
    # Analyze component magnitudes
    component_names = ['X', 'Y', 'Z']
    max_component_idx = np.argmax(np.abs(diff))
    
    print()
    print("Component analysis:")
    for i, name in enumerate(component_names):
        component_diff = abs(diff[i])
        percentage = (component_diff / np.linalg.norm(diff)) * 100
        print(f"  {name} component: {component_diff:.6f} m ({component_diff*100:.2f} cm, {percentage:.1f}% of total)")
    
    print(f"\nLargest contribution: {component_names[max_component_idx]} component")
    
    # Check if offset is primarily in beam direction (X)
    if max_component_idx == 0:
        print("⚠️  Largest offset is in beam direction (X) - suggests rotation application issue")
    elif max_component_idx == 1 or max_component_idx == 2:
        print("⚠️  Largest offset is in detector plane - suggests beam center or pixel calculation issue")
    
    return {
        'c_pix0': c_pix0,
        'py_pix0': py_pix0,
        'difference': diff,
        'total_offset_cm': np.linalg.norm(diff) * 100,
        'max_component': component_names[max_component_idx],
        'component_contributions': {
            component_names[i]: {'diff_m': abs(diff[i]), 'diff_cm': abs(diff[i])*100, 'percentage': (abs(diff[i])/np.linalg.norm(diff))*100}
            for i in range(3)
        }
    }


def plot_scaling_results(scaling_results):
    """Create plots showing offset vs angle relationships."""
    print("Creating scaling analysis plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Rotation Offset Scaling Analysis', fontsize=16)
    
    colors = ['blue', 'green', 'red', 'orange']
    
    for idx, (rot_type, results) in enumerate(scaling_results.items()):
        if not results:
            continue
        
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]
        
        angles = [r['angle'] for r in results]
        offsets_cm = [r['offset_cm'] for r in results]
        
        # Plot data points
        ax.scatter(angles, offsets_cm, color=colors[idx], s=50, alpha=0.7, label='Measured')
        
        # Fit linear relationship
        if len(angles) > 2:
            coeffs = np.polyfit(angles, offsets_cm, 1)
            fit_line = np.poly1d(coeffs)
            angle_range = np.linspace(0, max(angles), 100)
            ax.plot(angle_range, fit_line(angle_range), '--', color=colors[idx], alpha=0.5, label=f'Linear fit (slope={coeffs[0]:.3f})')
        
        ax.set_xlabel(f'{rot_type} angle (degrees)')
        ax.set_ylabel('Offset (cm)')
        ax.set_title(f'{rot_type.capitalize()} Scaling')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add 3cm reference line
        ax.axhline(y=3.0, color='red', linestyle=':', alpha=0.5, label='3cm target')
    
    plt.tight_layout()
    plt.savefig('rotation_offset_scaling.png', dpi=150, bbox_inches='tight')
    print("Scaling plots saved to: rotation_offset_scaling.png")
    
    return 'rotation_offset_scaling.png'


def run_offset_analysis():
    """Run complete rotation offset analysis."""
    print("=" * 80)
    print("PHASE 5 ROTATION OFFSET ANALYSIS")
    print("=" * 80)
    print()
    print("Analyzing mathematical relationships between rotation angles and 3cm offset")
    print("Configuration: beam_center_s=51.2, beam_center_f=51.2, distance=100mm, pixel_size=0.1mm")
    print()
    
    results = {}
    
    # 1. Test angle scaling
    print("STEP 1: Testing angle scaling relationships...")
    scaling_results = test_angle_scaling()
    results['scaling'] = scaling_results
    
    # 2. Test geometric relationships
    print("STEP 2: Testing geometric relationships...")
    geometric_results = test_geometric_relationships()
    results['geometric'] = geometric_results
    
    # 3. Analyze component contributions
    print("STEP 3: Analyzing pix0 component contributions...")
    component_results = analyze_component_contributions()
    results['components'] = component_results
    
    # 4. Create plots
    if scaling_results:
        plot_file = plot_scaling_results(scaling_results)
        results['plot_file'] = plot_file
    
    # Summary analysis
    print("\n" + "=" * 80)
    print("OFFSET ANALYSIS SUMMARY")
    print("=" * 80)
    
    # Find maximum offsets for each rotation type
    max_offsets = {}
    for rot_type, data in scaling_results.items():
        if data:
            max_offset = max([r['offset_cm'] for r in data])
            max_offsets[rot_type] = max_offset
            print(f"Max {rot_type} offset: {max_offset:.2f} cm")
    
    # Check if any single rotation can cause 3cm offset
    has_3cm_single = any(offset > 2.5 for offset in max_offsets.values())
    
    print()
    print("KEY FINDINGS:")
    
    if has_3cm_single:
        worst_rotation = max(max_offsets, key=max_offsets.get)
        print(f"✅ FOUND: {worst_rotation} can cause >2.5cm offset")
        print(f"   → Single rotation IS sufficient to explain 3cm offset")
    else:
        print("❌ No single rotation causes >2.5cm offset")
        print("   → 3cm offset requires rotation combinations or other factors")
    
    # Geometric analysis
    if geometric_results:
        print()
        print(f"Full configuration offset: {geometric_results['measured_offset_cm']:.2f} cm")
        print(f"Expected geometric offset: {geometric_results['expected_sin_cm']:.2f} cm")
        print(f"Offset per degree: {geometric_results['offset_per_degree']:.3f} cm/deg")
        
        if abs(geometric_results['measured_offset_cm'] - geometric_results['expected_sin_cm']) < 0.5:
            print("✅ Measured offset matches geometric expectation")
        else:
            print("❌ Measured offset differs from geometric expectation")
    
    # Component analysis
    if component_results:
        print()
        print(f"Primary offset component: {component_results['max_component']}")
        for comp, data in component_results['component_contributions'].items():
            print(f"  {comp}: {data['diff_cm']:.2f} cm ({data['percentage']:.1f}%)")
    
    # Overall assessment
    print()
    print("ROTATION OFFSET HYPOTHESIS ASSESSMENT:")
    
    if has_3cm_single or (geometric_results and geometric_results['measured_offset_cm'] > 2.5):
        print("✅ HYPOTHESIS CONFIRMED: Rotation logic can cause ~3cm offset")
        print("   → Focus on rotation implementation differences between C and Python")
        if component_results:
            print(f"   → Primary issue in {component_results['max_component']} component calculation")
    else:
        print("❌ HYPOTHESIS UNCLEAR: Rotation effects are smaller than expected")
        print("   → May require combination effects or different pivot modes")
        print("   → Consider beam center calculation or other systematic errors")
    
    print()
    print("RECOMMENDATIONS:")
    print("1. Focus on the rotation with largest offset contribution")
    print("2. Debug rotation matrix application step-by-step")
    print("3. Check pivot mode implementation (BEAM vs SAMPLE)")
    print("4. Verify trigonometric function precision")
    
    # Save comprehensive results
    results_file = "rotation_offset_analysis_results.json"
    
    # Convert numpy arrays to lists for JSON serialization
    def convert_numpy(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(item) for item in obj]
        return obj
    
    results_serializable = convert_numpy(results)
    
    with open(results_file, 'w') as f:
        json.dump(results_serializable, f, indent=2)
    
    print(f"\nComprehensive results saved to: {results_file}")
    if 'plot_file' in results:
        print(f"Scaling plots saved to: {results['plot_file']}")
    
    return results


if __name__ == "__main__":
    run_offset_analysis()