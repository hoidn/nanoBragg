#!/usr/bin/env python
"""
Phase L2c: Compare C and PyTorch scaling traces.

This script aligns TRACE_C and TRACE_PY outputs from the scaling audit and
reports percentage deltas for each scaling factor to identify the first divergence.

Usage:
    python scripts/validation/compare_scaling_traces.py \\
        --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log \\
        --py reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log \\
        --out reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md

Plan Reference: plans/active/cli-noise-pix0/plan.md Phase L2c
"""

import argparse
import re
from pathlib import Path
from typing import Dict, Tuple


def parse_trace_file(filepath: Path, prefix: str) -> Dict[str, float]:
    """
    Parse a trace file and extract scaling factors.

    Args:
        filepath: Path to trace log file
        prefix: Either "TRACE_C:" or "TRACE_PY:"

    Returns:
        Dictionary mapping variable names to values
    """
    values = {}

    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith(prefix):
                # Format: "TRACE_C: variable_name value"
                parts = line.strip().split()
                if len(parts) >= 3:
                    var_name = parts[1]
                    try:
                        # Handle special cases
                        if var_name == "I_before_scaling" and parts[2] == "NOT_EXTRACTED":
                            values[var_name] = None
                        else:
                            var_value = float(parts[2])
                            values[var_name] = var_value
                    except ValueError:
                        # Skip non-numeric values
                        pass

    return values


def compute_delta(c_val: float, py_val: float) -> Tuple[float, float, str]:
    """
    Compute absolute delta, relative delta, and assessment.

    Returns:
        (absolute_delta, relative_delta_percent, assessment_string)
    """
    if c_val is None or py_val is None:
        return (None, None, "MISSING")

    abs_delta = py_val - c_val

    if abs(c_val) < 1e-30:
        # Avoid division by zero for very small values
        if abs(py_val) < 1e-30:
            return (abs_delta, 0.0, "MATCH (both ~0)")
        else:
            return (abs_delta, None, "DIVERGENT (C≈0, Py≠0)")

    rel_delta_pct = (abs_delta / c_val) * 100.0

    # Assessment thresholds
    if abs(rel_delta_pct) < 0.001:
        status = "MATCH"
    elif abs(rel_delta_pct) < 1.0:
        status = "MINOR"
    elif abs(rel_delta_pct) < 10.0:
        status = "DIVERGENT"
    else:
        status = "CRITICAL"

    return (abs_delta, rel_delta_pct, status)


def format_value(val: float) -> str:
    """Format a value for display."""
    if val is None:
        return "NOT_EXTRACTED"
    if abs(val) < 1e-6 or abs(val) > 1e6:
        return f"{val:.6e}"
    else:
        return f"{val:.9g}"


