#!/usr/bin/env python3
"""
Generate C trace for comparison with PyTorch debug output.

This script runs the C nanoBragg with the exact same parameters as the failing test
and captures the trace output.
"""

import os
import subprocess
import tempfile
from pathlib import Path

def create_identity_matrix(filepath):
    """Create identity orientation matrix."""
    with open(filepath, 'w') as f:
        # Identity matrix in MOSFLM format: a*, b*, c* vectors
        f.write("1.000000000000E-02 0.000000000000E+00 0.000000000000E+00\n")
        f.write("0.000000000000E+00 1.000000000000E-02 0.000000000000E+00\n")
        f.write("0.000000000000E+00 0.000000000000E+00 1.000000000000E-02\n")

def main():
    """Generate C trace."""
    print("🔬 Generating C trace for comparison")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create identity matrix
        matrix_file = tmpdir / "identity.mat"
        create_identity_matrix(matrix_file)

        # C command exactly matching the failing test
        cmd = [
            "./golden_suite_generator/nanoBragg",
            "-default_F", "100.0",
            "-lambda", "1.0",
            "-distance", "100.0",
            "-pixel", "0.1",
            "-detpixels", "64",
            "-Xbeam", "3.25",  # beam center in mm (for 64x64 detector with 0.1mm pixels)
            "-Ybeam", "3.25",
            "-cell", "100.0", "100.0", "100.0", "90.0", "90.0", "90.0",
            "-N", "1",
            "-matrix", str(matrix_file)
        ]

        print(f"Running C command: {' '.join(cmd)}")

        # Run and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

        print("C STDOUT:")
        print(result.stdout)

        print("\nC STDERR:")
        print(result.stderr)

        print(f"\nReturn code: {result.returncode}")

        # Look for output files
        output_files = ["floatimage.bin", "intimage.img", "noiseimage.img"]
        for filename in output_files:
            if os.path.exists(filename):
                import numpy as np
                if filename.endswith('.bin'):
                    # Read float binary
                    data = np.fromfile(filename, dtype=np.float32).reshape(64, 64)
                    print(f"\n{filename} statistics:")
                    print(f"  Max: {data.max():.6e} at position {np.unravel_index(data.argmax(), data.shape)}")
                    print(f"  Min: {data.min():.6e}")
                    print(f"  Value at [34,34]: {data[34,34]:.6e}")
                    print(f"  Value at [33,33]: {data[33,33]:.6e}")

if __name__ == "__main__":
    main()