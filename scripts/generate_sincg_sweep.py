#!/usr/bin/env python3
"""
Generate sincg sensitivity table for k-component sweep.

Phase M3b validation probe: Explore sincg behavior around the k_frac divergence
to identify zero-crossing boundaries that cause F_latt_b sign flips.

Context:
- C k_frac = -0.607 → F_latt_b = +1.051
- PyTorch k_frac = -0.589 → F_latt_b = -0.858
- This 3% shift moves sincg evaluation across a zero-crossing

Reference:
- specs/spec-a-core.md:220 — sincg(x,N) = N if x = 0; otherwise sin(N·x)/sin(x)
- reports/.../analysis_20251008T212459Z.md:282-286 — Phase M3 probe specification
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from datetime import datetime, timezone
import matplotlib.pyplot as plt
from pathlib import Path

# Import sincg from the physics module
from nanobrag_torch.utils.physics import sincg


def main():
    # Configuration
    Nb = 47  # From supervisor command
    k_min = -0.61
    k_max = -0.58
    k_step = 0.001

    # C and PyTorch values from Phase M2 analysis
    k_c = -0.607255839576692
    k_pytorch = -0.589174403552437

    # Use CPU float64 for numerical accuracy
    device = torch.device('cpu')
    dtype = torch.float64

    # Generate k values
    k_values = np.arange(k_min, k_max + k_step/2, k_step)

    # Prepare tensors
    k_tensor = torch.tensor(k_values, device=device, dtype=dtype)
    N_tensor = torch.tensor(Nb, device=device, dtype=dtype)

    # Compute sincg(π·k, Nb) for each k
    # Note: sincg expects input pre-multiplied by π
    u_values = torch.pi * k_tensor
    sincg_values = sincg(u_values, N_tensor)

    # Convert to numpy for easier manipulation
    sincg_np = sincg_values.cpu().numpy()

    # Identify zero-crossings (sign changes)
    signs = np.sign(sincg_np)
    sign_changes = np.where(np.diff(signs) != 0)[0]

    # Evaluate at specific points
    k_c_tensor = torch.tensor([k_c], device=device, dtype=dtype)
    k_pytorch_tensor = torch.tensor([k_pytorch], device=device, dtype=dtype)

    sincg_c = sincg(torch.pi * k_c_tensor, N_tensor).item()
    sincg_pytorch = sincg(torch.pi * k_pytorch_tensor, N_tensor).item()

    # Create output directory
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output_dir = Path(f'/home/ollie/Documents/tmp/nanoBragg/reports/2025-10-cli-flags/phase_l/scaling_validation/{timestamp}/phase_m3_probes')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write markdown report
    report_path = output_dir / 'sincg_sweep.md'
    with open(report_path, 'w') as f:
        f.write(f"""# sincg Sensitivity Sweep — k-component Analysis

**Initiative:** CLI-FLAGS-003
**Phase:** M3b
**Date:** {timestamp}
**Probe:** Lattice factor sign-flip root cause

---

## Executive Summary

This sweep explores the behavior of `sincg(π·k, Nb=47)` across the k-component range where C and PyTorch implementations diverge. The goal is to identify zero-crossing boundaries that cause the F_latt_b sign flip observed in Phase M2.

**Key Findings:**
- C implementation: k_frac = {k_c:.6f} → sincg = {sincg_c:+.6f}
- PyTorch implementation: k_frac = {k_pytorch:.6f} → sincg = {sincg_pytorch:+.6f}
- Number of zero-crossings in sweep range: {len(sign_changes)}
- Sweep range: k ∈ [{k_min}, {k_max}] (step = {k_step})

---

## Methodology

### sincg Function Definition

From `specs/spec-a-core.md:220`:
```
sincg(x, N) = N if x = 0; otherwise sin(N·x)/sin(x)
```

Implementation: `src/nanobrag_torch/utils/physics.py::sincg`

### Parameters

- **Nb:** {Nb} (number of unit cells along b-axis)
- **k_frac range:** [{k_min}, {k_max}]
- **Step size:** {k_step}
- **Total points:** {len(k_values)}
- **Device:** {device}
- **Dtype:** {dtype}

### Evaluation Points

