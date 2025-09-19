#!/usr/bin/env python3
"""
Phase 5 Rotation Matrix Comparison Test Script

Extracts and compares rotation matrices element-by-element between C and Python
to identify differences in matrix construction, multiplication order, or values.

This script:
1. Generates detailed traces of rotation matrix construction
2. Compares individual matrix elements
3. Tests different rotation orders and combinations
4. Analyzes matrix multiplication sequences
"""

import os
import sys
import subprocess
import numpy as np
import re
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Set environment variable to prevent MKL conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from nanobrag_torch.models.detector import Detector


def extract_matrix_from_c_trace(trace_file, matrix_name):
    """Extract a 3x3 matrix from C trace file."""
    if not trace_file.exists():
        return None
    
    matrix = np.zeros((3, 3))
    matrix_found = False
    
    with open(trace_file, 'r') as f:
        for line in f:
            if f'TRACE_C:{matrix_name}=' in line:
                # C format: matrix=[row0; row1; row2] with space-separated values
                match = re.search(rf'{matrix_name}=\[(.*?)\]', line)
                if match:
                    matrix_str = match.group(1)
                    # Split by semicolon to get rows
                    rows = matrix_str.split(';')
                    if len(rows) == 3:
                        for i, row_str in enumerate(rows):
                            values = [float(x) for x in row_str.strip().split()]
                            if len(values) == 3:
                                matrix[i] = values
                                matrix_found = True
    
    return matrix if matrix_found else None


def extract_vector_from_c_trace(trace_file, vector_name):
    """Extract a vector from C trace file."""
    if not trace_file.exists():
        return None
    
    with open(trace_file, 'r') as f:
        for line in f:
            if f'TRACE_C:{vector_name}=' in line:
                # Extract vector values (space-separated)
                match = re.search(rf'{vector_name}=([0-9.-]+)\s+([0-9.-]+)\s+([0-9.-]+)', line)
                if match:
                    return np.array([float(match.group(1)), float(match.group(2)), float(match.group(3))])
    return None


def run_c_matrix_trace(rotx=5, roty=3, rotz=2, twotheta=20, output_file="c_matrix_trace.log"):
    """Run C implementation and extract matrix trace."""
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
        "-detector_rotx", str(rotx),
        "-detector_roty", str(roty),
        "-detector_rotz", str(rotz),
        "-twotheta", str(twotheta),
        "-floatfile", "matrix_test.bin"
    ]
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=golden_dir,
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            f.write(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"C code error: {e}")
        return False


def build_python_rotation_matrices(rotx=5, roty=3, rotz=2, twotheta=20):
    """Build rotation matrices using Python implementation."""
    # Convert to radians
    rotx_rad = np.radians(rotx)
    roty_rad = np.radians(roty)
    rotz_rad = np.radians(rotz)
    twotheta_rad = np.radians(twotheta)
    
    # Build individual rotation matrices
    # X-axis rotation
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(rotx_rad), -np.sin(rotx_rad)],
        [0, np.sin(rotx_rad), np.cos(rotx_rad)]
    ])
    
    # Y-axis rotation
    Ry = np.array([
        [np.cos(roty_rad), 0, np.sin(roty_rad)],
        [0, 1, 0],
        [-np.sin(roty_rad), 0, np.cos(roty_rad)]
    ])
    
    # Z-axis rotation
    Rz = np.array([
        [np.cos(rotz_rad), -np.sin(rotz_rad), 0],
        [np.sin(rotz_rad), np.cos(rotz_rad), 0],
        [0, 0, 1]
    ])
    
    # Two-theta rotation (around Y-axis)
    Rtheta = np.array([
        [np.cos(twotheta_rad), 0, np.sin(twotheta_rad)],
        [0, 1, 0],
        [-np.sin(twotheta_rad), 0, np.cos(twotheta_rad)]
    ])
    
    # Combined rotation: Rtheta * Rz * Ry * Rx (C order)
    R_combined = Rtheta @ Rz @ Ry @ Rx
    
    return {
        'Rx': Rx,
        'Ry': Ry,
        'Rz': Rz,
        'Rtheta': Rtheta,
        'R_combined': R_combined,
        'rotx_rad': rotx_rad,
        'roty_rad': roty_rad,
        'rotz_rad': rotz_rad,
        'twotheta_rad': twotheta_rad
    }


