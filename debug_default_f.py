#!/usr/bin/env python3
"""Quick debug script to see what's happening with the minimal -default_F test."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import torch
import numpy as np

# Add src to path
sys.path.insert(0, 'src')

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, CrystalShape
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

print("Creating minimal test configuration...")

# Crystal config - simple cubic
crystal_config = CrystalConfig(
    cell_a=100, cell_b=100, cell_c=100,
    cell_alpha=90, cell_beta=90, cell_gamma=90,
    N_cells=(5, 5, 5),
    default_F=100.0,  # This should be returned when no HKL data
    phi_start_deg=0.0,
    osc_range_deg=0.0,
    phi_steps=1,
    mosaic_spread_deg=0.0,
    mosaic_domains=1,
    shape=CrystalShape.SQUARE
)

# Detector config - small for speed
detector_config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=32,
    fpixels=32,
)

# Beam config - default
beam_config = BeamConfig(
    wavelength_A=6.2,
    dmin=0.0,
)

print(f"Crystal config: default_F = {crystal_config.default_F}")
print(f"Detector: {detector_config.spixels}x{detector_config.fpixels}, distance={detector_config.distance_mm}mm")
print(f"Beam: λ={beam_config.wavelength_A}Å, fluence={beam_config.fluence:.3e}")

# Create models
detector = Detector(detector_config)
crystal = Crystal(crystal_config, beam_config=beam_config)

# Verify HKL data is None (no file loaded)
print(f"\nCrystal HKL data: {crystal.hkl_data}")
print(f"Crystal default_F from config: {crystal.config.default_F}")

# Test get_structure_factor directly
print("\nTesting get_structure_factor method:")
h = torch.tensor([1.0, 2.0, 0.0])
k = torch.tensor([0.0, 1.0, 3.0])
l = torch.tensor([0.0, 0.0, 1.0])
F_result = crystal.get_structure_factor(h, k, l)
print(f"  Input: h={h.tolist()}, k={k.tolist()}, l={l.tolist()}")
print(f"  F_result = {F_result}")
print(f"  Expected: all {crystal.config.default_F}")

# Create simulator
print("\nCreating simulator...")
simulator = Simulator(crystal, detector, beam_config=beam_config,
                     device=torch.device('cpu'), dtype=torch.float32)

print("\nRunning simulation...")
intensity = simulator.run()

print(f"\nIntensity statistics:")
print(f"  Shape: {intensity.shape}")
print(f"  Min: {intensity.min().item():.6e}")
print(f"  Max: {intensity.max().item():.6e}")
print(f"  Mean: {intensity.mean().item():.6e}")
print(f"  Non-zero pixels: {(intensity > 0).sum().item()}")

if intensity.max().item() == 0:
    print("\n⚠️  ALL ZEROS - This is the bug!")
else:
    print("\n✓  Got non-zero intensity")
