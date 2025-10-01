#!/usr/bin/env python3
"""Quick test to check if removing twotheta improves correlation."""

import os
import sys
import torch
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator

# Set environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Configuration with rotations but NO twotheta
detector_config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=61.2,
    beam_center_f=61.2,
    detector_convention=DetectorConvention.MOSFLM,
    detector_rotx_deg=5.0,
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=0.0,  # NO TWOTHETA
    detector_pivot=DetectorPivot.BEAM,  # Use BEAM pivot when twotheta=0
)

crystal_config = CrystalConfig(
    cell_a=100.0,
    cell_b=100.0,
    cell_c=100.0,
    cell_alpha=90.0,
    cell_beta=90.0,
    cell_gamma=90.0,
    N_cells=(5, 5, 5),
)

beam_config = BeamConfig(
    wavelength_A=6.2,
    N_source_points=1,
    source_distance_mm=10000.0,
    source_size_mm=0.0,
)

# Initialize models
detector = Detector(config=detector_config, device=torch.device("cpu"), dtype=torch.float64)
crystal = Crystal(config=crystal_config, device=torch.device("cpu"), dtype=torch.float64)

# Create and run simulator
simulator = Simulator(detector=detector, crystal=crystal, beam_config=beam_config, device=torch.device("cpu"), dtype=torch.float64)
image = simulator.run()

# Save for inspection
np.save("test_no_twotheta.npy", image.numpy())
print(f"Image saved. Shape: {image.shape}, Min: {image.min():.3e}, Max: {image.max():.3e}")

# Print detector info
print(f"\nDetector basis vectors:")
print(f"  fdet_vec: {detector.fdet_vec.numpy()}")
print(f"  sdet_vec: {detector.sdet_vec.numpy()}")
print(f"  odet_vec: {detector.odet_vec.numpy()}")
print(f"  pix0_vector (Angstroms): {detector.pix0_vector.numpy()}")
print(f"  pix0_vector (meters): {(detector.pix0_vector / 1e10).numpy()}")