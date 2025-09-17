#!/usr/bin/env python3
"""Diagnose the correlation issue."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import numpy as np
import torch
from pathlib import Path

# Import our modules
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.simulator import Simulator
from src.nanobrag_torch.config import DetectorConfig, CrystalConfig

# Test 1: Check golden data size
golden_path = Path("tests/golden_data/simple_cubic.bin")
golden_data = np.fromfile(str(golden_path), dtype=np.float32)
print(f"Golden data size: {golden_data.shape[0]} elements")
print(f"This suggests a {int(np.sqrt(golden_data.shape[0]))}x{int(np.sqrt(golden_data.shape[0]))} image")

# Test 2: Run with the exact config from the test
detector_config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=500,
    fpixels=500,
    beam_center_s=25.0,
    beam_center_f=25.0,
)

crystal_config = CrystalConfig(
    phi_start_deg=0.0,
    osc_range_deg=0.0,
    mosaic_spread_deg=0.0,
)

crystal = Crystal()
detector = Detector(detector_config)
simulator = Simulator(crystal, detector, crystal_config)

# Run simulation
pytorch_image = simulator.run().cpu().numpy()
print(f"\nPyTorch image shape: {pytorch_image.shape}")
print(f"PyTorch image stats: min={pytorch_image.min():.3e}, max={pytorch_image.max():.3e}, mean={pytorch_image.mean():.3e}")

# Reshape golden data
golden_image = golden_data.reshape(500, 500)
print(f"Golden image stats: min={golden_image.min():.3e}, max={golden_image.max():.3e}, mean={golden_image.mean():.3e}")

# Calculate correlation
pytorch_flat = pytorch_image.flatten()
golden_flat = golden_image.flatten()

# Remove zeros for correlation (many pixels have no signal)
mask = (pytorch_flat > 1e-10) | (golden_flat > 1e-10)
if mask.sum() > 0:
    corr = np.corrcoef(pytorch_flat[mask], golden_flat[mask])[0, 1]
    print(f"\nCorrelation (non-zero pixels): {corr:.6f}")
else:
    print("\nNo non-zero pixels found!")

# Check if images are shifted
print("\nChecking for spatial shift...")
# Find brightest spot in each image
py_max_idx = np.unravel_index(np.argmax(pytorch_image), pytorch_image.shape)
gold_max_idx = np.unravel_index(np.argmax(golden_image), golden_image.shape)
print(f"PyTorch brightest pixel: {py_max_idx}")
print(f"Golden brightest pixel: {gold_max_idx}")
print(f"Shift: ({py_max_idx[0] - gold_max_idx[0]}, {py_max_idx[1] - gold_max_idx[1]}) pixels")

# Save images for visual inspection
np.save("pytorch_image.npy", pytorch_image)
np.save("golden_image.npy", golden_image)
print("\nSaved images to pytorch_image.npy and golden_image.npy for inspection")