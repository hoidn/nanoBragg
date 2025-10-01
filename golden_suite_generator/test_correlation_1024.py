#!/usr/bin/env python3
"""Test correlation with the correct 1024x1024 golden data."""

import os
import sys
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import torch

from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.simulator import Simulator
from src.nanobrag_torch.config import DetectorConfig, CrystalConfig

# Load the correct golden data (1024x1024)
golden_data = np.fromfile('golden_suite_generator/floatimage.bin', dtype=np.float32).reshape(1024, 1024)
print(f"Golden data shape: {golden_data.shape}")
print(f"Golden stats: min={golden_data.min():.3e}, max={golden_data.max():.3e}, mean={golden_data.mean():.3e}")

# Create PyTorch simulation with matching parameters
detector_config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=51.2,  # For 1024 detector: 512 pixels * 0.1mm
    beam_center_f=51.2,  # For 1024 detector: 512 pixels * 0.1mm
)

crystal_config = CrystalConfig(
    cell_a=100.0,
    cell_b=100.0, 
    cell_c=100.0,
    cell_alpha=90.0,
    cell_beta=90.0,
    cell_gamma=90.0,
    N_cells=(5, 5, 5),
    default_F=100.0,
    phi_start_deg=0.0,
    osc_range_deg=0.0,
    mosaic_spread_deg=0.0,
)

crystal = Crystal(crystal_config)
detector = Detector(detector_config)
simulator = Simulator(crystal, detector, crystal_config)

# Run simulation
pytorch_image = simulator.run().cpu().numpy()
print(f"\nPyTorch shape: {pytorch_image.shape}")
print(f"PyTorch stats: min={pytorch_image.min():.3e}, max={pytorch_image.max():.3e}, mean={pytorch_image.mean():.3e}")

# Calculate correlation
mask = (pytorch_image > 1e-10) | (golden_data > 1e-10)
if mask.sum() > 0:
    corr = np.corrcoef(pytorch_image.flatten()[mask.flatten()], 
                       golden_data.flatten()[mask.flatten()])[0, 1]
    print(f"\nCorrelation: {corr:.6f}")
    
# Check brightest spots
py_max = np.unravel_index(np.argmax(pytorch_image), pytorch_image.shape)
gold_max = np.unravel_index(np.argmax(golden_data), golden_data.shape)
print(f"\nBrightest pixel - PyTorch: {py_max}, Golden: {gold_max}")
print(f"Shift: ({py_max[0] - gold_max[0]}, {py_max[1] - gold_max[1]}) pixels")

# Check center region
center = 512
window = 10
py_center = pytorch_image[center-window:center+window, center-window:center+window]
gold_center = golden_data[center-window:center+window, center-window:center+window]
print(f"\nCenter region max - PyTorch: {py_center.max():.3e}, Golden: {gold_center.max():.3e}")