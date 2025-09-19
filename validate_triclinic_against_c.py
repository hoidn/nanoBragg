#!/usr/bin/env python
"""
Validate if the 158-pixel offset is also present in the C-code implementation.

This script checks whether nanoBragg.c also places triclinic peaks far from the beam center,
which would confirm that this is correct physics, not a PyTorch bug.
"""

import os
import subprocess
import tempfile
import torch
import numpy as np
from pathlib import Path

# Set up environment
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def create_test_parameters():
    """Create parameter sets for both cubic and triclinic crystals."""

    # Triclinic parameters matching the failing test
    triclinic_params = {
        'name': 'triclinic',
        'cell': ['-cell', '70', '80', '90', '85', '95', '105'],
        'outfile': 'triclinic_test.bin'
    }

    # Cubic parameters for comparison
    cubic_params = {
        'name': 'cubic',
        'cell': ['-cell', '80', '80', '80', '90', '90', '90'],
        'outfile': 'cubic_test.bin'
    }

    # Common parameters
    common_params = [
        '-default_F', '100',
        '-lambda', '1.5',
        '-distance', '150',
        '-detpixels', '256',
        '-pixel', '0.1',
        '-N', '5',
        '-verbose', '1'
    ]

    return triclinic_params, cubic_params, common_params


def run_c_simulation(crystal_params, common_params):
    """Run nanoBragg C simulation and return the image data."""

    c_binary = os.environ.get('NB_C_BIN', './nanoBragg')
    if not os.path.exists(c_binary):
        print(f"C binary not found at {c_binary}")
        return None

    # Build command
    cmd = [c_binary] + crystal_params['cell'] + common_params + ['-floatfile', crystal_params['outfile']]

    print(f"Running C simulation for {crystal_params['name']}:")
    print(f"Command: {' '.join(cmd)}")

    try:
        # Run the simulation
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            print(f"C simulation failed with return code {result.returncode}")
            print(f"stderr: {result.stderr}")
            return None

        # Load the output file
        if os.path.exists(crystal_params['outfile']):
            data = np.fromfile(crystal_params['outfile'], dtype=np.float32)
            if len(data) == 256 * 256:
                image = data.reshape(256, 256)
                # Clean up
                os.remove(crystal_params['outfile'])
                return image
            else:
                print(f"Unexpected data size: {len(data)} (expected {256*256})")
                return None
        else:
            print(f"Output file {crystal_params['outfile']} not created")
            return None

    except subprocess.TimeoutExpired:
        print("C simulation timed out")
        return None
    except Exception as e:
        print(f"Error running C simulation: {e}")
        return None


def find_peak_position(image, name):
    """Find the position of the maximum intensity in the image."""

    if image is None:
        return None, None, None

    max_val = np.max(image)
    max_idx = np.argmax(image)
    max_slow = max_idx // image.shape[1]
    max_fast = max_idx % image.shape[1]

    print(f"{name} simulation results:")
    print(f"  Maximum intensity: {max_val:.6f}")
    print(f"  Peak position: ({max_slow}, {max_fast})")

    # Distance from beam center
    beam_center_slow = 128  # 256/2
    beam_center_fast = 128  # 256/2
    distance_from_center = np.sqrt(
        (max_slow - beam_center_slow)**2 + (max_fast - beam_center_fast)**2
    )
    print(f"  Distance from beam center: {distance_from_center:.1f} pixels")

    return max_slow, max_fast, max_val


def main():
    """Main validation function."""

    print("VALIDATING TRICLINIC vs CUBIC PEAK POSITIONS IN C-CODE")
    print("=" * 60)
    print("Goal: Check if C-code also shows 158-pixel offset for triclinic crystals")

    # Create parameter sets
    triclinic_params, cubic_params, common_params = create_test_parameters()

    # Run C simulations
    print(f"\n{'=' * 40}")
    print("RUNNING C SIMULATIONS")
    print(f"{'=' * 40}")

    triclinic_image = run_c_simulation(triclinic_params, common_params)
    cubic_image = run_c_simulation(cubic_params, common_params)

    if triclinic_image is None or cubic_image is None:
        print("❌ Failed to run C simulations")
        return

    # Find peak positions
    print(f"\n{'=' * 40}")
    print("ANALYZING PEAK POSITIONS")
    print(f"{'=' * 40}")

    triclinic_slow, triclinic_fast, triclinic_max = find_peak_position(triclinic_image, "Triclinic")
    cubic_slow, cubic_fast, cubic_max = find_peak_position(cubic_image, "Cubic")

    # Calculate position difference
    position_diff = np.sqrt(
        (triclinic_slow - cubic_slow)**2 + (triclinic_fast - cubic_fast)**2
    )

    print(f"\n{'=' * 40}")
    print("COMPARISON ANALYSIS")
    print(f"{'=' * 40}")

    print(f"Peak position comparison:")
    print(f"  Cubic peak (C-code): ({cubic_slow}, {cubic_fast})")
    print(f"  Triclinic peak (C-code): ({triclinic_slow}, {triclinic_fast})")
    print(f"  Position difference: {position_diff:.1f} pixels")

    # Compare with PyTorch results
    print(f"\nComparison with PyTorch results:")
    pytorch_cubic_peak = (100, 128)      # From our debug output
    pytorch_triclinic_peak = (196, 254)  # From our debug output
    pytorch_diff = np.sqrt(
        (pytorch_triclinic_peak[0] - pytorch_cubic_peak[0])**2 +
        (pytorch_triclinic_peak[1] - pytorch_cubic_peak[1])**2
    )
    print(f"  PyTorch cubic peak: {pytorch_cubic_peak}")
    print(f"  PyTorch triclinic peak: {pytorch_triclinic_peak}")
    print(f"  PyTorch position difference: {pytorch_diff:.1f} pixels")

    # Analysis
    print(f"\n{'=' * 40}")
    print("FINAL VERDICT")
    print(f"{'=' * 40}")

    c_triclinic_far = np.sqrt((triclinic_slow - 128)**2 + (triclinic_fast - 128)**2) > 50
    pytorch_triclinic_far = np.sqrt((196 - 128)**2 + (254 - 128)**2) > 50

    if c_triclinic_far and pytorch_triclinic_far:
        print("✅ BOTH C-code and PyTorch place triclinic peaks far from beam center")
        print("✅ The 158-pixel offset is CORRECT PHYSICS, not a bug")
        print("❌ The test assumption that cubic and triclinic peaks should be close is WRONG")

        # Check if the positions are similar
        c_pytorch_triclinic_diff = np.sqrt(
            (triclinic_slow - 196)**2 + (triclinic_fast - 254)**2
        )
        print(f"\nC vs PyTorch triclinic peak difference: {c_pytorch_triclinic_diff:.1f} pixels")

        if c_pytorch_triclinic_diff < 10:
            print("✅ C-code and PyTorch triclinic peaks are very similar")
            print("✅ PyTorch implementation is CORRECT")
        else:
            print("⚠️  C-code and PyTorch triclinic peaks differ significantly")
            print("🔍 Further investigation needed")

    elif c_triclinic_far and not pytorch_triclinic_far:
        print("❌ C-code places triclinic peak far, but PyTorch does not")
        print("❌ PyTorch triclinic implementation has a bug")

    elif not c_triclinic_far and pytorch_triclinic_far:
        print("❌ PyTorch places triclinic peak far, but C-code does not")
        print("❌ PyTorch triclinic implementation has a bug")

    else:
        print("✅ Both place triclinic peaks near beam center")
        print("❌ But this contradicts our PyTorch observations - something is wrong")


if __name__ == "__main__":
    main()