def get_detector_matrices(rotx=5, roty=3, rotz=2, twotheta=20):
    """Get rotation matrices from Detector class."""
    try:
        from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot

        config = DetectorConfig(
            distance_mm=100.0,
            beam_center_s=51.2,
            beam_center_f=51.2,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            detector_rotx_deg=rotx,
            detector_roty_deg=roty,
            detector_rotz_deg=rotz,
            detector_twotheta_deg=twotheta,
            detector_pivot=DetectorPivot.BEAM,
            detector_convention=DetectorConvention.MOSFLM
        )

        detector = Detector(config)
        
        # Extract internal matrices (need to access detector's internal structure)
        # For now, just get the final vectors
        return {
            'fdet_vec': detector.fdet_vec.detach().numpy(),
            'sdet_vec': detector.sdet_vec.detach().numpy(),
            'odet_vec': detector.odet_vec.detach().numpy(),
            'pix0_vector': detector.pix0_vector.detach().numpy()
        }
        
    except Exception as e:
        print(f"Detector error: {e}")
        return None


def compare_matrices(c_matrix, py_matrix, name):
    """Compare two matrices element by element."""
    if c_matrix is None or py_matrix is None:
        print(f"❌ {name}: Missing matrix data")
        return False
    
    print(f"\n{'='*60}")
    print(f"MATRIX COMPARISON: {name}")
    print(f"{'='*60}")
    
    print("C Matrix:")
    for i in range(3):
        print(f"  [{c_matrix[i,0]:12.8f}, {c_matrix[i,1]:12.8f}, {c_matrix[i,2]:12.8f}]")
    
    print("\nPython Matrix:")
    for i in range(3):
        print(f"  [{py_matrix[i,0]:12.8f}, {py_matrix[i,1]:12.8f}, {py_matrix[i,2]:12.8f}]")
    
    diff_matrix = py_matrix - c_matrix
    max_diff = np.max(np.abs(diff_matrix))
    rms_diff = np.sqrt(np.mean(diff_matrix**2))
    
    print("\nDifference (Python - C):")
    for i in range(3):
        print(f"  [{diff_matrix[i,0]:12.2e}, {diff_matrix[i,1]:12.2e}, {diff_matrix[i,2]:12.2e}]")
    
    print(f"\nMax abs difference: {max_diff:.2e}")
    print(f"RMS difference: {rms_diff:.2e}")
    
    tolerance = 1e-12
    is_equal = max_diff < tolerance
    
    if is_equal:
        print(f"✅ Matrices match (within {tolerance})")
    else:
        print(f"❌ Matrices differ (max diff {max_diff:.2e})")
        
        # Check for common issues
        if np.allclose(c_matrix.T, py_matrix, atol=1e-10):
            print("⚠️  Python matrix appears to be transpose of C matrix")
        
        # Check determinants
        c_det = np.linalg.det(c_matrix)
        py_det = np.linalg.det(py_matrix)
        print(f"C determinant: {c_det:.8f}")
        print(f"Python determinant: {py_det:.8f}")
        
        if abs(c_det - py_det) > 1e-8:
            print("⚠️  Determinants differ significantly")
    
    return is_equal


