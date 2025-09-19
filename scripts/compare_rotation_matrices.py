#!/usr/bin/env python3
"""
Rotation matrix comparison tool for Phase 4.1 diagnostic deep dive.

This script extracts and compares rotation matrices from both C and Python traces
to identify differences in rotation order or values.
"""

import re
import numpy as np
from pathlib import Path


def parse_matrix_from_trace(trace_lines, matrix_name, prefix):
    """Extract a 3x3 matrix from trace lines."""
    matrix = np.zeros((3, 3))
    matrix_found = False
    
    for line in trace_lines:
        line = line.strip()
        if f"{prefix}:{matrix_name}_row" in line:
            # Extract row number and values
            match = re.search(rf"{prefix}:{matrix_name}_row(\d+)=\[(.*?)\]", line)
            if match:
                row_idx = int(match.group(1))
                values_str = match.group(2)
                values = [float(x) for x in values_str.split()]
                if len(values) == 3 and 0 <= row_idx <= 2:
                    matrix[row_idx] = values
                    matrix_found = True
    
    return matrix if matrix_found else None


def parse_vector_from_trace(trace_lines, vector_name, prefix):
    """Extract a vector from trace lines."""
    for line in trace_lines:
        line = line.strip()
        if f"{prefix}:{vector_name}=" in line:
            # Extract vector values
            match = re.search(rf"{prefix}:{vector_name}=\[(.*?)\]", line)
            if match:
                values_str = match.group(1)
                values = [float(x) for x in values_str.split()]
                if len(values) == 3:
                    return np.array(values)
    return None


def parse_scalar_from_trace(trace_lines, scalar_name, prefix):
    """Extract a scalar value from trace lines."""
    for line in trace_lines:
        line = line.strip()
        if f"{prefix}:{scalar_name}=" in line:
            # Extract scalar value
            match = re.search(rf"{prefix}:{scalar_name}=(.*?)$", line)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
    return None


def compare_matrices(c_matrix, py_matrix, name):
    """Compare two matrices and print detailed analysis."""
    if c_matrix is None and py_matrix is None:
        print(f"⚠️  {name}: Both matrices not found")
        return False
    elif c_matrix is None:
        print(f"❌ {name}: C matrix not found")
        return False
    elif py_matrix is None:
        print(f"❌ {name}: Python matrix not found")
        return False
    
    print(f"\n{'='*60}")
    print(f"MATRIX COMPARISON: {name}")
    print(f"{'='*60}")
    
    print("C Matrix:")
    for i in range(3):
        row_str = "  ".join(f"{c_matrix[i,j]:12.8f}" for j in range(3))
        print(f"  [{row_str}]")
    
    print("\nPython Matrix:")
    for i in range(3):
        row_str = "  ".join(f"{py_matrix[i,j]:12.8f}" for j in range(3))
        print(f"  [{row_str}]")
    
    # Calculate differences
    diff_matrix = py_matrix - c_matrix
    max_diff = np.max(np.abs(diff_matrix))
    rms_diff = np.sqrt(np.mean(diff_matrix**2))
    
    print("\nDifference (Python - C):")
    for i in range(3):
        row_str = "  ".join(f"{diff_matrix[i,j]:12.8e}" for j in range(3))
        print(f"  [{row_str}]")
    
    print(f"\nStatistics:")
    print(f"  Max absolute difference: {max_diff:.2e}")
    print(f"  RMS difference: {rms_diff:.2e}")
    
    # Check if matrices are effectively equal
    tolerance = 1e-12
    are_equal = max_diff < tolerance
    
    if are_equal:
        print(f"✅ Matrices are equal (within {tolerance})")
    else:
        print(f"❌ Matrices differ (max diff {max_diff:.2e} > {tolerance})")
        
        # Check for common issues
        if np.allclose(c_matrix.T, py_matrix):
            print("⚠️  Python matrix appears to be transpose of C matrix")
        
        # Check determinants
        c_det = np.linalg.det(c_matrix)
        py_det = np.linalg.det(py_matrix)
        print(f"  C determinant: {c_det:.8f}")
        print(f"  Python determinant: {py_det:.8f}")
        
        if abs(c_det - py_det) > 1e-8:
            print("⚠️  Determinants differ significantly")
    
    return are_equal


