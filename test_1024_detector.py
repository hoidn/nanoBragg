#!/usr/bin/env python3
"""
Test with 1024x1024 detector to see if that fixes intensity scaling.
"""

import os
import torch
import numpy as np

# Set the environment variable to prevent MKL conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention
)
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator


def test_1024_detector():
    """Test with 1024x1024 detector like golden data."""
    print("=== TESTING 1024x1024 DETECTOR ===")

    pixel_size = 0.1  # mm
    # For 1024x1024 detector, center is at 512 pixels
    beam_center_mm = 512 * pixel_size  # 51.2mm

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        distance_mm=100.0,
        pixel_size_mm=pixel_size,
        spixels=1024,
        fpixels=1024,
        beam_center_s=beam_center_mm,
        beam_center_f=beam_center_mm,
    )

    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )

    beam_config = BeamConfig(
        wavelength_A=6.2,
        fluence=1e12
    )

    print(f"Detector: {detector_config.spixels}x{detector_config.fpixels}")
    print(f"Beam center: {beam_center_mm}mm")

    # Run simulation
    detector = Detector(detector_config)
    crystal = Crystal(crystal_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    image = simulator.run()

    print(f"\n=== RESULTS ===")
    print(f"Image shape: {image.shape}")
    print(f"Image min: {image.min()}")
    print(f"Image max: {image.max()}")
    print(f"Image mean: {image.mean()}")
    print(f"Image sum: {image.sum()}")

    # Check for significant intensity
    nonzero_count = (image > 1e-10).sum()
    print(f"Non-zero pixels (>1e-10): {nonzero_count}")

    significant_count = (image > 1e-6).sum()
    print(f"Significant pixels (>1e-6): {significant_count}")

    if image.max() > 1e-6:
        # Find peak position
        max_idx = torch.argmax(image)
        peak_s = max_idx // 1024
        peak_f = max_idx % 1024
        print(f"Peak position: ({peak_s}, {peak_f})")
        print(f"Peak value: {image[peak_s, peak_f]}")

        # Test correlation calculation
        print(f"\n=== CORRELATION TEST ===")
        # Simple auto-correlation (should be 1.0)
        img_flat = image.flatten()
        img_norm = (img_flat - img_flat.mean()) / (img_flat.std() + 1e-10)
        correlation = (img_norm * img_norm).mean()
        print(f"Auto-correlation: {correlation}")

        return image
    else:
        print("Still too low intensity!")
        return None


if __name__ == "__main__":
    test_1024_detector()