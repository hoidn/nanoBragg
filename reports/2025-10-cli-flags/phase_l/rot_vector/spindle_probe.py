#!/usr/bin/env python3
"""
Spindle-Axis & Volume Probe for CLI-FLAGS-003 Phase L3g

Extracts and compares spindle-axis vectors and volume metrics between
C and PyTorch traces to diagnose φ=0 rotation drift.

Usage:
    python spindle_probe.py \\
        --trace reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log \\
        --ctrace reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log \\
        --out reports/2025-10-cli-flags/phase_l/rot_vector/spindle_audit.log
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import math


def parse_vector(line: str, prefix: str) -> Optional[Tuple[float, float, float]]:
    """Extract 3D vector from trace line."""
    pattern = rf"{re.escape(prefix)}\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)"
    match = re.search(pattern, line)
    if match:
        return (float(match.group(1)), float(match.group(2)), float(match.group(3)))
    return None


def compute_norm(vec: Tuple[float, float, float]) -> float:
    """Compute L2 norm of 3D vector."""
    return math.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)


def compute_volume_formula(a: float, b: float, c: float,
                           alpha_deg: float, beta_deg: float, gamma_deg: float) -> float:
    """Compute unit cell volume using crystallographic formula."""
    alpha_rad = math.radians(alpha_deg)
    beta_rad = math.radians(beta_deg)
    gamma_rad = math.radians(gamma_deg)

    cos_alpha = math.cos(alpha_rad)
    cos_beta = math.cos(beta_rad)
    cos_gamma = math.cos(gamma_rad)

    return a * b * c * math.sqrt(1.0
                                 - cos_alpha**2
                                 - cos_beta**2
                                 - cos_gamma**2
                                 + 2.0 * cos_alpha * cos_beta * cos_gamma)


def compute_volume_actual(a_vec: Tuple[float, float, float],
                          b_vec: Tuple[float, float, float],
                          c_vec: Tuple[float, float, float]) -> float:
    """Compute actual volume from real-space vectors: V = a · (b × c)."""
    # b × c
    cross_x = b_vec[1] * c_vec[2] - b_vec[2] * c_vec[1]
    cross_y = b_vec[2] * c_vec[0] - b_vec[0] * c_vec[2]
    cross_z = b_vec[0] * c_vec[1] - b_vec[1] * c_vec[0]

    # a · (b × c)
    return a_vec[0] * cross_x + a_vec[1] * cross_y + a_vec[2] * cross_z


def parse_trace(trace_path: Path) -> Dict:
    """Extract spindle axis, cell params, and rotation vectors from trace."""
    data = {
        'spindle_axis': None,
        'cell_params': {},
        'rot_a': None,
        'rot_b': None,
        'rot_c': None,
        'reciprocal_a': None,
        'reciprocal_b': None,
        'reciprocal_c': None,
        'phi_deg': None,
    }

    with open(trace_path, 'r') as f:
        for line in f:
            line = line.strip()

            # Spindle axis (PyTorch and C have different labels)
            if 'spindle_axis' in line or 'TRACE_C: spindle_vector' in line:
                if vec := parse_vector(line, 'spindle_axis'):
                    data['spindle_axis'] = vec
                elif vec := parse_vector(line, 'TRACE_C: spindle_vector'):
                    data['spindle_axis'] = vec

            # Cell parameters
            if 'cell_a' in line or 'TRACE_C: cell_a' in line:
                match = re.search(r'(cell_a|TRACE_C: cell_a)\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)', line)
                if match:
                    data['cell_params']['a'] = float(match.group(2))

            if 'cell_b' in line or 'TRACE_C: cell_b' in line:
                match = re.search(r'(cell_b|TRACE_C: cell_b)\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)', line)
                if match:
                    data['cell_params']['b'] = float(match.group(2))

            if 'cell_c' in line or 'TRACE_C: cell_c' in line:
                match = re.search(r'(cell_c|TRACE_C: cell_c)\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)', line)
                if match:
                    data['cell_params']['c'] = float(match.group(2))

            if 'cell_alpha' in line or 'TRACE_C: alpha' in line:
                match = re.search(r'(cell_alpha|TRACE_C: alpha)\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)', line)
                if match:
                    data['cell_params']['alpha'] = float(match.group(2))

            if 'cell_beta' in line or 'TRACE_C: beta' in line:
                match = re.search(r'(cell_beta|TRACE_C: beta)\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)', line)
                if match:
                    data['cell_params']['beta'] = float(match.group(2))

            if 'cell_gamma' in line or 'TRACE_C: gamma' in line:
                match = re.search(r'(cell_gamma|TRACE_C: gamma)\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)', line)
                if match:
                    data['cell_params']['gamma'] = float(match.group(2))

            # Phi angle
            if 'phi_deg' in line or 'TRACE_C: phi' in line:
                match = re.search(r'(phi_deg|TRACE_C: phi)\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)', line)
                if match:
                    data['phi_deg'] = float(match.group(2))

            # Rotated real-space vectors
            if vec := parse_vector(line, 'rot_a'):
                data['rot_a'] = vec
            elif vec := parse_vector(line, 'TRACE_C: rot_a'):
                data['rot_a'] = vec

            if vec := parse_vector(line, 'rot_b'):
                data['rot_b'] = vec
            elif vec := parse_vector(line, 'TRACE_C: rot_b'):
                data['rot_b'] = vec

            if vec := parse_vector(line, 'rot_c'):
                data['rot_c'] = vec
            elif vec := parse_vector(line, 'TRACE_C: rot_c'):
                data['rot_c'] = vec

            # Reciprocal vectors
            if vec := parse_vector(line, 'reciprocal_a'):
                data['reciprocal_a'] = vec
            elif vec := parse_vector(line, 'TRACE_C: a*'):
                data['reciprocal_a'] = vec

            if vec := parse_vector(line, 'reciprocal_b'):
                data['reciprocal_b'] = vec
            elif vec := parse_vector(line, 'TRACE_C: b*'):
                data['reciprocal_b'] = vec

            if vec := parse_vector(line, 'reciprocal_c'):
                data['reciprocal_c'] = vec
            elif vec := parse_vector(line, 'TRACE_C: c*'):
                data['reciprocal_c'] = vec

    return data


def main():
    parser = argparse.ArgumentParser(description='Spindle-axis and volume probe for CLI-FLAGS-003 Phase L3g')
    parser.add_argument('--trace', required=True, type=Path, help='PyTorch trace log path')
    parser.add_argument('--ctrace', required=True, type=Path, help='C trace log path')
    parser.add_argument('--out', required=True, type=Path, help='Output audit log path')
    args = parser.parse_args()

    # Parse traces
    py_data = parse_trace(args.trace)
    c_data = parse_trace(args.ctrace)

    # Open output file
    out = args.out
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("Spindle-Axis & Volume Audit for CLI-FLAGS-003 Phase L3g\n")
        f.write("=" * 80 + "\n\n")

        # Spindle axis comparison
        f.write("## Spindle-Axis Comparison\n\n")

        if py_data['spindle_axis'] and c_data['spindle_axis']:
            py_spindle = py_data['spindle_axis']
            c_spindle = c_data['spindle_axis']
            py_norm = compute_norm(py_spindle)
            c_norm = compute_norm(c_spindle)

            f.write(f"PyTorch: ({py_spindle[0]:.15g}, {py_spindle[1]:.15g}, {py_spindle[2]:.15g})\n")
            f.write(f"C:       ({c_spindle[0]:.15g}, {c_spindle[1]:.15g}, {c_spindle[2]:.15g})\n")
            f.write(f"\n")
            f.write(f"PyTorch norm: {py_norm:.15g}\n")
            f.write(f"C norm:       {c_norm:.15g}\n")
            f.write(f"Norm delta:   {py_norm - c_norm:.15g}\n")
            f.write(f"Norm rel err: {abs(py_norm - c_norm) / c_norm * 100:.4f}%\n")
            f.write(f"\n")

            # Component deltas
            dx = py_spindle[0] - c_spindle[0]
            dy = py_spindle[1] - c_spindle[1]
            dz = py_spindle[2] - c_spindle[2]
            f.write(f"Component deltas:\n")
            f.write(f"  ΔX: {dx:.15g} ({abs(dx)/abs(c_spindle[0])*100 if c_spindle[0] != 0 else 0:.4f}%)\n")
            f.write(f"  ΔY: {dy:.15g} ({abs(dy)/abs(c_spindle[1])*100 if c_spindle[1] != 0 else 0:.4f}%)\n")
            f.write(f"  ΔZ: {dz:.15g} ({abs(dz)/abs(c_spindle[2])*100 if c_spindle[2] != 0 else 0:.4f}%)\n")
            f.write(f"\n")

            # Tolerance verdict
            max_norm_delta = 5e-4
            if abs(py_norm - c_norm) <= max_norm_delta:
                f.write(f"✓ PASS: Norm delta within tolerance (≤{max_norm_delta})\n")
            else:
                f.write(f"✗ FAIL: Norm delta exceeds tolerance (>{max_norm_delta})\n")
        else:
            f.write("ERROR: Missing spindle axis data in one or both traces\n")

        f.write("\n" + "=" * 80 + "\n\n")

        # Volume analysis
        f.write("## Volume Analysis\n\n")

        # Check if we have cell parameters and rotation vectors
        py_has_cell = all(k in py_data['cell_params'] for k in ['a', 'b', 'c', 'alpha', 'beta', 'gamma'])
        c_has_cell = all(k in c_data['cell_params'] for k in ['a', 'b', 'c', 'alpha', 'beta', 'gamma'])
        py_has_rot = all(py_data[k] for k in ['rot_a', 'rot_b', 'rot_c'])
        c_has_rot = all(c_data[k] for k in ['rot_a', 'rot_b', 'rot_c'])

        if py_has_cell and py_has_rot:
            # PyTorch volumes
            py_v_formula = compute_volume_formula(
                py_data['cell_params']['a'],
                py_data['cell_params']['b'],
                py_data['cell_params']['c'],
                py_data['cell_params']['alpha'],
                py_data['cell_params']['beta'],
                py_data['cell_params']['gamma']
            )
            py_v_actual = compute_volume_actual(
                py_data['rot_a'],
                py_data['rot_b'],
                py_data['rot_c']
            )

            f.write(f"### PyTorch\n")
            f.write(f"V_formula: {py_v_formula:.15g} Å³\n")
            f.write(f"V_actual:  {py_v_actual:.15g} Å³\n")
            f.write(f"Delta:     {py_v_actual - py_v_formula:.15g} Å³\n")
            f.write(f"Rel err:   {abs(py_v_actual - py_v_formula) / py_v_formula * 100:.6f}%\n")
            f.write(f"\n")
        else:
            f.write("WARNING: Missing PyTorch cell params or rotation vectors\n\n")

        if c_has_cell and c_has_rot:
            # C volumes
            c_v_formula = compute_volume_formula(
                c_data['cell_params']['a'],
                c_data['cell_params']['b'],
                c_data['cell_params']['c'],
                c_data['cell_params']['alpha'],
                c_data['cell_params']['beta'],
                c_data['cell_params']['gamma']
            )
            c_v_actual = compute_volume_actual(
                c_data['rot_a'],
                c_data['rot_b'],
                c_data['rot_c']
            )

            f.write(f"### C Reference\n")
            f.write(f"V_formula: {c_v_formula:.15g} Å³\n")
            f.write(f"V_actual:  {c_v_actual:.15g} Å³\n")
            f.write(f"Delta:     {c_v_actual - c_v_formula:.15g} Å³\n")
            f.write(f"Rel err:   {abs(c_v_actual - c_v_formula) / c_v_formula * 100:.6f}%\n")
            f.write(f"\n")
        else:
            f.write("WARNING: Missing C cell params or rotation vectors\n\n")

        if py_has_cell and c_has_cell and py_has_rot and c_has_rot:
            f.write(f"### Cross-Implementation Comparison\n")
            f.write(f"Δ(V_formula): {py_v_formula - c_v_formula:.15g} Å³ ")
            f.write(f"({abs(py_v_formula - c_v_formula) / c_v_formula * 100:.6f}%)\n")
            f.write(f"Δ(V_actual):  {py_v_actual - c_v_actual:.15g} Å³ ")
            f.write(f"({abs(py_v_actual - c_v_actual) / c_v_actual * 100:.6f}%)\n")
            f.write(f"\n")

            # Tolerance verdict
            max_vol_delta = 1e-6
            v_delta = abs(py_v_actual - c_v_actual)
            if v_delta <= max_vol_delta:
                f.write(f"✓ PASS: V_actual delta within tolerance (≤{max_vol_delta} Å³)\n")
            else:
                f.write(f"✗ FAIL: V_actual delta exceeds tolerance (>{max_vol_delta} Å³)\n")

        f.write("\n" + "=" * 80 + "\n\n")

        # Device/dtype metadata
        f.write("## Execution Metadata\n\n")
        f.write(f"PyTorch trace: {args.trace}\n")
        f.write(f"C trace:       {args.ctrace}\n")

        if py_data.get('phi_deg') is not None:
            f.write(f"Phi angle:     {py_data['phi_deg']:.15g}°\n")

        f.write(f"\n")
        f.write("=" * 80 + "\n")

    print(f"Spindle audit written to {out}")

    # Return exit code based on tolerances
    if py_data['spindle_axis'] and c_data['spindle_axis']:
        py_norm = compute_norm(py_data['spindle_axis'])
        c_norm = compute_norm(c_data['spindle_axis'])
        if abs(py_norm - c_norm) > 5e-4:
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
