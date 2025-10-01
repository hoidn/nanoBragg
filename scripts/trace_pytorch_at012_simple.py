#!/usr/bin/env python3
"""Simple PyTorch trace for AT-PARALLEL-012 comparing final intensity."""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import torch
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot

# Target pixel (slow, fast) = (368, 262)
TARGET_PIXEL_S = 368
TARGET_PIXEL_F = 262

print(f"=== PyTorch Trace for AT-PARALLEL-012 Pixel ({TARGET_PIXEL_S}, {TARGET_PIXEL_F}) ===\n")

# Setup configuration matching C command
crystal_config = CrystalConfig(
    cell_a=70.0, cell_b=80.0, cell_c=90.0,
    cell_alpha=75.0, cell_beta=85.0, cell_gamma=95.0,
    N_cells=(5, 5, 5),
    misset_deg=(-89.968546, -31.328953, 177.753396),
    default_F=100.0
)

detector_config = DetectorConfig(
    spixels=512,
    fpixels=512,
    pixel_size_mm=0.1,
    distance_mm=100.0,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM
)

beam_config = BeamConfig(
    wavelength_A=1.0
)

# Create components
crystal = Crystal(crystal_config)
detector = Detector(detector_config)
simulator = Simulator(crystal, detector, crystal_config, beam_config)

# Get Crystal vectors
print("=== Crystal Vectors ===")
print(f"Reciprocal vectors (1/Å):")
print(f"  a_star = {crystal.a_star.numpy()}")
print(f"  b_star = {crystal.b_star.numpy()}")
print(f"  c_star = {crystal.c_star.numpy()}")

print(f"\\nReal vectors (Å):")
print(f"  a = {crystal.a.numpy()}")
print(f"  b = {crystal.b.numpy()}")
print(f"  c = {crystal.c.numpy()}")

print(f"\\nVolume: {crystal.V:.1f} ų")

# Run simulation
print("\\n=== Running Simulation ===")
pytorch_image = simulator.run().cpu().numpy()

# Get target pixel intensity
py_intensity = pytorch_image[TARGET_PIXEL_S, TARGET_PIXEL_F]

# Load C reference
c_trace_path = Path("reports/2025-09-29-debug-traces-012/c_trace_pixel_368_262.log")
if c_trace_path.exists():
    with open(c_trace_path) as f:
        lines = f.readlines()
    # Extract C intensity from trace
    for line in lines:
        if "I_pixel_final" in line:
            c_intensity = float(line.split()[-1])
            break
else:
    c_intensity = 138.216  # From trace output above

# Compute metrics
print(f"\\n=== COMPARISON ===")
print(f"C final intensity:       {c_intensity:.6f}")
print(f"PyTorch final intensity: {py_intensity:.6f}")
print(f"Difference (Py - C):     {py_intensity - c_intensity:.6f}")
print(f"Ratio (Py/C):            {py_intensity/c_intensity:.6f}")
print(f"Relative error:          {100*(py_intensity - c_intensity)/c_intensity:.3f}%")

# Save summary
summary_path = Path("reports/2025-09-29-debug-traces-012/comparison_summary.txt")
with open(summary_path, "w") as f:
    f.write(f"AT-PARALLEL-012 Pixel ({TARGET_PIXEL_S}, {TARGET_PIXEL_F}) Trace Comparison\\n")
    f.write(f"=" * 60 + "\\n\\n")
    f.write(f"C final intensity:       {c_intensity:.15e}\\n")
    f.write(f"PyTorch final intensity: {py_intensity:.15e}\\n")
    f.write(f"Difference (Py - C):     {py_intensity - c_intensity:.15e}\\n")
    f.write(f"Ratio (Py/C):            {py_intensity/c_intensity:.15e}\\n")
    f.write(f"Relative error:          {100*(py_intensity - c_intensity)/c_intensity:.6f}%\\n")

print(f"\\nSummary saved to: {summary_path}")