#!/usr/bin/env python3
"""
Compare C and Python trace outputs to identify first divergence point.

This script parses both C (c_trace.log) and Python (py_trace.log) traces,
compares corresponding values with tight tolerance (1e-12), and reports
the first location where they differ.

Usage:
    python compare_c_python_traces.py [--tolerance 1e-12] [--verbose]
"""

import re
import sys
import argparse
from typing import Dict, List, Tuple, Any
from pathlib import Path


def parse_trace_line(line: str) -> Tuple[str, Any]:
    """
    Parse a trace line into variable name and value(s).
    
    Expected formats:
    - TRACE_C:variable=value
    - TRACE_C:variable=value1 value2 value3  (for vectors)
    - TRACE_C:variable=[m11 m12 m13; m21 m22 m23; m31 m32 m33]  (for matrices)
    """
    line = line.strip()
    
    # Remove prefix
    if line.startswith("TRACE_C:"):
        line = line[8:]
    elif line.startswith("TRACE_PY:"):
        line = line[8:]
    else:
        return None, None
    
    # Split on first equals sign
    if "=" not in line:
        return None, None
    
    var_name, value_str = line.split("=", 1)
    var_name = var_name.strip()
    value_str = value_str.strip()
    
    # Handle different value formats
    if value_str.startswith("[") and value_str.endswith("]"):
        # Matrix format: [v1 v2 v3; v4 v5 v6; v7 v8 v9]
        matrix_str = value_str[1:-1]  # Remove brackets
        rows = matrix_str.split(";")
        matrix_values = []
        for row in rows:
            row_values = [float(x.strip()) for x in row.split() if x.strip()]
            matrix_values.extend(row_values)
        return var_name, matrix_values
    elif " " in value_str:
        # Vector format: v1 v2 v3
        try:
            values = [float(x) for x in value_str.split()]
            return var_name, values
        except ValueError:
            # String value with spaces
            return var_name, value_str
    else:
        # Scalar value
        try:
            return var_name, float(value_str)
        except ValueError:
            # String value
            return var_name, value_str


def parse_trace_file(filename: str) -> Dict[str, List[Any]]:
    """
    Parse a trace file and return a dictionary of variable names to lists of values.
    Multiple occurrences of the same variable are stored as a list.
    """
    traces = {}
    
    try:
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                var_name, value = parse_trace_line(line)
                if var_name is not None:
                    if var_name not in traces:
                        traces[var_name] = []
                    traces[var_name].append((line_num, value))
    except FileNotFoundError:
        print(f"Error: File {filename} not found!")
        return {}
    
    return traces


def values_equal(val1: Any, val2: Any, tolerance: float) -> bool:
    """Compare two values with given tolerance."""
    if type(val1) != type(val2):
        return False
    
    if isinstance(val1, str):
        return val1 == val2
    elif isinstance(val1, (int, float)):
        return abs(val1 - val2) < tolerance
    elif isinstance(val1, list):
        if len(val1) != len(val2):
            return False
        return all(abs(a - b) < tolerance for a, b in zip(val1, val2))
    else:
        return val1 == val2


def format_value(value: Any) -> str:
    """Format a value for display."""
    if isinstance(value, str):
        return value
    elif isinstance(value, (int, float)):
        return f"{value:.15g}"
    elif isinstance(value, list):
        if len(value) <= 3:
            return " ".join(f"{v:.15g}" for v in value)
        else:
            # Matrix format
            return f"[{' '.join(f'{v:.6g}' for v in value)}]"
    else:
        return str(value)


