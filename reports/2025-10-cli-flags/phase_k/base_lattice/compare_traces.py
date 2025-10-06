#!/usr/bin/env python3
"""
Phase K3f3: Compare C and PyTorch base lattice traces
Identifies first divergence in reciprocal/real vectors and scattering components.
"""

import re
import sys
from pathlib import Path

def parse_vector(line):
    """Extract 3D vector from trace line like 'a_star = [x, y, z]'."""
    match = re.search(r'\[([-\d.e+]+),\s*([-\d.e+]+),\s*([-\d.e+]+)\]', line)
    if match:
        return [float(match.group(i)) for i in [1, 2, 3]]
    return None

def parse_scalar(line):
    """Extract scalar from trace line."""
    match = re.search(r'=\s*([-\d.e+]+)', line)
    if match:
        return float(match.group(1))
    return None

def compare_vectors(c_vec, py_vec, name, tolerance=5e-4):
    """Compare two 3D vectors and report differences."""
    if c_vec is None or py_vec is None:
        return f"  {name}: MISSING DATA"

    delta = [abs(c - p) for c, p in zip(c_vec, py_vec)]
    max_delta = max(delta)
    ratio = [p/c if c != 0 else float('inf') for c, p in zip(c_vec, py_vec)]

    status = "MATCH" if max_delta < tolerance else "DIVERGE"
    result = f"  {name}: {status}\n"
    result += f"    C:      [{c_vec[0]:.10g}, {c_vec[1]:.10g}, {c_vec[2]:.10g}]\n"
    result += f"    Py:     [{py_vec[0]:.10g}, {py_vec[1]:.10g}, {py_vec[2]:.10g}]\n"
    result += f"    Delta:  [{delta[0]:.10g}, {delta[1]:.10g}, {delta[2]:.10g}] (max={max_delta:.10g})\n"
    result += f"    Ratio:  [{ratio[0]:.10g}, {ratio[1]:.10g}, {ratio[2]:.10g}]\n"

    return result, status != "MATCH"

