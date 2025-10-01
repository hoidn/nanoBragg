#!/usr/bin/env python3
"""
Comprehensive analysis of pix0_vector discrepancy for Phase 4.1.

This script compares all available pix0 calculations:
1. Manual calculation (reference implementation)
2. PyTorch Detector class
3. Actual C implementation (from trace)
4. Expected C values (from problem statement)

The goal is to identify the exact source of the discrepancy.
"""

import os
import sys
import numpy as np
import torch
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig, DetectorPivot, DetectorConvention


def parse_c_trace():
    """Parse the C trace to extract key values."""
    trace_file = Path("c_pix0_trace_existing.log")
    
    if not trace_file.exists():
        print(f"❌ C trace file not found: {trace_file}")
        return None
    
    c_data = {}
    
    with open(trace_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Parse angles
            if "angles_rad=" in line:
                # TRACE_C:angles_rad=rotx:0.0872664625997165 roty:0.0523598775598299 rotz:0.0349065850398866 twotheta:0.349065850398866
                parts = line.split('=')[1].split()
                for part in parts:
                    key, val = part.split(':')
                    c_data[f"{key}_rad"] = float(val)
            
            # Parse beam center
            elif "beam_center_m=" in line:
                # TRACE_C:beam_center_m=X:5.125e-05 Y:5.125e-05 pixel_mm:0.1
                parts = line.split('=')[1].split()
                for part in parts:
                    if ':' in part:
                        key, val = part.split(':')
                        if key == 'X':
                            c_data['beam_center_x_m'] = float(val)
                        elif key == 'Y':
                            c_data['beam_center_y_m'] = float(val)
                        elif key == 'pixel_mm':
                            c_data['pixel_size_mm'] = float(val)
            
            # Parse basis vectors
            elif "initial_fdet=" in line:
                values = line.split('=')[1].split()
                c_data['initial_fdet'] = np.array([float(v) for v in values])
            elif "initial_sdet=" in line:
                values = line.split('=')[1].split()
                c_data['initial_sdet'] = np.array([float(v) for v in values])
            elif "initial_odet=" in line:
                values = line.split('=')[1].split()
                c_data['initial_odet'] = np.array([float(v) for v in values])
            
            # Parse final basis vectors
            elif "fdet_after_twotheta=" in line:
                values = line.split('=')[1].split()
                c_data['fdet_final'] = np.array([float(v) for v in values])
            elif "sdet_after_twotheta=" in line:
                values = line.split('=')[1].split()
                c_data['sdet_final'] = np.array([float(v) for v in values])
            elif "odet_after_twotheta=" in line:
                values = line.split('=')[1].split()
                c_data['odet_final'] = np.array([float(v) for v in values])
            
            # Parse beam calculations
            elif "Fbeam_m=" in line:
                c_data['Fbeam_m'] = float(line.split('=')[1])
            elif "Sbeam_m=" in line:
                c_data['Sbeam_m'] = float(line.split('=')[1])
            elif "distance_m=" in line:
                c_data['distance_m'] = float(line.split('=')[1])
            
            # Parse pix0 components
            elif "term_fast=" in line:
                values = line.split('=')[1].split()
                c_data['term_fast'] = np.array([float(v) for v in values])
            elif "term_slow=" in line:
                values = line.split('=')[1].split()
                c_data['term_slow'] = np.array([float(v) for v in values])
            elif "term_beam=" in line:
                values = line.split('=')[1].split()
                c_data['term_beam'] = np.array([float(v) for v in values])
            
            # Parse final pix0
            elif "pix0_vector=" in line:
                values = line.split('=')[1].split()
                c_data['pix0_vector'] = np.array([float(v) for v in values])
    
    return c_data


def manual_calculation():
    """Reproduce the manual calculation from verify_pix0_manually.py"""
    
    # Configuration
    distance_mm = 100.0
    beam_center_s = 51.2  # mm
    beam_center_f = 51.2  # mm
    pixel_size_mm = 0.1
    
    rotx_deg = 5.0
    roty_deg = 3.0  
    rotz_deg = 2.0
    twotheta_deg = 20.0
    
    # Convert to radians
    import math
    rotx_rad = math.radians(rotx_deg)
    roty_rad = math.radians(roty_deg)
    rotz_rad = math.radians(rotz_deg)
    twotheta_rad = math.radians(twotheta_deg)
    
    # Initial basis vectors (MOSFLM convention)
    fdet_init = np.array([0.0, 0.0, 1.0])
    sdet_init = np.array([0.0, -1.0, 0.0])  
    odet_init = np.array([1.0, 0.0, 0.0])
    
    # Calculate unrotated pix0 (SAMPLE pivot mode)
    # MOSFLM beam center convention: add 0.5 for pixel center
    Fclose = (beam_center_f + 0.5) * pixel_size_mm / 1000.0  # Convert mm to m
    Sclose = (beam_center_s + 0.5) * pixel_size_mm / 1000.0  # Convert mm to m
    distance_m = distance_mm / 1000.0  # Convert mm to m
    
    # Calculate components
    fdet_component = -Fclose * fdet_init
    sdet_component = -Sclose * sdet_init
    odet_component = distance_m * odet_init
    
    # Sum components for unrotated pix0
    pix0_unrotated = fdet_component + sdet_component + odet_component
    
    # Create rotation matrices
    cos_x = math.cos(rotx_rad)
    sin_x = math.sin(rotx_rad)
    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, cos_x, -sin_x],
        [0.0, sin_x, cos_x]
    ])
    
    cos_y = math.cos(roty_rad)
    sin_y = math.sin(roty_rad)
    Ry = np.array([
        [cos_y, 0.0, sin_y],
        [0.0, 1.0, 0.0],
        [-sin_y, 0.0, cos_y]
    ])
    
    cos_z = math.cos(rotz_rad)
    sin_z = math.sin(rotz_rad)
    Rz = np.array([
        [cos_z, -sin_z, 0.0],
        [sin_z, cos_z, 0.0],
        [0.0, 0.0, 1.0]
    ])
    
    cos_tt = math.cos(twotheta_rad)
    sin_tt = math.sin(twotheta_rad)
    R_twotheta = np.array([
        [cos_tt, 0.0, sin_tt],
        [0.0, 1.0, 0.0],
        [-sin_tt, 0.0, cos_tt]
    ])
    
    # Combined rotation matrix
    R_combined = R_twotheta @ Rz @ Ry @ Rx
    
    # Apply rotation to pix0
    pix0_rotated = R_combined @ pix0_unrotated
    
    # Also calculate rotated basis vectors
    fdet_rotated = R_combined @ fdet_init
    sdet_rotated = R_combined @ sdet_init  
    odet_rotated = R_combined @ odet_init
    
    return {
        'pix0_vector': pix0_rotated,
        'fdet_vec': fdet_rotated,
        'sdet_vec': sdet_rotated,
        'odet_vec': odet_rotated,
        'components': {
            'fdet_component': fdet_component,
            'sdet_component': sdet_component,
            'odet_component': odet_component,
            'pix0_unrotated': pix0_unrotated
        },
        'beam_params': {
            'Fclose': Fclose,
            'Sclose': Sclose,
            'distance_m': distance_m
        }
    }


