#!/usr/bin/env python
"""
HKL Parity Validation Script for CLI-FLAGS-003 Phase L1

Compares structure factors loaded by PyTorch and C implementations to ensure
identical HKL grid semantics.

Usage:
    python scripts/validation/compare_structure_factors.py \
        --hkl scaled.hkl \
        --fdump Fdump_scaled_TIMESTAMP.bin \
        --out reports/2025-10-cli-flags/phase_l/hkl_parity/summary.md \
        --metrics reports/2025-10-cli-flags/phase_l/hkl_parity/metrics.json
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

# Set KMP_DUPLICATE_LIB_OK before importing torch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np

# Import HKL I/O utilities
from nanobrag_torch.io.hkl import read_hkl_file, read_fdump


def compute_sha256(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def compare_structure_factors(
    hkl_path: str,
    fdump_path: str,
    device: str = 'cpu',
    dtype_str: str = 'float64'
) -> dict:
    """
    Compare structure factors from HKL file and Fdump binary.

    Args:
        hkl_path: Path to HKL text file
        fdump_path: Path to Fdump binary
        device: PyTorch device ('cpu' or 'cuda')
        dtype_str: Data type for comparison ('float32' or 'float64')

    Returns:
        Dictionary with comparison metrics
    """
    # Convert dtype string to torch dtype
    dtype = torch.float64 if dtype_str == 'float64' else torch.float32
    device_obj = torch.device(device)

    # Load HKL file via PyTorch
    print(f"Loading HKL file: {hkl_path}")
    F_hkl, meta_hkl = read_hkl_file(
        hkl_path,
        default_F=0.0,
        device=device_obj,
        dtype=dtype
    )

    # Load Fdump binary via PyTorch
    print(f"Loading Fdump binary: {fdump_path}")
    F_fdump, meta_fdump = read_fdump(
        fdump_path,
        device=device_obj,
        dtype=dtype
    )

    # Compute SHA256 hashes
    hkl_hash = compute_sha256(hkl_path)
    fdump_hash = compute_sha256(fdump_path)

    # Compare metadata
    metadata_match = (
        meta_hkl['h_min'] == meta_fdump['h_min'] and
        meta_hkl['h_max'] == meta_fdump['h_max'] and
        meta_hkl['k_min'] == meta_fdump['k_min'] and
        meta_hkl['k_max'] == meta_fdump['k_max'] and
        meta_hkl['l_min'] == meta_fdump['l_min'] and
        meta_hkl['l_max'] == meta_fdump['l_max']
    )

    # Compare shapes
    shape_match = F_hkl.shape == F_fdump.shape

    # Compute numerical metrics
    max_abs_diff = torch.max(torch.abs(F_hkl - F_fdump)).item()

    # Relative RMS error
    diff_squared = (F_hkl - F_fdump) ** 2
    mean_squared_diff = torch.mean(diff_squared).item()
    rms_diff = np.sqrt(mean_squared_diff)

    # Compute relative RMS (avoid division by zero)
    mean_squared_hkl = torch.mean(F_hkl ** 2).item()
    if mean_squared_hkl > 0:
        relative_rms = rms_diff / np.sqrt(mean_squared_hkl)
    else:
        relative_rms = float('inf')

    # Count mismatched voxels above tolerance
    tolerance = 1e-6
    mismatches = torch.sum(torch.abs(F_hkl - F_fdump) > tolerance).item()

    # Compute min/max values
    hkl_min = torch.min(F_hkl).item()
    hkl_max = torch.max(F_hkl).item()
    fdump_min = torch.min(F_fdump).item()
    fdump_max = torch.max(F_fdump).item()

    # Build results dictionary
    results = {
        'files': {
            'hkl': hkl_path,
            'fdump': fdump_path,
            'hkl_sha256': hkl_hash,
            'fdump_sha256': fdump_hash
        },
        'metadata': {
            'hkl': meta_hkl,
            'fdump': meta_fdump,
            'match': metadata_match
        },
        'shapes': {
            'hkl': list(F_hkl.shape),
            'fdump': list(F_fdump.shape),
            'match': shape_match
        },
        'numerical': {
            'max_abs_diff': max_abs_diff,
            'rms_diff': rms_diff,
            'relative_rms': relative_rms,
            'mismatches_above_tolerance': mismatches,
            'tolerance': tolerance,
            'hkl_min': hkl_min,
            'hkl_max': hkl_max,
            'fdump_min': fdump_min,
            'fdump_max': fdump_max
        },
        'device': device,
        'dtype': dtype_str
    }

    return results


def generate_markdown_report(results: dict, output_path: str):
    """Generate Markdown summary report."""

    md = f"""# HKL Parity Validation Report

## Summary

Comparison of structure factors loaded from HKL text file and Fdump binary cache.

**Status**: {'✅ PASS' if results['numerical']['max_abs_diff'] <= 1e-6 else '❌ FAIL'}

## Files

- **HKL File**: `{results['files']['hkl']}`
  - SHA256: `{results['files']['hkl_sha256']}`
- **Fdump Binary**: `{results['files']['fdump']}`
  - SHA256: `{results['files']['fdump_sha256']}`

## Metadata Comparison

