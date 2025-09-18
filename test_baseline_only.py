#!/usr/bin/env python3
"""
Test ONLY the baseline case to check if it should have 99.34% correlation as claimed in PHASE_6_FINAL_REPORT.
"""

import os
import sys
import torch
from pathlib import Path

# Set environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import (
    CrystalConfig,
    DetectorConfig,
    BeamConfig,
    DetectorConvention,
    DetectorPivot,
)

def main():
    """Test baseline detector geometry without any rotations."""
    
    print("Testing Baseline Detector Geometry (No Rotations)")
    print("=" * 60)
    
    # Create configuration for baseline simple_cubic test
    crystal_config = CrystalConfig(
        cell_a=torch.tensor(100.0),
        cell_b=torch.tensor(100.0),
        cell_c=torch.tensor(100.0),
        cell_alpha=torch.tensor(90.0),
        cell_beta=torch.tensor(90.0),
        cell_gamma=torch.tensor(90.0),
        space_group="P1",
        default_f=torch.tensor(100.0),
    )
    
    # Baseline detector config - NO rotations
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=51.25,
        beam_center_f=51.25,
        detector_convention=DetectorConvention.MOSFLM,
        detector_rotx_deg=0.0,   # NO ROTATION
        detector_roty_deg=0.0,   # NO ROTATION
        detector_rotz_deg=0.0,   # NO ROTATION
        detector_twotheta_deg=0.0,  # NO TWOTHETA
        detector_pivot=DetectorPivot.BEAM,
    )
    
    beam_config = BeamConfig(wavelength_angstrom=torch.tensor(6.2))

    print(f"Configuration:")
    print(f"  Crystal: {crystal_config.cell_a}Å cubic cell")
    print(f"  Detector distance: {detector_config.distance_mm} mm")
    print(f"  Beam center: ({detector_config.beam_center_s}, {detector_config.beam_center_f}) mm")
    print(f"  Rotations: ALL ZERO")
    print(f"  Convention: {detector_config.detector_convention}")
    print(f"  Pivot: {detector_config.detector_pivot}")

    # Create and run simulation
    simulator = Simulator(
        crystal_config=crystal_config,
        detector_config=detector_config,
        beam_config=beam_config,
    )
    
    print(f"\nRunning simulation...")
    image = simulator.simulate()
    
    print(f"Generated image shape: {image.shape}")
    print(f"Generated image statistics:")
    print(f"  Min: {image.min():.2e}")
    print(f"  Max: {image.max():.2e}")
    print(f"  Mean: {image.mean():.2e}")
    print(f"  Nonzero pixels: {(image > 0).sum().item()}")
    
    # Save the image
    output_path = "baseline_test_only.npy"
    torch.save(image, output_path)
    print(f"\nSaved image to: {output_path}")
    
    # Print detector geometry values for debugging
    detector = simulator.detector
    print(f"\nDetector Geometry Debug Info:")
    print(f"  Basis vectors:")
    print(f"    fdet_vec: {detector.fdet_vec}")
    print(f"    sdet_vec: {detector.sdet_vec}") 
    print(f"    odet_vec: {detector.odet_vec}")
    print(f"  pix0_vector: {detector.pix0_vector}")
    print(f"  beam_center (mm): ({detector.beam_center_s}, {detector.beam_center_f})")

if __name__ == "__main__":
    main()