def compare_vectors(c_vec, py_vec, name):
    """Compare two vectors element by element."""
    if c_vec is None or py_vec is None:
        print(f"❌ {name}: Missing vector data")
        return False
    
    print(f"\n{'-'*40}")
    print(f"VECTOR COMPARISON: {name}")
    print(f"{'-'*40}")
    
    print(f"C Vector:      [{c_vec[0]:12.8f}, {c_vec[1]:12.8f}, {c_vec[2]:12.8f}]")
    print(f"Python Vector: [{py_vec[0]:12.8f}, {py_vec[1]:12.8f}, {py_vec[2]:12.8f}]")
    
    diff = py_vec - c_vec
    max_diff = np.max(np.abs(diff))
    
    print(f"Difference:    [{diff[0]:12.2e}, {diff[1]:12.2e}, {diff[2]:12.2e}]")
    print(f"Max abs diff:  {max_diff:.2e}")
    
    tolerance = 1e-12
    is_equal = max_diff < tolerance
    
    if is_equal:
        print(f"✅ Vectors match (within {tolerance})")
    else:
        print(f"❌ Vectors differ (max diff {max_diff:.2e})")
    
    return is_equal


def test_rotation_order_variations():
    """Test different rotation orders to see if that's the issue."""
    print("\n" + "="*80)
    print("ROTATION ORDER VARIATION TEST")
    print("="*80)
    
    angles = [5, 3, 2, 20]  # rotx, roty, rotz, twotheta in degrees
    rotx_rad, roty_rad, rotz_rad, twotheta_rad = np.radians(angles)
    
    # Build individual matrices
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(rotx_rad), -np.sin(rotx_rad)],
        [0, np.sin(rotx_rad), np.cos(rotx_rad)]
    ])
    
    Ry = np.array([
        [np.cos(roty_rad), 0, np.sin(roty_rad)],
        [0, 1, 0],
        [-np.sin(roty_rad), 0, np.cos(roty_rad)]
    ])
    
    Rz = np.array([
        [np.cos(rotz_rad), -np.sin(rotz_rad), 0],
        [np.sin(rotz_rad), np.cos(rotz_rad), 0],
        [0, 0, 1]
    ])
    
    Rtheta = np.array([
        [np.cos(twotheta_rad), 0, np.sin(twotheta_rad)],
        [0, 1, 0],
        [-np.sin(twotheta_rad), 0, np.cos(twotheta_rad)]
    ])
    
    # Test different multiplication orders
    orders = [
        ("Rtheta @ Rz @ Ry @ Rx (C order)", Rtheta @ Rz @ Ry @ Rx),
        ("Rx @ Ry @ Rz @ Rtheta (reverse)", Rx @ Ry @ Rz @ Rtheta),
        ("Rz @ Ry @ Rx @ Rtheta (no initial Rtheta)", Rz @ Ry @ Rx @ Rtheta),
        ("Rtheta @ Rx @ Ry @ Rz (XYZ order)", Rtheta @ Rx @ Ry @ Rz),
    ]
    
    print(f"Testing {len(orders)} different rotation orders:")
    print()
    
    # Get C reference matrix
    c_trace_file = "c_matrix_order_test.log"
    run_c_matrix_trace(5, 3, 2, 20, c_trace_file)
    c_combined = extract_matrix_from_c_trace(Path(c_trace_file), "R_total")
    
    if c_combined is None:
        print("❌ Could not extract C combined matrix")
        return
    
    print("C Reference Combined Matrix:")
    for i in range(3):
        print(f"  [{c_combined[i,0]:12.8f}, {c_combined[i,1]:12.8f}, {c_combined[i,2]:12.8f}]")
    print()
    
    best_match = None
    best_diff = float('inf')
    
    for order_name, py_matrix in orders:
        diff = py_matrix - c_combined
        max_diff = np.max(np.abs(diff))
        
        print(f"{order_name}:")
        print(f"  Max diff: {max_diff:.2e}")
        
        if max_diff < best_diff:
            best_diff = max_diff
            best_match = order_name
        
        if max_diff < 1e-12:
            print(f"  ✅ EXACT MATCH!")
        elif max_diff < 1e-8:
            print(f"  ✅ Very close")
        else:
            print(f"  ❌ Significant difference")
        print()
    
    print(f"Best match: {best_match} (max diff: {best_diff:.2e})")


