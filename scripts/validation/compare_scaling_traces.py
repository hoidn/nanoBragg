#!/usr/bin/env python
"""
Phase L3e: Compare C and PyTorch scaling traces with sub-micro tolerance enforcement.

This script aligns TRACE_C and TRACE_PY outputs from the scaling audit and
reports percentage deltas for each scaling factor to identify the first divergence.

Outputs:
    - Markdown summary (--out argument)
    - metrics.json (structured per-factor deltas)
    - run_metadata.json (environment snapshot + command parameters)

Usage:
    python scripts/validation/compare_scaling_traces.py \\
        --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log \\
        --py reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log \\
        --out reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md

Plan Reference: plans/active/cli-noise-pix0/plan.md Phase L3e

IMPORTANT - Option 1 Spec-Mode Behavior:
    When comparing spec-compliant PyTorch traces to legacy C traces, expect I_before_scaling
    discrepancies due to C-PARITY-001 (φ=0 carryover bug, documented in
    docs/bugs/verified_c_bugs.md:166). This is an intentional divergence per Phase M5d decision.
    PyTorch correctly recalculates rotation matrices per φ step (specs/spec-a-core.md:204);
    C code incorrectly caches φ=0 lattice factors.

    For Option 1 validation bundles, adjust threshold expectations:
    - I_before_scaling: expect ~14.6% delta (C legacy behavior)
    - Downstream factors (r_e², fluence, steps, polar, omega): expect ≤1e-6

    Reference: reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
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
                        # CLI-FLAGS-003 Phase M1: Map pre-polar to standard I_before_scaling for C comparison
                        elif var_name == "I_before_scaling_pre_polar":
                            # Use pre-polar value as the canonical I_before_scaling (matches C-code)
                            var_value = float(parts[2])
                            values["I_before_scaling"] = var_value
                            values[var_name] = var_value  # Keep original too
                        elif var_name == "I_before_scaling_post_polar":
                            # Store post-polar separately (for reference only)
                            var_value = float(parts[2])
                            values[var_name] = var_value
                        else:
                            var_value = float(parts[2])
                            values[var_name] = var_value
                    except ValueError:
                        # Skip non-numeric values
                        pass

    return values


def compute_delta(c_val: float, py_val: float, tolerance_rel: float = 1e-6) -> Tuple[float, float, str]:
    """
    Compute absolute delta, relative delta, and assessment.

    Args:
        c_val: C reference value
        py_val: PyTorch value
        tolerance_rel: Relative tolerance threshold (default 1e-6 per Phase L3e)

    Returns:
        (absolute_delta, relative_delta_fraction, assessment_string)
        Note: relative_delta_fraction is the fractional value (not percent)
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

    rel_delta = abs_delta / c_val  # Fractional delta

    # Assessment thresholds (Phase L3e: enforce ≤1e-6 tolerance)
    if abs(rel_delta) <= tolerance_rel:
        status = "PASS"
    elif abs(rel_delta) < 1e-4:
        status = "MINOR"
    elif abs(rel_delta) < 1e-2:
        status = "DIVERGENT"
    else:
        status = "CRITICAL"

    return (abs_delta, rel_delta, status)


def format_value(val: float) -> str:
    """Format a value for display."""
    if val is None:
        return "NOT_EXTRACTED"
    if abs(val) < 1e-6 or abs(val) > 1e6:
        return f"{val:.6e}"
    else:
        return f"{val:.9g}"


def get_git_sha() -> str:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def get_torch_version() -> str:
    """Get PyTorch version if available."""
    try:
        import torch
        return torch.__version__
    except ImportError:
        return "not_installed"


