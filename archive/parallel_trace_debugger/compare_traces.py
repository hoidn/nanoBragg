#!/usr/bin/env python3
"""
Compare Traces Tool

Parses C and Python trace logs and reports the first numerical discrepancy
that exceeds a tolerance of 1e-12.
"""
import sys
import math
import re

TOL = 1e-12


def parse_line(line):
    """Parse a trace line into key and value."""
    try:
        _, rest = line.strip().split(":", 1)
        key, val = rest.split("=", 1)
        return key, val.strip()
    except ValueError:
        return None, None


def parse_vals(s):
    """Parse values which can be scalars, vectors, matrices, or key:value pairs."""
    # Matrix format: [a b c; d e f; g h i]
    if s.startswith("[") and s.endswith("]"):
        rows = [r.strip() for r in s[1:-1].split(";")]
        return [list(map(float, r.split())) for r in rows]
    
    # Key:value pairs (like angles_rad)
    if ":" in s and " " in s and re.search(r":[-+0-9.]", s):
        out = {}
        for tok in s.split():
            if ":" in tok:
                k, v = tok.split(":", 1)
                try:
                    out[k] = float(v)
                except ValueError:
                    out[k] = v
        return out
    
    # Space-separated values (vectors) or single value
    parts = s.split()
    if len(parts) == 1:
        try:
            return float(parts[0])
        except ValueError:
            return s  # Return as string if not a number
    
    # Try to parse as floats
    try:
        return list(map(float, parts))
    except ValueError:
        return s  # Return original string if parsing fails


def close(a, b, tol=TOL):
    """Check if two values are close within tolerance."""
    if type(a) != type(b):
        return False
    
    if isinstance(a, float):
        return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol
    
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        # Check if it's a matrix (list of lists)
        if a and isinstance(a[0], list):
            return all(close(r1, r2, tol) for r1, r2 in zip(a, b))
        # It's a vector
        return all(abs(x - y) <= tol for x, y in zip(a, b))
    
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(close(a[k], b[k], tol) for k in a.keys())
    
    # For strings or other types
    return a == b


def format_value(v):
    """Format a value for display."""
    if isinstance(v, float):
        return f"{v:.15g}"
    elif isinstance(v, list):
        if v and isinstance(v[0], list):
            # Matrix
            return "[" + "; ".join(" ".join(f"{x:.15g}" for x in row) for row in v) + "]"
        else:
            # Vector
            return " ".join(f"{x:.15g}" for x in v)
    elif isinstance(v, dict):
        return " ".join(f"{k}:{v[k]:.15g}" if isinstance(v[k], float) else f"{k}:{v[k]}" for k in sorted(v.keys()))
    else:
        return str(v)


def compute_difference(a, b):
    """Compute the difference between two values."""
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b)
    elif isinstance(a, list) and isinstance(b, list):
        if a and isinstance(a[0], list):
            # Matrix - return max difference
            diffs = []
            for r1, r2 in zip(a, b):
                for x1, x2 in zip(r1, r2):
                    diffs.append(abs(x1 - x2))
            return max(diffs) if diffs else 0.0
        else:
            # Vector - return max difference
            return max(abs(x - y) for x, y in zip(a, b)) if a else 0.0
    elif isinstance(a, dict) and isinstance(b, dict):
        diffs = []
        for k in a.keys():
            if k in b and isinstance(a[k], float) and isinstance(b[k], float):
                diffs.append(abs(a[k] - b[k]))
        return max(diffs) if diffs else 0.0
    return None


def main(c_log, p_log):
    """Compare C and Python trace logs."""
    print(f"Comparing traces with tolerance {TOL}")
    print(f"C log: {c_log}")
    print(f"Python log: {p_log}")
    print("=" * 60)
    
    # Read trace lines
    with open(c_log) as f:
        c_lines = [l for l in f if l.startswith("TRACE_C:")]
    
    with open(p_log) as f:
        p_lines = [l for l in f if l.startswith("TRACE_PY:")]
    
    print(f"Found {len(c_lines)} C trace lines")
    print(f"Found {len(p_lines)} Python trace lines")
    
    if len(c_lines) != len(p_lines):
        print(f"\n❌ Line count differs: C={len(c_lines)} PY={len(p_lines)}")
        sys.exit(1)
    
    # Compare line by line
    for i, (lc, lp) in enumerate(zip(c_lines, p_lines), 1):
        kc, vc = parse_line(lc)
        kp, vp = parse_line(lp)
        
        if kc != kp:
            print(f"\n❌ Key mismatch at line {i}: C:{kc} vs PY:{kp}")
            sys.exit(1)
        
        pc = parse_vals(vc)
        pp = parse_vals(vp)
        
        if not close(pc, pp):
            print(f"\n❌ Value mismatch at key '{kc}' (line {i}):")
            print(f"  C : {vc}")
            print(f"  PY: {vp}")
            
            # Show parsed values
            print(f"\n  Parsed C : {format_value(pc)}")
            print(f"  Parsed PY: {format_value(pp)}")
            
            # Compute difference if possible
            diff = compute_difference(pc, pp)
            if diff is not None:
                print(f"  Max difference: {diff:.15g}")
            
            sys.exit(1)
    
    print("\n✅ OK: traces match within tolerance.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: compare_traces.py <c_trace.log> <py_trace.log>")
        sys.exit(1)
    
    sys.exit(main(sys.argv[1], sys.argv[2]))