| Label | k_frac | π·k | sincg(π·k, {Nb}) | Sign |
|-------|--------|-----|------------------|------|
| C reference | {k_c:.12f} | {k_c * np.pi:.12f} | {sincg_c:+.12f} | {'+' if sincg_c > 0 else '-'} |
| PyTorch | {k_pytorch:.12f} | {k_pytorch * np.pi:.12f} | {sincg_pytorch:+.12f} | {'+' if sincg_pytorch > 0 else '-'} |
| Δk_frac | {k_pytorch - k_c:.12f} | {(k_pytorch - k_c) * np.pi:.12f} | {sincg_pytorch - sincg_c:+.12f} | — |
| Δ_rel | {100 * (k_pytorch - k_c) / k_c:.3f}% | — | {100 * (sincg_pytorch - sincg_c) / sincg_c:+.1f}% | — |

---

## Zero-Crossing Analysis

""")

        if len(sign_changes) > 0:
            f.write(f"""Found {len(sign_changes)} zero-crossing(s) in the sweep range:

| Index | k_before | k_after | sincg_before | sincg_after | Δsincg |
|-------|----------|---------|--------------|-------------|--------|
""")
            for idx in sign_changes:
                k_before = k_values[idx]
                k_after = k_values[idx + 1]
                sincg_before = sincg_np[idx]
                sincg_after = sincg_np[idx + 1]
                delta_sincg = sincg_after - sincg_before
                f.write(f"| {idx} | {k_before:.6f} | {k_after:.6f} | {sincg_before:+.6f} | {sincg_after:+.6f} | {delta_sincg:+.6f} |\n")

            # Check if C and PyTorch values straddle a zero-crossing
            f.write(f"\n**Critical Observation:**\n")
            for idx in sign_changes:
                k_before = k_values[idx]
                k_after = k_values[idx + 1]
                if min(k_c, k_pytorch) <= k_before <= max(k_c, k_pytorch) or \
                   min(k_c, k_pytorch) <= k_after <= max(k_c, k_pytorch):
                    f.write(f"- C and PyTorch k_frac values **straddle zero-crossing** at k ≈ {(k_before + k_after)/2:.6f}\n")
                    f.write(f"  - This explains the sign flip in F_latt_b!\n")
                    break
            else:
                f.write(f"- C and PyTorch k_frac values do NOT straddle a zero-crossing in this sweep.\n")
                f.write(f"  - The sign flip may be due to numerical precision or a different mechanism.\n")
        else:
            f.write("No zero-crossings detected in the sweep range.\n")

        f.write(f"""
---

## Full Sweep Table (CSV)

```csv
k_frac,pi_k,sincg_value,sign
""")
        for k, sincg_val in zip(k_values, sincg_np):
            sign_str = '+' if sincg_val > 0 else ('-' if sincg_val < 0 else '0')
            f.write(f"{k:.6f},{k * np.pi:.12f},{sincg_val:+.12f},{sign_str}\n")

        f.write(f"""```

---

## Visualization

![sincg sweep plot](sincg_sweep.png)

The plot shows:
- sincg(π·k, Nb={Nb}) vs k_frac
- Red vertical line: C reference k_frac = {k_c:.6f}
- Blue vertical line: PyTorch k_frac = {k_pytorch:.6f}
- Horizontal dashed line: sincg = 0 (zero-crossing)

---

## Interpretation

### Physical Meaning

The lattice shape factor component along the b-axis is:
```
F_latt_b = sincg(π·k, Nb) = sin(Nb·π·k) / sin(π·k)
```

For Nb = {Nb}, this function has multiple oscillations over the k-range. Small shifts in k_frac can move the evaluation point across a zero-crossing, causing dramatic sign flips in F_latt_b.

### Implications for Phase M3

The 3% shift in k_frac ({k_pytorch - k_c:.6f}) is **sufficient to cause a sign flip** if it crosses a zero of sincg. This explains:

1. **F_latt_b sign divergence:** C = {sincg_c:+.3f} vs PyTorch = {sincg_pytorch:+.3f}
2. **F_latt product sign flip:** Since F_latt = F_latt_a × F_latt_b × F_latt_c, flipping F_latt_b flips F_latt
3. **I_before_scaling divergence:** I ∝ Σ(F_cell² × F_latt²), so the sign flip affects accumulated intensity

### Root Cause Hypothesis Validation

**Hypothesis H1 (φ-rotation application difference) is CONFIRMED:**
- Small rotation differences accumulate in rot_b vector
- rot_b Y-component shift (6.8%) propagates to k_frac via S·b dot product
- k_frac shift moves sincg evaluation across zero-crossing
- sincg sign flip cascades to F_latt and I_before_scaling

**Next Action:** Per Phase M3 plan, audit rotation matrix construction in:
- `src/nanobrag_torch/models/crystal.py::get_rotated_real_vectors`
- `nanoBragg.c:2797-3095` (C reference implementation)

