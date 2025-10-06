#!/usr/bin/env python3
"""
Analyze scaling factor differences between C and PyTorch implementations.
Part of CLI-FLAGS-003 Phase J.
"""

import sys
import re
from pathlib import Path

def parse_trace(filepath):
    """Extract scaling factors from trace log."""
    factors = {}

    with open(filepath) as f:
        for line in f:
            # Match both TRACE_C: and TRACE_PY: lines
            match = re.match(r'TRACE_(?:C|PY):\s+(\w+)\s+([\d.e+-]+)', line)
            if match:
                key, value = match.groups()
                factors[key] = float(value)

    return factors

def main():
    if len(sys.argv) != 5 or sys.argv[1] != '--c-log' or sys.argv[3] != '--py-log':
        print("Usage: analyze_scaling.py --c-log <c_trace.log> --py-log <py_trace.log>")
        sys.exit(1)

    c_log = Path(sys.argv[2])
    py_log = Path(sys.argv[4])

    c_factors = parse_trace(c_log)
    py_factors = parse_trace(py_log)

    # Key scaling factors in order of application
    keys = [
        'I_before_scaling',
        'steps',
        'r_e_sqr',
        'fluence_photons_per_m2',
        'polar',
        'omega_pixel',
        'I_pixel_final'
    ]

    print("# Scaling Chain Analysis: C vs PyTorch")
    print()
    print("Pixel: (slow=1039, fast=685)")
    print()
    print("## Factor-by-Factor Comparison")
    print()
    print("| Factor | C Value | PyTorch Value | Ratio (Py/C) | Match? |")
    print("|--------|---------|---------------|--------------|--------|")

    first_divergence = None

    for key in keys:
        c_val = c_factors.get(key, 0.0)
        py_val = py_factors.get(key, 0.0)

        if c_val != 0:
            ratio = py_val / c_val
        else:
            ratio = float('inf') if py_val != 0 else 1.0

        # Check if values match within tolerance
        if abs(ratio - 1.0) < 1e-6:
            match = "✅"
        else:
            match = "❌"
            if first_divergence is None:
                first_divergence = (key, c_val, py_val, ratio)

        print(f"| {key} | {c_val:.6e} | {py_val:.6e} | {ratio:.6e} | {match} |")

    print()
    print("## Normalization Formula")
    print()
    print("Expected (from C code):")
    print("```")
    print("I_pixel = (I_before_scaling / steps) * r_e² * fluence * polar * omega")
    print("```")
    print()

    # Calculate step-by-step
    c_steps = [
        ("Start", c_factors.get('I_before_scaling', 0)),
        ("÷ steps", c_factors.get('I_before_scaling', 0) / c_factors.get('steps', 1)),
        ("× r_e²", (c_factors.get('I_before_scaling', 0) / c_factors.get('steps', 1)) * c_factors.get('r_e_sqr', 1)),
        ("× fluence", (c_factors.get('I_before_scaling', 0) / c_factors.get('steps', 1)) * c_factors.get('r_e_sqr', 1) * c_factors.get('fluence_photons_per_m2', 1)),
        ("× polar", (c_factors.get('I_before_scaling', 0) / c_factors.get('steps', 1)) * c_factors.get('r_e_sqr', 1) * c_factors.get('fluence_photons_per_m2', 1) * c_factors.get('polar', 1)),
        ("× omega", c_factors.get('I_pixel_final', 0))
    ]

    py_steps = [
        ("Start", py_factors.get('I_before_scaling', 0)),
        ("÷ steps", py_factors.get('I_before_scaling', 0) / py_factors.get('steps', 1)),
        ("× r_e²", (py_factors.get('I_before_scaling', 0) / py_factors.get('steps', 1)) * py_factors.get('r_e_sqr', 1)),
        ("× fluence", (py_factors.get('I_before_scaling', 0) / py_factors.get('steps', 1)) * py_factors.get('r_e_sqr', 1) * py_factors.get('fluence_photons_per_m2', 1)),
        ("× polar", (py_factors.get('I_before_scaling', 0) / py_factors.get('steps', 1)) * py_factors.get('r_e_sqr', 1) * py_factors.get('fluence_photons_per_m2', 1) * py_factors.get('polar', 1)),
        ("× omega", py_factors.get('I_pixel_final', 0))
    ]

    print("### C Normalization Chain")
    print()
    for step, value in c_steps:
        print(f"- {step}: {value:.6e}")

    print()
    print("### PyTorch Normalization Chain")
    print()
    for step, value in py_steps:
        print(f"- {step}: {value:.6e}")

    print()
    print("## First Divergence")
    print()

    if first_divergence:
        key, c_val, py_val, ratio = first_divergence
        print(f"**Factor:** `{key}`")
        print(f"- C value: {c_val:.12e}")
        print(f"- PyTorch value: {py_val:.12e}")
        print(f"- Ratio (Py/C): {ratio:.6e}")
        print()

        # Specific diagnosis
        if key == 'I_before_scaling':
            print("**Diagnosis:** The lattice structure factor computation diverges before normalization.")
            print("This indicates an issue with `F_latt` calculation (lattice shape factor).")
        elif key == 'polar':
            print("**Diagnosis:** Polarization factor mismatch.")
            print(f"C polar = {c_val:.6f} (Kahn factor applied)")
            print(f"PyTorch polar = {py_val:.6f}")
        elif key == 'omega_pixel':
            print("**Diagnosis:** Solid angle (omega) calculation differs.")
        elif key == 'I_pixel_final':
            print("**Diagnosis:** Final intensity mismatch despite matching intermediate factors.")
            print("Check for application order or missing terms.")
    else:
        print("All scaling factors match within tolerance (< 1e-6 relative error).")

    print()
    print("## Summary")
    print()

    final_ratio = py_factors.get('I_pixel_final', 0) / c_factors.get('I_pixel_final', 1)
    print(f"- Final intensity ratio (Py/C): **{final_ratio:.3e}**")
    print(f"- Matches 124,538× global sum ratio: {'✅' if abs(final_ratio / 124538 - 1.0) < 0.1 else '❌'}")
    print()

    # Write summary to markdown file
    outdir = Path(sys.argv[4]).parent
    with open(outdir / 'scaling_chain.md', 'w') as f:
        f.write("# Scaling Chain Analysis: C vs PyTorch\n\n")
        f.write(f"**Pixel:** (slow=1039, fast=685)\n\n")
        f.write("## Key Findings\n\n")

        if first_divergence:
            key, c_val, py_val, ratio = first_divergence
            f.write(f"**First Divergence:** `{key}`\n")
            f.write(f"- C value: {c_val:.12e}\n")
            f.write(f"- PyTorch value: {py_val:.12e}\n")
            f.write(f"- Ratio (Py/C): {ratio:.6e}\n\n")

        f.write(f"**Final Intensity Ratio (Py/C):** {final_ratio:.3e}\n\n")
        f.write("## Full Factor Comparison\n\n")
        f.write("| Factor | C Value | PyTorch Value | Ratio (Py/C) | Match? |\n")
        f.write("|--------|---------|---------------|--------------|--------|\n")

        for key in keys:
            c_val = c_factors.get(key, 0.0)
            py_val = py_factors.get(key, 0.0)
            ratio = py_val / c_val if c_val != 0 else float('inf')
            match = "✅" if abs(ratio - 1.0) < 1e-6 else "❌"
            f.write(f"| {key} | {c_val:.6e} | {py_val:.6e} | {ratio:.6e} | {match} |\n")

        f.write("\n## Artifacts\n\n")
        f.write(f"- C trace: `{c_log.name}`\n")
        f.write(f"- PyTorch trace: `{py_log.name}`\n")
        f.write(f"- Analysis script: `analyze_scaling.py`\n")

    print(f"Markdown report written to: {outdir / 'scaling_chain.md'}")

if __name__ == '__main__':
    main()