def compare_vectors(c_vec, py_vec, name):
    """Compare two vectors and print detailed analysis."""
    if c_vec is None and py_vec is None:
        print(f"⚠️  {name}: Both vectors not found")
        return False
    elif c_vec is None:
        print(f"❌ {name}: C vector not found")
        return False
    elif py_vec is None:
        print(f"❌ {name}: Python vector not found")
        return False
    
    print(f"\n{'-'*40}")
    print(f"VECTOR COMPARISON: {name}")
    print(f"{'-'*40}")
    
    print(f"C Vector:      [{c_vec[0]:12.8f}, {c_vec[1]:12.8f}, {c_vec[2]:12.8f}]")
    print(f"Python Vector: [{py_vec[0]:12.8f}, {py_vec[1]:12.8f}, {py_vec[2]:12.8f}]")
    
    diff_vec = py_vec - c_vec
    max_diff = np.max(np.abs(diff_vec))
    rms_diff = np.sqrt(np.mean(diff_vec**2))
    
    print(f"Difference:    [{diff_vec[0]:12.8e}, {diff_vec[1]:12.8e}, {diff_vec[2]:12.8e}]")
    print(f"Max abs diff: {max_diff:.2e}, RMS diff: {rms_diff:.2e}")
    
    tolerance = 1e-12
    are_equal = max_diff < tolerance
    
    if are_equal:
        print(f"✅ Vectors are equal (within {tolerance})")
    else:
        print(f"❌ Vectors differ (max diff {max_diff:.2e} > {tolerance})")
    
    return are_equal


def compare_scalars(c_val, py_val, name):
    """Compare two scalar values."""
    if c_val is None and py_val is None:
        print(f"⚠️  {name}: Both values not found")
        return False
    elif c_val is None:
        print(f"❌ {name}: C value not found")
        return False
    elif py_val is None:
        print(f"❌ {name}: Python value not found")
        return False
    
    diff = py_val - c_val
    rel_diff = abs(diff / c_val) if abs(c_val) > 1e-15 else float('inf')
    
    tolerance = 1e-12
    are_equal = abs(diff) < tolerance
    
    status = "✅" if are_equal else "❌"
    print(f"{status} {name:<25}: C={c_val:15.8e}, Py={py_val:15.8e}, diff={diff:10.2e}")
    
    return are_equal


