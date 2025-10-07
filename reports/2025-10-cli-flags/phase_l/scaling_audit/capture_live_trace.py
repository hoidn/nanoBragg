#!/usr/bin/env python
"""
Quick script to capture live TRACE_PY output from simulator.
Run with PYTHONPATH=src to use editable install.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import subprocess

# Run the test with pytest but capture the stderr where TRACE_PY goes
cmd = [
    sys.executable, '-m', 'pytest',
    '-s',  # Don't capture output
    'tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics[dtype0-cpu]',
    '--tb=no'  # No traceback on success
]

# Run and capture
result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'})

# Extract TRACE_PY lines from stdout
trace_lines = [line for line in result.stdout.split('\n') if line.startswith('TRACE_PY:')]

if trace_lines:
    output_path = 'reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log'
    with open(output_path, 'w') as f:
        f.write('\n'.join(trace_lines) + '\n')
    print(f"Captured {len(trace_lines)} TRACE_PY lines to {output_path}")
else:
    print("No TRACE_PY output found!")
    print("STDOUT:", result.stdout[:500])
    print("STDERR:", result.stderr[:500])
