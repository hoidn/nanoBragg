#!/usr/bin/env python3
"""
Check what the C code actually does with Xbeam and Ybeam parameters.
"""

import os
import tempfile
import subprocess
from pathlib import Path

# Use instrumented binary with absolute path
import sys
project_root = Path(__file__).parent.resolve()
NB_C_BIN = os.getenv("NB_C_BIN", str(project_root / "golden_suite_generator" / "nanoBragg"))

# Simple test case
with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)

    # Create a simple matrix file
    matrix_file = tmpdir / "identity.mat"
    matrix_file.write_text("1 0 0\n0 1 0\n0 0 1\n")

    # Run with explicit Xbeam and Ybeam values
    cmd = [
        NB_C_BIN,
        "-matrix", str(matrix_file),
        "-lambda", "1.0",
        "-N", "1",
        "-cell", "100", "100", "100", "90", "90", "90",
        "-default_F", "100",
        "-distance", "100",
        "-detpixels", "64",
        "-pixel", "0.1",
        "-Xbeam", "3.25",  # This should be fast axis
        "-Ybeam", "3.25",  # This should be slow axis
        "-printout_pixel_fastslow", "33", "33",  # Check pixel 33,33
        "-floatfile", str(tmpdir / "output.bin")
    ]

    print(f"Running C command:")
    print(" ".join(cmd))
    print()

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=tmpdir)

    # Look for relevant output
    for line in result.stdout.split('\n'):
        if 'beam' in line.lower() or 'pixel 33,33' in line:
            print(line)

    # Check stderr for trace output
    for line in result.stderr.split('\n'):
        if 'TRACE_C' in line:
            print(line)