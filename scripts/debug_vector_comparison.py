#!/usr/bin/env python3
"""Compare the vectors more carefully."""

import numpy as np

# C-code vectors
c_fast = np.array([0.0311947630447082, -0.096650175316428, 0.994829447880333])
c_slow = np.array([-0.228539518954453, -0.969636205471835, -0.0870362988312832])
c_normal = np.array([0.973034724475264, -0.224642766741965, -0.0523359562429438])

# PyTorch vectors
py_fast = np.array([0.31074847, -0.0852831, 0.94665843])
py_slow = np.array([0.00665213, -0.99574703, -0.09188904])
py_normal = np.array([0.9504689, 0.03485167, -0.30885955])

print("Comparing vectors:")
print(f"\nFast axis:")
print(f"  C-code:  {c_fast}")
print(f"  PyTorch: {py_fast}")
print(f"  Ratio:   {py_fast / c_fast}")
print(f"  Difference: {py_fast - c_fast}")

print(f"\nSlow axis:")
print(f"  C-code:  {c_slow}")
print(f"  PyTorch: {py_slow}")
print(f"  Ratio X: {py_slow[0] / c_slow[0] if c_slow[0] != 0 else 'inf'}")
print(f"  Ratio Y: {py_slow[1] / c_slow[1] if c_slow[1] != 0 else 'inf'}")
print(f"  Ratio Z: {py_slow[2] / c_slow[2] if c_slow[2] != 0 else 'inf'}")

print(f"\nNormal axis:")
print(f"  C-code:  {c_normal}")
print(f"  PyTorch: {py_normal}")

# Check if vectors are unit vectors
print(f"\nVector magnitudes:")
print(f"  C-code fast:  {np.linalg.norm(c_fast)}")
print(f"  C-code slow:  {np.linalg.norm(c_slow)}")
print(f"  C-code normal: {np.linalg.norm(c_normal)}")
print(f"  PyTorch fast:  {np.linalg.norm(py_fast)}")
print(f"  PyTorch slow:  {np.linalg.norm(py_slow)}")
print(f"  PyTorch normal: {np.linalg.norm(py_normal)}")

# Check orthogonality
print(f"\nOrthogonality check (should be close to 0):")
print(f"  C-code: fast·slow = {np.dot(c_fast, c_slow)}")
print(f"  C-code: fast·normal = {np.dot(c_fast, c_normal)}")
print(f"  C-code: slow·normal = {np.dot(c_slow, c_normal)}")
print(f"  PyTorch: fast·slow = {np.dot(py_fast, py_slow)}")
print(f"  PyTorch: fast·normal = {np.dot(py_fast, py_normal)}")
print(f"  PyTorch: slow·normal = {np.dot(py_slow, py_normal)}")