def compare_traces(c_traces: Dict[str, List], py_traces: Dict[str, List], 
                  tolerance: float, verbose: bool = False) -> None:
    """Compare C and Python traces and report differences."""
    
    all_vars = set(c_traces.keys()) | set(py_traces.keys())
    
    # Track matching and differing variables
    matching_vars = []
    differing_vars = []
    c_only_vars = []
    py_only_vars = []
    
    print("=" * 80)
    print("TRACE COMPARISON RESULTS")
    print("=" * 80)
    print(f"Tolerance: {tolerance}")
    print(f"C variables: {len(c_traces)}")
    print(f"Python variables: {len(py_traces)}")
    print(f"Total unique variables: {len(all_vars)}")
    print()
    
    for var_name in sorted(all_vars):
        c_values = c_traces.get(var_name, [])
        py_values = py_traces.get(var_name, [])
        
        if not c_values:
            py_only_vars.append(var_name)
            if verbose:
                print(f"PYTHON_ONLY: {var_name} = {format_value(py_values[0][1]) if py_values else 'N/A'}")
            continue
        
        if not py_values:
            c_only_vars.append(var_name)
            if verbose:
                print(f"C_ONLY: {var_name} = {format_value(c_values[0][1]) if c_values else 'N/A'}")
            continue
        
        # Compare the first occurrence of each variable
        c_val = c_values[0][1]
        py_val = py_values[0][1]
        c_line = c_values[0][0]
        py_line = py_values[0][0]
        
        if values_equal(c_val, py_val, tolerance):
            matching_vars.append(var_name)
            if verbose:
                print(f"MATCH: {var_name} = {format_value(c_val)}")
        else:
            differing_vars.append(var_name)
            print(f"DIFFER: {var_name}")
            print(f"  C  (line {c_line}): {format_value(c_val)}")
            print(f"  PY (line {py_line}): {format_value(py_val)}")
            
            # Calculate difference for numerical values
            if isinstance(c_val, (int, float)) and isinstance(py_val, (int, float)):
                diff = abs(c_val - py_val)
                rel_diff = diff / max(abs(c_val), abs(py_val), 1e-15) * 100
                print(f"  Difference: {diff:.2e} (relative: {rel_diff:.2e}%)")
            elif isinstance(c_val, list) and isinstance(py_val, list) and len(c_val) == len(py_val):
                diffs = [abs(a - b) for a, b in zip(c_val, py_val)]
                max_diff = max(diffs)
                max_rel_diff = max(d / max(abs(a), abs(b), 1e-15) for d, a, b in zip(diffs, c_val, py_val)) * 100
                print(f"  Max difference: {max_diff:.2e} (relative: {max_rel_diff:.2e}%)")
            print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Variables matching:     {len(matching_vars)}")
    print(f"Variables differing:    {len(differing_vars)}")
    print(f"C-only variables:       {len(c_only_vars)}")
    print(f"Python-only variables:  {len(py_only_vars)}")
    
    if differing_vars:
        print("\nFIRST DIVERGENCE POINT:")
        print(f"Variable: {differing_vars[0]}")
        print("This is likely where the implementations start to differ.")
        
        print("\nAll differing variables:")
        for var in differing_vars[:10]:  # Show first 10
            print(f"  - {var}")
        if len(differing_vars) > 10:
            print(f"  ... and {len(differing_vars) - 10} more")
    else:
        print("\n✅ All variables match within tolerance!")
    
    if c_only_vars:
        print(f"\nC-only variables ({len(c_only_vars)}):")
        for var in c_only_vars[:5]:
            print(f"  - {var}")
        if len(c_only_vars) > 5:
            print(f"  ... and {len(c_only_vars) - 5} more")
    
    if py_only_vars:
        print(f"\nPython-only variables ({len(py_only_vars)}):")
        for var in py_only_vars[:5]:
            print(f"  - {var}")
        if len(py_only_vars) > 5:
            print(f"  ... and {len(py_only_vars) - 5} more")


def main():
    parser = argparse.ArgumentParser(description="Compare C and Python trace outputs")
    parser.add_argument("--tolerance", type=float, default=1e-12,
                       help="Numerical comparison tolerance (default: 1e-12)")
    parser.add_argument("--verbose", action="store_true",
                       help="Show matching variables in addition to differences")
    parser.add_argument("--c-trace", default="c_trace.log",
                       help="C trace file (default: c_trace.log)")
    parser.add_argument("--py-trace", default="py_trace.log",
                       help="Python trace file (default: py_trace.log)")
    
    args = parser.parse_args()
    
    print("Loading trace files...")
    c_traces = parse_trace_file(args.c_trace)
    py_traces = parse_trace_file(args.py_trace)
    
    if not c_traces and not py_traces:
        print("Error: No trace data found in either file!")
        sys.exit(1)
    
    if not c_traces:
        print(f"Warning: No C trace data found in {args.c_trace}")
    
    if not py_traces:
        print(f"Warning: No Python trace data found in {args.py_trace}")
    
    compare_traces(c_traces, py_traces, args.tolerance, args.verbose)


if __name__ == "__main__":
    main()