def main():
    parser = argparse.ArgumentParser(description="Compare C and PyTorch scaling traces")
    parser.add_argument('--c', dest='c_trace', required=True,
                        help='Path to C trace log (e.g., c_trace_scaling.log)')
    parser.add_argument('--py', dest='py_trace', required=True,
                        help='Path to PyTorch trace log (e.g., trace_py_scaling.log)')
    parser.add_argument('--out', dest='output', required=True,
                        help='Output summary file (e.g., scaling_audit_summary.md)')

    args = parser.parse_args()

    # Parse both traces
    c_values = parse_trace_file(Path(args.c_trace), "TRACE_C:")
    py_values = parse_trace_file(Path(args.py_trace), "TRACE_PY:")

    # Define scaling factors to compare (in order of the scaling chain)
    scaling_factors = [
        ('I_before_scaling', 'Raw accumulated intensity before normalization'),
        ('r_e_sqr', 'Thomson scattering cross section (r_e²)'),
        ('fluence_photons_per_m2', 'Incident photon fluence'),
        ('steps', 'Normalization divisor (sources×mosaic×φ×oversample²)'),
        ('capture_fraction', 'Detector absorption capture fraction'),
        ('polar', 'Kahn polarization factor'),
        ('omega_pixel', 'Solid angle (steradians)'),
        ('cos_2theta', 'Cosine of scattering angle 2θ'),
        ('I_pixel_final', 'Final normalized pixel intensity'),
    ]

    # Build comparison table
    output_lines = []
    output_lines.append("# Scaling Chain Comparison: C vs PyTorch")
    output_lines.append("")
    output_lines.append("**Phase L2c Analysis** (CLI-FLAGS-003)")
    output_lines.append("")
    output_lines.append("## Summary")
    output_lines.append("")
    output_lines.append("Comparing scaling factors for supervisor command pixel (685, 1039).")
    output_lines.append("")
    output_lines.append("## Detailed Comparison")
    output_lines.append("")
    output_lines.append("| Factor | C Value | PyTorch Value | Δ (abs) | Δ (%) | Status |")
    output_lines.append("|--------|---------|---------------|---------|-------|--------|")

    first_divergent = None
    divergent_factors = []

    for var_name, description in scaling_factors:
        c_val = c_values.get(var_name)
        py_val = py_values.get(var_name)

        abs_delta, rel_delta, status = compute_delta(c_val, py_val)

        # Track divergences
        if status in ["DIVERGENT", "CRITICAL", "MISSING"]:
            divergent_factors.append((var_name, description, c_val, py_val, status))
            if first_divergent is None:
                first_divergent = (var_name, description)

        # Format row
        c_str = format_value(c_val)
        py_str = format_value(py_val)

        if abs_delta is None:
            delta_abs_str = "N/A"
            delta_pct_str = "N/A"
        else:
            delta_abs_str = format_value(abs_delta)
            if rel_delta is not None:
                delta_pct_str = f"{rel_delta:+.3f}"
            else:
                delta_pct_str = "N/A"

        output_lines.append(f"| {var_name} | {c_str} | {py_str} | {delta_abs_str} | {delta_pct_str} | {status} |")

    output_lines.append("")
    output_lines.append("## First Divergence")
    output_lines.append("")

    if first_divergent:
        var_name, description = first_divergent
        output_lines.append(f"**{var_name}** ({description})")
        output_lines.append("")
        c_val = c_values.get(var_name)
        py_val = py_values.get(var_name)
        abs_delta, rel_delta, status = compute_delta(c_val, py_val)

        output_lines.append(f"- C value: `{format_value(c_val)}`")
        output_lines.append(f"- PyTorch value: `{format_value(py_val)}`")
        if abs_delta is not None:
            output_lines.append(f"- Absolute delta: `{format_value(abs_delta)}`")
        if rel_delta is not None:
            output_lines.append(f"- Relative delta: `{rel_delta:+.3f}%`")
        output_lines.append(f"- Status: **{status}**")
    else:
        output_lines.append("**No divergence detected!** All scaling factors match within tolerances.")

    output_lines.append("")
    output_lines.append("## All Divergent Factors")
    output_lines.append("")

    if divergent_factors:
        for var_name, description, c_val, py_val, status in divergent_factors:
            abs_delta, rel_delta, _ = compute_delta(c_val, py_val)
            output_lines.append(f"### {var_name}")
            output_lines.append(f"- Description: {description}")
            output_lines.append(f"- C: `{format_value(c_val)}`")
            output_lines.append(f"- PyTorch: `{format_value(py_val)}`")
            if abs_delta is not None:
                output_lines.append(f"- Δ: `{format_value(abs_delta)}` ({rel_delta:+.3f}% if available)")
            output_lines.append(f"- Status: **{status}**")
            output_lines.append("")
    else:
        output_lines.append("None - all factors match!")

    output_lines.append("## Next Actions")
    output_lines.append("")
    if first_divergent:
        output_lines.append(f"1. Investigate root cause of {first_divergent[0]} mismatch")
        output_lines.append("2. Implement fix in Phase L3")
        output_lines.append("3. Regenerate PyTorch trace after fix")
        output_lines.append("4. Rerun this comparison to verify")
    else:
        output_lines.append("1. Proceed to Phase L4 (supervisor command parity rerun)")

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write('\n'.join(output_lines))

    print(f"Comparison written to {output_path}")
    print(f"First divergence: {first_divergent[0] if first_divergent else 'None'}")
    print(f"Divergent factors: {len(divergent_factors)}")


if __name__ == '__main__':
    main()
