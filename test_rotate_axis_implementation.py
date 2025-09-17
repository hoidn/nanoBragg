#!/usr/bin/env python3
"""
Test our rotate_axis implementation against the exact C code logic.
"""

import os
import sys
from pathlib import Path
import torch
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.utils.geometry import rotate_axis as pytorch_rotate_axis

def c_style_rotate_axis(v, axis, phi):
    """
    Direct translation of C code rotate_axis function to PyTorch.
    
    C code:
    double sinphi = sin(phi);
    double cosphi = cos(phi);
    double dot = (axis[1]*v[1]+axis[2]*v[2]+axis[3]*v[3])*(1.0-cosphi);

    temp[1] = axis[1]*dot+v[1]*cosphi+(-axis[3]*v[2]+axis[2]*v[3])*sinphi;
    temp[2] = axis[2]*dot+v[2]*cosphi+(+axis[3]*v[1]-axis[1]*v[3])*sinphi;
    temp[3] = axis[3]*dot+v[3]*cosphi+(-axis[2]*v[1]+axis[1]*v[2])*sinphi;
    """
    # Ensure inputs are tensors
    if not isinstance(v, torch.Tensor):
        v = torch.tensor(v, dtype=torch.float64)
    if not isinstance(axis, torch.Tensor):
        axis = torch.tensor(axis, dtype=torch.float64)
    if not isinstance(phi, torch.Tensor):
        phi = torch.tensor(phi, dtype=torch.float64)
        
    sinphi = torch.sin(phi)
    cosphi = torch.cos(phi)
    
    # dot = (axis[0]*v[0] + axis[1]*v[1] + axis[2]*v[2]) * (1.0 - cosphi)
    dot = torch.sum(axis * v, dim=-1, keepdim=True) * (1.0 - cosphi.unsqueeze(-1))
    
    # Expand dot for each component
    if v.dim() == 1:
        # Single vector case
        temp = torch.zeros_like(v)
        
        temp[0] = axis[0]*dot[0] + v[0]*cosphi + (-axis[2]*v[1] + axis[1]*v[2])*sinphi
        temp[1] = axis[1]*dot[0] + v[1]*cosphi + ( axis[2]*v[0] - axis[0]*v[2])*sinphi
        temp[2] = axis[2]*dot[0] + v[2]*cosphi + (-axis[1]*v[0] + axis[0]*v[1])*sinphi
    else:
        # Handle batch case
        temp = torch.zeros_like(v)
        temp[..., 0] = axis[..., 0]*dot.squeeze(-1) + v[..., 0]*cosphi + (-axis[..., 2]*v[..., 1] + axis[..., 1]*v[..., 2])*sinphi
        temp[..., 1] = axis[..., 1]*dot.squeeze(-1) + v[..., 1]*cosphi + ( axis[..., 2]*v[..., 0] - axis[..., 0]*v[..., 2])*sinphi  
        temp[..., 2] = axis[..., 2]*dot.squeeze(-1) + v[..., 2]*cosphi + (-axis[..., 1]*v[..., 0] + axis[..., 0]*v[..., 1])*sinphi
    
    return temp

def test_rotate_axis_implementations():
    """Test our implementations against each other."""
    print("Testing rotate_axis implementations")
    print("=" * 40)
    
    # Test cases
    test_cases = [
        {
            "name": "twotheta_15deg_negZ",
            "vector": torch.tensor([0.1, 0.05125, -0.05125], dtype=torch.float64),
            "axis": torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64),
            "angle": torch.tensor(15.0 * np.pi / 180.0, dtype=torch.float64)
        },
        {
            "name": "basis_vector_fast",
            "vector": torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64),
            "axis": torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64),
            "angle": torch.tensor(15.0 * np.pi / 180.0, dtype=torch.float64)
        },
        {
            "name": "basis_vector_slow",
            "vector": torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64),
            "axis": torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64),
            "angle": torch.tensor(15.0 * np.pi / 180.0, dtype=torch.float64)
        },
        {
            "name": "basis_vector_normal",
            "vector": torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64),
            "axis": torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64),
            "angle": torch.tensor(15.0 * np.pi / 180.0, dtype=torch.float64)
        },
    ]
    
    for test_case in test_cases:
        print(f"\n🔬 Test case: {test_case['name']}")
        
        # Our current implementation
        pytorch_result = pytorch_rotate_axis(test_case["vector"], test_case["axis"], test_case["angle"])
        
        # C-style implementation
        c_style_result = c_style_rotate_axis(test_case["vector"], test_case["axis"], test_case["angle"])
        
        print(f"   Input vector: {test_case['vector'].numpy()}")
        print(f"   Rotation axis: {test_case['axis'].numpy()}")
        print(f"   Angle (deg): {test_case['angle'].item() * 180.0 / np.pi}")
        print(f"   PyTorch result: {pytorch_result.numpy()}")
        print(f"   C-style result: {c_style_result.numpy()}")
        
        # Compare results
        diff = torch.abs(pytorch_result - c_style_result)
        max_diff = torch.max(diff).item()
        print(f"   Max difference: {max_diff:.2e}")
        
        status = "✅ Match" if max_diff < 1e-12 else "❌ Differ"
        print(f"   Status: {status}")
        
        if max_diff >= 1e-12:
            print(f"   Component differences: {diff.numpy()}")

if __name__ == "__main__":
    test_rotate_axis_implementations()