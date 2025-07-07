#!/usr/bin/env python3
"""Debug script to examine the golden reference data."""

import numpy as np
import torch
from pathlib import Path

def main():
    print("=== Golden Data Analysis ===")
    
    # Load the binary file
    golden_path = Path("tests/golden_data/simple_cubic.bin")
    if not golden_path.exists():
        print(f"Error: {golden_path} not found")
        return
    
    # Load as different data types to understand the format
    print(f"File size: {golden_path.stat().st_size} bytes")
    
    # Try loading as float32 (current assumption)
    data_f32 = np.fromfile(str(golden_path), dtype=np.float32)
    print(f"As float32: {len(data_f32)} values")
    print(f"Shape if 500x500: {data_f32.shape} -> reshape to (500,500)")
    print(f"Range: min={np.min(data_f32):.2e}, max={np.max(data_f32):.2e}")
    print(f"Mean: {np.mean(data_f32):.2e}")
    print(f"Non-zero count: {np.count_nonzero(data_f32)}")
    
    # Show some sample values
    print(f"First 10 values: {data_f32[:10]}")
    print(f"Last 10 values: {data_f32[-10:]}")
    
    # Try loading as float64
    data_f64 = np.fromfile(str(golden_path), dtype=np.float64)
    print(f"\nAs float64: {len(data_f64)} values")
    if len(data_f64) == 250000:  # 500x500
        print(f"Range: min={np.min(data_f64):.2e}, max={np.max(data_f64):.2e}")
    
    # Check if there are any large values when interpreted differently
    data_int32 = np.fromfile(str(golden_path), dtype=np.int32)
    print(f"\nAs int32: {len(data_int32)} values")
    print(f"Range: min={np.min(data_int32)}, max={np.max(data_int32)}")

if __name__ == "__main__":
    main()