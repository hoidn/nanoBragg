#!/usr/bin/env python
"""Summarize correlations from all generated comparisons."""

from pathlib import Path

print("=" * 60)
print("Correlation Summary for AT-PARALLEL Tests")
print("=" * 60)

# Find all summary files
summary_files = sorted(Path("tmp").glob("AT-PARALLEL-*/*/summary.txt"))

for summary_file in summary_files:
    with open(summary_file) as f:
        lines = f.readlines()
        test_suite = lines[0].split(": ")[1].strip()
        scenario = lines[1].split(": ")[1].strip()
        detector_size = lines[2].split(": ")[1].strip()
        correlation = float(lines[-1].split(": ")[1].strip())

        print(f"{test_suite}/{scenario:20s} ({detector_size:12s}): {correlation:.6f}")

# Calculate overall statistics
correlations = []
for summary_file in summary_files:
    with open(summary_file) as f:
        lines = f.readlines()
        correlation = float(lines[-1].split(": ")[1].strip())
        correlations.append(correlation)

if correlations:
    print("\n" + "-" * 60)
    print(f"Overall Statistics:")
    print(f"  Mean correlation: {sum(correlations)/len(correlations):.6f}")
    print(f"  Min correlation:  {min(correlations):.6f}")
    print(f"  Max correlation:  {max(correlations):.6f}")
    print(f"  All above 0.99:   {'✓ Yes' if all(c > 0.99 for c in correlations) else '✗ No'}")
    print(f"  All above 0.95:   {'✓ Yes' if all(c > 0.95 for c in correlations) else '✗ No'}")