def main():
    """Main comparison function."""
    print("Rotation Matrix Comparison Tool for Phase 4.1")
    print("=" * 60)
    
    # Read trace files
    c_trace_file = Path("c_pix0_trace_enhanced.log")
    py_trace_file = Path("py_pix0_trace_detailed.log")
    
    if not c_trace_file.exists():
        print(f"❌ C trace file not found: {c_trace_file}")
        print("   Run: ./run_enhanced_c_trace.sh")
        return
    
    if not py_trace_file.exists():
        print(f"❌ Python trace file not found: {py_trace_file}")
        print("   Run: python scripts/trace_pix0_detailed.py > py_pix0_trace_detailed.log")
        return
    
    # Read trace lines
    with open(c_trace_file, 'r') as f:
        c_lines = f.readlines()
    
    with open(py_trace_file, 'r') as f:
        py_lines = f.readlines()
    
    print(f"Loaded {len(c_lines)} C trace lines, {len(py_lines)} Python trace lines")
    
    # Compare configuration parameters
    print(f"\n{'='*60}")
    print("CONFIGURATION PARAMETER COMPARISON")
    print(f"{'='*60}")
    
    config_params = [
        "distance_mm", "beam_center_s", "beam_center_f", "pixel_size_mm",
        "detector_rotx_deg", "detector_roty_deg", "detector_rotz_deg", "detector_twotheta_deg",
        "rotx_rad", "roty_rad", "rotz_rad", "twotheta_rad"
    ]
    
    config_equal = True
    for param in config_params:
        c_val = parse_scalar_from_trace(c_lines, param, "PIX0_C")
        py_val = parse_scalar_from_trace(py_lines, param, "PIX0_PY")
        param_equal = compare_scalars(c_val, py_val, param)
        config_equal = config_equal and param_equal
    
    # Compare initial basis vectors
    print(f"\n{'='*60}")
    print("INITIAL BASIS VECTOR COMPARISON")
    print(f"{'='*60}")
    
    basis_equal = True
    for vec_name in ["fdet_initial", "sdet_initial", "odet_initial"]:
        c_vec = parse_vector_from_trace(c_lines, vec_name, "PIX0_C")
        py_vec = parse_vector_from_trace(py_lines, vec_name, "PIX0_PY")
        vec_equal = compare_vectors(c_vec, py_vec, vec_name)
        basis_equal = basis_equal and vec_equal
    
    # Compare rotation matrices
    print(f"\n{'='*60}")
    print("ROTATION MATRIX COMPARISON")
    print(f"{'='*60}")
    
    matrices_equal = True
    matrix_names = ["rot_x_matrix", "rot_y_matrix", "rot_z_matrix"]
    
    for matrix_name in matrix_names:
        c_matrix = parse_matrix_from_trace(c_lines, matrix_name, "PIX0_C")
        py_matrix = parse_matrix_from_trace(py_lines, matrix_name, "PIX0_PY")
        matrix_equal = compare_matrices(c_matrix, py_matrix, matrix_name)
        matrices_equal = matrices_equal and matrix_equal
    
    # Compare rotation trigonometric values
    print(f"\n{'='*60}")
    print("TRIGONOMETRIC VALUE COMPARISON")
    print(f"{'='*60}")
    
    trig_equal = True
    trig_params = [
        "rot_x_cos", "rot_x_sin", "rot_y_cos", "rot_y_sin", 
        "rot_z_cos", "rot_z_sin", "twotheta_cos", "twotheta_sin"
    ]
    
    for param in trig_params:
        c_val = parse_scalar_from_trace(c_lines, param, "PIX0_C")
        py_val = parse_scalar_from_trace(py_lines, param, "PIX0_PY")
        param_equal = compare_scalars(c_val, py_val, param)
        trig_equal = trig_equal and param_equal
    
    # Compare pix0 calculation components
    print(f"\n{'='*60}")
    print("PIX0 CALCULATION COMPONENT COMPARISON")
    print(f"{'='*60}")
    
    pix0_equal = True
    
    # Beam center calculations
    beam_params = ["beam_center_f_plus_half", "beam_center_s_plus_half", "Fclose_m", "Sclose_m", "distance_m"]
    for param in beam_params:
        c_val = parse_scalar_from_trace(c_lines, param, "PIX0_C")
        py_val = parse_scalar_from_trace(py_lines, param, "PIX0_PY")
        param_equal = compare_scalars(c_val, py_val, param)
        pix0_equal = pix0_equal and param_equal
    
    # Vector components
    component_vecs = ["fdet_component", "sdet_component", "odet_component", "pix0_unrotated"]
    for vec_name in component_vecs:
        c_vec = parse_vector_from_trace(c_lines, vec_name, "PIX0_C")
        py_vec = parse_vector_from_trace(py_lines, vec_name, "PIX0_PY")
        vec_equal = compare_vectors(c_vec, py_vec, vec_name)
        pix0_equal = pix0_equal and vec_equal
    
    # Compare final results
    print(f"\n{'='*60}")
    print("FINAL RESULT COMPARISON")
    print(f"{'='*60}")
    
    final_equal = True
    final_vecs = ["pix0_rotated_final", "fdet_rotated", "sdet_rotated", "odet_rotated"]
    
    for vec_name in final_vecs:
        c_vec = parse_vector_from_trace(c_lines, vec_name, "PIX0_C")
        py_vec = parse_vector_from_trace(py_lines, vec_name, "PIX0_PY")
        vec_equal = compare_vectors(c_vec, py_vec, vec_name)
        final_equal = final_equal and vec_equal
    
    # Overall summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    overall_equal = config_equal and basis_equal and matrices_equal and trig_equal and pix0_equal and final_equal
    
    print(f"Configuration parameters: {'✅ MATCH' if config_equal else '❌ DIFFER'}")
    print(f"Initial basis vectors:    {'✅ MATCH' if basis_equal else '❌ DIFFER'}")
    print(f"Rotation matrices:        {'✅ MATCH' if matrices_equal else '❌ DIFFER'}")
    print(f"Trigonometric values:     {'✅ MATCH' if trig_equal else '❌ DIFFER'}")
    print(f"Pix0 calculation:         {'✅ MATCH' if pix0_equal else '❌ DIFFER'}")
    print(f"Final results:            {'✅ MATCH' if final_equal else '❌ DIFFER'}")
    
    print(f"\nOVERALL: {'✅ C AND PYTHON IMPLEMENTATIONS MATCH' if overall_equal else '❌ IMPLEMENTATIONS DIFFER'}")
    
    if not overall_equal:
        print("\n🔍 NEXT STEPS:")
        if not config_equal:
            print("   • Check parameter parsing and unit conversions")
        if not matrices_equal:
            print("   • Check rotation matrix construction and order")
        if not pix0_equal:
            print("   • Check pix0 calculation formula and pivot mode logic")
        if not final_equal:
            print("   • Check matrix multiplication and vector rotation")


if __name__ == "__main__":
    main()