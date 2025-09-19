#!/usr/bin/env python3
"""
Test with correct fluence value from C code.
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


def test_correct_fluence():
    """Test with correct fluence value from C code."""
    print("=== TESTING WITH CORRECT FLUENCE ===")

    pixel_size = 0.1  # mm
    # Use 256x256 for faster testing
    beam_center_mm = 128 * pixel_size  # 12.8mm

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        distance_mm=100.0,
        pixel_size_mm=pixel_size,
        spixels=256,
        fpixels=256,
        beam_center_s=beam_center_mm,
        beam_center_f=beam_center_mm,
    )

    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )

    # Test different fluence values
    fluence_values = [
        1e12,  # Original (too low)
        1e18,  # Intermediate
        1e24,  # From C code examples
        125932015286227086360700780544.0  # C code default
    ]

    for fluence in fluence_values:
        print(f"\n--- Testing fluence: {fluence:.2e} ---")

        beam_config = BeamConfig(
            wavelength_A=6.2,
            fluence=fluence
        )

        detector = Detector(detector_config)
        crystal = Crystal(crystal_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        image = simulator.run()

        print(f"Image max: {image.max():.6e}")
        print(f"Image mean: {image.mean():.6e}")

        # Count significant pixels
        significant_count = (image > 1e-6).sum()
        very_significant_count = (image > 1).sum()

        print(f"Pixels > 1e-6: {significant_count}")
        print(f"Pixels > 1: {very_significant_count}")

        if image.max() > 1e-6:
            # Test correlation
            img_flat = image.flatten()
            img_norm = (img_flat - img_flat.mean()) / (img_flat.std() + 1e-10)
            correlation = (img_norm * img_norm).mean()
            print(f"Auto-correlation: {correlation}")

            if image.max() > 1:
                print("✓ This fluence produces reasonable intensities!")
                return fluence, image

    print("None of the fluence values produced reasonable results")
    return None, None


if __name__ == "__main__":
    test_correct_fluence()