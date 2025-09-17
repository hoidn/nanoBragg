#!/usr/bin/env python3
"""
Compare rotation matrices between C and PyTorch implementations.

This script tests different rotation matrix construction methods and 
composition orders to identify convention differences.
"""

import os
import sys
from pathlib import Path
import numpy as np
import torch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

# Set environment variable for MKL
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.utils.geometry import angles_to_rotation_matrix


def construct_rotation_matrix_xyz(rotx, roty, rotz):
    """Construct rotation matrix using XYZ Euler angles (Rz·Ry·Rx order)."""
    # Rx - rotation around X axis
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(rotx), -np.sin(rotx)],
        [0, np.sin(rotx), np.cos(rotx)]
    ])
    
    # Ry - rotation around Y axis  
    Ry = np.array([
        [np.cos(roty), 0, np.sin(roty)],
        [0, 1, 0],
        [-np.sin(roty), 0, np.cos(roty)]
    ])
    
    # Rz - rotation around Z axis
    Rz = np.array([
        [np.cos(rotz), -np.sin(rotz), 0],
        [np.sin(rotz), np.cos(rotz), 0],
        [0, 0, 1]
    ])
    
    return Rz @ Ry @ Rx


def construct_rotation_matrix_zyx(rotx, roty, rotz):
    """Construct rotation matrix using reverse order (Rx·Ry·Rz)."""
    # Individual matrices same as above
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(rotx), -np.sin(rotx)],
        [0, np.sin(rotx), np.cos(rotx)]
    ])
    
    Ry = np.array([
        [np.cos(roty), 0, np.sin(roty)],
        [0, 1, 0],
        [-np.sin(roty), 0, np.cos(roty)]
    ])
    
    Rz = np.array([
        [np.cos(rotz), -np.sin(rotz), 0],
        [np.sin(rotz), np.cos(rotz), 0],
        [0, 0, 1]
    ])
    
    return Rx @ Ry @ Rz


def test_rotation_matrices():
    """Test individual and composite rotation matrices."""
    
    print("=" * 60)
    print("ROTATION MATRIX COMPARISON TEST")
    print("=" * 60)
    
    # Test angles (in degrees for display, radians for calculation)
    angles_deg = (5.0, 3.0, 2.0)
    rotx = np.deg2rad(angles_deg[0])
    roty = np.deg2rad(angles_deg[1])
    rotz = np.deg2rad(angles_deg[2])
    
    print(f"\nTest angles: rotx={angles_deg[0]}°, roty={angles_deg[1]}°, rotz={angles_deg[2]}°")
    print(f"In radians: rotx={rotx:.6f}, roty={roty:.6f}, rotz={rotz:.6f}")
    
    # PyTorch rotation matrix
    R_pytorch = angles_to_rotation_matrix(
        torch.tensor(rotx, dtype=torch.float64), 
        torch.tensor(roty, dtype=torch.float64), 
        torch.tensor(rotz, dtype=torch.float64)
    ).numpy()
    
    # C-style XYZ composition (standard Euler angles)
    R_xyz = construct_rotation_matrix_xyz(rotx, roty, rotz)
    
    # Alternative ZYX composition
    R_zyx = construct_rotation_matrix_zyx(rotx, roty, rotz)
    
    print("\n" + "=" * 40)
    print("PyTorch rotation matrix:")
    print(R_pytorch)
    
    print("\n" + "=" * 40)
    print("C-style XYZ composition (Rz·Ry·Rx):")
    print(R_xyz)
    
    print("\nDifference from PyTorch:")
    diff_xyz = R_pytorch - R_xyz
    print(diff_xyz)
    print(f"Max absolute difference: {np.abs(diff_xyz).max():.2e}")
    
    print("\n" + "=" * 40)
    print("Alternative ZYX composition (Rx·Ry·Rz):")
    print(R_zyx)
    
    print("\nDifference from PyTorch:")
    diff_zyx = R_pytorch - R_zyx
    print(diff_zyx)
    print(f"Max absolute difference: {np.abs(diff_zyx).max():.2e}")
    
    # Test with a sample vector
    print("\n" + "=" * 40)
    print("VECTOR ROTATION TEST")
    print("-" * 40)
    
    test_vector = np.array([1.0, 0.0, 0.0])
    print(f"Test vector: {test_vector}")
    
    v_pytorch = R_pytorch @ test_vector
    v_xyz = R_xyz @ test_vector
    v_zyx = R_zyx @ test_vector
    
    print(f"\nPyTorch result: {v_pytorch}")
    print(f"XYZ result:     {v_xyz}")
    print(f"ZYX result:     {v_zyx}")
    
    print(f"\nPyTorch vs XYZ difference: {np.linalg.norm(v_pytorch - v_xyz):.2e}")
    print(f"PyTorch vs ZYX difference: {np.linalg.norm(v_pytorch - v_zyx):.2e}")
    
    # Determine which convention PyTorch uses
    print("\n" + "=" * 40)
    print("CONCLUSION")
    print("-" * 40)
    
    if np.allclose(R_pytorch, R_xyz, rtol=1e-10):
        print("✅ PyTorch uses XYZ Euler angles (Rz·Ry·Rx composition)")
    elif np.allclose(R_pytorch, R_zyx, rtol=1e-10):
        print("✅ PyTorch uses ZYX order (Rx·Ry·Rz composition)")
    else:
        print("❌ PyTorch uses a different rotation convention")
        print("   Further investigation needed!")
    
    # Save results for documentation
    output_dir = Path(__file__).parent.parent / "results" / "rotation_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "rotation_matrix_comparison.txt", "w") as f:
        f.write(f"Rotation Matrix Comparison\n")
        f.write(f"Test angles: {angles_deg}\n\n")
        f.write(f"PyTorch matrix:\n{R_pytorch}\n\n")
        f.write(f"XYZ matrix:\n{R_xyz}\n\n")
        f.write(f"Difference: {np.abs(diff_xyz).max():.2e}\n")
    
    print(f"\nResults saved to: {output_dir / 'rotation_matrix_comparison.txt'}")


if __name__ == "__main__":
    test_rotation_matrices()