def run_matrix_test():
    """Run complete rotation matrix comparison test."""
    print("=" * 80)
    print("PHASE 5 ROTATION MATRIX COMPARISON TEST")
    print("=" * 80)
    print()
    print("Testing rotation matrix construction and multiplication order")
    print("Configuration: rotx=5°, roty=3°, rotz=2°, twotheta=20°")
    print()
    
    # Test parameters (tilted detector case)
    rotx, roty, rotz, twotheta = 5, 3, 2, 20
    
    # Run C implementation
    print("Running C implementation...")
    c_trace_file = "c_matrix_detailed.log"
    c_success = run_c_matrix_trace(rotx, roty, rotz, twotheta, c_trace_file)
    
    if not c_success:
        print("❌ C implementation failed")
        return
    
    # Extract C matrices
    print("Extracting C matrices...")
    c_matrices = {}
    c_matrices['Rx'] = extract_matrix_from_c_trace(Path(c_trace_file), "Rx")
    c_matrices['Ry'] = extract_matrix_from_c_trace(Path(c_trace_file), "Ry")
    c_matrices['Rz'] = extract_matrix_from_c_trace(Path(c_trace_file), "Rz")
    c_matrices['R_total'] = extract_matrix_from_c_trace(Path(c_trace_file), "R_total")
    
    # Extract C vectors
    c_vectors = {}
    c_vectors['fdet'] = extract_vector_from_c_trace(Path(c_trace_file), "fdet_after_twotheta")
    c_vectors['sdet'] = extract_vector_from_c_trace(Path(c_trace_file), "sdet_after_twotheta")
    c_vectors['odet'] = extract_vector_from_c_trace(Path(c_trace_file), "odet_after_twotheta")
    c_vectors['pix0'] = extract_vector_from_c_trace(Path(c_trace_file), "pix0_vector")
    
    # Build Python matrices
    print("Building Python matrices...")
    py_data = build_python_rotation_matrices(rotx, roty, rotz, twotheta)
    
    # Get detector vectors
    print("Getting detector vectors...")
    detector_data = get_detector_matrices(rotx, roty, rotz, twotheta)
    
    # Compare individual matrices
    print("\n" + "="*80)
    print("INDIVIDUAL MATRIX COMPARISONS")
    print("="*80)
    
    matrix_matches = []
    for matrix_name in ['Rx', 'Ry', 'Rz']:
        if matrix_name in c_matrices and matrix_name in py_data:
            match = compare_matrices(c_matrices[matrix_name], py_data[matrix_name], matrix_name)
            matrix_matches.append(match)
    
    # Compare combined matrix
    if 'R_total' in c_matrices and 'R_combined' in py_data:
        combined_match = compare_matrices(c_matrices['R_total'], py_data['R_combined'], "Combined Matrix")
        matrix_matches.append(combined_match)
    
    # Compare final vectors
    print("\n" + "="*80)
    print("FINAL VECTOR COMPARISONS")
    print("="*80)
    
    vector_matches = []
    if detector_data:
        for vec_name in ['fdet', 'sdet', 'odet']:
            if vec_name in c_vectors and f'{vec_name}_vec' in detector_data:
                match = compare_vectors(c_vectors[vec_name], detector_data[f'{vec_name}_vec'], f"{vec_name}_vec")
                vector_matches.append(match)
        
        if 'pix0' in c_vectors and 'pix0_vector' in detector_data:
            pix0_match = compare_vectors(c_vectors['pix0'], detector_data['pix0_vector'], "pix0_vector")
            vector_matches.append(pix0_match)
    
    # Test rotation order variations
    test_rotation_order_variations()
    
    # Summary
    print("\n" + "="*80)
    print("MATRIX TEST SUMMARY")
    print("="*80)
    
    all_matrices_match = all(matrix_matches) if matrix_matches else False
    all_vectors_match = all(vector_matches) if vector_matches else False
    
    print(f"Individual matrices match: {'✅ YES' if len(matrix_matches) > 0 and matrix_matches[:-1] and all(matrix_matches[:-1]) else '❌ NO'}")
    print(f"Combined matrix matches:   {'✅ YES' if len(matrix_matches) > 0 and matrix_matches[-1] else '❌ NO'}")
    print(f"Final vectors match:       {'✅ YES' if all_vectors_match else '❌ NO'}")
    
    print()
    print("CONCLUSIONS:")
    
    if all_matrices_match and all_vectors_match:
        print("✅ All matrices and vectors match perfectly")
        print("   → Rotation matrix construction is NOT the source of the 3cm offset")
        print("   → Issue likely in beam center calculation or pivot mode logic")
    elif all_matrices_match and not all_vectors_match:
        print("✅ Matrices match, but final vectors differ")
        print("   → Matrix construction is correct")
        print("   → Issue in vector application or beam center calculation")
    elif not all_matrices_match:
        print("❌ Rotation matrices differ between C and Python")
        print("   → Matrix construction or multiplication order is incorrect")
        print("   → This could be the source of the 3cm offset")
    
    print()
    print("NEXT STEPS:")
    if not all_matrices_match:
        print("1. Debug matrix construction element by element")
        print("2. Check trigonometric function precision")
        print("3. Verify matrix multiplication order")
    else:
        print("1. Focus on beam center calculation and pivot mode logic")
        print("2. Run offset analysis script (analyze_rotation_offset.py)")
        print("3. Test SAMPLE vs BEAM pivot modes")
    
    # Save results
    results_file = "rotation_matrix_test_results.txt"
    with open(results_file, 'w') as f:
        f.write("Phase 5 Rotation Matrix Test Results\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Configuration: rotx={rotx}°, roty={roty}°, rotz={rotz}°, twotheta={twotheta}°\n\n")
        
        f.write("Matrix Matches:\n")
        for i, matrix_name in enumerate(['Rx', 'Ry', 'Rz', 'Combined']):
            if i < len(matrix_matches):
                f.write(f"  {matrix_name}: {'✅ MATCH' if matrix_matches[i] else '❌ DIFFER'}\n")
        
        f.write("\nVector Matches:\n")
        for i, vec_name in enumerate(['fdet_vec', 'sdet_vec', 'odet_vec', 'pix0_vector']):
            if i < len(vector_matches):
                f.write(f"  {vec_name}: {'✅ MATCH' if vector_matches[i] else '❌ DIFFER'}\n")
        
        f.write(f"\nOverall Status: {'✅ ALL MATCH' if all_matrices_match and all_vectors_match else '❌ DIFFERENCES FOUND'}\n")
    
    print(f"Results saved to: {results_file}")
    print(f"C trace saved to: {c_trace_file}")


def test_simple_detector_creation():
    """Test to prevent pytest collection errors."""
    # This is a complex debugging script, not a unit test
    # Just test that we can create a detector with rotations
    try:
        from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot

        config = DetectorConfig(
            distance_mm=100.0,
            beam_center_s=51.2,
            beam_center_f=51.2,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            detector_rotx_deg=5.0,
            detector_roty_deg=3.0,
            detector_rotz_deg=2.0,
            detector_twotheta_deg=20.0,
            detector_pivot=DetectorPivot.BEAM,
            detector_convention=DetectorConvention.MOSFLM
        )

        detector = Detector(config)
        assert detector is not None
        print("✅ Detector with rotations created successfully")

    except Exception as e:
        print(f"❌ Error creating detector: {e}")
        assert False, f"Failed to create detector: {e}"


if __name__ == "__main__":
    run_matrix_test()