def pytorch_calculation():
    """Get PyTorch Detector class results."""
    config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=20.0,
        detector_pivot=DetectorPivot.SAMPLE,
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        fpixels=1024,
        spixels=1024,
    )
    
    detector = Detector(config)
    
    return {
        'pix0_vector': detector.pix0_vector.numpy(),
        'fdet_vec': detector.fdet_vec.numpy(),
        'sdet_vec': detector.sdet_vec.numpy(),
        'odet_vec': detector.odet_vec.numpy()
    }


def analyze_c_beam_calculation(c_data):
    """Analyze how C calculates the beam center terms."""
    print(f"\nC BEAM CENTER ANALYSIS:")
    print(f"{'='*60}")
    
    # From C trace
    print(f"C beam center (from trace):")
    print(f"  X (Fbeam): {c_data.get('beam_center_x_m', 'N/A')} m")
    print(f"  Y (Sbeam): {c_data.get('beam_center_y_m', 'N/A')} m")
    print(f"  Pixel size: {c_data.get('pixel_size_mm', 'N/A')} mm")
    
    if 'Fbeam_m' in c_data:
        print(f"  Fbeam_m: {c_data['Fbeam_m']} m")
        print(f"  Sbeam_m: {c_data['Sbeam_m']} m")
        print(f"  Distance: {c_data['distance_m']} m")
    
    # Expected calculation
    expected_x = (51.2 + 0.5) * 0.1 / 1000.0  # (beam_center + 0.5) * pixel_size / 1000
    expected_y = (51.2 + 0.5) * 0.1 / 1000.0
    
    print(f"\nExpected calculation:")
    print(f"  (51.2 + 0.5) * 0.1 / 1000 = {expected_x} m")
    print(f"  (51.2 + 0.5) * 0.1 / 1000 = {expected_y} m")
    
    # Check if C uses different convention
    if 'beam_center_x_m' in c_data:
        x_diff = c_data['beam_center_x_m'] - expected_x
        y_diff = c_data['beam_center_y_m'] - expected_y
        
        print(f"\nDifference from expected:")
        print(f"  X difference: {x_diff:.2e} m")
        print(f"  Y difference: {y_diff:.2e} m")
        
        if abs(x_diff) > 1e-8 or abs(y_diff) > 1e-8:
            print(f"  ⚠️  C uses different beam center calculation!")
        else:
            print(f"  ✅ C beam center matches expected calculation")


