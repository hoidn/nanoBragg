#!/usr/bin/env python3
"""
CLI-FLAGS-003 Phase K3e: Compare C vs PyTorch per-φ traces

Identifies the first φ where Δk exceeds tolerance (5e-4) to isolate the φ-grid mismatch.
"""

import json
import sys
from pathlib import Path

def parse_c_trace(log_file):
    """Parse C trace log file."""
    traces = []
    with open(log_file) as f:
        for line in f:
            if line.startswith('TRACE_C_PHI'):
                parts = line.split()
                traces.append({
                    'phi_tic': int(parts[1].split('=')[1]),
                    'phi_deg': float(parts[2].split('=')[1]),
                    'k_frac': float(parts[3].split('=')[1]),
                    'F_latt_b': float(parts[4].split('=')[1]),
                    'F_latt': float(parts[5].split('=')[1]),
                })
    return traces

def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_per_phi_traces.py <pytorch_json> <c_log>")
        sys.exit(1)

    pytorch_file = Path(sys.argv[1])
    c_file = Path(sys.argv[2])
    outdir = pytorch_file.parent

    # Load traces
    with open(pytorch_file) as f:
        py_data = json.load(f)
    py_traces = py_data['traces']

    c_traces = parse_c_trace(c_file)

    # Compare
    print("="*80)
    print("CLI-FLAGS-003 Phase K3e: Per-φ Parity Comparison")
    print("="*80)
    print()
    print(f"PyTorch: {pytorch_file}")
    print(f"C:       {c_file}")
    print()

    print("-"*80)
    print(f"{'φ_tic':<7} {'φ (deg)':<10} {'Δk':<15} {'ΔF_latt_b':<15} {'Status':<10}")
    print("-"*80)

    first_divergence = None
    max_delta_k = 0.0

    for i in range(min(len(py_traces), len(c_traces))):
        py = py_traces[i]
        c = c_traces[i]

        delta_k = abs(py['k_frac'] - c['k_frac'])
        delta_F_b = abs(py['F_latt_b'] - c['F_latt_b'])

        if delta_k > max_delta_k:
            max_delta_k = delta_k

        status = "OK" if delta_k < 5e-4 else "DIVERGE"
        if status == "DIVERGE" and first_divergence is None:
            first_divergence = i

        print(f"{py['phi_tic']:<7} {py['phi_deg']:<10.6f} {delta_k:<15.6e} {delta_F_b:<15.6f} {status:<10}")

    print()
    print("="*80)
    print("Summary")
    print("="*80)
    print()

    if first_divergence is not None:
        print(f"❌ First divergence at φ_tic={first_divergence}")
        print(f"   φ = {py_traces[first_divergence]['phi_deg']:.6f}°")
        print(f"   Δk = {abs(py_traces[first_divergence]['k_frac'] - c_traces[first_divergence]['k_frac']):.6e}")
        print()
        print("Root Cause Analysis:")
        print()
        print("C implementation:")
        print(f"  k_frac @ φ_tic=0: {c_traces[0]['k_frac']:.15f}")
        print(f"  k_frac @ φ_tic=9: {c_traces[9]['k_frac']:.15f}")
        print()
        print("PyTorch implementation:")
        print(f"  k_frac @ φ_tic=0: {py_traces[0]['k_frac']:.15f}")
        print(f"  k_frac @ φ_tic=9: {py_traces[9]['k_frac']:.15f}")
        print()
        print("Hypothesis: The φ sampling grid or rotation calculation differs")
        print("between C and PyTorch, leading to different k_frac values at all φ steps.")
    else:
        print("✅ All φ steps within tolerance (Δk < 5e-4)")
        print(f"   Max Δk = {max_delta_k:.6e}")

    print()

    # Write comparison markdown
    summary_file = outdir / 'comparison_summary.md'
    with open(summary_file, 'w') as f:
        f.write("# CLI-FLAGS-003 Phase K3e: Per-φ Parity Comparison\n\n")
        f.write(f"**PyTorch:** `{pytorch_file.name}`  \n")
        f.write(f"**C:**       `{c_file.name}`  \n\n")

        f.write("## Comparison Table\n\n")
        f.write("| φ_tic | φ (deg) | C k_frac | PyTorch k_frac | Δk | Status |\n")
        f.write("|-------|---------|----------|----------------|-------|--------|\n")
        for i in range(min(len(py_traces), len(c_traces))):
            py = py_traces[i]
            c = c_traces[i]
            delta_k = abs(py['k_frac'] - c['k_frac'])
            status = "✅" if delta_k < 5e-4 else "❌"
            f.write(f"| {py['phi_tic']} | {py['phi_deg']:.6f} | {c['k_frac']:.6f} | "
                   f"{py['k_frac']:.6f} | {delta_k:.6e} | {status} |\n")

        f.write("\n## Summary\n\n")
        if first_divergence is not None:
            f.write(f"**❌ DIVERGENCE DETECTED**\n\n")
            f.write(f"- First divergence: φ_tic={first_divergence} (φ={py_traces[first_divergence]['phi_deg']:.6f}°)\n")
            f.write(f"- Max Δk: {max_delta_k:.6e}\n\n")
            f.write("### Root Cause\n\n")
            f.write("The C and PyTorch implementations compute **different k_frac values** at all φ steps.\n\n")
            f.write("**Evidence:**\n")
            f.write(f"- C k_frac @ φ=0°: `{c_traces[0]['k_frac']:.15f}`\n")
            f.write(f"- PyTorch k_frac @ φ=0°: `{py_traces[0]['k_frac']:.15f}`\n")
            f.write(f"- Δk @ φ=0°: `{abs(py_traces[0]['k_frac'] - c_traces[0]['k_frac']):.6e}`\n\n")
            f.write("This indicates a **fundamental difference** in either:\n")
            f.write("1. The φ rotation matrix calculation\n")
            f.write("2. The base lattice vectors before φ rotation\n")
            f.write("3. The scattering vector S calculation\n\n")
        else:
            f.write(f"**✅ PARITY ACHIEVED**\n\n")
            f.write(f"- Max Δk: {max_delta_k:.6e} (< 5e-4 threshold)\n")

        f.write("\n## Next Actions\n\n")
        if first_divergence is not None:
            f.write("1. Compare base lattice vectors (a, b, c) before φ rotation in both implementations\n")
            f.write("2. Compare scattering vector S calculation\n")
            f.write("3. Verify φ rotation matrix formulation (Rodrigues vs axis-angle)\n")
            f.write("4. Check spindle_axis sign convention\n")
            f.write("5. Proceed to Phase K3f with identified fix\n")
        else:
            f.write("1. Proceed to Phase K3f validation\n")
            f.write("2. Close Phase K3e with success evidence\n")

    print(f"✅ Comparison summary saved to: {summary_file}")
    print()

if __name__ == '__main__':
    main()
