#!/usr/bin/env python3
"""Debug script to check source counts."""
import subprocess
import sys
from pathlib import Path

# Test parameters
params = [
    '-mat', 'A.mat',
    '-sourcefile', 'reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt',
    '-default_F', '100',
    '-hdivsteps', '0',
    '-vdivsteps', '0',
    '-dispsteps', '1',
    '-distance', '231.274660',
    '-lambda', '0.9768',
    '-pixel', '0.172',
    '-detpixels_x', '16',
    '-detpixels_y', '16',
    '-oversample', '1',
    '-floatfile', '/tmp/debug.bin',
]

print("="*60)
print("C BINARY OUTPUT")
print("="*60)
result_c = subprocess.run(
    ['./golden_suite_generator/nanoBragg'] + params,
    capture_output=True,
    text=True
)
print(result_c.stdout)
print(result_c.stderr)

print("\n" + "="*60)
print("PYTORCH OUTPUT")
print("="*60)
result_py = subprocess.run(
    [sys.executable, '-m', 'nanobrag_torch'] + params,
    capture_output=True,
    text=True
)
print(result_py.stdout)
print(result_py.stderr)
