#!/usr/bin/env python3
"""
Fdump Binary Layout Analysis Tool

Analyzes the structure of Fdump.bin caches to understand discrepancies between
HKL text files and binary cache format. This is evidence-gathering for Phase L1b
of CLI-FLAGS-003.

Usage:
    python scripts/validation/analyze_fdump_layout.py \\
        --hkl scaled.hkl \\
        --fdump reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_*.bin \\
        --out reports/2025-10-cli-flags/phase_l/hkl_parity/layout_analysis.md \\
        --metrics reports/2025-10-cli-flags/phase_l/hkl_parity/index_deltas.json

References:
    - specs/spec-a-core.md §Structure Factors & Fdump
    - golden_suite_generator/nanoBragg.c:2359-2486 (C reference implementation)
    - plans/active/cli-noise-pix0/plan.md Phase L1b
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import argparse
import struct
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
import hashlib


def read_hkl_file(hkl_path):
    """
    Parse HKL text file (h k l F format).

    Returns:
        dict: {(h,k,l): F_value}
        tuple: (h_min, h_max, k_min, k_max, l_min, l_max)
    """
    hkl_dict = {}
    h_vals, k_vals, l_vals = [], [], []

    with open(hkl_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            parts = line.strip().split()
            if len(parts) < 4:
                continue
            try:
                h = int(float(parts[0]))
                k = int(float(parts[1]))
                l = int(float(parts[2]))
                F = float(parts[3])

                hkl_dict[(h, k, l)] = F
                h_vals.append(h)
                k_vals.append(k)
                l_vals.append(l)
            except ValueError as e:
                print(f"Warning: skipping malformed line {line_num}: {line.strip()}", file=sys.stderr)
                continue

    if not h_vals:
        raise ValueError(f"No valid HKL entries found in {hkl_path}")

    bounds = (min(h_vals), max(h_vals), min(k_vals), max(k_vals), min(l_vals), max(l_vals))
    return hkl_dict, bounds


def read_fdump_header(fdump_path):
    """
    Read Fdump.bin header: six integers followed by form feed.

    C Reference (golden_suite_generator/nanoBragg.c:2483):
        fprintf(outfile,"%d %d %d %d %d %d\\n\\f",h_min,h_max,k_min,k_max,l_min,l_max);

    Returns:
        tuple: (h_min, h_max, k_min, k_max, l_min, l_max, header_end_offset)
    """
    with open(fdump_path, 'rb') as f:
        # Read ASCII header (six ints + newline + form feed)
        header_line = b''
        while True:
            byte = f.read(1)
            if not byte:
                raise ValueError("EOF before form feed in Fdump header")
            header_line += byte
            if byte == b'\f':
                break

        header_str = header_line.decode('ascii').strip()
        # Remove form feed
        header_str = header_str.rstrip('\f')

        parts = header_str.split()
        if len(parts) != 6:
            raise ValueError(f"Expected 6 integers in Fdump header, got {len(parts)}: {header_str}")

        h_min, h_max, k_min, k_max, l_min, l_max = map(int, parts)
        header_end_offset = f.tell()

    return h_min, h_max, k_min, k_max, l_min, l_max, header_end_offset


def read_fdump_data(fdump_path, h_min, h_max, k_min, k_max, l_min, l_max, header_offset):
    """
    Read Fdump binary data in C layout order: h (outer) → k → l (inner).

    C Reference (golden_suite_generator/nanoBragg.c:2484-2487):
        for (h0=0; h0<=h_range;h0++) {       // NOTE: <= means 0..h_range inclusive!
            for (k0=0; k0<=k_range;k0++) {   // NOTE: <= means 0..k_range inclusive!
                fwrite(*(*(Fhkl +h0)+k0),sizeof(double),l_range+1,outfile);

    The C code writes (h_range+1) × (k_range+1) slices, each with (l_range+1) doubles.

    Returns:
        dict: {(h,k,l): F_value}
    """
    h_range = h_max - h_min + 1
    k_range = k_max - k_min + 1
    l_range = l_max - l_min + 1

    fdump_dict = {}

    with open(fdump_path, 'rb') as f:
        f.seek(header_offset)

        # Read in C order: h (outer) → k → l (inner)
        # CRITICAL: C uses <= in loops, so we iterate 0..h_range inclusive (h_range+1 iterations)
        for h0 in range(h_range + 1):  # Match C: h0=0; h0<=h_range; h0++
            for k0 in range(k_range + 1):  # Match C: k0=0; k0<=k_range; k0++
                # Read l_range+1 doubles for this (h0, k0) slice
                data = f.read(8 * (l_range + 1))
                if len(data) != 8 * (l_range + 1):
                    raise ValueError(f"Unexpected EOF at h0={h0}, k0={k0}")

                values = struct.unpack(f'{l_range + 1}d', data)

                for l0, F in enumerate(values):
                    h = h_min + h0
                    k = k_min + k0
                    l = l_min + l0
                    # Only store if within original bounds (avoid C's +1 padding edge)
                    if h <= h_max and k <= k_max and l <= l_max:
                        fdump_dict[(h, k, l)] = F

        # Check for surplus data
        surplus = f.read()
        if surplus:
            surplus_count = len(surplus) // 8
            print(f"Warning: {len(surplus)} surplus bytes ({surplus_count} doubles) after expected data", file=sys.stderr)

    return fdump_dict


def analyze_layout(hkl_dict, fdump_dict, hkl_bounds, fdump_bounds):
    """
    Compare HKL and Fdump dictionaries to identify layout discrepancies.

    Returns:
        dict: Analysis metrics including index deltas
    """
    h_min_hkl, h_max_hkl, k_min_hkl, k_max_hkl, l_min_hkl, l_max_hkl = hkl_bounds
    h_min_fd, h_max_fd, k_min_fd, k_max_fd, l_min_fd, l_max_fd = fdump_bounds

    # Collect mismatches
    mismatches = []
    delta_h_counter = Counter()
    delta_k_counter = Counter()
    delta_l_counter = Counter()

    max_delta_examples = 20  # Limit examples for readability

    for (h, k, l), F_hkl in hkl_dict.items():
        if (h, k, l) in fdump_dict:
            F_fd = fdump_dict[(h, k, l)]
            if abs(F_hkl - F_fd) > 1e-6:
                mismatches.append({
                    'hkl': (h, k, l),
                    'F_hkl': F_hkl,
                    'F_fdump': F_fd,
                    'delta_F': F_fd - F_hkl
                })
        else:
            # Try to find this F value somewhere else in Fdump
            found_at = None
            for (h_fd, k_fd, l_fd), F_fd in fdump_dict.items():
                if abs(F_fd - F_hkl) < 1e-6:
                    found_at = (h_fd, k_fd, l_fd)
                    delta_h = h_fd - h
                    delta_k = k_fd - k
                    delta_l = l_fd - l

                    delta_h_counter[delta_h] += 1
                    delta_k_counter[delta_k] += 1
                    delta_l_counter[delta_l] += 1

                    if len(mismatches) < max_delta_examples:
                        mismatches.append({
                            'hkl': (h, k, l),
                            'F_hkl': F_hkl,
                            'found_at': found_at,
                            'delta_h': delta_h,
                            'delta_k': delta_k,
                            'delta_l': delta_l
                        })
                    break

    # Calculate expected vs actual sizes
    h_range_hkl = h_max_hkl - h_min_hkl + 1
    k_range_hkl = k_max_hkl - k_min_hkl + 1
    l_range_hkl = l_max_hkl - l_min_hkl + 1
    expected_grid_size = h_range_hkl * k_range_hkl * l_range_hkl

    h_range_fd = h_max_fd - h_min_fd + 1
    k_range_fd = k_max_fd - k_min_fd + 1
    l_range_fd = l_max_fd - l_min_fd + 1
    # C allocates and writes (h_range+1) × (k_range+1) × (l_range+1)
    actual_grid_size_with_padding = (h_range_fd + 1) * (k_range_fd + 1) * (l_range_fd + 1)
    actual_grid_size = h_range_fd * k_range_fd * l_range_fd

    return {
        'hkl_bounds': hkl_bounds,
        'fdump_bounds': fdump_bounds,
        'hkl_grid_dimensions': (h_range_hkl, k_range_hkl, l_range_hkl),
        'fdump_grid_dimensions': (h_range_fd, k_range_fd, l_range_fd),
        'expected_grid_size': expected_grid_size,
        'actual_grid_size': actual_grid_size,
        'actual_grid_size_with_padding': actual_grid_size_with_padding,
        'hkl_entry_count': len(hkl_dict),
        'fdump_entry_count': len(fdump_dict),
        'mismatch_count': len(mismatches),
        'mismatches': mismatches[:max_delta_examples],  # Truncate for report
        'delta_h_histogram': dict(delta_h_counter.most_common(10)),
        'delta_k_histogram': dict(delta_k_counter.most_common(10)),
        'delta_l_histogram': dict(delta_l_counter.most_common(10)),
    }


def write_markdown_report(analysis, hkl_path, fdump_path, out_path):
    """
    Generate Markdown report documenting Fdump layout findings.
    """
    h_min_hkl, h_max_hkl, k_min_hkl, k_max_hkl, l_min_hkl, l_max_hkl = analysis['hkl_bounds']
    h_min_fd, h_max_fd, k_min_fd, k_max_fd, l_min_fd, l_max_fd = analysis['fdump_bounds']

    h_range_hkl, k_range_hkl, l_range_hkl = analysis['hkl_grid_dimensions']
    h_range_fd, k_range_fd, l_range_fd = analysis['fdump_grid_dimensions']

    with open(out_path, 'w') as f:
        f.write("# Fdump Binary Layout Analysis\n\n")
        f.write("**Phase:** CLI-FLAGS-003 Phase L1b\n")
        f.write("**Purpose:** Characterize binary layout discrepancies between HKL text and Fdump cache\n")
        f.write("**References:**\n")
        f.write("- specs/spec-a-core.md §Structure Factors & Fdump (line 474)\n")
        f.write("- golden_suite_generator/nanoBragg.c:2484-2487 (C writer loop)\n\n")

        f.write("## Input Files\n\n")
        f.write(f"- **HKL:** `{hkl_path}`\n")
        f.write(f"- **Fdump:** `{fdump_path}`\n\n")

        f.write("## Grid Dimensions\n\n")
        f.write("### HKL Text File\n")
        f.write(f"- Bounds: h=[{h_min_hkl}, {h_max_hkl}], k=[{k_min_hkl}, {k_max_hkl}], l=[{l_min_hkl}, {l_max_hkl}]\n")
        f.write(f"- Ranges: h_range={h_range_hkl}, k_range={k_range_hkl}, l_range={l_range_hkl}\n")
        f.write(f"- Expected grid size: {h_range_hkl} × {k_range_hkl} × {l_range_hkl} = {analysis['expected_grid_size']:,} voxels\n")
        f.write(f"- Populated entries: {analysis['hkl_entry_count']:,}\n\n")

        f.write("### Fdump Binary Cache\n")
        f.write(f"- Bounds (header): h=[{h_min_fd}, {h_max_fd}], k=[{k_min_fd}, {k_max_fd}], l=[{l_min_fd}, {l_max_fd}]\n")
        f.write(f"- Ranges: h_range={h_range_fd}, k_range={k_range_fd}, l_range={l_range_fd}\n")
        f.write(f"- Nominal grid size: {h_range_fd} × {k_range_fd} × {l_range_fd} = {analysis['actual_grid_size']:,} voxels\n")
        f.write(f"- **C allocated size:** ({h_range_fd}+1) × ({k_range_fd}+1) × ({l_range_fd}+1) = {analysis['actual_grid_size_with_padding']:,} voxels\n")
        f.write(f"- Entries read (within bounds): {analysis['fdump_entry_count']:,}\n\n")

        # Size discrepancy
        padding_voxels = analysis['actual_grid_size_with_padding'] - analysis['expected_grid_size']
        if padding_voxels != 0:
            f.write(f"**⚠️ Off-by-One Allocation:** C allocates `(h_range+1) × (k_range+1) × (l_range+1)` per lines 2427-2437, creating {padding_voxels:,} padding voxels ({padding_voxels*8:,} bytes).\n\n")

        f.write("## Parity Analysis\n\n")
        f.write(f"- **Total mismatches:** {analysis['mismatch_count']:,}\n")
        f.write(f"- **Parity ratio:** {(1 - analysis['mismatch_count'] / analysis['hkl_entry_count'])*100:.2f}%\n\n")

        if analysis['mismatch_count'] > 0:
            f.write("### Index Delta Histograms\n\n")
            f.write("When an HKL entry's F value is found at a different (h,k,l) in Fdump:\n\n")

            f.write("**Δh (most common offsets):**\n")
            for delta, count in sorted(analysis['delta_h_histogram'].items()):
                f.write(f"- Δh={delta:+d}: {count:,} occurrences\n")
            f.write("\n")

            f.write("**Δk (most common offsets):**\n")
            for delta, count in sorted(analysis['delta_k_histogram'].items()):
                f.write(f"- Δk={delta:+d}: {count:,} occurrences\n")
            f.write("\n")

            f.write("**Δl (most common offsets):**\n")
            for delta, count in sorted(analysis['delta_l_histogram'].items()):
                f.write(f"- Δl={delta:+d}: {count:,} occurrences\n")
            f.write("\n")

            f.write("### Example Mismatches\n\n")
            f.write("First 20 mismatches where F value was found at a different index:\n\n")
            f.write("| HKL Index | F_hkl | Found At (Fdump) | Δh | Δk | Δl |\n")
            f.write("|-----------|-------|------------------|----|----|----|\n")
            for m in analysis['mismatches']:
                if 'found_at' in m:
                    h, k, l = m['hkl']
                    h_fd, k_fd, l_fd = m['found_at']
                    f.write(f"| ({h},{k},{l}) | {m['F_hkl']:.2f} | ({h_fd},{k_fd},{l_fd}) | {m['delta_h']:+d} | {m['delta_k']:+d} | {m['delta_l']:+d} |\n")
            f.write("\n")

        f.write("## Hypotheses\n\n")

        if padding_voxels > 0:
            f.write(f"1. **Grid Over-Allocation (Confirmed):** C code allocates `(h_range+1) × (k_range+1) × (l_range+1)` per lines 2427-2437 and writes all entries via loops `for(h0=0; h0<=h_range; h0++)` (line 2484), creating {padding_voxels:,} padding voxels. These contain zeros from `calloc` and represent indices beyond the HKL bounds.\n\n")

        if analysis['delta_k_histogram']:
            most_common_k = max(analysis['delta_k_histogram'], key=analysis['delta_k_histogram'].get)
            f.write(f"2. **k-axis Permutation:** Most common Δk = {most_common_k:+d} suggests systematic k-index shift.\n\n")

        if analysis['delta_l_histogram']:
            f.write("3. **l-axis Variance:** Variable Δl offsets suggest complex layout permutation or off-by-one indexing.\n\n")

        if analysis['mismatch_count'] > 0 and not analysis['delta_k_histogram']:
            f.write("2. **No Index Permutation Detected:** F values from HKL are not found at different indices in Fdump, suggesting the layout matches but values differ (possibly due to default_F initialization or numerical precision).\n\n")

        f.write("\n## Next Actions (Phase L1c)\n\n")
        f.write("1. Update `src/nanobrag_torch/io/hkl.py::read_fdump()` to match C layout (h→k→l order with +1 padding).\n")
        f.write("2. Update `write_fdump()` to replicate C writer loop exactly.\n")
        f.write("3. Add regression test ensuring `read_hkl_file()` ≡ `read_fdump()` for same input.\n")
        f.write("4. Re-run parity script (Phase L1d) and verify mismatches → 0.\n")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze Fdump binary layout for Phase L1b evidence gathering'
    )
    parser.add_argument('--hkl', required=True, help='HKL text file path')
    parser.add_argument('--fdump', required=True, help='Fdump.bin binary cache path')
    parser.add_argument('--out', required=True, help='Output Markdown report path')
    parser.add_argument('--metrics', required=True, help='Output JSON metrics path')

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.hkl).exists():
        print(f"Error: HKL file not found: {args.hkl}", file=sys.stderr)
        sys.exit(1)

    if not Path(args.fdump).exists():
        print(f"Error: Fdump file not found: {args.fdump}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metrics).parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading HKL file: {args.hkl}")
    hkl_dict, hkl_bounds = read_hkl_file(args.hkl)

    print(f"Reading Fdump header: {args.fdump}")
    h_min, h_max, k_min, k_max, l_min, l_max, header_offset = read_fdump_header(args.fdump)
    fdump_bounds = (h_min, h_max, k_min, k_max, l_min, l_max)

    print(f"Reading Fdump data (header ends at byte {header_offset})")
    fdump_dict = read_fdump_data(args.fdump, h_min, h_max, k_min, k_max, l_min, l_max, header_offset)

    print("Analyzing layout discrepancies")
    analysis = analyze_layout(hkl_dict, fdump_dict, hkl_bounds, fdump_bounds)

    print(f"Writing Markdown report: {args.out}")
    write_markdown_report(analysis, args.hkl, args.fdump, args.out)

    print(f"Writing JSON metrics: {args.metrics}")
    # Serialize metrics (remove non-serializable full mismatch list)
    metrics_export = {k: v for k, v in analysis.items() if k != 'mismatches'}
    metrics_export['mismatch_sample'] = analysis['mismatches'][:5]  # Keep small sample

    with open(args.metrics, 'w') as f:
        json.dump(metrics_export, f, indent=2)

    print(f"\n✅ Analysis complete. Found {analysis['mismatch_count']:,} mismatches out of {analysis['hkl_entry_count']:,} HKL entries.")
    print(f"   Report: {args.out}")
    print(f"   Metrics: {args.metrics}")


if __name__ == '__main__':
    main()
