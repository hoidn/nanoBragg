#!/usr/bin/env python3
"""Quick test of detector correlation."""

import os
import sys
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, 'scripts')

import numpy as np
from c_reference_runner import CReferenceRunner, compute_agreement_metrics
from src.nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator

# Create configurations
detector_config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=51.2,
    beam_center_f=51.2,
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
)

beam_config = BeamConfig(
    wavelength_A=6.2,
)

# Run PyTorch simulation
detector = Detector(detector_config)
crystal = Crystal(crystal_config)
simulator = Simulator(crystal, detector, crystal_config, beam_config)
pytorch_image = simulator.run().cpu().numpy()

# Run C reference
runner = CReferenceRunner()
c_config = {
    'detector_distance_mm': 100.0,
    'detector_pixel_size_mm': 0.1,
    'beam_center_x_mm': 51.2,
    'beam_center_y_mm': 51.2,
    'detector_pixels': 1024,
}
c_beam_config = {'wavelength_A': 6.2}
c_image = runner.run_simulation('simple_cubic', c_config, c_beam_config)

# Compute correlation
metrics = compute_agreement_metrics(c_image, pytorch_image)
print(f"Correlation: {metrics['correlation']:.4f}")
print(f"RMSE: {metrics['rmse']:.4f}")
print(f"Max Diff: {metrics['max_diff']:.4f}")