def main():
    c_trace_path = Path(__file__).parent / "c_stdout.txt"
    py_trace_path = Path(__file__).parent / "trace_py.log"

    print("=" * 70)
    print("Phase K3f3: Base Lattice Trace Comparison")
    print("=" * 70)
    print(f"C trace:  {c_trace_path}")
    print(f"Py trace: {py_trace_path}")
    print()

    # Parse C trace
    c_data = {}
    with open(c_trace_path) as f:
        for line in f:
            if 'TRACE:   a_star = ' in line:
                c_data['a_star'] = parse_vector(line)
            elif 'TRACE:   b_star = ' in line:
                c_data['b_star'] = parse_vector(line)
            elif 'TRACE:   c_star = ' in line:
                c_data['c_star'] = parse_vector(line)
            elif 'TRACE:   a0 = ' in line:
                c_data['a0'] = parse_vector(line)
            elif 'TRACE:   b0 = ' in line:
                c_data['b0'] = parse_vector(line)
            elif 'TRACE:   c0 = ' in line:
                c_data['c0'] = parse_vector(line)
            elif 'V_cell =' in line and 'V_star' in line:
                match = re.search(r'V_cell = ([-\d.e+]+)', line)
                if match:
                    c_data['V_cell_m3'] = float(match.group(1))

    # Parse PyTorch trace
    py_data = {}
    with open(py_trace_path) as f:
        for line in f:
            if 'TRACE_PY_BASE:   a_star = ' in line:
                py_data['a_star'] = parse_vector(line)
            elif 'TRACE_PY_BASE:   b_star = ' in line:
                py_data['b_star'] = parse_vector(line)
            elif 'TRACE_PY_BASE:   c_star = ' in line:
                py_data['c_star'] = parse_vector(line)
            elif 'TRACE_PY_BASE:   a = ' in line:
                py_data['a'] = parse_vector(line)
            elif 'TRACE_PY_BASE:   b = ' in line:
                py_data['b'] = parse_vector(line)
            elif 'TRACE_PY_BASE:   c = ' in line:
                py_data['c'] = parse_vector(line)
            elif 'V_cell = ' in line and 'm³' in line:
                py_data['V_cell_m3'] = parse_scalar(line)

    # Comparisons
    print("=" * 70)
    print("RECIPROCAL VECTORS (Å⁻¹, λ-scaled)")
    print("=" * 70)

    first_divergence = None

    msg, diverged = compare_vectors(c_data.get('a_star'), py_data.get('a_star'), "a_star")
    print(msg)
    if diverged and first_divergence is None:
        first_divergence = "a_star"

    msg, diverged = compare_vectors(c_data.get('b_star'), py_data.get('b_star'), "b_star")
    print(msg)
    if diverged and first_divergence is None:
        first_divergence = "b_star"

    msg, diverged = compare_vectors(c_data.get('c_star'), py_data.get('c_star'), "c_star")
    print(msg)
    if diverged and first_divergence is None:
        first_divergence = "c_star"

    print("\n" + "=" * 70)
    print("REAL-SPACE VECTORS (meters)")
    print("=" * 70)

    msg, diverged = compare_vectors(c_data.get('a0'), py_data.get('a'), "a (real)")
    print(msg)
    if diverged and first_divergence is None:
        first_divergence = "a (real)"

    msg, diverged = compare_vectors(c_data.get('b0'), py_data.get('b'), "b (real)")
    print(msg)
    if diverged and first_divergence is None:
        first_divergence = "b (real)"

    msg, diverged = compare_vectors(c_data.get('c0'), py_data.get('c'), "c (real)")
    print(msg)
    if diverged and first_divergence is None:
        first_divergence = "c (real)"

    print("\n" + "=" * 70)
    print("CELL VOLUMES")
    print("=" * 70)

    if 'V_cell_m3' in c_data and 'V_cell_m3' in py_data:
        c_vol = c_data['V_cell_m3']
        py_vol = py_data['V_cell_m3']
        delta_vol = abs(c_vol - py_vol)
        ratio_vol = py_vol / c_vol if c_vol != 0 else float('inf')

        print(f"  V_cell:")
        print(f"    C:      {c_vol:.10g} m³")
        print(f"    Py:     {py_vol:.10g} m³")
        print(f"    Delta:  {delta_vol:.10g}")
        print(f"    Ratio:  {ratio_vol:.10g}")

    print("\n" + "=" * 70)
    print("FIRST DIVERGENCE")
    print("=" * 70)
    print(f"First component exceeding 5e-4 tolerance: {first_divergence or 'NONE - ALL MATCH'}")

    print("\n" + "=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)

    if first_divergence:
        print(f"The first divergence is in {first_divergence}.")
        print("\nKey observations:")

        # Check for λ-scaling issue
        if c_data.get('a_star') and py_data.get('a_star'):
            c_mag = sum(x**2 for x in c_data['a_star'])**0.5
            py_mag = sum(x**2 for x in py_data['a_star'])**0.5
            ratio = py_mag / c_mag
            print(f"  - a_star magnitude ratio (Py/C): {ratio:.6f}")
            if ratio > 10:
                print("  - PyTorch reciprocal vectors are much larger than C (~40×)")
                print("  - This suggests λ-scaling is being applied incorrectly or twice")
                print("  - Check MOSFLM matrix reader and Crystal.compute_cell_tensors()")

        # Check real vector scaling
        if c_data.get('a0') and py_data.get('a'):
            c_real_mag = sum(x**2 for x in c_data['a0'])**0.5
            py_real_mag = sum(x**2 for x in py_data['a'])**0.5
            ratio_real = py_real_mag / c_real_mag
            print(f"  - a (real) magnitude ratio (Py/C): {ratio_real:.6f}")
            if ratio_real > 1000:
                print(f"  - PyTorch real vectors are ~{ratio_real:.0f}× larger than C")
                print("  - This cascades from the reciprocal vector error")
    else:
        print("All base lattice vectors match within tolerance.")

    print("=" * 70)

if __name__ == '__main__':
    main()
