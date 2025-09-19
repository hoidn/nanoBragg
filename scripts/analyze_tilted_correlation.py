#!/usr/bin/env python3
"""Analyze the poor correlation in tilted detector case."""

import os
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.debug_correlation_outliers import analyze_correlation_outliers

# Set environment
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Load the most recent C reference data
c_reference_file = "golden_suite_generator/c_reference_tilted_trace_params.bin"
if Path(c_reference_file).exists():
    c_data = np.fromfile(c_reference_file, dtype=np.float32).reshape(1024, 1024)
    print(f"Loaded C reference from {c_reference_file}")
else:
    print(f"C reference file {c_reference_file} not found!")
    sys.exit(1)

# Generate PyTorch data
print("\nGenerating PyTorch data...")
import torch
from nanobrag_torch.config import (
    BeamConfig, CrystalConfig, DetectorConfig, 
    DetectorConvention, DetectorPivot
)
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

# Match the configuration
detector_config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=51.2,
    beam_center_f=51.2,
    detector_convention=DetectorConvention.MOSFLM,
    detector_rotx_deg=0.0,
    detector_roty_deg=0.0,
    detector_rotz_deg=0.0,
    detector_twotheta_deg=20.0,
    detector_pivot=DetectorPivot.BEAM,
)

crystal_config = CrystalConfig(
    cell_a=100.0, cell_b=100.0, cell_c=100.0,
    cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
    N_cells=(5, 5, 5),
)

beam_config = BeamConfig(
    wavelength_A=6.2,
    N_source_points=1,
    source_distance_mm=10000.0,
    source_size_mm=0.0,
)

# Create models and run simulation
detector = Detector(config=detector_config, dtype=torch.float64)
crystal = Crystal(config=crystal_config, dtype=torch.float64)
simulator = Simulator(
    crystal=crystal,
    detector=detector,
    beam_config=beam_config,
    dtype=torch.float64,
)

pytorch_data = simulator.run().numpy()
print(f"PyTorch simulation complete: shape {pytorch_data.shape}")

# Analyze correlation issues
print("\n" + "="*60)
print("CORRELATION ANALYSIS")
print("="*60)

fig, corr_all, corr_clean = analyze_correlation_outliers(
    pytorch_data, c_data, "Tilted 20° twotheta"
)

plt.savefig("reports/detector_verification/correlation_outlier_analysis.png", dpi=150)
print("\nSaved analysis to reports/detector_verification/correlation_outlier_analysis.png")

# Additional edge/boundary analysis
print("\n" + "="*60)
print("EDGE ANALYSIS")
print("="*60)

# Check edges specifically (first/last 10 pixels)
edge_mask = np.zeros_like(pytorch_data, dtype=bool)
edge_mask[:10, :] = True
edge_mask[-10:, :] = True
edge_mask[:, :10] = True
edge_mask[:, -10:] = True

interior_mask = ~edge_mask

corr_interior = np.corrcoef(
    pytorch_data[interior_mask].ravel(),
    c_data[interior_mask].ravel()
)[0, 1]

print(f"Correlation (interior only): {corr_interior:.6f}")
print(f"Edge pixels: {np.sum(edge_mask)} ({100*np.sum(edge_mask)/edge_mask.size:.1f}%)")

# Check for scaling differences
scale_factor = np.sum(pytorch_data * c_data) / np.sum(c_data * c_data)
print(f"\nOptimal scale factor (PyTorch/C): {scale_factor:.6f}")

scaled_c_data = c_data * scale_factor
corr_scaled = np.corrcoef(pytorch_data.ravel(), scaled_c_data.ravel())[0, 1]
print(f"Correlation after scaling: {corr_scaled:.6f}")

plt.show()