def analyze_c_pix0_components(c_data):
    """Analyze how C builds pix0 from components."""
    print(f"\nC PIX0 COMPONENT ANALYSIS:")
    print(f"{'='*60}")
    
    if all(k in c_data for k in ['term_fast', 'term_slow', 'term_beam', 'pix0_vector']):
        print(f"C pix0 components:")
        print(f"  term_fast: {c_data['term_fast']}")
        print(f"  term_slow: {c_data['term_slow']}")
        print(f"  term_beam: {c_data['term_beam']}")
        
        # Calculate sum
        c_sum = c_data['term_fast'] + c_data['term_slow'] + c_data['term_beam']
        print(f"  Sum: {c_sum}")
        print(f"  Final pix0: {c_data['pix0_vector']}")
        
        # Check if sum matches final
        diff = c_data['pix0_vector'] - c_sum
        max_diff = np.max(np.abs(diff))
        
        print(f"  Difference (final - sum): {diff}")
        print(f"  Max difference: {max_diff:.2e}")
        
        if max_diff < 1e-12:
            print(f"  ✅ C pix0 is sum of components")
        else:
            print(f"  ⚠️  C pix0 differs from sum of components")
    else:
        print(f"  ❌ Missing C component data")


def main():
    """Main analysis function."""
    print("Comprehensive pix0_vector Discrepancy Analysis")
    print("=" * 80)
    
    # Parse C trace data
    print("Loading C trace data...")
    c_data = parse_c_trace()
    
    if c_data is None:
        print("❌ Failed to load C trace data")
        return
    
    print(f"✅ Loaded C trace with {len(c_data)} parameters")
    
    # Calculate manual reference
    print("\nCalculating manual reference...")
    manual_data = manual_calculation()
    
    # Get PyTorch results
    print("Getting PyTorch results...")
    pytorch_data = pytorch_calculation()
    
    # Known values
    expected_c_pix0 = np.array([0.09523, 0.05882, -0.05170])  # From problem statement
    actual_c_pix0 = c_data.get('pix0_vector', np.array([0, 0, 0]))
    
    # Display all results
    print(f"\n{'='*80}")
    print("PIX0_VECTOR COMPARISON")
    print(f"{'='*80}")
    
    print(f"Expected C (problem):  [{expected_c_pix0[0]:10.6f}, {expected_c_pix0[1]:10.6f}, {expected_c_pix0[2]:10.6f}]")
    print(f"Actual C (trace):      [{actual_c_pix0[0]:10.6f}, {actual_c_pix0[1]:10.6f}, {actual_c_pix0[2]:10.6f}]")
    print(f"Manual calculation:    [{manual_data['pix0_vector'][0]:10.6f}, {manual_data['pix0_vector'][1]:10.6f}, {manual_data['pix0_vector'][2]:10.6f}]")
    print(f"PyTorch Detector:      [{pytorch_data['pix0_vector'][0]:10.6f}, {pytorch_data['pix0_vector'][1]:10.6f}, {pytorch_data['pix0_vector'][2]:10.6f}]")
    
    # Calculate differences
    print(f"\nDIFFERENCE ANALYSIS:")
    print(f"{'-'*60}")
    
    # Expected vs Actual C
    expected_actual_diff = actual_c_pix0 - expected_c_pix0
    expected_actual_max = np.max(np.abs(expected_actual_diff))
    print(f"Actual C - Expected C: [{expected_actual_diff[0]:10.6f}, {expected_actual_diff[1]:10.6f}, {expected_actual_diff[2]:10.6f}] (max: {expected_actual_max:.4f})")
    
    # Manual vs Actual C
    manual_c_diff = manual_data['pix0_vector'] - actual_c_pix0
    manual_c_max = np.max(np.abs(manual_c_diff))
    print(f"Manual - Actual C:     [{manual_c_diff[0]:10.6f}, {manual_c_diff[1]:10.6f}, {manual_c_diff[2]:10.6f}] (max: {manual_c_max:.4f})")
    
    # PyTorch vs Actual C
    pytorch_c_diff = pytorch_data['pix0_vector'] - actual_c_pix0
    pytorch_c_max = np.max(np.abs(pytorch_c_diff))
    print(f"PyTorch - Actual C:    [{pytorch_c_diff[0]:10.6f}, {pytorch_c_diff[1]:10.6f}, {pytorch_c_diff[2]:10.6f}] (max: {pytorch_c_max:.4f})")
    
    # Manual vs PyTorch
    manual_pytorch_diff = manual_data['pix0_vector'] - pytorch_data['pix0_vector']
    manual_pytorch_max = np.max(np.abs(manual_pytorch_diff))
    print(f"Manual - PyTorch:      [{manual_pytorch_diff[0]:10.6f}, {manual_pytorch_diff[1]:10.6f}, {manual_pytorch_diff[2]:10.6f}] (max: {manual_pytorch_max:.4f})")
    
    # Analysis
    print(f"\nKEY FINDINGS:")
    print(f"{'-'*60}")
    
    tolerance = 1e-3
    
    if expected_actual_max > tolerance:
        print(f"🔍 ISSUE 1: Expected C values from problem statement don't match actual C implementation (diff: {expected_actual_max:.4f})")
    
    if manual_c_max > tolerance:
        print(f"🔍 ISSUE 2: Manual calculation differs from actual C implementation (diff: {manual_c_max:.4f})")
    
    if pytorch_c_max > tolerance:
        print(f"🔍 ISSUE 3: PyTorch implementation differs from actual C implementation (diff: {pytorch_c_max:.4f})")
    
    if manual_pytorch_max > tolerance:
        print(f"🔍 ISSUE 4: Manual and PyTorch calculations differ from each other (diff: {manual_pytorch_max:.4f})")
    
    # Detailed C analysis
    analyze_c_beam_calculation(c_data)
    analyze_c_pix0_components(c_data)
    
    # Final basis vector comparison
    print(f"\nBASIS VECTOR COMPARISON:")
    print(f"{'='*60}")
    
    if 'fdet_final' in c_data:
        print(f"C fdet:      [{c_data['fdet_final'][0]:10.6f}, {c_data['fdet_final'][1]:10.6f}, {c_data['fdet_final'][2]:10.6f}]")
        print(f"Manual fdet: [{manual_data['fdet_vec'][0]:10.6f}, {manual_data['fdet_vec'][1]:10.6f}, {manual_data['fdet_vec'][2]:10.6f}]")
        print(f"PyTorch fdet:[{pytorch_data['fdet_vec'][0]:10.6f}, {pytorch_data['fdet_vec'][1]:10.6f}, {pytorch_data['fdet_vec'][2]:10.6f}]")
        
        fdet_manual_c_diff = manual_data['fdet_vec'] - c_data['fdet_final']
        fdet_pytorch_c_diff = pytorch_data['fdet_vec'] - c_data['fdet_final']
        
        print(f"Manual-C diff: [{fdet_manual_c_diff[0]:10.6f}, {fdet_manual_c_diff[1]:10.6f}, {fdet_manual_c_diff[2]:10.6f}] (max: {np.max(np.abs(fdet_manual_c_diff)):.4f})")
        print(f"PyTorch-C diff:[{fdet_pytorch_c_diff[0]:10.6f}, {fdet_pytorch_c_diff[1]:10.6f}, {fdet_pytorch_c_diff[2]:10.6f}] (max: {np.max(np.abs(fdet_pytorch_c_diff)):.4f})")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    if expected_actual_max > tolerance:
        print(f"❌ The expected C values in the problem statement appear to be incorrect.")
        print(f"   Actual C pix0: {actual_c_pix0}")
        print(f"   Expected C pix0: {expected_c_pix0}")
    
    if manual_c_max < tolerance:
        print(f"✅ Manual calculation matches C implementation (within {tolerance})")
    else:
        print(f"❌ Manual calculation differs from C implementation")
        print(f"   This suggests different mathematical formulations")
    
    if pytorch_c_max < tolerance:
        print(f"✅ PyTorch implementation matches C implementation (within {tolerance})")
        print(f"   The correlation issue must be elsewhere")
    else:
        print(f"❌ PyTorch implementation differs from C implementation")
        print(f"   This explains the correlation issue")
    
    # Provide specific recommendations
    print(f"\n🎯 NEXT STEPS:")
    
    if pytorch_c_max > tolerance:
        print(f"   1. Fix PyTorch Detector class to match C implementation")
        print(f"   2. Focus on rotation matrix order or pivot mode logic")
        
        if manual_c_max < tolerance:
            print(f"   3. Use manual calculation as reference for PyTorch fix")
        
    if manual_c_max > tolerance:
        print(f"   1. Investigate C-specific conventions (beam center, rotation order)")
        print(f"   2. Check if C uses different coordinate system or pivot logic")
    
    print(f"   • Update problem statement with correct C values: {actual_c_pix0}")


if __name__ == "__main__":
    main()