| Field | HKL | Fdump | Match |
|-------|-----|-------|-------|
| h_min | {results['metadata']['hkl']['h_min']} | {results['metadata']['fdump']['h_min']} | {'✓' if results['metadata']['hkl']['h_min'] == results['metadata']['fdump']['h_min'] else '✗'} |
| h_max | {results['metadata']['hkl']['h_max']} | {results['metadata']['fdump']['h_max']} | {'✓' if results['metadata']['hkl']['h_max'] == results['metadata']['fdump']['h_max'] else '✗'} |
| k_min | {results['metadata']['hkl']['k_min']} | {results['metadata']['fdump']['k_min']} | {'✓' if results['metadata']['hkl']['k_min'] == results['metadata']['fdump']['k_min'] else '✗'} |
| k_max | {results['metadata']['hkl']['k_max']} | {results['metadata']['fdump']['k_max']} | {'✓' if results['metadata']['hkl']['k_max'] == results['metadata']['fdump']['k_max'] else '✗'} |
| l_min | {results['metadata']['hkl']['l_min']} | {results['metadata']['fdump']['l_min']} | {'✓' if results['metadata']['hkl']['l_min'] == results['metadata']['fdump']['l_min'] else '✗'} |
| l_max | {results['metadata']['hkl']['l_max']} | {results['metadata']['fdump']['l_max']} | {'✓' if results['metadata']['hkl']['l_max'] == results['metadata']['fdump']['l_max'] else '✗'} |

**Overall Metadata Match**: {'✅ Yes' if results['metadata']['match'] else '❌ No'}

## Shape Comparison

- **HKL Shape**: {results['shapes']['hkl']}
- **Fdump Shape**: {results['shapes']['fdump']}
- **Match**: {'✅ Yes' if results['shapes']['match'] else '❌ No'}

## Numerical Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Max \\|ΔF\\| | {results['numerical']['max_abs_diff']:.6e} electrons | ≤ 1e-6 | {'✅' if results['numerical']['max_abs_diff'] <= 1e-6 else '❌'} |
| RMS Difference | {results['numerical']['rms_diff']:.6e} electrons | - | - |
| Relative RMS Error | {results['numerical']['relative_rms']:.6e} | ≤ 1e-8 | {'✅' if results['numerical']['relative_rms'] <= 1e-8 else '❌'} |
| Mismatched Voxels | {results['numerical']['mismatches_above_tolerance']} | 0 | {'✅' if results['numerical']['mismatches_above_tolerance'] == 0 else '❌'} |
| Tolerance | {results['numerical']['tolerance']:.6e} | - | - |

## Value Ranges

| Source | Min | Max |
|--------|-----|-----|
| HKL | {results['numerical']['hkl_min']:.6f} | {results['numerical']['hkl_max']:.6f} |
| Fdump | {results['numerical']['fdump_min']:.6f} | {results['numerical']['fdump_max']:.6f} |

## Environment

- **Device**: {results['device']}
- **Dtype**: {results['dtype']}

## Interpretation

"""

    if results['numerical']['max_abs_diff'] <= 1e-6:
        md += """The HKL text file and Fdump binary cache contain **identical structure factors**
to within numerical precision. This confirms that PyTorch and C implementations
ingest the structure factor data identically.

**Conclusion**: HKL parity verified ✅
"""
    else:
        md += f"""**WARNING**: Numerical differences detected between HKL and Fdump data.
Max absolute difference of {results['numerical']['max_abs_diff']:.6e} exceeds
the target tolerance of 1e-6 electrons.

**Action Required**: Investigate source of discrepancy before proceeding with
Phase L2 scaling traces.
"""

    # Write report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(md)

    print(f"\nMarkdown report written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Compare structure factors from HKL file and Fdump binary'
    )
    parser.add_argument('--hkl', required=True, help='Path to HKL text file')
    parser.add_argument('--fdump', required=True, help='Path to Fdump binary')
    parser.add_argument('--out', required=True, help='Output Markdown report path')
    parser.add_argument('--metrics', help='Output JSON metrics path')
    parser.add_argument('--device', default='cpu', help='PyTorch device (cpu/cuda)')
    parser.add_argument('--dtype', default='float64', choices=['float32', 'float64'],
                       help='Data type for comparison')

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.hkl).exists():
        print(f"ERROR: HKL file not found: {args.hkl}", file=sys.stderr)
        sys.exit(1)

    if not Path(args.fdump).exists():
        print(f"ERROR: Fdump binary not found: {args.fdump}", file=sys.stderr)
        sys.exit(1)

    # Run comparison
    print("=" * 80)
    print("HKL Parity Validation Script")
    print("CLI-FLAGS-003 Phase L1")
    print("=" * 80)

    results = compare_structure_factors(
        args.hkl,
        args.fdump,
        device=args.device,
        dtype_str=args.dtype
    )

    # Generate Markdown report
    generate_markdown_report(results, args.out)

    # Optionally save JSON metrics
    if args.metrics:
        metrics_path = Path(args.metrics)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"JSON metrics written to: {metrics_path}")

    # Print summary to console
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"Max |ΔF|:              {results['numerical']['max_abs_diff']:.6e} electrons")
    print(f"Relative RMS Error:    {results['numerical']['relative_rms']:.6e}")
    print(f"Mismatched Voxels:     {results['numerical']['mismatches_above_tolerance']}")
    print(f"Metadata Match:        {'✅ Yes' if results['metadata']['match'] else '❌ No'}")
    print(f"Shape Match:           {'✅ Yes' if results['shapes']['match'] else '❌ No'}")

    if results['numerical']['max_abs_diff'] <= 1e-6:
        print("\n✅ HKL PARITY VERIFIED")
        return 0
    else:
        print("\n❌ HKL PARITY FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
