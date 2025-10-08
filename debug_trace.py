#!/usr/bin/env python
"""Debug wrapper to see what args.out is being set to."""
import sys
import argparse

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--pixel', type=int, nargs=2, required=True)
parser.add_argument('--out', type=str, required=True)
parser.add_argument('--config', type=str, choices=['supervisor'], required=True)
parser.add_argument('--device', type=str, default='cpu')
parser.add_argument('--dtype', type=str, default='float32', choices=['float32', 'float64'])
parser.add_argument('--phi-mode', type=str, default='spec', choices=['spec', 'c-parity'])
args = parser.parse_args()

print(f"DEBUG: sys.argv = {sys.argv}", file=sys.stderr)
print(f"DEBUG: args.out = {repr(args.out)}", file=sys.stderr)
print(f"DEBUG: args.pixel = {args.pixel}", file=sys.stderr)

# Now call the real trace harness
exec(open('reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py').read())
