#!/usr/bin/env python
"""
Generate PyTorch trace for pixel (64,128) in AT-PARALLEL-006 (dist-50mm-lambda-1.0).
This script traces the polarization calculation to find divergence from C code.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import torch
import numpy as np

# Add src to path
sys.path.insert(0, '/home/ollie/Documents/nanoBragg/src')

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, DetectorConvention
from nanobrag_torch.simulator import Simulator

def main():
    # AT-PARALLEL-006 dist-50mm-lambda-1.0 parameters
    detector_config = DetectorConfig(
        distance_mm=50.0,
        pixel_size_mm=0.1,
        spixels=256,
        fpixels=256,
        beam_center_s=12.8 + 0.05,  # MOSFLM convention: +0.5px offset
        beam_center_f=12.8 + 0.05,
        detector_convention=DetectorConvention.MOSFLM
    )

    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(1, 1, 1),
        default_F=100.0,
        mosaic_seed=1
    )

    beam_config = BeamConfig(
        wavelength_A=1.0,
        fluence=1.25932015286227e+29,  # From C trace
        polarization_factor=0.0,  # Kahn factor (0.0 = unpolarized)
        nopolar=False
    )

    # Create components
    detector = Detector(detector_config)
    crystal = Crystal(crystal_config)

    # Create simulator with trace enabled for pixel (64, 128)
    # Note: In (S,F) indexing, slow=64, fast=128
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        beam_config=beam_config,
        debug_config={'trace_pixel': (64, 128)}  # (slow, fast) = (S, F)
    )

    print("=== PyTorch Trace for Pixel (64, 128) - AT-PARALLEL-006 ===", file=sys.stderr)
    print(f"Detector: {detector_config.distance_mm}mm, {detector_config.pixel_size_mm}mm/px, ({detector_config.spixels}x{detector_config.fpixels})", file=sys.stderr)
    print(f"Crystal: {crystal_config.cell_a}Å cubic, N={crystal_config.N_cells}", file=sys.stderr)
    print(f"Beam: λ={beam_config.wavelength_A}Å, fluence={beam_config.fluence:.6e}", file=sys.stderr)
    print("", file=sys.stderr)

    # Run simulation
    image = simulator.run()

    # Get final pixel value
    pixel_value = image[64, 128].item()
    print(f"\nFinal pixel value: {pixel_value:.15e}", file=sys.stderr)
    print(f"C reference value: 3.870247018406600e-02", file=sys.stderr)
    print(f"Ratio (Py/C): {pixel_value / 0.038702470184066:.12f}", file=sys.stderr)

if __name__ == '__main__':
    main()