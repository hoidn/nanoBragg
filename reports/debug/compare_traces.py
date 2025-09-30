#!/usr/bin/env python3
"""
Compare C and PyTorch traces to identify first divergence point.
"""

import re
import sys

def parse_trace_file(filename):
    """Parse trace file and extract key variables."""
    data = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('==='):
                continue

            # Parse various formats
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().replace('TRACE_C:', '').replace('TRACE_C', '').strip()
                    value = parts[1].strip()

                    # Try to parse as number or vector
                    try:
                        # Check if it's a vector
                        if '[' in value or 'tensor' in value:
                            # Extract numbers from tensor or vector format
                            numbers = re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?', value)
                            if numbers:
                                data[key] = [float(n) for n in numbers]
                        else:
                            # Single number
                            data[key] = float(value)
                    except ValueError:
                        data[key] = value

    return data

def compare_values(c_val, py_val, rtol=1e-6):
    """Compare two values with relative tolerance."""
    if isinstance(c_val, list) and isinstance(py_val, list):
        if len(c_val) != len(py_val):
            return False, f"Different lengths: {len(c_val)} vs {len(py_val)}"

        max_rel_diff = 0.0
        for i, (c, p) in enumerate(zip(c_val, py_val)):
            if abs(p) > 1e-15:
                rel_diff = abs(c - p) / abs(p)
                max_rel_diff = max(max_rel_diff, rel_diff)

        if max_rel_diff > rtol:
            return False, f"Max relative difference: {max_rel_diff:.6e}"
        return True, "OK"

    elif isinstance(c_val, (int, float)) and isinstance(py_val, (int, float)):
        if abs(py_val) > 1e-15:
            rel_diff = abs(c_val - py_val) / abs(py_val)
            if rel_diff > rtol:
                return False, f"Relative difference: {rel_diff:.6e}"
        elif abs(c_val - py_val) > 1e-15:
            return False, f"Absolute difference: {abs(c_val - py_val):.6e}"
        return True, "OK"

    else:
        return str(c_val) == str(py_val), "Type mismatch" if str(c_val) != str(py_val) else "OK"

def main():
    c_file = '/home/ollie/Documents/nanoBragg/reports/debug/c_trace_at_parallel_002_0.4mm_pixel120x120.log'
    py_file = '/home/ollie/Documents/nanoBragg/reports/debug/py_trace_at_parallel_002_0.4mm.log'

    print("=" * 80)
    print("C vs PyTorch Trace Comparison")
    print("=" * 80)
    print()

    # Parse both files
    c_data = parse_trace_file(c_file)
    py_data = parse_trace_file(py_file)

    # Key mappings between C and PyTorch variable names
    mappings = {
        'pixel_pos_meters': 'Pixel coordinate (m)',
        'R_distance_meters': 'Distance to pixel (R)',
        'omega_pixel_sr': 'Omega (point-pixel, pixel_size^2/R^2)',
        'close_distance_meters': 'Close distance',
        'obliquity_factor': 'Obliquity factor (close_distance/R)',
        'lambda_meters': 'Wavelength (m)',
        'hkl_frac': 'Miller indices (fractional)',
        'hkl_rounded': 'Miller indices (rounded)',
        'F_latt_a': 'F_latt_a = sincg(π*',
        'F_latt_b': 'F_latt_b = sincg(π*',
        'F_latt_c': 'F_latt_c = sincg(π*',
        'F_latt': 'F_latt (product)',
        'F_cell': 'Structure factor F',
        'I_pixel_final': 'I_final (with fluence)',
    }

    first_divergence = None
    all_comparisons = []

    # Compare all mapped variables
    for c_key, py_desc in mappings.items():
        if c_key in c_data:
            # Find corresponding PyTorch value
            py_val = None
            for py_key, py_value in py_data.items():
                if py_desc in py_key:
                    py_val = py_value
                    break

            if py_val is not None:
                c_val = c_data[c_key]
                match, msg = compare_values(c_val, py_val, rtol=1e-6)

                result = {
                    'key': c_key,
                    'c_val': c_val,
                    'py_val': py_val,
                    'match': match,
                    'msg': msg
                }
                all_comparisons.append(result)

                if not match and first_divergence is None:
                    first_divergence = result

    # Print comparison results
    print("Variable Comparison:")
    print("-" * 80)
    for comp in all_comparisons:
        status = "✓ MATCH" if comp['match'] else "✗ DIVERGE"
        print(f"{status:10} | {comp['key']:30} | {comp['msg']}")
        if not comp['match']:
            print(f"           | C value:  {comp['c_val']}")
            print(f"           | Py value: {comp['py_val']}")
            print()

    print()
    print("=" * 80)
    if first_divergence:
        print("FIRST DIVERGENCE FOUND:")
        print("=" * 80)
        print(f"Variable: {first_divergence['key']}")
        print(f"C value:  {first_divergence['c_val']}")
        print(f"Py value: {first_divergence['py_val']}")
        print(f"Status:   {first_divergence['msg']}")
    else:
        print("All variables match within tolerance!")
    print("=" * 80)

if __name__ == '__main__':
    main()