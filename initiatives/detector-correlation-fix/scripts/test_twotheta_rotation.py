#!/usr/bin/env python3
"""
Test twotheta rotation implementation.

This script verifies how twotheta rotation is applied around different axes
and compares with manual Rodrigues' rotation formula.
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

from nanobrag_torch.utils.geometry import rotate_around_axis


def rodrigues_rotation(vector, axis, angle):
    """
    Apply Rodrigues' rotation formula manually.
    
    v_rot = v*cos(θ) + (k×v)*sin(θ) + k*(k·v)*(1-cos(θ))
    
    where k is the unit vector along the rotation axis.
    """
    # Normalize axis
    k = axis / np.linalg.norm(axis)
    
    # Apply Rodrigues formula
    v_rot = (vector * np.cos(angle) + 
             np.cross(k, vector) * np.sin(angle) + 
             k * np.dot(k, vector) * (1 - np.cos(angle)))
    
    return v_rot


def test_twotheta_rotation():
    """Compare twotheta rotation implementations."""
    
    print("=" * 60)
    print("TWOTHETA ROTATION TEST")
    print("=" * 60)
    
    # Test parameters
    twotheta_deg = 20.0
    twotheta = np.deg2rad(twotheta_deg)
    
    print(f"\nTwotheta angle: {twotheta_deg}° ({twotheta:.6f} rad)")
    
    # Different axis conventions to test
    axes = {
        "MOSFLM": np.array([0.0, 0.0, -1.0]),
        "XDS": np.array([0.0, 1.0, 0.0]),
        "Alternative": np.array([0.0, 0.0, 1.0]),
        "Custom": np.array([1.0, 1.0, 1.0]) / np.sqrt(3)  # Normalized diagonal
    }
    
    # Test vectors
    test_vectors = {
        "X-axis": np.array([1.0, 0.0, 0.0]),
        "Y-axis": np.array([0.0, 1.0, 0.0]),
        "Z-axis": np.array([0.0, 0.0, 1.0]),
        "Diagonal": np.array([1.0, 1.0, 1.0]) / np.sqrt(3)
    }
    
    results = {}
    
    for axis_name, axis in axes.items():
        print(f"\n{'=' * 40}")
        print(f"Testing axis: {axis_name} = {axis}")
        print("-" * 40)
        
        for vec_name, test_vec in test_vectors.items():
            # PyTorch rotation
            vec_torch = torch.tensor(test_vec, dtype=torch.float64)
            axis_torch = torch.tensor(axis, dtype=torch.float64)
            angle_torch = torch.tensor(twotheta, dtype=torch.float64)
            
            rotated_pytorch = rotate_around_axis(vec_torch, axis_torch, angle_torch).numpy()
            
            # Manual Rodrigues rotation
            rotated_rodrigues = rodrigues_rotation(test_vec, axis, twotheta)
            
            # Compare
            difference = np.linalg.norm(rotated_pytorch - rotated_rodrigues)
            
            print(f"\n{vec_name} vector: {test_vec}")
            print(f"  PyTorch result:   {rotated_pytorch}")
            print(f"  Rodrigues result: {rotated_rodrigues}")
            print(f"  Difference: {difference:.2e}")
            
            # Store results
            key = f"{axis_name}_{vec_name}"
            results[key] = {
                "pytorch": rotated_pytorch,
                "rodrigues": rotated_rodrigues,
                "difference": difference
            }
    
    # Special test: detector basis vectors with MOSFLM convention
    print("\n" + "=" * 60)
    print("DETECTOR BASIS VECTOR ROTATION (MOSFLM)")
    print("-" * 60)
    
    # MOSFLM basis vectors
    fdet_initial = np.array([0.0, 0.0, 1.0])  # Fast axis
    sdet_initial = np.array([0.0, -1.0, 0.0])  # Slow axis
    odet_initial = np.array([1.0, 0.0, 0.0])  # Beam/origin axis
    
    mosflm_axis = np.array([0.0, 0.0, -1.0])
    
    print(f"\nInitial basis vectors:")
    print(f"  fdet (fast): {fdet_initial}")
    print(f"  sdet (slow): {sdet_initial}")
    print(f"  odet (beam): {odet_initial}")
    
    print(f"\nRotating by {twotheta_deg}° around MOSFLM axis {mosflm_axis}:")
    
    for name, vec in [("fdet", fdet_initial), ("sdet", sdet_initial), ("odet", odet_initial)]:
        vec_torch = torch.tensor(vec, dtype=torch.float64)
        axis_torch = torch.tensor(mosflm_axis, dtype=torch.float64)
        angle_torch = torch.tensor(twotheta, dtype=torch.float64)
        
        rotated = rotate_around_axis(vec_torch, axis_torch, angle_torch).numpy()
        
        print(f"\n  {name}: {vec} → {rotated}")
        
        # Verify orthogonality is preserved
        if name == "fdet":
            fdet_rotated = rotated
        elif name == "sdet":
            sdet_rotated = rotated
    
    # Check orthogonality
    dot_product = np.dot(fdet_rotated, sdet_rotated)
    print(f"\nOrthogonality check: fdet·sdet = {dot_product:.2e} (should be ~0)")
    
    # Check handedness
    cross = np.cross(fdet_rotated, sdet_rotated)
    print(f"Handedness check: fdet×sdet = {cross}")
    print(f"Should align with rotated odet (beam direction)")
    
    # Save results
    output_dir = Path(__file__).parent.parent / "results" / "rotation_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "twotheta_rotation_test.txt", "w") as f:
        f.write(f"Twotheta Rotation Test Results\n")
        f.write(f"Angle: {twotheta_deg}°\n\n")
        
        for axis_name in axes:
            f.write(f"\nAxis {axis_name}:\n")
            for vec_name in test_vectors:
                key = f"{axis_name}_{vec_name}"
                f.write(f"  {vec_name}: difference = {results[key]['difference']:.2e}\n")
    
    print(f"\nResults saved to: {output_dir / 'twotheta_rotation_test.txt'}")
    
    # Final verification
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("-" * 60)
    
    all_match = all(r["difference"] < 1e-10 for r in results.values())
    if all_match:
        print("✅ PyTorch rotate_around_axis matches Rodrigues formula")
        print("   Implementation is mathematically correct")
    else:
        print("❌ Discrepancy detected in rotation implementation")
        print("   Further investigation needed!")


if __name__ == "__main__":
    test_twotheta_rotation()