def main():
    parser = argparse.ArgumentParser(description="Compare C and PyTorch scaling traces with ≤1e-6 tolerance")
    parser.add_argument('--c', dest='c_trace', required=True,
                        help='Path to C trace log (e.g., c_trace_scaling.log)')
    parser.add_argument('--py', dest='py_trace', required=True,
                        help='Path to PyTorch trace log (e.g., trace_py_scaling.log)')
    parser.add_argument('--out', dest='output', required=True,
                        help='Output summary file (e.g., scaling_validation_summary.md)')
    parser.add_argument('--tolerance', type=float, default=1e-6,
                        help='Relative tolerance threshold (default: 1e-6)')

    args = parser.parse_args()

    # Capture run metadata
    run_metadata = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "git_sha": get_git_sha(),
        "torch_version": get_torch_version(),
        "command": " ".join(sys.argv),
        "c_trace": str(Path(args.c_trace).absolute()),
        "py_trace": str(Path(args.py_trace).absolute()),
        "tolerance_rel": args.tolerance,
    }

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

    # Build comparison table and structured metrics
    output_lines = []
    output_lines.append("# Scaling Chain Comparison: C vs PyTorch")
    output_lines.append("")
    output_lines.append("**Phase L3e Validation** (CLI-FLAGS-003)")
    output_lines.append("")
    output_lines.append(f"**Tolerance:** ≤{args.tolerance:.2e} relative")
    output_lines.append("")
    output_lines.append("## Summary")
    output_lines.append("")
    output_lines.append("Comparing scaling factors for supervisor command pixel (685, 1039).")
    output_lines.append("")
    output_lines.append("## Detailed Comparison")
    output_lines.append("")
    output_lines.append("| Factor | C Value | PyTorch Value | Δ (abs) | Δ (rel) | Status |")
    output_lines.append("|--------|---------|---------------|---------|---------|--------|")

    first_divergent = None
    divergent_factors = []
    metrics_data = {}

    for var_name, description in scaling_factors:
        c_val = c_values.get(var_name)
        py_val = py_values.get(var_name)

        abs_delta, rel_delta, status = compute_delta(c_val, py_val, args.tolerance)

        # Store structured metrics
        metrics_data[var_name] = {
            "description": description,
            "c_value": c_val,
            "py_value": py_val,
            "abs_delta": abs_delta,
            "rel_delta": rel_delta,
            "status": status
        }

        # Track divergences
        if status in ["DIVERGENT", "CRITICAL", "MISSING", "MINOR"]:
            divergent_factors.append((var_name, description, c_val, py_val, status))
            if first_divergent is None:
                first_divergent = (var_name, description)

        # Format row
        c_str = format_value(c_val)
        py_str = format_value(py_val)

        if abs_delta is None:
            delta_abs_str = "N/A"
            delta_rel_str = "N/A"
        else:
            delta_abs_str = format_value(abs_delta)
            if rel_delta is not None:
                delta_rel_str = f"{rel_delta:+.6e}"
            else:
                delta_rel_str = "N/A"

        output_lines.append(f"| {var_name} | {c_str} | {py_str} | {delta_abs_str} | {delta_rel_str} | {status} |")

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
            output_lines.append(f"- Relative delta: `{rel_delta:+.6e}`")
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
                if rel_delta is not None:
                    output_lines.append(f"- Δ: `{format_value(abs_delta)}` (rel: {rel_delta:+.6e})")
                else:
                    output_lines.append(f"- Δ: `{format_value(abs_delta)}` (rel: N/A)")
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

    # Write outputs
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write markdown summary
    with open(output_path, 'w') as f:
        f.write('\n'.join(output_lines))

    # Write metrics.json
    metrics_path = output_path.parent / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump({
            "tolerance_rel": args.tolerance,
            "first_divergence": first_divergent[0] if first_divergent else None,
            "num_divergent": len(divergent_factors),
            "factors": metrics_data
        }, f, indent=2)

    # Write run_metadata.json
    metadata_path = output_path.parent / "run_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(run_metadata, f, indent=2)

    print(f"Comparison written to {output_path}")
    print(f"Metrics written to {metrics_path}")
    print(f"Metadata written to {metadata_path}")
    print(f"First divergence: {first_divergent[0] if first_divergent else 'None'}")
    print(f"Divergent factors: {len(divergent_factors)}")


if __name__ == '__main__':
    main()