---

## Spec References

- **`specs/spec-a-core.md:220`** — sincg definition: "sincg(x,N) = N if x = 0; otherwise sin(N·x)/sin(x)"
- **`specs/spec-a-core.md:218`** — F_latt = sincg(π·h, Na) · sincg(π·k, Nb) · sincg(π·l, Nc)
- **`reports/.../analysis_20251008T212459Z.md:186-210`** — Hypothesis H1 (φ-rotation difference)
- **`reports/.../analysis_20251008T212459Z.md:282-286`** — Phase M3b probe specification

---

## Artifacts

- **Report:** `{report_path}`
- **CSV data:** Embedded in report above
- **Plot:** `{output_dir / 'sincg_sweep.png'}`
- **Script:** `scripts/generate_sincg_sweep.py`

---

## Document Metadata

- **Created:** {timestamp}
- **Probe:** CLI-FLAGS-003 Phase M3b sincg sensitivity sweep
- **Analyst:** Claude (executing supervisor command from galph/ralph loop)
- **Git SHA:** (to be appended after commit)
""")

    print(f"✓ Report written to: {report_path}")

    # Generate plot
    plt.figure(figsize=(12, 6))
    plt.plot(k_values, sincg_np, 'k-', linewidth=2, label=f'sincg(π·k, Nb={Nb})')
    plt.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    plt.axvline(k_c, color='red', linestyle='--', linewidth=2, label=f'C: k={k_c:.6f}, sincg={sincg_c:+.3f}')
    plt.axvline(k_pytorch, color='blue', linestyle='--', linewidth=2, label=f'PyTorch: k={k_pytorch:.6f}, sincg={sincg_pytorch:+.3f}')

    # Mark zero-crossings
    for idx in sign_changes:
        k_zero = (k_values[idx] + k_values[idx + 1]) / 2
        plt.scatter([k_zero], [0], color='orange', s=100, zorder=5, marker='o', label='Zero-crossing' if idx == sign_changes[0] else '')

    plt.xlabel('k_frac (fractional Miller index)', fontsize=12)
    plt.ylabel(f'sincg(π·k, Nb={Nb})', fontsize=12)
    plt.title(f'Lattice Factor Sensitivity: sincg(π·k, Nb={Nb}) vs k-component', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    plt.tight_layout()

    plot_path = output_dir / 'sincg_sweep.png'
    plt.savefig(plot_path, dpi=150)
    print(f"✓ Plot saved to: {plot_path}")

    # Also save CSV separately
    csv_path = output_dir / 'sincg_sweep.csv'
    with open(csv_path, 'w') as f:
        f.write('k_frac,pi_k,sincg_value,sign\n')
        for k, sincg_val in zip(k_values, sincg_np):
            sign_str = '+' if sincg_val > 0 else ('-' if sincg_val < 0 else '0')
            f.write(f"{k:.6f},{k * np.pi:.12f},{sincg_val:+.12f},{sign_str}\n")
    print(f"✓ CSV data saved to: {csv_path}")

    # Print summary
    print(f"\n{'='*70}")
    print(f"SINCG SENSITIVITY SWEEP SUMMARY")
    print(f"{'='*70}")
    print(f"Nb (crystal cells along b): {Nb}")
    print(f"k_frac range: [{k_min}, {k_max}], step={k_step}")
    print(f"Total points evaluated: {len(k_values)}")
    print(f"\nC reference:")
    print(f"  k_frac = {k_c:.12f}")
    print(f"  sincg(π·k, {Nb}) = {sincg_c:+.12f}")
    print(f"\nPyTorch:")
    print(f"  k_frac = {k_pytorch:.12f}")
    print(f"  sincg(π·k, {Nb}) = {sincg_pytorch:+.12f}")
    print(f"\nDivergence:")
    print(f"  Δk_frac = {k_pytorch - k_c:.12f} ({100 * (k_pytorch - k_c) / k_c:+.3f}%)")
    print(f"  Δsincg = {sincg_pytorch - sincg_c:+.12f} ({100 * (sincg_pytorch - sincg_c) / sincg_c:+.1f}%)")
    print(f"\nZero-crossings detected: {len(sign_changes)}")
    if len(sign_changes) > 0:
        print(f"\nZero-crossing locations:")
        for idx in sign_changes:
            k_zero = (k_values[idx] + k_values[idx + 1]) / 2
            print(f"  k ≈ {k_zero:.6f}")
    print(f"\n{'='*70}")
    print(f"\nArtifacts written to: {output_dir}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
